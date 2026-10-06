from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from aiomax2.exceptions import ValidationError
from aiomax2.types import (
    CallbackButton,
    ClipboardButton,
    InlineKeyboardAttachmentRequest,
    Keyboard,
    LinkButton,
    MessageButton,
    OpenAppButton,
    RequestContactButton,
    RequestGeoLocationButton,
)
from aiomax2.utils.keyboard import InlineKeyboardBuilder


def test_all_button_shortcuts_serialize_to_max_models() -> None:
    markup = (
        InlineKeyboardBuilder()
        .callback(text="Callback", payload="confirm")
        .link(text="Link", url="https://dev.max.ru")
        .clipboard(text="Copy", payload="ABC-123")
        .message(text="/help")
        .request_contact(text="Contact")
        .request_geo_location(text="Location", quick=False)
        .open_app(
            text="App",
            web_app="max-app",
            payload="screen-1",
            contact_id=42,
        )
        .adjust(3, 2)
        .as_markup()
    )

    assert markup.api_dump() == {
        "type": "inline_keyboard",
        "payload": {
            "buttons": [
                [
                    {"type": "callback", "text": "Callback", "payload": "confirm"},
                    {"type": "link", "text": "Link", "url": "https://dev.max.ru"},
                    {"type": "clipboard", "text": "Copy", "payload": "ABC-123"},
                ],
                [
                    {"type": "message", "text": "/help"},
                    {"type": "request_contact", "text": "Contact"},
                ],
                [
                    {
                        "type": "request_geo_location",
                        "text": "Location",
                        "quick": False,
                    },
                    {
                        "type": "open_app",
                        "text": "App",
                        "web_app": "max-app",
                        "payload": "screen-1",
                        "contact_id": 42,
                    },
                ],
            ]
        },
    }


def test_button_callback_data_maps_to_payload_only() -> None:
    markup = (
        InlineKeyboardBuilder()
        .button(text="Confirm", callback_data="confirm")
        .as_markup()
    )

    button = markup.api_dump()["payload"]["buttons"][0][0]
    assert button == {"type": "callback", "text": "Confirm", "payload": "confirm"}
    assert "callback_data" not in button


def test_button_requires_exactly_one_action() -> None:
    builder = InlineKeyboardBuilder()

    with pytest.raises(ValidationError, match="exactly one action"):
        builder.button(text="No action")
    with pytest.raises(ValidationError, match="exactly one action"):
        builder.button(text="Two", callback_data="x", url="https://example.test")


def test_add_row_adjust_attach_and_from_markup() -> None:
    first = InlineKeyboardBuilder().add(
        CallbackButton(text="1", payload="1"),
        CallbackButton(text="2", payload="2"),
    )
    second = InlineKeyboardBuilder().row(
        MessageButton(text="3"),
        ClipboardButton(text="4", payload="four"),
        width=1,
    )

    markup = first.attach(second).adjust(2).as_markup()
    restored = InlineKeyboardBuilder.from_markup(markup).as_markup()

    assert [len(row) for row in markup.payload.buttons] == [2, 2]
    assert restored == markup
    assert [button.text for button in first.buttons] == ["1", "2", "3", "4"]


@pytest.mark.parametrize(
    "button",
    [
        LinkButton(text="Link", url="https://dev.max.ru"),
        OpenAppButton(text="App", web_app="app"),
        RequestContactButton(text="Contact"),
        RequestGeoLocationButton(text="Location"),
    ],
)
def test_restricted_button_rows_allow_at_most_three(button: object) -> None:
    with pytest.raises(PydanticValidationError, match="cannot contain more than 3"):
        Keyboard(buttons=[[button] * 4])  # type: ignore[list-item]


def test_keyboard_layout_limits() -> None:
    button = CallbackButton(text="Button", payload="payload")

    with pytest.raises(PydanticValidationError, match="at least one row"):
        Keyboard(buttons=[])
    with pytest.raises(PydanticValidationError, match="cannot be empty"):
        Keyboard(buttons=[[]])
    with pytest.raises(PydanticValidationError, match="more than 7"):
        Keyboard(buttons=[[button] * 8])
    with pytest.raises(PydanticValidationError, match="more than 30"):
        Keyboard(buttons=[[button]] * 31)
    with pytest.raises(PydanticValidationError):
        Keyboard(buttons=[[button] * 7 for _ in range(30)] + [[button]])


def test_button_field_limits_from_openapi() -> None:
    with pytest.raises(PydanticValidationError):
        CallbackButton(text="", payload="payload")
    with pytest.raises(PydanticValidationError):
        CallbackButton(text="x" * 129, payload="payload")
    with pytest.raises(PydanticValidationError):
        CallbackButton(text="Callback", payload="x" * 1025)
    with pytest.raises(PydanticValidationError):
        LinkButton(text="Link", url="x" * 2049)
    with pytest.raises(PydanticValidationError):
        ClipboardButton(text="Copy", payload="x" * 1025)


def test_open_app_payload_accepts_only_documented_ascii_characters() -> None:
    assert (
        OpenAppButton(
            text="App",
            web_app="app",
            payload="screen-1_test",
        ).payload
        == "screen-1_test"
    )
    assert OpenAppButton(text="App", web_app="app", payload="").payload == ""


@pytest.mark.parametrize("payload", ["привет", "has space", "screen.1", "a/b"])
def test_open_app_payload_rejects_non_ascii_or_punctuation(payload: str) -> None:
    with pytest.raises(PydanticValidationError):
        OpenAppButton(text="App", web_app="app", payload=payload)


def test_open_app_payload_rejects_513_characters() -> None:
    with pytest.raises(PydanticValidationError):
        OpenAppButton(text="App", web_app="app", payload="x" * 513)


def test_low_level_keyboard_api_remains_available() -> None:
    markup = InlineKeyboardAttachmentRequest(
        payload=Keyboard(buttons=[[CallbackButton(text="Yes", payload="yes")]])
    )

    assert markup.payload.buttons[0][0].payload == "yes"
