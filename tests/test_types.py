from __future__ import annotations

from typing import Any

import pytest

from aiomax2.types import (
    MessageCreatedUpdate,
    Update,
    UpdateList,
    parse_update,
)
from aiomax2.types.update import UPDATE_MODELS


def test_parse_known_update(message_update: dict[str, Any]) -> None:
    update = parse_update(message_update)

    assert isinstance(update, MessageCreatedUpdate)
    assert update.message.body is not None
    assert update.message.body.text == "/start 123"
    assert update.message.text == "/start 123"
    assert update.message.chat_id == 100
    assert update.message.sender is not None
    assert update.message.sender.full_name == "Ada Lovelace"


def test_unknown_update_is_forward_compatible() -> None:
    update = parse_update(
        {"update_type": "future_event", "timestamp": 123, "new_field": "value"}
    )

    assert type(update) is Update
    assert update.update_type == "future_event"
    assert update.model_extra == {"new_field": "value"}


def test_update_list_dispatches_each_discriminator(
    message_update: dict[str, Any],
) -> None:
    result = UpdateList.model_validate({"updates": [message_update], "marker": 1234})

    assert isinstance(result.updates[0], MessageCreatedUpdate)
    assert result.marker == 1234


def _user() -> dict[str, Any]:
    return {"user_id": 42, "first_name": "Ada", "is_bot": False}


def _message() -> dict[str, Any]:
    return {
        "sender": _user(),
        "recipient": {"chat_id": 100, "chat_type": "chat"},
        "timestamp": 1,
        "body": {"mid": "mid.1", "seq": 1, "text": "text"},
    }


@pytest.mark.parametrize(
    ("update_type", "payload"),
    [
        ("message_created", {"message": _message()}),
        (
            "message_callback",
            {
                "callback": {
                    "timestamp": 1,
                    "callback_id": "cb",
                    "user": _user(),
                },
                "message": _message(),
            },
        ),
        ("message_edited", {"message": _message()}),
        (
            "message_removed",
            {"message_id": "mid.1", "chat_id": 100, "user_id": 42},
        ),
        ("comment_created", {"message": _message()}),
        ("comment_edited", {"message": _message()}),
        (
            "comment_removed",
            {
                "message_id": "comment.1",
                "chat_id": 100,
                "user_id": 42,
                "post_id": "post.1",
            },
        ),
        ("bot_added", {"chat_id": 100, "user": _user(), "is_channel": False}),
        (
            "bot_removed",
            {"chat_id": 100, "user": _user(), "is_channel": False},
        ),
        ("user_added", {"chat_id": 100, "user": _user(), "is_channel": False}),
        (
            "user_removed",
            {"chat_id": 100, "user": _user(), "is_channel": False},
        ),
        ("bot_started", {"chat_id": 100, "user": _user()}),
        ("bot_stopped", {"chat_id": 100, "user": _user()}),
        ("dialog_cleared", {"chat_id": 100, "user": _user()}),
        ("dialog_removed", {"chat_id": 100, "user": _user()}),
        (
            "dialog_muted",
            {"chat_id": 100, "user": _user(), "muted_until": 2},
        ),
        ("dialog_unmuted", {"chat_id": 100, "user": _user()}),
        (
            "chat_title_changed",
            {"chat_id": 100, "user": _user(), "title": "New"},
        ),
        (
            "bot_admin_permissions_changed",
            {
                "chat_id": 100,
                "user_id": 42,
                "bot_id": 1,
                "is_channel": False,
                "is_admin": False,
                "permissions": None,
            },
        ),
    ],
)
def test_all_current_update_discriminators(
    update_type: str, payload: dict[str, Any]
) -> None:
    update = parse_update({"update_type": update_type, "timestamp": 1, **payload})

    assert isinstance(update, UPDATE_MODELS[update_type])
