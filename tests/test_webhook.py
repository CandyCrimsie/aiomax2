from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from aiomax2 import Bot, Dispatcher
from aiomax2.exceptions import WebhookSecretError
from aiomax2.types import Message
from aiomax2.webhook import MAX_SECRET_HEADER, WebhookHandler


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
