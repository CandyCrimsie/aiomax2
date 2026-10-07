from __future__ import annotations

from typing import Any, cast

import pytest

from aiomax2 import Bot, TextFormat
from aiomax2.client import AiohttpSession
from aiomax2.exceptions import BadRequestError, ValidationError
from aiomax2.types import CallbackQuery, Message
from aiomax2.utils.keyboard import InlineKeyboardBuilder


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


class UploadStubTransport(StubTransport):
    def __init__(self) -> None:
        super().__init__()
        self.uploads: list[dict[str, Any]] = []

    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        if method == "POST" and path == "/uploads":
            self.calls.append((method, path, kwargs))
            upload_type = str(kwargs["params"]["type"])
            payload: dict[str, Any] = {
                "url": f"https://uploads.example.test/{upload_type}"
            }
            # Deliberately include a token for every type. Conformance code
            # must still select the source defined for each upload protocol.
            payload["token"] = f"{upload_type}-endpoint-token"
            return payload
        return await super().request(method, path, **kwargs)

    async def upload(self, url: str, file_data: Any, **kwargs: Any) -> Any:
        self.uploads.append({"url": url, "file_data": file_data, **kwargs})
        upload_type = url.rsplit("/", 1)[-1]
        if upload_type == "image":
            return {"photos": {"photoIds": {"token": "image-upload-token"}}}
        if upload_type == "file":
            return {"fileId": 1, "token": "file-upload-token"}
        return {"token": f"{upload_type}-wrong-upload-token"}


class FailingUploadStubTransport(UploadStubTransport):
    async def upload(self, url: str, file_data: Any, **kwargs: Any) -> Any:
        self.uploads.append({"url": url, "file_data": file_data, **kwargs})
        raise attachment_not_ready()


class RecordingLimiter:
    def __init__(self) -> None:
        self.keys: list[str] = []

    async def acquire(self, key: str) -> None:
        self.keys.append(key)


class SequenceTransport(StubTransport):
    def __init__(self, responses: list[Any]) -> None:
        super().__init__()
        self.responses = responses

    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        self.calls.append((method, path, kwargs))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def attachment_not_ready() -> BadRequestError:
    return BadRequestError(
        400,
        "Key: errors.process.attachment.file.not.processed",
        payload={
            "code": "attachment.not.ready",
            "message": "Key: errors.process.attachment.file.not.processed",
        },
    )


def sent_message_result(text: str = "sent") -> dict[str, Any]:
    return {
        "message": {
            "sender": {"user_id": 1, "first_name": "Bot", "is_bot": True},
            "recipient": {"chat_id": 100, "chat_type": "chat"},
            "timestamp": 1,
            "body": {"mid": "sent.1", "seq": 1, "text": text},
        }
    }


def incoming_message() -> Message:
    return Message.model_validate(
        {
            "sender": {"user_id": 42, "first_name": "Ada", "is_bot": False},
            "recipient": {"chat_id": 100, "chat_type": "chat"},
            "timestamp": 1,
            "body": {"mid": "original", "seq": 1, "text": "hello"},
        }
    )


def outgoing_dialog_message() -> Message:
    return Message.model_validate(
        {
            "sender": {"user_id": 1, "first_name": "Bot", "is_bot": True},
            "recipient": {"user_id": 42, "chat_type": "dialog"},
            "timestamp": 1,
            "body": {"mid": "sent", "seq": 1, "text": "hello"},
        }
    )


def test_text_format_is_public_and_matches_max_values() -> None:
    assert list(TextFormat) == [TextFormat.MARKDOWN, TextFormat.HTML]
    assert [item.value for item in TextFormat] == ["markdown", "html"]
    assert not hasattr(TextFormat, "MARKDOWN_V2")


@pytest.mark.asyncio
async def test_message_shortcuts_use_real_max_shapes() -> None:
    stub = StubTransport()
    bot = Bot("token", transport=cast(AiohttpSession, stub))
    limiter = RecordingLimiter()
    bot._target_limiter = cast(Any, limiter)
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
    assert limiter.keys == ["chat:100"] * 4


