from typing import Any

from aiomax2.bot import Bot
from aiomax2.dispatcher import Dispatcher
from aiomax2.exceptions import WebhookSecretError

from .handler import WebhookHandler


def create_webhook_router(
    dispatcher: Dispatcher,
    bot: Bot,
    *,
    path: str = "/webhook",
    secret: str | None = None,
    **feed_data: Any,
) -> Any:
    """Create a FastAPI `APIRouter` without making FastAPI a core dependency."""

    try:
        from fastapi import APIRouter, HTTPException, Request, Response
    except ImportError as exc:
        raise RuntimeError(
            "FastAPI integration requires `pip install aiomax2[fastapi]`"
        ) from exc

    router = APIRouter()
    webhook = WebhookHandler(dispatcher, bot, secret=secret, **feed_data)

    @router.post(path, include_in_schema=False)
    async def max_webhook(request: Request) -> Response:
        try:
            await webhook.handle(await request.body(), headers=request.headers)
        except WebhookSecretError as exc:
            raise HTTPException(
                status_code=403, detail="invalid webhook secret"
            ) from exc
        return Response(status_code=200)

    return router
