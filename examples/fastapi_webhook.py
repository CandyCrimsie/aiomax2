import os

from fastapi import FastAPI

from aiomax2 import Bot, Dispatcher, Router
from aiomax2.filters import Command
from aiomax2.types import Message

bot = Bot(os.environ["MAX_BOT_TOKEN"])
dispatcher = Dispatcher()
router = Router(name=__name__)


@router.message(Command("start"))
async def start(message: Message) -> None:
    await message.answer("Hello from a MAX webhook")


dispatcher.include_router(router)
app = FastAPI()
app.include_router(
    dispatcher.webhook_router(
        "/webhook",
        bot=bot,
        secret=os.environ.get("MAX_WEBHOOK_SECRET"),
    )
)


@app.on_event("shutdown")
async def shutdown() -> None:
    await bot.close()
    await dispatcher.close()