@pytest.mark.asyncio
async def test_callback_answer_uses_answers_endpoint() -> None:
    stub = StubTransport()
    bot = Bot("token", transport=cast(AiohttpSession, stub))
    limiter = RecordingLimiter()
    bot._target_limiter = cast(Any, limiter)
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
    assert limiter.keys == ["user:42"]


@pytest.mark.asyncio
async def test_callback_shortcut_passes_message_chat_target() -> None:
    stub = StubTransport()
    bot = Bot("token", transport=cast(AiohttpSession, stub))
    limiter = RecordingLimiter()
    bot._target_limiter = cast(Any, limiter)
    callback = CallbackQuery.model_validate(
        {
            "timestamp": 1,
            "callback_id": "callback.2",
            "user": {"user_id": 42, "first_name": "Ada", "is_bot": False},
            "message": incoming_message().model_dump(),
        }
    ).bind(bot)

    await callback.answer(notification="Done")

    assert limiter.keys == ["chat:100"]


@pytest.mark.asyncio
async def test_callback_notification_only_omits_message() -> None:
    stub = StubTransport()
    bot = Bot("token", transport=cast(AiohttpSession, stub))
    callback = CallbackQuery.model_validate(
        {
            "timestamp": 1,
            "callback_id": "callback.notification",
            "user": {"user_id": 42, "first_name": "Ada", "is_bot": False},
        }
    ).bind(bot)

    assert await callback.answer(notification="Cancelled") is True
    assert stub.calls[0][2]["json"] == {"notification": "Cancelled"}


@pytest.mark.asyncio
async def test_callback_message_only_and_empty_answer_serialization() -> None:
    stub = StubTransport()
    bot = Bot("token", transport=cast(AiohttpSession, stub))

    assert await bot.answer_callback("callback.message", text="Updated") is True
    assert await bot.answer_callback("callback.empty") is True

    assert stub.calls[0][2]["json"] == {"message": {"text": "Updated"}}
    assert stub.calls[1][2]["json"] == {}


@pytest.mark.asyncio
async def test_callback_result_preserves_unsuccessful_server_message() -> None:
    stub = SequenceTransport(
        [
            {"success": False, "message": "Callback expired"},
            {"success": False, "message": "Callback expired"},
        ]
    )
    bot = Bot("token", transport=cast(AiohttpSession, stub))

    result = await bot.answer_callback_result("callback.result")
    legacy_result = await bot.answer_callback("callback.bool")

    assert result.success is False
    assert result.message == "Callback expired"
    assert legacy_result is False


@pytest.mark.asyncio
async def test_outgoing_dialog_shortcuts_keep_recipient_as_target() -> None:
    stub = StubTransport()
    bot = Bot("token", transport=cast(AiohttpSession, stub))
    limiter = RecordingLimiter()
    bot._target_limiter = cast(Any, limiter)
    message = outgoing_dialog_message().bind(bot)

    await message.edit_text("edited")
    await message.delete()

    assert message.user_id == 42
    assert limiter.keys == ["user:42", "user:42"]


@pytest.mark.asyncio
async def test_low_level_message_methods_use_target_or_fallback_bucket() -> None:
    stub = StubTransport()
    bot = Bot("token", transport=cast(AiohttpSession, stub))
    limiter = RecordingLimiter()
    bot._target_limiter = cast(Any, limiter)

    await bot.send_message("sent", chat_id=100)
    await bot.edit_message("message.1")
    await bot.delete_message("message.1", user_id=42)
    await bot.answer_callback("callback.1")

    assert limiter.keys == ["chat:100", "unknown", "user:42", "unknown"]


@pytest.mark.asyncio
async def test_media_upload_authorization_is_scoped_by_max_protocol() -> None:
    stub = UploadStubTransport()
    bot = Bot("token", transport=cast(AiohttpSession, stub))

    image = await bot.upload_image(b"image", filename="image.png")
    video = await bot.upload_video(b"video", filename="video.mp4")
    audio = await bot.upload_audio(b"audio", filename="audio.mp3")
    document = await bot.upload_file(b"file", filename="file.pdf")

    assert image.payload.token == "image-upload-token"
    assert video.payload.token == "video-endpoint-token"
    assert audio.payload.token == "audio-endpoint-token"
    assert document.payload.token == "file-upload-token"
    assert [upload["authorization"] for upload in stub.uploads] == [
        True,
        False,
        False,
        False,
    ]
    assert all(
        upload["url"].startswith("https://uploads.example.test/")
        for upload in stub.uploads
    )


