from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from aiomax2 import Bot, Dispatcher, Router
from aiomax2.exceptions import WebhookPayloadError, WebhookSecretError
from aiomax2.types import Message, Update
from aiomax2.webhook import MAX_SECRET_HEADER, WebhookHandler
from tests.update_cases import ALL_UPDATE_CASES, ALL_UPDATE_TYPES


@pytest.mark.asyncio
async def test_webhook_secret_and_dispatch(
    message_update: dict[str, Any],
) -> None:
    bot = Bot("token")
    dispatcher = Dispatcher()
    seen: list[str | None] = []

    @dispatcher.message()
    async def handler(message: Message) -> None:
        seen.append(message.text)

    webhook = WebhookHandler(dispatcher, bot, secret="secret")
    await webhook.handle(
        json.dumps(message_update),
        headers={MAX_SECRET_HEADER.lower(): "secret"},
    )

    assert seen == ["/start 123"]
    await bot.close()


@pytest.mark.asyncio
async def test_webhook_rejects_invalid_secret(
    message_update: dict[str, Any],
) -> None:
    webhook = WebhookHandler(Dispatcher(), Bot("token"), secret="secret")

    with pytest.raises(WebhookSecretError):
        await webhook.handle(message_update, headers={MAX_SECRET_HEADER: "wrong"})

    await webhook.bot.close()


@pytest.mark.asyncio
async def test_fastapi_adapter(
    message_update: dict[str, Any],
) -> None:
    bot = Bot("token")
    dispatcher = Dispatcher()
    seen: list[str | None] = []

    @dispatcher.message()
    async def handler(message: Message) -> None:
        seen.append(message.text)

    app = FastAPI()
    app.include_router(dispatcher.webhook_router("/webhook", bot=bot, secret="secret"))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        forbidden = await client.post("/webhook", json=message_update)
        accepted = await client.post(
            "/webhook",
            json=message_update,
            headers={MAX_SECRET_HEADER: "secret"},
        )

    assert forbidden.status_code == 403
    assert accepted.status_code == 200
    assert seen == ["/start 123"]
    await bot.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ALL_UPDATE_CASES, ids=ALL_UPDATE_TYPES)
async def test_every_update_round_trips_through_fastapi_webhook(case: Any) -> None:
    bot = Bot("token")
    dispatcher = Dispatcher()
    router = Router(name=f"webhook-{case.update_type}")
    dispatcher.include_router(router)
    seen: list[tuple[object, Update]] = []

    async def handler(event: object, event_update: Update) -> None:
        seen.append((event, event_update))

    getattr(router, case.observer).register(handler)
    app = FastAPI()
    app.include_router(dispatcher.webhook_router("/webhook", bot=bot, secret="secret"))

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/webhook",
            json=case.raw(),
            headers={MAX_SECRET_HEADER: "secret"},
        )

    assert response.status_code == 200
    assert len(seen) == 1
    event, update = seen[0]
    assert isinstance(event, case.event_type)
    assert isinstance(update, case.model_type)
    assert update.require_bot() is bot
    await dispatcher.close()
    await bot.close()


@pytest.mark.asyncio
async def test_fastapi_webhook_secret_missing_wrong_and_valid(
    message_update: dict[str, Any],
) -> None:
    bot = Bot("token")
    dispatcher = Dispatcher()
    app = FastAPI()
    app.include_router(dispatcher.webhook_router("/webhook", bot=bot, secret="secret"))

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        missing = await client.post("/webhook", json=message_update)
        wrong = await client.post(
            "/webhook",
            json=message_update,
            headers={MAX_SECRET_HEADER: "wrong"},
        )
        valid = await client.post(
            "/webhook",
            json=message_update,
            headers={MAX_SECRET_HEADER: "secret"},
        )

    assert missing.status_code == 403
    assert wrong.status_code == 403
    assert valid.status_code == 200
    await dispatcher.close()
    await bot.close()


def test_webhook_secret_uses_constant_time_comparison(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str]] = []

    def compare_digest(left: str, right: str) -> bool:
        calls.append((left, right))
        return left == right

    monkeypatch.setattr("aiomax2.webhook.handler.hmac.compare_digest", compare_digest)
    webhook = WebhookHandler(Dispatcher(), Bot("token"), secret="secret")

    webhook.verify_secret({MAX_SECRET_HEADER.lower(): "secret"})

    assert calls == [("secret", "secret")]


@pytest.mark.asyncio
async def test_unknown_update_and_extra_fields_are_forward_compatible() -> None:
    bot = Bot("token")
    dispatcher = Dispatcher()
    seen: list[Update] = []

    @dispatcher.update()
    async def handler(update: Update) -> None:
        seen.append(update)

    app = FastAPI()
    app.include_router(dispatcher.webhook_router("/webhook", bot=bot, secret="secret"))
    payload = {
        "update_type": "future_update",
        "timestamp": 1,
        "future_field": {"enabled": True},
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/webhook",
            json=payload,
            headers={MAX_SECRET_HEADER: "secret"},
        )

    assert response.status_code == 200
    assert type(seen[0]) is Update
    assert seen[0].model_extra == {"future_field": {"enabled": True}}
    await dispatcher.close()
    await bot.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("body", "content_type"),
    [
        (b"{not-json", "application/json"),
        (json.dumps({"update_type": "message_created"}).encode(), "application/json"),
        (json.dumps(["not", "an", "object"]).encode(), "application/json"),
    ],
)
async def test_malformed_webhook_payload_returns_400(
    body: bytes,
    content_type: str,
) -> None:
    bot = Bot("token")
    dispatcher = Dispatcher()
    app = FastAPI()
    app.include_router(dispatcher.webhook_router("/webhook", bot=bot, secret="secret"))

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/webhook",
            content=body,
            headers={
                MAX_SECRET_HEADER: "secret",
                "Content-Type": content_type,
            },
        )

    assert response.status_code == 400
    assert response.json() == {"detail": "invalid MAX webhook payload"}
    await dispatcher.close()
    await bot.close()


@pytest.mark.asyncio
async def test_webhook_handler_exceptions_remain_http_500(
    message_update: dict[str, Any],
) -> None:
    bot = Bot("token")
    dispatcher = Dispatcher()

    @dispatcher.message()
    async def failing_handler(message: Message) -> None:
        raise RuntimeError("handler failed")

    app = FastAPI()
    app.include_router(dispatcher.webhook_router("/webhook", bot=bot, secret="secret"))

    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/webhook",
            json=message_update,
            headers={MAX_SECRET_HEADER: "secret"},
        )

    assert response.status_code == 500
    await dispatcher.close()
    await bot.close()


@pytest.mark.asyncio
async def test_framework_webhook_rejects_invalid_json_directly() -> None:
    webhook = WebhookHandler(Dispatcher(), Bot("token"))

    with pytest.raises(WebhookPayloadError, match="not valid JSON"):
        await webhook.handle(b"{broken", headers={})

    await webhook.dispatcher.close()
    await webhook.bot.close()
