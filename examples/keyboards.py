import asyncio
import os

from aiomax2 import Bot, Dispatcher, F, Router
from aiomax2.filters import Command
from aiomax2.types import CallbackQuery, Message
from aiomax2.utils.keyboard import InlineKeyboardBuilder

router = Router(name=__name__)


@router.message(Command("keyboard"))
async def keyboard(message: Message) -> None:
    builder = InlineKeyboardBuilder()
    builder.button(text="Подтвердить", callback_data="confirm")
    builder.button(text="Отменить", callback_data="cancel")
    builder.link(text="Документация MAX", url="https://dev.max.ru/docs-api")
    builder.clipboard(text="Скопировать код", payload="ABC-123")
    builder.message(text="/help")
    builder.request_contact(text="Поделиться контактом")
    builder.request_geo_location(text="Отправить геопозицию", quick=False)
    builder.open_app(
        text="Открыть приложение",
        web_app="your-web-app-id",
        payload="start-screen",
    )
    builder.adjust(2, 2, 1)

    await message.answer(
        "Выберите действие",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.payload == "confirm")
async def confirm(callback: CallbackQuery) -> None:
    await callback.answer(
        notification="Подтверждено",
        text="Готово",
    )


@router.callback_query(F.payload == "cancel")
async def cancel(callback: CallbackQuery) -> None:
    # MAX допускает notification без изменения исходного сообщения.
    await callback.answer(notification="Отменено")


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
