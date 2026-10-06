from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from aiomax2.types import (
    BotAddedToChatUpdate,
    BotAdminPermissionsChangedUpdate,
    BotRemovedFromChatUpdate,
    BotStartedUpdate,
    BotStoppedUpdate,
    CallbackQuery,
    ChatTitleChangedUpdate,
    CommentCreatedUpdate,
    CommentEditedUpdate,
    CommentRemovedUpdate,
    DialogClearedUpdate,
    DialogMutedUpdate,
    DialogRemovedUpdate,
    DialogUnmutedUpdate,
    Message,
    MessageCallbackUpdate,
    MessageCreatedUpdate,
    MessageEditedUpdate,
    MessageRemovedUpdate,
    Update,
    UserAddedToChatUpdate,
    UserRemovedFromChatUpdate,
)


@dataclass(frozen=True, slots=True)
class UpdateCase:
    update_type: str
    model_type: type[Update]
    observer: str
    event_type: type[Any]
    context_name: str
    payload: dict[str, Any]
    fsm_chat_id: int | None = 100
    fsm_user_id: int | None = 42

    def raw(self, **extra: Any) -> dict[str, Any]:
        return {
            "update_type": self.update_type,
            "timestamp": 1_760_000_000_000,
            **deepcopy(self.payload),
            **extra,
        }


def user() -> dict[str, Any]:
    return {
        "user_id": 42,
        "first_name": "Ada",
        "last_name": "Lovelace",
        "is_bot": False,
    }


def message(*, sender_is_bot: bool = False) -> dict[str, Any]:
    sender = user()
    sender["is_bot"] = sender_is_bot
    if sender_is_bot:
        sender["user_id"] = 99
        sender["first_name"] = "Bot"
    return {
        "sender": sender,
        "recipient": {"chat_id": 100, "chat_type": "chat"},
        "timestamp": 1_760_000_000_000,
        "body": {"mid": "mid.1", "seq": 1, "text": "text"},
    }


ALL_UPDATE_CASES = (
    UpdateCase(
        "message_created",
        MessageCreatedUpdate,
        "message",
        Message,
        "message",
        {"message": message(), "user_locale": "ru"},
    ),
    UpdateCase(
        "message_callback",
        MessageCallbackUpdate,
        "callback_query",
        CallbackQuery,
        "callback_query",
        {
            "callback": {
                "timestamp": 1_760_000_000_100,
                "callback_id": "callback.1",
                "payload": "confirm",
                "user": user(),
            },
            "message": message(sender_is_bot=True),
            "user_locale": "ru",
        },
    ),
    UpdateCase(
        "message_edited",
        MessageEditedUpdate,
        "message_edited",
        Message,
        "message_edited",
        {"message": message()},
    ),
    UpdateCase(
        "message_removed",
        MessageRemovedUpdate,
        "message_removed",
        MessageRemovedUpdate,
        "message_removed",
        {"message_id": "mid.1", "chat_id": 100, "user_id": 42},
    ),
    UpdateCase(
        "comment_created",
        CommentCreatedUpdate,
        "comment_created",
        Message,
        "comment_created",
        {"message": message()},
    ),
    UpdateCase(
        "comment_edited",
        CommentEditedUpdate,
        "comment_edited",
        Message,
        "comment_edited",
        {"message": message()},
    ),
    UpdateCase(
        "comment_removed",
        CommentRemovedUpdate,
        "comment_removed",
        CommentRemovedUpdate,
        "comment_removed",
        {
            "message_id": "comment.1",
            "chat_id": 100,
            "user_id": 42,
            "post_id": "post.1",
        },
    ),
    UpdateCase(
        "bot_added",
        BotAddedToChatUpdate,
        "bot_added",
        BotAddedToChatUpdate,
        "bot_added",
        {"chat_id": 100, "user": user(), "is_channel": False},
    ),
    UpdateCase(
        "bot_removed",
        BotRemovedFromChatUpdate,
        "bot_removed",
        BotRemovedFromChatUpdate,
        "bot_removed",
        {"chat_id": 100, "user": user(), "is_channel": False},
    ),
    UpdateCase(
        "user_added",
        UserAddedToChatUpdate,
        "user_added",
        UserAddedToChatUpdate,
        "user_added",
        {
            "chat_id": 100,
            "user": user(),
            "inviter_id": 7,
            "is_channel": False,
        },
    ),
    UpdateCase(
        "user_removed",
        UserRemovedFromChatUpdate,
        "user_removed",
        UserRemovedFromChatUpdate,
        "user_removed",
        {
            "chat_id": 100,
            "user": user(),
            "admin_id": 7,
            "is_channel": False,
        },
    ),
    UpdateCase(
        "bot_started",
        BotStartedUpdate,
        "bot_started",
        BotStartedUpdate,
        "bot_started",
        {
            "chat_id": 100,
            "user": user(),
            "payload": "start",
            "user_locale": "ru",
        },
    ),
    UpdateCase(
        "bot_stopped",
        BotStoppedUpdate,
        "bot_stopped",
        BotStoppedUpdate,
        "bot_stopped",
        {"chat_id": 100, "user": user(), "user_locale": "ru"},
    ),
    UpdateCase(
        "dialog_cleared",
        DialogClearedUpdate,
        "dialog_cleared",
        DialogClearedUpdate,
        "dialog_cleared",
        {"chat_id": 100, "user": user(), "user_locale": "ru"},
    ),
    UpdateCase(
        "dialog_removed",
        DialogRemovedUpdate,
        "dialog_removed",
        DialogRemovedUpdate,
        "dialog_removed",
        {"chat_id": 100, "user": user(), "user_locale": "ru"},
    ),
    UpdateCase(
        "dialog_muted",
        DialogMutedUpdate,
        "dialog_muted",
        DialogMutedUpdate,
        "dialog_muted",
        {
            "chat_id": 100,
            "user": user(),
            "muted_until": 1_760_000_100_000,
            "user_locale": "ru",
        },
    ),
    UpdateCase(
        "dialog_unmuted",
        DialogUnmutedUpdate,
        "dialog_unmuted",
        DialogUnmutedUpdate,
        "dialog_unmuted",
        {"chat_id": 100, "user": user(), "user_locale": "ru"},
    ),
    UpdateCase(
        "chat_title_changed",
        ChatTitleChangedUpdate,
        "chat_title_changed",
        ChatTitleChangedUpdate,
        "chat_title_changed",
        {"chat_id": 100, "user": user(), "title": "New title"},
    ),
    UpdateCase(
        "bot_admin_permissions_changed",
        BotAdminPermissionsChangedUpdate,
        "bot_admin_permissions_changed",
        BotAdminPermissionsChangedUpdate,
        "bot_admin_permissions_changed",
        {
            "chat_id": 100,
            "user_id": 42,
            "bot_id": 99,
            "is_channel": True,
            "is_admin": True,
            "permissions": ["read_all_messages", "write"],
        },
    ),
)

ALL_UPDATE_TYPES = tuple(case.update_type for case in ALL_UPDATE_CASES)
