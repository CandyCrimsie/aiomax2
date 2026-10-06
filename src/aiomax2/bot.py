from __future__ import annotations

import asyncio
import ssl
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import IO, Any

import aiohttp
from pydantic import BaseModel

from aiomax2.client import AiohttpSession, KeyedRateLimiter
from aiomax2.enums import SenderAction, TextFormat, UploadType
from aiomax2.exceptions import BadRequestError, ValidationError
from aiomax2.types import (
    AttachmentRequest,
    AudioAttachmentRequest,
    BotCommand,
    BotCommandsInfo,
    BotInfo,
    CallbackAnswer,
    Chat,
    ChatAdmin,
    ChatAdminsList,
    ChatMember,
    ChatMembersList,
    CommentMessage,
    CommentMessageList,
    FileAttachmentRequest,
    GetPinnedMessageResult,
    GetSubscriptionsResult,
    InlineKeyboardAttachmentRequest,
    Message,
    MessageList,
    NewCommentBody,
    NewMessageBody,
    NewMessageLink,
    PhotoAttachmentRequest,
    PhotoAttachmentRequestPayload,
    SendCommentResult,
    SendMessageResult,
    SimpleQueryResult,
    Subscription,
    UpdateList,
    UploadedInfo,
    UploadEndpoint,
    VideoAttachmentDetails,
    VideoAttachmentRequest,
)


