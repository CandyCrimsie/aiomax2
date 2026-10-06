from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError as PydanticValidationError

from aiomax2.dispatcher.router import EVENT_NAMES
from aiomax2.enums import UpdateType
from aiomax2.types import (
    CallbackQuery,
    ChatMember,
    CommentCreatedUpdate,
    MessageCallbackUpdate,
    MessageCreatedUpdate,
    Update,
    UpdateList,
    parse_update,
)
from aiomax2.types.update import UPDATE_MODELS
from tests.update_cases import ALL_UPDATE_CASES, ALL_UPDATE_TYPES


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


def test_update_list_dispatches_each_discriminator() -> None:
    result = UpdateList.model_validate(
        {"updates": [case.raw() for case in ALL_UPDATE_CASES], "marker": 1234}
    )

    assert [type(update) for update in result.updates] == [
        case.model_type for case in ALL_UPDATE_CASES
    ]
    assert result.marker == 1234


def test_update_model_router_and_public_enum_stay_in_sync() -> None:
    assert tuple(UPDATE_MODELS) == ALL_UPDATE_TYPES
    assert EVENT_NAMES == ALL_UPDATE_TYPES
    assert tuple(item.value for item in UpdateType) == ALL_UPDATE_TYPES


@pytest.mark.parametrize("case", ALL_UPDATE_CASES, ids=ALL_UPDATE_TYPES)
def test_all_current_update_discriminators(case: Any) -> None:
    update = parse_update(case.raw(future_top_level_field="preserved"))

    assert isinstance(update, case.model_type)
    assert isinstance(update, UPDATE_MODELS[case.update_type])
    assert update.model_extra == {"future_top_level_field": "preserved"}


def test_callback_update_without_deleted_message_keeps_locale_and_binds() -> None:
    raw = next(
        case.raw()
        for case in ALL_UPDATE_CASES
        if case.update_type == "message_callback"
    )
    raw["message"] = None
    update = parse_update(raw)

    assert isinstance(update, MessageCallbackUpdate)
    assert update.message is None
    query = update.as_callback_query()
    assert isinstance(query, CallbackQuery)
    assert query.message is None
    assert query.user_locale == "ru"


def test_comment_update_uses_schema_message_payload() -> None:
    raw = next(
        case.raw() for case in ALL_UPDATE_CASES if case.update_type == "comment_created"
    )
    update = parse_update(raw)

    assert isinstance(update, CommentCreatedUpdate)
    assert update.message.body is not None
    assert update.message.body.mid == "mid.1"


def test_chat_member_accepts_documented_legacy_permission_values() -> None:
    member = ChatMember.model_validate(
        {
            "user_id": 42,
            "first_name": "Ada",
            "is_bot": False,
            "last_access_time": 1,
            "is_owner": False,
            "is_admin": True,
            "join_time": 1,
            "permissions": [
                "post_edit_delete_message",
                "edit_message",
                "delete_message",
            ],
        }
    )

    assert member.permissions == [
        "post_edit_delete_message",
        "edit_message",
        "delete_message",
    ]


def test_bot_started_payload_honors_openapi_length_limit() -> None:
    raw = next(
        case.raw() for case in ALL_UPDATE_CASES if case.update_type == "bot_started"
    )
    raw["payload"] = "x" * 512
    assert parse_update(raw).payload == "x" * 512

    raw["payload"] = "x" * 513
    with pytest.raises(PydanticValidationError):
        parse_update(raw)
