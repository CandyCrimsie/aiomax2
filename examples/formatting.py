import asyncio
import os

from aiomax2 import Bot, Dispatcher, Router, TextFormat
from aiomax2.filters import Command
from aiomax2.types import Message

router = Router(name=__name__)


@router.message(Command("html"))
async def html_example(message: Message) -> None:
    await message.answer(
        "<b>Жирный</b> <i>курсив</i> <u>подчёркнутый</u> "
        '<a href="https://dev.max.ru">ссылка</a>\n'
        '<a href="max://user/123456">упоминание</a>\n'
        "<s>зачёркнутый</s> <code>код</code>\n"
        "<blockquote>Цитата</blockquote>",
        format=TextFormat.HTML,
    )


@router.message(Command("markdown"))
async def markdown_example(message: Message) -> None:
    await message.answer(
        "**Жирный** _курсив_ ++подчёркнутый++ ~~зачёркнутый~~\n"
        "`код` [ссылка](https://dev.max.ru)\n"
        "[Упоминание](max://user/123456)\n"
        "> Цитата",
        format=TextFormat.MARKDOWN,
    )


async def main() -> None:
    bot = Bot(os.environ["MAX_BOT_TOKEN"])
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.close()
        await dispatcher.close()


if __name__ == "__main__":
    asyncio.run(main())
