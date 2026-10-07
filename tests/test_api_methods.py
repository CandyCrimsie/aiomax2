from __future__ import annotations

from typing import Any, cast

import pytest

from aiomax2 import Bot, TextFormat
from aiomax2.client import AiohttpSession
from aiomax2.enums import SenderAction
from aiomax2.exceptions import ValidationError
from aiomax2.types import BotCommand, ChatMember, NewCommentBody


def message_payload() -> dict[str, Any]:
    return {
        "sender": {"user_id": 1, "first_name": "Bot", "is_bot": True},
        "recipient": {"chat_id": 100, "chat_type": "chat"},
        "timestamp": 1,
        "body": {"mid": "mid.1", "seq": 1, "text": "text"},
    }


def comment_payload() -> dict[str, Any]:
    return {
        "sender": {"user_id": 42, "first_name": "Ada", "is_bot": False},
        "recipient": {
            "chat_id": 100,
            "chat_type": "channel",
            "post_id": "post.1",
        },
        "timestamp": 1,
        "body": {"mid": "comment.1", "seq": 1, "text": "comment"},
    }


def member_payload() -> dict[str, Any]:
    return {
        "user_id": 42,
        "first_name": "Ada",
        "is_bot": False,
        "last_access_time": 1,
        "is_owner": False,
        "is_admin": True,
        "join_time": 1,
        "permissions": ["read_all_messages", "write"],
    }


class NoopLimiter:
    async def acquire(self, key: str) -> None:
        return None


class ApiAuditTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self.closed = False

    async def open(self) -> None:
        return None

    async def close(self) -> None:
        self.closed = True

    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        self.calls.append((method, path, kwargs))
        if path == "/me":
            return {
                "user_id": 1,
                "first_name": "Audit Bot",
                "is_bot": True,
            }
        if path == "/me/commands":
            return {"commands": kwargs["json"]["commands"]}
        if path == "/chats/100":
            return {
                "chat_id": 100,
                "type": "chat",
                "status": "active",
                "title": "Audit",
                "last_event_time": 1,
                "participants_count": 2,
                "is_public": False,
            }
        if path == "/chats/100/pin" and method == "GET":
            return {"message": message_payload()}
        if path == "/chats/100/members/me":
            return member_payload() if method == "GET" else {"success": True}
        if path == "/chats/100/members/admins" and method == "GET":
            return {"members": [member_payload()], "marker": None}
        if path == "/chats/100/members" and method == "GET":
            return {"members": [member_payload()], "marker": 7}
        if path == "/subscriptions" and method == "GET":
            return {"subscriptions": []}
        if path == "/uploads":
            return {"url": "https://uploads.example.test/file", "token": "token"}
        if path == "/messages" and method == "GET":
            return {"messages": [message_payload()]}
        if path == "/messages" and method == "POST":
            return {"message": message_payload()}
        if path == "/messages/mid.1":
            return message_payload()
        if path == "/messages/post.1/comments" and method == "GET":
            return {"messages": [comment_payload()]}
        if path == "/messages/post.1/comments" and method == "POST":
            return {"message": comment_payload()}
        if path == "/messages/post.1/comments/comment.1":
            return comment_payload()
        if path == "/videos/video-token":
            return {
                "token": "video-token",
                "width": 1920,
                "height": 1080,
                "duration": 10,
            }
        if path == "/updates":
            return {"updates": [], "marker": 10}
        return {"success": True}


def find_call(
    calls: list[tuple[str, str, dict[str, Any]]], method: str, path: str
) -> dict[str, Any]:
    return next(
        kwargs
        for item_method, item_path, kwargs in calls
        if (item_method, item_path) == (method, path)
    )


