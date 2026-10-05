from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture
def message_update() -> dict[str, Any]:
    return {
        "update_type": "message_created",
        "timestamp": 1_760_000_000_000,
        "user_locale": "ru",
        "message": {
            "sender": {
                "user_id": 42,
                "first_name": "Ada",
                "last_name": "Lovelace",
                "is_bot": False,
            },
            "recipient": {"chat_id": 100, "chat_type": "chat"},
            "timestamp": 1_760_000_000_000,
            "body": {"mid": "mid.1", "seq": 1, "text": "/start 123"},
        },
    }


@pytest.fixture
def callback_update() -> dict[str, Any]:
    return {
        "update_type": "message_callback",
        "timestamp": 1_760_000_000_100,
        "callback": {
            "timestamp": 1_760_000_000_100,
            "callback_id": "callback.1",
            "payload": "confirm",
            "user": {
                "user_id": 42,
                "first_name": "Ada",
                "is_bot": False,
            },
        },
        "message": {
            "sender": {
                "user_id": 99,
                "first_name": "Bot",
                "is_bot": True,
            },
            "recipient": {"chat_id": 100, "chat_type": "chat"},
            "timestamp": 1_760_000_000_000,
            "body": {"mid": "mid.1", "seq": 1, "text": "Choose"},
        },
        "user_locale": "ru",
    }
