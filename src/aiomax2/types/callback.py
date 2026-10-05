from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiomax2.enums import TextFormat

from .attachments import AttachmentRequest
from .base import MAXObject
from .message import Message, NewMessageBody
from .user import User

if TYPE_CHECKING:
    from aiomax2.bot import Bot


class Callback(MAXObject):
    timestamp: int
    callback_id: str
    payload: str | None = None
    user: User

    async def answer(
        self,
        *,
        notification: str | None = None,
        message: NewMessageBody | None = None,
        text: str | None = None,
        attachments: list[AttachmentRequest | dict[str, Any]] | None = None,
        format: TextFormat | str | None = None,
        disable_link_preview: bool | None = None,
    ) -> bool:
        return await self.require_bot().answer_callback(
            self.callback_id,
            notification=notification,
            message=message,
            text=text,
            attachments=attachments,
            format=format,
            disable_link_preview=disable_link_preview,
        )


class CallbackQuery(Callback):
    message: Message | None = None
    user_locale: str | None = None

    def bind(self, bot: Bot) -> CallbackQuery:
        super().bind(bot)
        if self.message is not None:
            self.message.bind(bot)
        return self
