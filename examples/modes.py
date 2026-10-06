import asyncio
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from aiomax2 import Bot, Dispatcher, Router
from aiomax2.filters import Command
from aiomax2.types import Message

WEBHOOK_PATH = "/webhook"
MAX_MODE = os.environ.get("MAX_MODE", "polling").lower()

if MAX_MODE not in {"polling", "webhook"}:
    raise RuntimeError("MAX_MODE must be 'polling' or 'webhook'")

MAX_WEBHOOK_BASE_URL = (
    os.environ["MAX_WEBHOOK_BASE_URL"].rstrip("/") if MAX_MODE == "webhook" else ""
)
MAX_WEBHOOK_SECRET = os.environ["MAX_WEBHOOK_SECRET"] if MAX_MODE == "webhook" else ""
WEBHOOK_URL = f"{MAX_WEBHOOK_BASE_URL}{WEBHOOK_PATH}"

bot = Bot(os.environ["MAX_BOT_TOKEN"])
dp = Dispatcher()
router = Router(name=__name__)


@router.message(Command("start"))
async def start(message: Message) -> None:
    await message.answer(f"Бот запущен в режиме {MAX_MODE}")


dp.include_router(router)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    if MAX_MODE != "webhook":
        raise RuntimeError("Set MAX_MODE=webhook before starting Uvicorn")
    try:
        await bot.subscribe(
            WEBHOOK_URL,
            secret=MAX_WEBHOOK_SECRET,
            update_types=dp.resolve_used_update_types(),
        )
        yield
    finally:
        await bot.close()
        await dp.close()


app = FastAPI(lifespan=lifespan)
if MAX_MODE == "webhook":
    app.include_router(
        dp.webhook_router(
            WEBHOOK_PATH,
            bot=bot,
            secret=MAX_WEBHOOK_SECRET,
        )
    )


async def run_polling() -> None:
    if MAX_MODE != "polling":
        raise RuntimeError("Set MAX_MODE=polling before running this script")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.close()
        await dp.close()


if __name__ == "__main__":
    asyncio.run(run_polling())
