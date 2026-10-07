from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError as PydanticValidationError

from aiomax2.dispatcher.router import EVENT_NAMES
from aiomax2.enums import UpdateType
from aiomax2.types import (
    AudioAttachmentRequest,
    CallbackQuery,
    ChatMember,
    CommentCreatedUpdate,
    ContactAttachmentRequest,
    ContactAttachmentRequestPayload,
    FileAttachmentRequest,
    InlineKeyboardAttachmentRequest,
    Keyboard,
    MessageCallbackUpdate,
    MessageCreatedUpdate,
    NewMessageBody,
    PhotoAttachmentPayload,
    PhotoAttachmentRequest,
    PhotoAttachmentRequestPayload,
    StickerAttachmentPayload,
    StickerAttachmentRequest,
    Update,
    UpdateList,
    UploadedInfo,
    User,
    parse_update,
)
from aiomax2.types.attachments import CallbackButton
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


def test_official_go_fixture_legacy_user_name_is_typed() -> None:
    user = User.model_validate(
        {
            "user_id": 123456789,
            "first_name": "John",
            "last_name": "Doe",
            "is_bot": False,
            "name": "John Doe",
        }
    )

    assert user.name == "John Doe"


def test_photo_response_payload_requires_openapi_fields() -> None:
    payload = PhotoAttachmentPayload(photo_id=1, token="token", url="https://img")
    assert payload.photo_id == 1

    with pytest.raises(PydanticValidationError):
        PhotoAttachmentPayload.model_validate({"token": "token"})


def test_photo_request_sources_are_mutually_exclusive() -> None:
    assert PhotoAttachmentRequestPayload(token="token").token == "token"

    with pytest.raises(PydanticValidationError, match="exactly one"):
        PhotoAttachmentRequestPayload()
    with pytest.raises(PydanticValidationError, match="exactly one"):
        PhotoAttachmentRequestPayload(token="token", url="https://img")


def test_documented_attachment_combinations_are_validated() -> None:
    token = UploadedInfo(token="token")
    keyboard = InlineKeyboardAttachmentRequest(
        payload=Keyboard(buttons=[[CallbackButton(text="Open", payload="open")]])
    )

    NewMessageBody(attachments=[FileAttachmentRequest(payload=token), keyboard])
    NewMessageBody(
        attachments=[
            ContactAttachmentRequest(
                payload=ContactAttachmentRequestPayload(contact_id=42)
            ),
            keyboard,
        ]
    )

    invalid = [
        [
            StickerAttachmentRequest(payload=StickerAttachmentPayload(code="sticker")),
            keyboard,
        ],
        [AudioAttachmentRequest(payload=token), keyboard],
        [
            FileAttachmentRequest(payload=token),
            PhotoAttachmentRequest(
                payload=PhotoAttachmentRequestPayload(token="photo")
            ),
        ],
    ]
    for attachments in invalid:
        with pytest.raises(PydanticValidationError):
            NewMessageBody(attachments=attachments)

    with pytest.raises(PydanticValidationError, match="more than 12"):
        NewMessageBody(
            attachments=[
                PhotoAttachmentRequest(
                    payload=PhotoAttachmentRequestPayload(token=f"photo-{index}")
                )
                for index in range(13)
            ]
        )


def test_official_go_v2_comment_fixture_shape_without_sender_parses() -> None:
    # Minimal independently-written fixture following stabs/update.comment_created.json
    # from the Apache-2.0 official Go SDK v2.
    update = parse_update(
        {
            "update_type": "comment_created",
            "timestamp": 1_788_528_471_428,
            "message": {
                "recipient": {
                    "chat_type": "channel",
                    "chat_id": -70_801_090_403_050,
                    "post_id": "mid.post",
                },
                "timestamp": 1_788_528_471_428,
                "body": {
                    "mid": "mid.comment",
                    "seq": 116_327_994_376_978_687,
                    "text": "Comment text",
                },
            },
        }
    )

    assert isinstance(update, CommentCreatedUpdate)
    assert update.message.sender is None
    assert update.message.recipient.post_id == "mid.post"
    assert update.message.message_id == "mid.comment"


def test_official_go_v2_callback_fixture_preserves_actor_and_payload() -> None:
    # Minimal wire shape based on stabs/update.message_callback.json.
    update = parse_update(
        {
            "update_type": "message_callback",
            "timestamp": 1,
            "callback": {
                "timestamp": 1,
                "callback_id": "callback.1",
                "payload": "picture",
                "user": {
                    "user_id": 42,
                    "first_name": "John",
                    "is_bot": False,
                    "name": "John Doe",
                },
            },
            "message": {
                "recipient": {
                    "chat_id": 100,
                    "chat_type": "dialog",
                    "user_id": 42,
                },
                "timestamp": 1,
                "body": {"mid": "mid.1", "seq": 1, "text": "Hello"},
                "sender": {
                    "user_id": 99,
                    "first_name": "Bot",
                    "is_bot": True,
                    "name": "Bot",
                },
            },
        }
    )

    assert isinstance(update, MessageCallbackUpdate)
    query = update.as_callback_query()
    assert query.user.user_id == 42
    assert query.user.name == "John Doe"
    assert query.payload == "picture"
    assert query.message is not None and query.message.chat_id == 100
