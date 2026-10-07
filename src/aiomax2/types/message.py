from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field, model_validator

from aiomax2.enums import ChatType, MessageLinkType, TextFormat
from aiomax2.exceptions import ValidationError

from .attachments import (
    Attachment,
    AttachmentRequest,
    BaseAttachmentRequest,
    InlineKeyboardAttachmentRequest,
    MarkupElement,
)
from .base import MAXObject
from .user import User

if TYPE_CHECKING:
    from aiomax2.bot import Bot


class Recipient(MAXObject):
    chat_id: int | None = None
    chat_type: ChatType
    user_id: int | None = None
    post_id: str | None = None


class MessageBody(MAXObject):
    mid: str
    seq: int
    text: str | None = None
    attachments: list[Attachment] | None = None
    markup: list[MarkupElement] | None = None


class CommentMessageBody(MAXObject):
    mid: str
    seq: int
    text: str | None = None
    markup: list[MarkupElement] | None = None


class MessageStat(MAXObject):
    views: int


class LinkedMessage(MAXObject):
    type: MessageLinkType
    sender: User | None = None
    chat_id: int | None = None
    message: MessageBody


class CommentLinkedMessage(MAXObject):
    type: MessageLinkType
    sender: User | None = None
    chat_id: int | None = None
    message: CommentMessageBody


class NewMessageLink(MAXObject):
    type: MessageLinkType
    mid: str


class NewMessageBody(MAXObject):
    text: str | None = Field(default=None, max_length=4000)
    attachments: list[AttachmentRequest | dict[str, Any]] | None = None
    link: NewMessageLink | None = None
    notify: bool | None = None
    format: TextFormat | None = None

    @model_validator(mode="after")
    def validate_attachment_combinations(self) -> NewMessageBody:
        attachments = self.attachments
        if not attachments:
            return self

        attachment_types = [
            attachment.type
            if isinstance(attachment, BaseAttachmentRequest)
            else attachment.get("type")
            for attachment in attachments
        ]
        known_types = {
            "image",
            "video",
            "audio",
            "file",
            "sticker",
            "contact",
            "inline_keyboard",
            "location",
            "share",
        }
        # Raw dicts are an intentional extension point for future MAX
        # attachment types. Do not apply today's combination rules to them.
        if any(item not in known_types for item in attachment_types):
            return self

        keyboard_count = attachment_types.count("inline_keyboard")
        if keyboard_count > 1:
            raise ValueError("a message cannot contain multiple inline keyboards")

        if "sticker" in attachment_types and len(attachments) != 1:
            raise ValueError("a sticker must be the only message attachment")
        if "audio" in attachment_types and len(attachments) != 1:
            raise ValueError("an audio file must be the only message attachment")

        if "file" in attachment_types:
            if attachment_types.count("file") != 1 or any(
                item not in {"file", "inline_keyboard"} for item in attachment_types
            ):
                raise ValueError(
                    "a message may contain one file and optionally one inline keyboard"
                )

        if "contact" in attachment_types:
            if attachment_types.count("contact") != 1 or any(
                item not in {"contact", "inline_keyboard"} for item in attachment_types
            ):
                raise ValueError(
                    "a message may contain one contact and optionally "
                    "one inline keyboard"
                )
            if keyboard_count:
                keyboard = next(
                    (
                        attachment
                        for attachment in attachments
                        if isinstance(attachment, InlineKeyboardAttachmentRequest)
                    ),
                    None,
                )
                if (
                    keyboard is not None
                    and sum(len(row) for row in keyboard.payload.buttons) > 1
                ):
                    raise ValueError(
                        "a contact may be combined with only one keyboard button"
                    )

        if set(attachment_types) <= {"image", "video", "inline_keyboard"}:
            if len(attachments) > 12:
                raise ValueError(
                    "image/video messages cannot contain more than 12 attachments"
                )
        return self


