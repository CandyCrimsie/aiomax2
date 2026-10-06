import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from aiomax2 import Bot, Dispatcher, Router
from aiomax2.filters import Command
from aiomax2.types import Message

WEBHOOK_PATH = "/webhook"
MAX_WEBHOOK_BASE_URL = os.environ["MAX_WEBHOOK_BASE_URL"].rstrip("/")
MAX_WEBHOOK_SECRET = os.environ["MAX_WEBHOOK_SECRET"]
WEBHOOK_URL = f"{MAX_WEBHOOK_BASE_URL}{WEBHOOK_PATH}"

bot = Bot(os.environ["MAX_BOT_TOKEN"])
dispatcher = Dispatcher()
router = Router(name=__name__)


@router.message(Command("start"))
async def start(message: Message) -> None:
    await message.answer("Привет из MAX Webhook")


dispatcher.include_router(router)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    try:
        await bot.subscribe(
            WEBHOOK_URL,
            secret=MAX_WEBHOOK_SECRET,
            update_types=dispatcher.resolve_used_update_types(),
        )
        yield
    finally:
        await bot.close()
        await dispatcher.close()


app = FastAPI(lifespan=lifespan)
app.include_router(
    dispatcher.webhook_router(
        WEBHOOK_PATH,
        bot=bot,
        secret=MAX_WEBHOOK_SECRET,
    )
)