@pytest.mark.asyncio
async def test_media_upload_strips_directory_components_from_filename() -> None:
    stub = UploadStubTransport()
    bot = Bot("token", transport=cast(AiohttpSession, stub))

    await bot.upload_file(b"file", filename=r"C:\private\reports\report.pdf")

    assert stub.uploads[0]["filename"] == "report.pdf"


@pytest.mark.asyncio
async def test_binary_upload_is_not_retried_on_attachment_error() -> None:
    stub = FailingUploadStubTransport()
    bot = Bot("token", transport=cast(AiohttpSession, stub))

    with pytest.raises(BadRequestError):
        await bot.upload_file(b"file", filename="file.pdf")

    assert len(stub.uploads) == 1


@pytest.mark.asyncio
async def test_reply_markup_is_converted_to_inline_keyboard_attachment() -> None:
    stub = StubTransport()
    bot = Bot("token", transport=cast(AiohttpSession, stub))
    markup = (
        InlineKeyboardBuilder()
        .button(text="Confirm", callback_data="confirm")
        .as_markup()
    )
    message = incoming_message().bind(bot)

    await message.answer("Choose", reply_markup=markup)
    await message.reply("Choose", reply_markup=markup)
    await message.edit_text("Choose", reply_markup=markup)
    await bot.answer_callback("callback.keyboard", text="Choose", reply_markup=markup)

    for index, call in enumerate(stub.calls):
        body = call[2]["json"]
        if index == 3:
            body = body["message"]
        assert body["attachments"] == [markup.api_dump()]


@pytest.mark.asyncio
async def test_reply_markup_conflicts_with_inline_keyboard_attachment() -> None:
    stub = StubTransport()
    bot = Bot("token", transport=cast(AiohttpSession, stub))
    markup = InlineKeyboardBuilder().callback(text="One", payload="1").as_markup()

    with pytest.raises(ValidationError, match="cannot be combined"):
        await bot.send_message(
            "Choose",
            chat_id=100,
            attachments=[markup],
            reply_markup=markup,
        )
    assert stub.calls == []


@pytest.mark.asyncio
async def test_edit_reply_markup_none_differs_from_empty_attachments() -> None:
    stub = StubTransport()
    bot = Bot("token", transport=cast(AiohttpSession, stub))
    bot._target_limiter = cast(Any, RecordingLimiter())

    await bot.edit_message("mid.keep", text="Keep", reply_markup=None)
    await bot.edit_message("mid.clear", text="Clear", attachments=[])

    assert "attachments" not in stub.calls[0][2]["json"]
    assert stub.calls[1][2]["json"]["attachments"] == []


