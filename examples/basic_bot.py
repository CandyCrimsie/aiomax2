import asyncio
import os

from aiomax2 import Bot, Dispatcher, F, Router
from aiomax2.filters import Command, CommandObject
from aiomax2.types import Message

router = Router(name=__name__)


@router.message(Command("start"))
async def start(message: Message, command: CommandObject) -> None:
    await message.answer(f"Привет из MAX! args={command.args!r}")


@router.message(F.text == "пинг")
async def ping(message: Message) -> None:
    await message.reply("понг")


async def main() -> None:
    bot = Bot(os.environ["MAX_BOT_TOKEN"])
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
