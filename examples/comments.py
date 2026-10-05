import asyncio
import os

from aiomax2 import Bot, Dispatcher, Router
from aiomax2.filters import Command
from aiomax2.types import Message

router = Router(name=__name__)


@router.message(Command("comment"))
async def comment(message: Message, bot: Bot) -> None:
    post_id = os.environ["MAX_POST_ID"]
    created = await bot.send_comment(post_id, "Комментарий от бота")
    await message.answer(f"Создан комментарий {created.body.mid}")


async def main() -> None:
    bot = Bot(os.environ["MAX_BOT_TOKEN"])
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
