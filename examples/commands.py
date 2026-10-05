import asyncio
import os

from aiomax2 import Bot, Dispatcher, Router
from aiomax2.filters import Command, CommandObject, CommandStart
from aiomax2.types import Message

router = Router(name=__name__)


@router.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer("Используйте /echo текст")


@router.message(Command("echo"))
async def echo(message: Message, command: CommandObject) -> None:
    await message.answer(command.args or "Аргументы не переданы")


async def main() -> None:
    bot = Bot(os.environ["MAX_BOT_TOKEN"])
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
