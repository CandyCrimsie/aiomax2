from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from aiomax2.enums import ChatType, MessageLinkType, TextFormat
from aiomax2.exceptions import ValidationError

from .attachments import (
    Attachment,
    AttachmentRequest,
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


class NewCommentBody(MAXObject):
    text: str | None = Field(default=None, max_length=4000)
    link: NewMessageLink | None = None
    notify: bool | None = None
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
