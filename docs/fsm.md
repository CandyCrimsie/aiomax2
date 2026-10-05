# FSM

Finite State Machine помогает вести многошаговый диалог. `aiomax2` предоставляет
`State`, `StatesGroup`, `FSMContext`, стратегии ключей и async storage API.

## Анкета: имя и возраст

```python
from aiomax2 import Router
from aiomax2.filters import CommandStart
from aiomax2.fsm import FSMContext, State, StatesGroup
from aiomax2.types import Message

router = Router()


class Form(StatesGroup):
    name = State()
    age = State()


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.name)
    await message.answer("Как вас зовут?")


@router.message(Form.name)
async def save_name(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Отправьте имя текстом")
        return
    await state.update_data(name=message.text)
    await state.set_state(Form.age)
    await message.answer("Сколько вам лет?")


@router.message(Form.age)
async def save_age(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.isdigit():
        await message.answer("Отправьте возраст числом")
        return
    data = await state.update_data(age=int(message.text))
    await message.answer(f"Готово: {data['name']}, {data['age']}")
    await state.clear()
```

`Dispatcher` по умолчанию использует стратегию `USER_IN_CHAT`: состояние
разделяется по bot, chat и user. Доступны также `CHAT` и `GLOBAL_USER`.

## Storage

По умолчанию создаётся `MemoryStorage`. Оно подходит для тестов, локальной
разработки и простого single-process bot, но данные теряются при перезапуске и
не разделяются между workers.

Для multi-process production потребуется внешнее storage. Redis storage и
event isolation находятся в roadmap. До их появления можно реализовать
собственный `BaseStorage` и передать его в `Dispatcher(storage=...)`.

