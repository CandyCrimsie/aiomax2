from __future__ import annotations

import hmac
import json
from collections.abc import Mapping
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from aiomax2.bot import Bot
from aiomax2.dispatcher import Dispatcher
from aiomax2.exceptions import WebhookPayloadError, WebhookSecretError
from aiomax2.types import parse_update

MAX_SECRET_HEADER = "X-Max-Bot-Api-Secret"


class WebhookHandler:
    """Framework-neutral MAX webhook parser, verifier, and dispatcher."""

    def __init__(
        self,
        dispatcher: Dispatcher,
        bot: Bot,
        *,
        secret: str | None = None,
        **feed_data: Any,
    ) -> None:
        self.dispatcher = dispatcher
        self.bot = bot
        self.secret = secret
        self.feed_data = feed_data

    def verify_secret(self, headers: Mapping[str, str]) -> None:
        if self.secret is None:
            return
        supplied = next(
            (
                value
                for key, value in headers.items()
                if key.casefold() == MAX_SECRET_HEADER.casefold()
            ),
            None,
        )
        if supplied is None or not hmac.compare_digest(supplied, self.secret):
            raise WebhookSecretError("invalid MAX webhook secret")

    async def handle(
        self,
        body: bytes | str | Mapping[str, Any],
        *,
        headers: Mapping[str, str],
    ) -> Any:
        self.verify_secret(headers)
        if isinstance(body, Mapping):
            payload = dict(body)
        else:
            try:
                payload = json.loads(body)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise WebhookPayloadError("webhook body is not valid JSON") from exc
        if not isinstance(payload, dict):
            raise WebhookPayloadError("MAX webhook payload must be a JSON object")
        try:
            update = parse_update(payload)
        except PydanticValidationError as exc:
            raise WebhookPayloadError("webhook body is not a valid MAX update") from exc
        return await self.dispatcher.feed_update(self.bot, update, **self.feed_data)