@pytest.mark.asyncio
async def test_high_level_methods_match_current_max_endpoint_shapes() -> None:
    transport = ApiAuditTransport()
    bot = Bot("token", transport=cast(AiohttpSession, transport))
    bot._target_limiter = cast(Any, NoopLimiter())

    info = await bot.get_my_info()
    commands = await bot.edit_my_commands([BotCommand(name="start")])
    cleared_commands = await bot.edit_my_commands(None)
    chat = await bot.get_chat(100)
    edited_chat = await bot.edit_chat(
        100,
        title="Edited",
        description="Description",
        notify=False,
    )
    assert await bot.send_action(100, SenderAction.TYPING_ON)
    pinned = await bot.get_pinned_message(100)
    assert await bot.pin_message(100, "mid.1", notify=False)
    assert await bot.unpin_message(100)
    membership = await bot.get_membership(100)
    assert await bot.leave_chat(100)
    admins = await bot.get_admins(100)
    assert await bot.set_admins(
        100,
        [
            {
                "user_id": 42,
                "permissions": ["read_all_messages", "write"],
            }
        ],
    )
    assert await bot.revoke_admin(100, 42)
    members = await bot.get_members(100, user_ids=[42], marker=5, count=20)
    assert await bot.remove_member(100, 42, block=True)
    assert await bot.get_subscriptions() == []
    assert await bot.subscribe(
        "https://bot.example/webhook",
        secret="secret",
        update_types=["message_created", "bot_started"],
    )
    assert await bot.unsubscribe("https://bot.example/webhook")
    upload = await bot.get_upload_url("file")
    messages = await bot.get_messages(
        chat_id=100,
        from_time=1,
        to_time=2,
        before=3,
        after=4,
        count=50,
    )
    sent = await bot.send_message("text", chat_id=100, format=TextFormat.HTML)
    assert await bot.edit_message("mid.1", text="edited", chat_id=100)
    assert await bot.delete_message("mid.1", chat_id=100)
    fetched = await bot.get_message("mid.1")
    comments = await bot.get_comments(
        "post.1",
        comment_ids=["comment.1"],
        before=1,
        after=2,
        count=50,
    )
    created_comment = await bot.send_comment(
        "post.1", "comment", format=TextFormat.MARKDOWN
    )
    assert await bot.edit_comment(
        "post.1",
        "comment.1",
        text="edited",
        format=TextFormat.HTML,
    )
    assert await bot.delete_comment("post.1", "comment.1")
    fetched_comment = await bot.get_comment("post.1", "comment.1")
    video = await bot.get_video_attachment_details("video-token")
    callback = await bot.answer_callback_result(
        "callback.1", notification="Done", chat_id=100
    )
    updates = await bot.get_updates(
        limit=100,
        timeout=30,
        marker=9,
        types=["message_created"],
    )

    assert info.user_id == 1
    assert commands is not None and commands[0].name == "start"
    assert cleared_commands == []
    assert chat.chat_id == edited_chat.chat_id == 100
    assert pinned is not None and pinned.require_bot() is bot
    assert membership.user_id == 42
    assert isinstance(admins[0], ChatMember)
    assert members.marker == 7
    assert upload.token == "token"
    assert messages[0].require_bot() is bot
    assert sent.require_bot() is bot
    assert fetched.require_bot() is bot
    assert comments[0].require_bot() is bot
    assert created_comment.require_bot() is bot
    assert fetched_comment.require_bot() is bot
    assert video.duration == 10
    assert callback.success is True
    assert updates.marker == 10

    assert find_call(transport.calls, "PATCH", "/me/commands")["json"] == {
        "commands": [{"name": "start"}]
    }
    command_calls = [
        kwargs
        for method, path, kwargs in transport.calls
        if (method, path) == ("PATCH", "/me/commands")
    ]
    assert command_calls[1]["json"] == {"commands": []}
    assert find_call(transport.calls, "PATCH", "/chats/100")["json"] == {
        "title": "Edited",
        "description": "Description",
        "notify": False,
    }
    assert find_call(transport.calls, "POST", "/chats/100/actions")["json"] == {
        "action": "typing_on"
    }
    assert find_call(transport.calls, "PUT", "/chats/100/pin")["json"] == {
        "message_id": "mid.1",
        "notify": False,
    }
    assert find_call(transport.calls, "GET", "/chats/100/members")["params"] == {
        "user_ids": [42],
        "marker": 5,
        "count": 20,
    }
    assert find_call(transport.calls, "DELETE", "/chats/100/members")["params"] == {
        "user_id": 42,
        "block": True,
    }
    assert find_call(transport.calls, "POST", "/subscriptions")["json"] == {
        "url": "https://bot.example/webhook",
        "secret": "secret",
        "update_types": ["message_created", "bot_started"],
    }
    assert find_call(transport.calls, "GET", "/messages")["params"] == {
        "chat_id": 100,
        "message_ids": None,
        "from": 1,
        "to": 2,
        "before": 3,
        "after": 4,
        "count": 50,
    }
    assert find_call(transport.calls, "GET", "/messages/post.1/comments")["params"] == {
        "comment_ids": ["comment.1"],
        "before": 1,
        "after": 2,
        "count": 50,
    }
    assert find_call(transport.calls, "POST", "/answers")["json"] == {
        "notification": "Done"
    }
    assert find_call(transport.calls, "GET", "/updates")["params"] == {
        "limit": 100,
        "timeout": 30,
        "marker": 9,
        "types": ["message_created"],
    }
    assert not hasattr(Bot, "add_members")
    await bot.close()
    assert transport.closed


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"message_ids": []},
        {"chat_id": 100, "message_ids": ["mid.1"]},
    ],
)
async def test_get_messages_requires_exactly_one_source(
    kwargs: dict[str, Any],
) -> None:
    transport = ApiAuditTransport()
    bot = Bot("token", transport=cast(AiohttpSession, transport))

    with pytest.raises(ValidationError, match="exactly one"):
        await bot.get_messages(**kwargs)

    assert transport.calls == []
    await bot.close()


@pytest.mark.asyncio
async def test_comment_notify_compatibility_argument_is_not_serialized() -> None:
    transport = ApiAuditTransport()
    bot = Bot("token", transport=cast(AiohttpSession, transport))

    with pytest.warns(DeprecationWarning, match="not supported"):
        await bot.send_comment("post.1", "comment", notify=False)
    with pytest.warns(DeprecationWarning, match="not supported"):
        await bot.edit_comment("post.1", "comment.1", text="edited", notify=True)

    assert (
        "notify"
        not in find_call(transport.calls, "POST", "/messages/post.1/comments")["json"]
    )
    assert (
        "notify"
        not in find_call(transport.calls, "PUT", "/messages/post.1/comments")["json"]
    )
    assert NewCommentBody(notify=True).api_dump() == {}
    await bot.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("url", "secret"),
    [
        ("http://bot.example/webhook", "secret"),
        ("https://bot.example/webhook", "1234"),
        ("https://bot.example/webhook", "секрет"),
        ("https://bot.example/webhook", "bad secret"),
    ],
)
async def test_subscribe_validates_current_webhook_contract(
    url: str, secret: str
) -> None:
    transport = ApiAuditTransport()
    bot = Bot("token", transport=cast(AiohttpSession, transport))

    with pytest.raises(ValidationError):
        await bot.subscribe(url, secret=secret)

    assert transport.calls == []
    await bot.close()


@pytest.mark.asyncio
async def test_get_upload_url_rejects_removed_photo_type() -> None:
    transport = ApiAuditTransport()
    bot = Bot("token", transport=cast(AiohttpSession, transport))

    with pytest.raises(ValueError):
        await bot.get_upload_url("photo")

    assert transport.calls == []
    await bot.close()
