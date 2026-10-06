from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal

from pydantic import Field, field_validator

from aiomax2.enums import ChatAdminPermission

from .base import MAXObject
from .callback import Callback, CallbackQuery
from .message import Message
from .user import User


class Update(MAXObject):
    update_type: str
    timestamp: int


class MessageCreatedUpdate(Update):
    update_type: Literal["message_created"] = "message_created"
    message: Message
    user_locale: str | None = None

    def bind(self, bot: Any) -> MessageCreatedUpdate:
        super().bind(bot)
        self.message.bind(bot)
        return self


class MessageCallbackUpdate(Update):
    update_type: Literal["message_callback"] = "message_callback"
    callback: Callback
    message: Message | None = None
    user_locale: str | None = None

    def bind(self, bot: Any) -> MessageCallbackUpdate:
        super().bind(bot)
        self.callback.bind(bot)
        if self.message is not None:
            self.message.bind(bot)
        return self

    def as_callback_query(self) -> CallbackQuery:
        query = CallbackQuery(
            **self.callback.model_dump(),
            message=self.message,
            user_locale=self.user_locale,
        )
        if self._bot is not None:
            query.bind(self._bot)
        return query


class MessageEditedUpdate(Update):
    update_type: Literal["message_edited"] = "message_edited"
    message: Message

    def bind(self, bot: Any) -> MessageEditedUpdate:
        super().bind(bot)
        self.message.bind(bot)
        return self


class MessageRemovedUpdate(Update):
    update_type: Literal["message_removed"] = "message_removed"
    message_id: str
    chat_id: int
    user_id: int


class CommentCreatedUpdate(Update):
    update_type: Literal["comment_created"] = "comment_created"
    message: Message

    def bind(self, bot: Any) -> CommentCreatedUpdate:
        super().bind(bot)
        self.message.bind(bot)
        return self


class CommentEditedUpdate(Update):
    update_type: Literal["comment_edited"] = "comment_edited"
    message: Message

    def bind(self, bot: Any) -> CommentEditedUpdate:
        super().bind(bot)
        self.message.bind(bot)
        return self


class CommentRemovedUpdate(Update):
    update_type: Literal["comment_removed"] = "comment_removed"
    message_id: str
    chat_id: int
    user_id: int
    post_id: str


class BotAddedToChatUpdate(Update):
    update_type: Literal["bot_added"] = "bot_added"
    chat_id: int
    user: User
    is_channel: bool


class BotRemovedFromChatUpdate(Update):
    update_type: Literal["bot_removed"] = "bot_removed"
    chat_id: int
    user: User
    is_channel: bool


class UserAddedToChatUpdate(Update):
    update_type: Literal["user_added"] = "user_added"
    chat_id: int
    user: User
    inviter_id: int | None = None
    is_channel: bool


class UserRemovedFromChatUpdate(Update):
    update_type: Literal["user_removed"] = "user_removed"
    chat_id: int
    user: User
    admin_id: int | None = None
    is_channel: bool


class BotStartedUpdate(Update):
    update_type: Literal["bot_started"] = "bot_started"
    chat_id: int
    user: User
    payload: str | None = Field(default=None, max_length=512)
    user_locale: str | None = None


class BotStoppedUpdate(Update):
    update_type: Literal["bot_stopped"] = "bot_stopped"
    chat_id: int
    user: User
    user_locale: str | None = None


class DialogClearedUpdate(Update):
    update_type: Literal["dialog_cleared"] = "dialog_cleared"
    chat_id: int
    user: User
    user_locale: str | None = None


class DialogRemovedUpdate(Update):
    update_type: Literal["dialog_removed"] = "dialog_removed"
    chat_id: int
    user: User
    user_locale: str | None = None


class DialogMutedUpdate(Update):
    update_type: Literal["dialog_muted"] = "dialog_muted"
    chat_id: int
    user: User
    muted_until: int
    user_locale: str | None = None


class DialogUnmutedUpdate(Update):
    update_type: Literal["dialog_unmuted"] = "dialog_unmuted"
    chat_id: int
    user: User
    user_locale: str | None = None


class ChatTitleChangedUpdate(Update):
    update_type: Literal["chat_title_changed"] = "chat_title_changed"
    chat_id: int
    user: User
    title: str


class BotAdminPermissionsChangedUpdate(Update):
    update_type: Literal["bot_admin_permissions_changed"] = (
        "bot_admin_permissions_changed"
    )
    chat_id: int
    user_id: int
    bot_id: int
    is_channel: bool
    is_admin: bool
    permissions: list[ChatAdminPermission] | None = None


UpdateT = (
    MessageCreatedUpdate
    | MessageCallbackUpdate
    | MessageEditedUpdate
    | MessageRemovedUpdate
    | CommentCreatedUpdate
    | CommentEditedUpdate
    | CommentRemovedUpdate
    | BotAddedToChatUpdate
    | BotRemovedFromChatUpdate
    | UserAddedToChatUpdate
    | UserRemovedFromChatUpdate
    | BotStartedUpdate
    | BotStoppedUpdate
    | DialogClearedUpdate
    | DialogRemovedUpdate
    | DialogMutedUpdate
    | DialogUnmutedUpdate
    | ChatTitleChangedUpdate
    | BotAdminPermissionsChangedUpdate
    | Update
)

UPDATE_MODELS: dict[str, type[Update]] = {
    "message_created": MessageCreatedUpdate,
    "message_callback": MessageCallbackUpdate,
    "message_edited": MessageEditedUpdate,
    "message_removed": MessageRemovedUpdate,
    "comment_created": CommentCreatedUpdate,
    "comment_edited": CommentEditedUpdate,
    "comment_removed": CommentRemovedUpdate,
    "bot_added": BotAddedToChatUpdate,
    "bot_removed": BotRemovedFromChatUpdate,
    "user_added": UserAddedToChatUpdate,
    "user_removed": UserRemovedFromChatUpdate,
    "bot_started": BotStartedUpdate,
    "bot_stopped": BotStoppedUpdate,
    "dialog_cleared": DialogClearedUpdate,
    "dialog_removed": DialogRemovedUpdate,
    "dialog_muted": DialogMutedUpdate,
    "dialog_unmuted": DialogUnmutedUpdate,
    "chat_title_changed": ChatTitleChangedUpdate,
    "bot_admin_permissions_changed": BotAdminPermissionsChangedUpdate,
}


def parse_update(data: Mapping[str, Any] | Update) -> Update:
    """Parse a current update, retaining unknown future update types."""

    if isinstance(data, Update):
        return data
    update_type = data.get("update_type")
    model = UPDATE_MODELS.get(str(update_type), Update)
    return model.model_validate(data)


class UpdateList(MAXObject):
    updates: list[UpdateT]
    marker: int | None = None

    @field_validator("updates", mode="before")
    @classmethod
    def parse_updates(cls, value: Any) -> list[Update]:
        if not isinstance(value, list):
            raise ValueError("updates must be a list")
        return [parse_update(item) for item in value]