@pytest.mark.asyncio
async def test_format_serialization_for_message_callback_and_comments() -> None:
    class FormattingTransport(StubTransport):
        async def request(self, method: str, path: str, **kwargs: Any) -> Any:
            if method == "POST" and path.endswith("/comments"):
                self.calls.append((method, path, kwargs))
                return {"message": sent_message_result()["message"]}
            return await super().request(method, path, **kwargs)

    stub = FormattingTransport()
    bot = Bot("token", transport=cast(AiohttpSession, stub))
    bot._target_limiter = cast(Any, RecordingLimiter())
    message = incoming_message().bind(bot)
    callback = CallbackQuery.model_validate(
        {
            "timestamp": 1,
            "callback_id": "callback.shortcut",
            "user": {"user_id": 42, "first_name": "Ada", "is_bot": False},
        }
    ).bind(bot)

    await bot.send_message("HTML", chat_id=100, format=TextFormat.HTML)
    await message.answer("Markdown", format=TextFormat.MARKDOWN)
    await message.reply("HTML", format=TextFormat.HTML)
    await bot.edit_message("mid.1", text="Markdown", format=TextFormat.MARKDOWN)
    await message.edit_text("HTML", format=TextFormat.HTML)
    await bot.answer_callback("callback.1", text="Markdown", format="markdown")
    await callback.answer(text="HTML", format=TextFormat.HTML)
    await bot.send_comment("post.1", "HTML", format=TextFormat.HTML)
    await bot.edit_comment("post.1", "comment.1", text="Markdown", format="markdown")

    formats = []
    for call in stub.calls:
        body = call[2]["json"]
        if call[1] == "/answers":
            body = body["message"]
        formats.append(body["format"])
    assert formats == [
        "html",
        "markdown",
        "html",
        "markdown",
        "html",
        "markdown",
        "html",
        "html",
        "markdown",
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("failure_count", "expected_sleeps"),
    [(1, [0.5]), (2, [0.5, 1.0])],
)
async def test_attachment_not_ready_retries_until_send_succeeds(
    monkeypatch: pytest.MonkeyPatch,
    failure_count: int,
    expected_sleeps: list[float],
) -> None:
    stub = SequenceTransport(
        [attachment_not_ready() for _ in range(failure_count)] + [sent_message_result()]
    )
    bot = Bot("token", transport=cast(AiohttpSession, stub))
    limiter = RecordingLimiter()
    bot._target_limiter = cast(Any, limiter)
    sleeps: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr("aiomax2.bot.asyncio.sleep", fake_sleep)
    result = await bot.send_message(
        "File",
        chat_id=100,
        attachments=[{"type": "file", "payload": {"token": "file-token"}}],
    )

    assert result.message_id == "sent.1"
    assert len(stub.calls) == failure_count + 1
    assert sleeps == expected_sleeps
    assert limiter.keys == ["chat:100"] * (failure_count + 1)


@pytest.mark.asyncio
async def test_attachment_not_ready_retry_budget_is_bounded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub = SequenceTransport(
        [attachment_not_ready(), attachment_not_ready(), attachment_not_ready()]
    )
    bot = Bot(
        "token",
        transport=cast(AiohttpSession, stub),
        attachment_retries=2,
    )
    sleeps: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr("aiomax2.bot.asyncio.sleep", fake_sleep)
    with pytest.raises(BadRequestError) as error:
        await bot.send_message(
            "File",
            chat_id=100,
            attachments=[{"type": "file", "payload": {"token": "file-token"}}],
        )

    assert error.value.payload["code"] == "attachment.not.ready"
    assert len(stub.calls) == 3
    assert sleeps == [0.5, 1.0]


@pytest.mark.asyncio
async def test_other_bad_request_is_not_retried(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bad_request = BadRequestError(
        400,
        "Invalid payload",
        payload={"code": "invalid.payload", "message": "Invalid payload"},
    )
    stub = SequenceTransport([bad_request])
    bot = Bot("token", transport=cast(AiohttpSession, stub))

    async def fail_sleep(_: float) -> None:
        pytest.fail("sleep must not be called for another 400 response")

    monkeypatch.setattr("aiomax2.bot.asyncio.sleep", fail_sleep)
    with pytest.raises(BadRequestError):
        await bot.send_message(
            "File",
            chat_id=100,
            attachments=[{"type": "file", "payload": {"token": "file-token"}}],
        )

    assert len(stub.calls) == 1


@pytest.mark.asyncio
async def test_attachment_retry_applies_to_edit_and_callback_update(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub = SequenceTransport(
        [
            attachment_not_ready(),
            {"success": True},
            attachment_not_ready(),
            {"success": True},
        ]
    )
    bot = Bot("token", transport=cast(AiohttpSession, stub))
    limiter = RecordingLimiter()
    bot._target_limiter = cast(Any, limiter)

    async def fake_sleep(_: float) -> None:
        return None

    monkeypatch.setattr("aiomax2.bot.asyncio.sleep", fake_sleep)
    attachment = {"type": "file", "payload": {"token": "file-token"}}

    assert (
        await bot.edit_message("mid.1", attachments=[attachment], chat_id=100) is True
    )
    assert (
        await bot.answer_callback(
            "callback.1",
            text="File",
            attachments=[attachment],
            user_id=42,
        )
        is True
    )
    assert [call[1] for call in stub.calls] == [
        "/messages",
        "/messages",
        "/answers",
        "/answers",
    ]
    assert limiter.keys == ["chat:100", "chat:100", "user:42", "user:42"]
