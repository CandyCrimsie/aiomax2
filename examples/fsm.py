import asyncio
import os

from aiomax2 import Bot, Dispatcher, Router
from aiomax2.filters import CommandStart
from aiomax2.fsm import FSMContext, State, StatesGroup
from aiomax2.types import Message

router = Router(name=__name__)


class Form(StatesGroup):
    name = State()
    age = State()


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.name)
    await message.answer("Как вас зовут?")


@router.message(Form.name)
async def name(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Отправьте имя текстом")
        return
    await state.update_data(name=message.text)
    await state.set_state(Form.age)
    await message.answer("Сколько вам лет?")


@router.message(Form.age)
async def age(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.isdigit():
        await message.answer("Отправьте возраст числом")
        return
    data = await state.update_data(age=int(message.text))
    await message.answer(f"Готово: {data['name']}, {data['age']}")
    await state.clear()


async def main() -> None:
    bot = Bot(os.environ["MAX_BOT_TOKEN"])
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