class NewCommentBody(MAXObject):
    text: str | None = Field(default=None, max_length=4000)
    link: NewMessageLink | None = None
    # Kept as a compatibility input for 0.1.x. MAX NewCommentBody has no
    # ``notify`` property, so it must never be serialized onto the wire.
    notify: bool | None = Field(default=None, exclude=True)
    format: TextFormat | None = None


class Message(MAXObject):
    sender: User | None = None
    recipient: Recipient
    timestamp: int
    link: LinkedMessage | None = None
    # The current schema says required, while the official description says it can
    # be null for a forwarded-only message. Runtime behaviour wins here.
    body: MessageBody | None
    stat: MessageStat | None = None
    url: str | None = None

    @property
    def message_id(self) -> str | None:
        return self.body.mid if self.body is not None else None

    @property
    def text(self) -> str | None:
        return self.body.text if self.body is not None else None

    @property
    def chat_id(self) -> int | None:
        return self.recipient.chat_id

    @property
    def user_id(self) -> int | None:
        if self.sender is not None and self.sender.is_bot:
            return self.recipient.user_id
        if self.sender is not None:
            return self.sender.user_id
        return self.recipient.user_id

    def bind(self, bot: Bot) -> Message:
        super().bind(bot)
        return self

    async def answer(
        self,
        text: str | None = None,
        *,
        attachments: list[AttachmentRequest | dict[str, Any]] | None = None,
        reply_markup: InlineKeyboardAttachmentRequest | None = None,
        notify: bool | None = None,
        format: TextFormat | str | None = None,
        disable_link_preview: bool | None = None,
    ) -> Message:
        bot = self.require_bot()
        target_chat = self.recipient.chat_id
        target_user = None if target_chat is not None else self.user_id
        return await bot.send_message(
            text=text,
            chat_id=target_chat,
            user_id=target_user,
            attachments=attachments,
            reply_markup=reply_markup,
            notify=notify,
            format=format,
            disable_link_preview=disable_link_preview,
        )

    async def reply(
        self,
        text: str | None = None,
        *,
        attachments: list[AttachmentRequest | dict[str, Any]] | None = None,
        reply_markup: InlineKeyboardAttachmentRequest | None = None,
        notify: bool | None = None,
        format: TextFormat | str | None = None,
        disable_link_preview: bool | None = None,
    ) -> Message:
        if self.message_id is None:
            raise ValidationError("cannot reply to a message without body.mid")
        bot = self.require_bot()
        target_chat = self.recipient.chat_id
        target_user = None if target_chat is not None else self.user_id
        return await bot.send_message(
            text=text,
            chat_id=target_chat,
            user_id=target_user,
            attachments=attachments,
            reply_markup=reply_markup,
            link=NewMessageLink(type=MessageLinkType.REPLY, mid=self.message_id),
            notify=notify,
            format=format,
            disable_link_preview=disable_link_preview,
        )

    async def edit_text(
        self,
        text: str | None = None,
        *,
        attachments: list[AttachmentRequest | dict[str, Any]] | None = None,
        reply_markup: InlineKeyboardAttachmentRequest | None = None,
        notify: bool | None = None,
        format: TextFormat | str | None = None,
    ) -> bool:
        if self.message_id is None:
            raise ValidationError("cannot edit a message without body.mid")
        return await self.require_bot().edit_message(
            self.message_id,
            text=text,
            attachments=attachments,
            reply_markup=reply_markup,
            notify=notify,
            format=format,
            chat_id=self.chat_id,
            user_id=None if self.chat_id is not None else self.user_id,
        )

    async def delete(self) -> bool:
        if self.message_id is None:
            raise ValidationError("cannot delete a message without body.mid")
        return await self.require_bot().delete_message(
            self.message_id,
            chat_id=self.chat_id,
            user_id=None if self.chat_id is not None else self.user_id,
        )


class CommentMessage(MAXObject):
    sender: User | None = None
    recipient: Recipient
    timestamp: int
    link: CommentLinkedMessage | None = None
    body: CommentMessageBody
    stat: MessageStat | None = None
