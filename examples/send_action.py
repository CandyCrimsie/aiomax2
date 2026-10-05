import asyncio
import os

from aiomax2 import Bot, Dispatcher, Router
from aiomax2.enums import SenderAction
from aiomax2.filters import Command
from aiomax2.types import Message

router = Router(name=__name__)


@router.message(Command("typing"))
async def typing(message: Message, bot: Bot) -> None:
    if message.chat_id is None:
        await message.answer("send_action требует chat_id")
        return
    await bot.send_action(message.chat_id, SenderAction.TYPING_ON)
    await message.answer("Действие typing_on отправлено")


async def main() -> None:
    bot = Bot(os.environ["MAX_BOT_TOKEN"])
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
