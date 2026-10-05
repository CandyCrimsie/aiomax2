import asyncio
import os

from aiomax2 import Bot, Dispatcher, F, Router
from aiomax2.types import (
    CallbackButton,
    CallbackQuery,
    InlineKeyboardAttachmentRequest,
    Keyboard,
    Message,
)

router = Router(name=__name__)


@router.message(F.text == "кнопки")
async def buttons(message: Message) -> None:
    keyboard = InlineKeyboardAttachmentRequest(
        payload=Keyboard(
            buttons=[
                [CallbackButton(text="Подтвердить", payload="confirm")],
                [CallbackButton(text="Отменить", payload="cancel")],
            ]
        )
    )
    await message.answer("Выберите действие", attachments=[keyboard])


@router.callback_query(F.payload == "confirm")
async def confirm(callback_query: CallbackQuery) -> None:
    await callback_query.answer(notification="Подтверждено", text="Готово")


async def main() -> None:
    bot = Bot(os.environ["MAX_BOT_TOKEN"])
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
