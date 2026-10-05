import asyncio
import os

from aiomax2 import Bot, Dispatcher, F, Router
from aiomax2.types import Message

router = Router(name=__name__)


@router.message(F.text == "hello")
async def exact(message: Message) -> None:
    await message.answer("Точное совпадение")


@router.message(F.text.startswith("привет"))
async def prefix(message: Message) -> None:
    await message.answer("Сообщение начинается с «привет»")


@router.message(F.text.contains("max"))
async def contains(message: Message) -> None:
    await message.answer("В тексте найдено «max»")


async def main() -> None:
    bot = Bot(os.environ["MAX_BOT_TOKEN"])
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
