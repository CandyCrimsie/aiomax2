import asyncio
import os

from aiomax2 import Bot, Dispatcher, Router
from aiomax2.filters import Command
from aiomax2.types import Message

router = Router(name=__name__)


@router.message(Command("actions"))
async def actions(message: Message) -> None:
    await message.answer("Обычный ответ")
    await message.reply("Ответ со ссылкой на исходное сообщение")
    sent = await message.answer("Этот текст будет изменён")
    await sent.edit_text("Текст изменён")
    await sent.delete()


async def main() -> None:
    bot = Bot(os.environ["MAX_BOT_TOKEN"])
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
