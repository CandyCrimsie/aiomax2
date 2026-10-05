from __future__ import annotations

from typing import Any, cast

import pytest

from aiomax2 import Bot
from aiomax2.client import AiohttpSession
from aiomax2.types import CallbackQuery, Message


class StubTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self.closed = False

    async def open(self) -> None:
        return None

    async def close(self) -> None:
        self.closed = True

    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        self.calls.append((method, path, kwargs))
        if method == "POST" and path == "/messages":
            body = kwargs["json"]
            message_id = f"sent.{len(self.calls)}"
            return {
                "message": {
                    "sender": {
                        "user_id": 1,
                        "first_name": "Bot",
                        "is_bot": True,
                    },
                    "recipient": {
                        "chat_id": int(kwargs["params"]["chat_id"]),
                        "chat_type": "chat",
                    },
                    "timestamp": 1,
                    "body": {
                        "mid": message_id,
                        "seq": len(self.calls),
                        "text": body.get("text"),
                    },
                }
            }
        return {"success": True}


def incoming_message() -> Message:
    return Message.model_validate(
        {
            "sender": {"user_id": 42, "first_name": "Ada", "is_bot": False},
            "recipient": {"chat_id": 100, "chat_type": "chat"},
            "timestamp": 1,
            "body": {"mid": "original", "seq": 1, "text": "hello"},
        }
    )


@pytest.mark.asyncio
async def test_message_shortcuts_use_real_max_shapes() -> None:
    stub = StubTransport()
    bot = Bot("token", transport=cast(AiohttpSession, stub))
    message = incoming_message().bind(bot)

    answer = await message.answer("answer")
    reply = await message.reply("reply")
    edited = await message.edit_text("edited")
    deleted = await message.delete()

    assert answer.text == "answer"
    assert reply.text == "reply"
    assert stub.calls[0][2]["params"]["chat_id"] == 100
    assert stub.calls[1][2]["json"]["link"] == {
        "type": "reply",
        "mid": "original",
    }
    assert stub.calls[2][:2] == ("PUT", "/messages")
    assert stub.calls[2][2]["params"] == {"message_id": "original"}
    assert stub.calls[3][:2] == ("DELETE", "/messages")
    assert edited is True
    assert deleted is True


@pytest.mark.asyncio
async def test_callback_answer_uses_answers_endpoint() -> None:
    stub = StubTransport()
    bot = Bot("token", transport=cast(AiohttpSession, stub))
    callback = CallbackQuery.model_validate(
        {
            "timestamp": 1,
            "callback_id": "callback.1",
            "payload": "confirm",
            "user": {"user_id": 42, "first_name": "Ada", "is_bot": False},
        }
    ).bind(bot)

    result = await callback.answer(notification="Done", text="Updated")

    assert result is True
    assert stub.calls == [
        (
            "POST",
            "/answers",
            {
                "params": {
                    "callback_id": "callback.1",
                    "disable_link_preview": None,
                },
                "json": {
                    "message": {"text": "Updated"},
                    "notification": "Done",
                },
            },
        )
    ]