def _dump(value: BaseModel | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", by_alias=True, exclude_none=True)
    return {key: item for key, item in value.items() if item is not None}


def _success(payload: Any) -> bool:
    if payload is None:
        return True
    result = SimpleQueryResult.model_validate(payload)
    return result.success


def _with_reply_markup(
    attachments: list[AttachmentRequest | dict[str, Any]] | None,
    reply_markup: InlineKeyboardAttachmentRequest | None,
) -> list[AttachmentRequest | dict[str, Any]] | None:
    if reply_markup is None:
        return attachments
    if any(
        (
            attachment.type
            if isinstance(attachment, BaseModel)
            else attachment.get("type")
        )
        == "inline_keyboard"
        for attachment in attachments or ()
    ):
        raise ValidationError(
            "reply_markup cannot be combined with an inline_keyboard in attachments"
        )
    return [*(attachments or []), reply_markup]


def _find_token(value: Any) -> str | None:
    if isinstance(value, Mapping):
        token = value.get("token")
        if isinstance(token, str):
            return token
        for nested in value.values():
            found = _find_token(nested)
            if found is not None:
                return found
    elif isinstance(value, list):
        for nested in value:
            found = _find_token(nested)
            if found is not None:
                return found
    return None


class Bot:
    """Typed asynchronous facade over the current MAX Bot API."""

    def __init__(
        self,
        token: str,
        *,
        base_url: str = "https://platform-api2.max.ru",
        timeout: float = 30.0,
        max_retries: int = 3,
        rate_limit: int = 30,
        ssl_context: ssl.SSLContext | None = None,
        ca_file: str | Path | None = None,
        verify_ssl: bool = True,
        session: aiohttp.ClientSession | None = None,
        transport: AiohttpSession | None = None,
        attachment_retries: int = 3,
        attachment_retry_base_delay: float = 0.5,
    ) -> None:
        if attachment_retries < 0:
            raise ValueError("attachment_retries cannot be negative")
        if attachment_retry_base_delay < 0:
            raise ValueError("attachment_retry_base_delay cannot be negative")
        self.token = token
        self.transport = transport or AiohttpSession(
            token,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            rate_limit=rate_limit,
            ssl_context=ssl_context,
            ca_file=ca_file,
            verify_ssl=verify_ssl,
            session=session,
        )
        # Conservative client-side policy: MAX documents 2 ops/sec target
        # limits for these operations, but does not state that all endpoints
        # share one server-side budget. One shared bucket cannot exceed the
        # documented limits, at the cost of throughput in mixed workloads.
        self._target_limiter = KeyedRateLimiter(2, 1.0)
        self._me: BotInfo | None = None
        self.attachment_retries = attachment_retries
        self.attachment_retry_base_delay = attachment_retry_base_delay

    def __repr__(self) -> str:
        suffix = self.token[-4:] if len(self.token) >= 4 else "****"
        return f"Bot(token='***{suffix}')"

    @property
    def id(self) -> int | None:
        return self._me.user_id if self._me is not None else None

    async def __aenter__(self) -> Bot:
        await self.transport.open()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    async def close(self) -> None:
        await self.transport.close()

    async def request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> Any:
        """Call a MAX endpoint directly while retaining transport safeguards."""

        return await self.transport.request(method, path, **kwargs)

    async def _acquire_target_limit(
        self,
        *,
        chat_id: int | None = None,
        user_id: int | None = None,
    ) -> None:
        """Apply aiomax2's conservative per-target operation limit.

        Message and callback shortcuts pass the concrete target. Low-level
        calls that only have a message/callback id share a conservative
        fallback bucket until the caller supplies ``chat_id`` or ``user_id``.
        """

        if chat_id is not None and user_id is not None:
            raise ValidationError("pass at most one of chat_id or user_id")
        if chat_id is not None:
            target = f"chat:{chat_id}"
        elif user_id is not None:
            target = f"user:{user_id}"
        else:
            target = "unknown"
        await self._target_limiter.acquire(target)

    async def _request_with_attachment_retry(
        self,
        method: str,
        path: str,
        *,
        attachments_present: bool,
        chat_id: int | None = None,
        user_id: int | None = None,
        **kwargs: Any,
    ) -> Any:
        """Retry only MAX's explicit, safe ``attachment.not.ready`` response."""

        retry_index = 0
        while True:
            await self._acquire_target_limit(chat_id=chat_id, user_id=user_id)
            try:
                return await self.request(method, path, **kwargs)
            except BadRequestError as error:
                code = (
                    error.payload.get("code")
                    if isinstance(error.payload, Mapping)
                    else None
                )
                if (
                    not attachments_present
                    or code != "attachment.not.ready"
                    or retry_index >= self.attachment_retries
                ):
                    raise
                delay = self.attachment_retry_base_delay * (2**retry_index)
                retry_index += 1
                await asyncio.sleep(delay)

    async def get_my_info(self) -> BotInfo:
        result = BotInfo.model_validate(await self.request("GET", "/me"))
        result.bind(self)
        self._me = result
        return result

    async def edit_my_commands(
        self, commands: Sequence[BotCommand | Mapping[str, Any]] | None
    ) -> list[BotCommand] | None:
        payload = {
            "commands": [
                _dump(command) if isinstance(command, BaseModel) else dict(command)
                for command in commands
            ]
            if commands is not None
            else None
        }
        result = BotCommandsInfo.model_validate(
            await self.request("PATCH", "/me/commands", json=payload)
        )
        return result.commands

    async def get_chat(self, chat_id: int) -> Chat:
        chat = Chat.model_validate(await self.request("GET", f"/chats/{chat_id}"))
        chat.bind(self)
        if chat.pinned_message is not None:
            chat.pinned_message.bind(self)
        return chat

    async def edit_chat(
        self,
        chat_id: int,
        *,
        icon: Mapping[str, Any] | None = None,
        title: str | None = None,
        description: str | None = None,
        pin: str | None = None,
        notify: bool | None = None,
    ) -> Chat:
        payload = {
            "icon": icon,
            "title": title,
            "description": description,
            "pin": pin,
            "notify": notify,
        }
        chat = Chat.model_validate(
            await self.request("PATCH", f"/chats/{chat_id}", json=_dump(payload))
        )
        chat.bind(self)
        return chat

    async def send_action(self, chat_id: int, action: SenderAction | str) -> bool:
        payload = await self.request(
            "POST", f"/chats/{chat_id}/actions", json={"action": str(action)}
        )
        return _success(payload)

    async def get_pinned_message(self, chat_id: int) -> Message | None:
        result = GetPinnedMessageResult.model_validate(
            await self.request("GET", f"/chats/{chat_id}/pin")
        )
        if result.message is not None:
            result.message.bind(self)
        return result.message

    async def pin_message(
        self, chat_id: int, message_id: str, *, notify: bool | None = None
    ) -> bool:
        payload = await self.request(
            "PUT",
            f"/chats/{chat_id}/pin",
            json=_dump({"message_id": message_id, "notify": notify}),
        )
        return _success(payload)

    async def unpin_message(self, chat_id: int) -> bool:
        return _success(await self.request("DELETE", f"/chats/{chat_id}/pin"))

    async def get_membership(self, chat_id: int) -> ChatMember:
        return ChatMember.model_validate(
            await self.request("GET", f"/chats/{chat_id}/members/me")
        )

    async def leave_chat(self, chat_id: int) -> bool:
        return _success(await self.request("DELETE", f"/chats/{chat_id}/members/me"))

    async def get_admins(self, chat_id: int) -> list[ChatAdmin]:
        result = ChatAdminsList.model_validate(
            await self.request("GET", f"/chats/{chat_id}/members/admins")
        )
        return result.admins

    async def set_admins(
        self,
        chat_id: int,
        admins: Sequence[ChatAdmin | Mapping[str, Any]],
    ) -> bool:
        body = {
            "admins": [
                _dump(admin) if isinstance(admin, BaseModel) else dict(admin)
                for admin in admins
            ]
        }
        return _success(
            await self.request("POST", f"/chats/{chat_id}/members/admins", json=body)
        )

    async def revoke_admin(self, chat_id: int, user_id: int) -> bool:
        return _success(
            await self.request("DELETE", f"/chats/{chat_id}/members/admins/{user_id}")
        )

    async def get_members(
        self,
        chat_id: int,
        *,
        user_ids: Sequence[int] | None = None,
        marker: int | None = None,
        count: int | None = None,
    ) -> ChatMembersList:
        return ChatMembersList.model_validate(
            await self.request(
                "GET",
                f"/chats/{chat_id}/members",
                params={"user_ids": user_ids, "marker": marker, "count": count},
            )
        )

    async def remove_member(
        self, chat_id: int, user_id: int, *, block: bool | None = None
    ) -> bool:
        return _success(
            await self.request(
                "DELETE",
                f"/chats/{chat_id}/members",
                params={"user_id": user_id, "block": block},
            )
        )

    async def get_subscriptions(self) -> list[Subscription]:
        result = GetSubscriptionsResult.model_validate(
            await self.request("GET", "/subscriptions")
        )
        return result.subscriptions

    async def subscribe(
        self,
        url: str,
        *,
        secret: str | None = None,
        update_types: Sequence[str] | None = None,
    ) -> bool:
        payload = {
            "url": url,
            "secret": secret,
            "update_types": list(update_types) if update_types is not None else None,
        }
        return _success(
            await self.request("POST", "/subscriptions", json=_dump(payload))
        )

    async def unsubscribe(self, url: str) -> bool:
        return _success(
            await self.request("DELETE", "/subscriptions", params={"url": url})
        )

    async def get_upload_url(self, upload_type: UploadType | str) -> UploadEndpoint:
        return UploadEndpoint.model_validate(
            await self.request("POST", "/uploads", params={"type": str(upload_type)})
        )

    async def upload_media(
        self,
        upload_type: UploadType | str,
        source: str | Path | bytes | IO[bytes],
        *,
        filename: str | None = None,
        content_type: str | None = None,
    ) -> AttachmentRequest:
        """Upload one MAX media file and return a sendable attachment."""

        normalized_type = UploadType(upload_type)
        endpoint = await self.get_upload_url(normalized_type)
        if isinstance(source, (str, Path)):
            path = Path(source)
            file = await asyncio.to_thread(path.open, "rb")
            try:
                response = await self.transport.upload(
                    endpoint.url,
                    file,
                    filename=filename or path.name,
                    content_type=content_type,
                    authorization=normalized_type is UploadType.IMAGE,
                )
            finally:
                await asyncio.to_thread(file.close)
        else:
            if filename is None:
                filename = getattr(source, "name", None)
                if filename is not None:
                    filename = Path(str(filename)).name
            if filename is None:
                raise ValidationError("filename is required for bytes/file objects")
            response = await self.transport.upload(
                endpoint.url,
                source,
                filename=filename,
                content_type=content_type,
                authorization=normalized_type is UploadType.IMAGE,
            )
        token = endpoint.token or _find_token(response)
        if token is None:
            raise ValidationError("MAX upload response did not contain a media token")
        if normalized_type is UploadType.IMAGE:
            return PhotoAttachmentRequest(
                payload=PhotoAttachmentRequestPayload(token=token)
            )
        uploaded = UploadedInfo(token=token)
        if normalized_type is UploadType.VIDEO:
            return VideoAttachmentRequest(payload=uploaded)
        if normalized_type is UploadType.AUDIO:
            return AudioAttachmentRequest(payload=uploaded)
        return FileAttachmentRequest(payload=uploaded)

    async def upload_image(
        self,
        source: str | Path | bytes | IO[bytes],
        *,
        filename: str | None = None,
        content_type: str | None = None,
    ) -> PhotoAttachmentRequest:
        result = await self.upload_media(
            UploadType.IMAGE,
            source,
            filename=filename,
            content_type=content_type,
        )
        assert isinstance(result, PhotoAttachmentRequest)
        return result

    async def upload_video(
        self,
        source: str | Path | bytes | IO[bytes],
        *,
        filename: str | None = None,
        content_type: str | None = None,
    ) -> VideoAttachmentRequest:
        result = await self.upload_media(
            UploadType.VIDEO,
            source,
            filename=filename,
            content_type=content_type,
        )
        assert isinstance(result, VideoAttachmentRequest)
        return result

    async def upload_audio(
        self,
        source: str | Path | bytes | IO[bytes],
        *,
        filename: str | None = None,
        content_type: str | None = None,
    ) -> AudioAttachmentRequest:
        result = await self.upload_media(
            UploadType.AUDIO,
            source,
            filename=filename,
            content_type=content_type,
        )
        assert isinstance(result, AudioAttachmentRequest)
        return result

    async def upload_file(
        self,
        source: str | Path | bytes | IO[bytes],
        *,
        filename: str | None = None,
        content_type: str | None = None,
    ) -> FileAttachmentRequest:
        result = await self.upload_media(
            UploadType.FILE,
            source,
            filename=filename,
            content_type=content_type,
        )
        assert isinstance(result, FileAttachmentRequest)
        return result

    async def get_messages(
        self,
        *,
        chat_id: int | None = None,
        message_ids: Sequence[str] | None = None,
        from_time: int | None = None,
        to_time: int | None = None,
        before: int | None = None,
        after: int | None = None,
        count: int | None = None,
    ) -> list[Message]:
        result = MessageList.model_validate(
            await self.request(
                "GET",
                "/messages",
                params={
                    "chat_id": chat_id,
                    "message_ids": message_ids,
                    "from": from_time,
                    "to": to_time,
                    "before": before,
                    "after": after,
                    "count": count,
                },
            )
        )
        for message in result.messages:
            message.bind(self)
        return result.messages

    async def send_message(
        self,
        text: str | None = None,
        *,
        user_id: int | None = None,
        chat_id: int | None = None,
        attachments: list[AttachmentRequest | dict[str, Any]] | None = None,
        reply_markup: InlineKeyboardAttachmentRequest | None = None,
        link: NewMessageLink | None = None,
        notify: bool | None = None,
        format: TextFormat | str | None = None,
        disable_link_preview: bool | None = None,
    ) -> Message:
        if (user_id is None) == (chat_id is None):
            raise ValidationError("pass exactly one of user_id or chat_id")
        merged_attachments = _with_reply_markup(attachments, reply_markup)
        body = NewMessageBody(
            text=text,
            attachments=merged_attachments,
            link=link,
            notify=notify,
            format=format,
        )
        result = SendMessageResult.model_validate(
            await self._request_with_attachment_retry(
                "POST",
                "/messages",
                attachments_present=bool(merged_attachments),
                chat_id=chat_id,
                user_id=user_id,
                params={
                    "user_id": user_id,
                    "chat_id": chat_id,
                    "disable_link_preview": disable_link_preview,
                },
                json=body.api_dump(),
            )
        )
        return result.message.bind(self)

    async def edit_message(
        self,
        message_id: str,
        *,
        text: str | None = None,
        attachments: list[AttachmentRequest | dict[str, Any]] | None = None,
        reply_markup: InlineKeyboardAttachmentRequest | None = None,
        link: NewMessageLink | None = None,
        notify: bool | None = None,
        format: TextFormat | str | None = None,
        chat_id: int | None = None,
        user_id: int | None = None,
    ) -> bool:
        merged_attachments = _with_reply_markup(attachments, reply_markup)
        body = NewMessageBody(
            text=text,
            attachments=merged_attachments,
            link=link,
            notify=notify,
            format=format,
        )
        return _success(
            await self._request_with_attachment_retry(
                "PUT",
                "/messages",
                attachments_present=bool(merged_attachments),
                chat_id=chat_id,
                user_id=user_id,
                params={"message_id": message_id},
                json=body.api_dump(),
            )
        )

    async def delete_message(
        self,
        message_id: str,
        *,
        chat_id: int | None = None,
        user_id: int | None = None,
    ) -> bool:
        await self._acquire_target_limit(chat_id=chat_id, user_id=user_id)
        return _success(
            await self.request("DELETE", "/messages", params={"message_id": message_id})
        )

    async def get_message(self, message_id: str) -> Message:
        result = Message.model_validate(
            await self.request("GET", f"/messages/{message_id}")
        )
        return result.bind(self)

    async def get_comments(
        self,
        message_id: str,
        *,
        comment_ids: Sequence[str] | None = None,
        before: int | None = None,
        after: int | None = None,
        count: int | None = None,
    ) -> list[CommentMessage]:
        result = CommentMessageList.model_validate(
            await self.request(
                "GET",
                f"/messages/{message_id}/comments",
                params={
                    "comment_ids": comment_ids,
                    "before": before,
                    "after": after,
                    "count": count,
                },
            )
        )
        for comment in result.messages:
            comment.bind(self)
        return result.messages

    async def send_comment(
        self,
        message_id: str,
        text: str | None = None,
        *,
        link: NewMessageLink | None = None,
        notify: bool | None = None,
        format: TextFormat | str | None = None,
        disable_link_preview: bool | None = None,
    ) -> CommentMessage:
        body = NewCommentBody(
            text=text,
            link=link,
            notify=notify,
            format=format,
        )
        result = SendCommentResult.model_validate(
            await self.request(
                "POST",
                f"/messages/{message_id}/comments",
                params={"disable_link_preview": disable_link_preview},
                json=body.api_dump(),
            )
        )
        return result.message.bind(self)

    async def edit_comment(
        self,
        message_id: str,
        comment_id: str,
        *,
        text: str | None = None,
        link: NewMessageLink | None = None,
        notify: bool | None = None,
        format: TextFormat | str | None = None,
    ) -> bool:
        body = NewCommentBody(text=text, link=link, notify=notify, format=format)
        return _success(
            await self.request(
                "PUT",
                f"/messages/{message_id}/comments",
                params={"comment_id": comment_id},
                json=body.api_dump(),
            )
        )

    async def delete_comment(self, message_id: str, comment_id: str) -> bool:
        return _success(
            await self.request(
                "DELETE",
                f"/messages/{message_id}/comments",
                params={"comment_id": comment_id},
            )
        )

    async def get_comment(self, message_id: str, comment_id: str) -> CommentMessage:
        result = CommentMessage.model_validate(
            await self.request("GET", f"/messages/{message_id}/comments/{comment_id}")
        )
        return result.bind(self)

    async def get_video_attachment_details(
        self, video_token: str
    ) -> VideoAttachmentDetails:
        return VideoAttachmentDetails.model_validate(
            await self.request("GET", f"/videos/{video_token}")
        )

    async def answer_callback(
        self,
        callback_id: str,
        *,
        notification: str | None = None,
        message: NewMessageBody | None = None,
        text: str | None = None,
        attachments: list[AttachmentRequest | dict[str, Any]] | None = None,
        reply_markup: InlineKeyboardAttachmentRequest | None = None,
        format: TextFormat | str | None = None,
        disable_link_preview: bool | None = None,
        chat_id: int | None = None,
        user_id: int | None = None,
    ) -> bool:
        result = await self.answer_callback_result(
            callback_id,
            notification=notification,
            message=message,
            text=text,
            attachments=attachments,
            reply_markup=reply_markup,
            format=format,
            disable_link_preview=disable_link_preview,
            chat_id=chat_id,
            user_id=user_id,
        )
        return result.success

    async def answer_callback_result(
        self,
        callback_id: str,
        *,
        notification: str | None = None,
        message: NewMessageBody | None = None,
        text: str | None = None,
        attachments: list[AttachmentRequest | dict[str, Any]] | None = None,
        reply_markup: InlineKeyboardAttachmentRequest | None = None,
        format: TextFormat | str | None = None,
        disable_link_preview: bool | None = None,
        chat_id: int | None = None,
        user_id: int | None = None,
    ) -> SimpleQueryResult:
        """Answer a callback and preserve MAX's optional diagnostic message."""

        if message is not None and any(
            value is not None for value in (text, attachments, reply_markup, format)
        ):
            raise ValidationError(
                "pass message or message convenience fields, not both"
            )
        if message is None and any(
            value is not None for value in (text, attachments, reply_markup, format)
        ):
            message = NewMessageBody(
                text=text,
                attachments=_with_reply_markup(attachments, reply_markup),
                format=format,
            )
        body = CallbackAnswer(message=message, notification=notification)
        payload = await self._request_with_attachment_retry(
            "POST",
            "/answers",
            attachments_present=bool(message and message.attachments),
            chat_id=chat_id,
            user_id=user_id,
            params={
                "callback_id": callback_id,
                "disable_link_preview": disable_link_preview,
            },
            json=body.api_dump(),
        )
        return SimpleQueryResult.model_validate(payload)

    async def get_updates(
        self,
        *,
        limit: int = 100,
        timeout: int = 30,
        marker: int | None = None,
        types: Sequence[str] | None = None,
    ) -> UpdateList:
        payload = await self.request(
            "GET",
            "/updates",
            params={
                "limit": limit,
                "timeout": timeout,
                "marker": marker,
                "types": types,
            },
            timeout=timeout + 10,
        )
        result = UpdateList.model_validate(payload)
        for update in result.updates:
            update.bind(self)
        return result
