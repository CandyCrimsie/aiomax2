import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from aiomax2 import Bot, Dispatcher, Router
from aiomax2.filters import Command
from aiomax2.types import Message

bot = Bot(os.environ["MAX_BOT_TOKEN"])
dispatcher = Dispatcher()
router = Router(name=__name__)


@router.message(Command("start"))
async def start(message: Message) -> None:
    await message.answer("Привет из MAX Webhook")


dispatcher.include_router(router)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    webhook_url = os.environ.get("MAX_WEBHOOK_URL")
    if webhook_url is not None:
        await bot.subscribe(
            webhook_url,
            secret=os.environ.get("MAX_WEBHOOK_SECRET"),
            update_types=dispatcher.resolve_used_update_types(),
        )
    yield
    await bot.close()
    await dispatcher.close()


app = FastAPI(lifespan=lifespan)
app.include_router(
    dispatcher.webhook_router(
        "/webhook",
        bot=bot,
        secret=os.environ.get("MAX_WEBHOOK_SECRET"),
    )
)
