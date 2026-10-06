# Быстрый старт

Создайте `bot.py`:

```python
import asyncio
import os

from aiomax2 import Bot, Dispatcher, Router
from aiomax2.filters import Command
from aiomax2.types import Message

router = Router()


@router.message(Command("start"))
async def start(message: Message) -> None:
    await message.answer("Привет!")


async def main() -> None:
    bot = Bot(os.environ["MAX_BOT_TOKEN"])

    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
```

Запустите:

```bash
python bot.py
```

## Что здесь происходит

`Bot` хранит токен, управляет HTTP transport и предоставляет методы MAX API.
Обычно на всё приложение создаётся один объект `Bot`.

`Dispatcher` получает raw updates, превращает их в типизированные объекты,
создаёт context/FSM и запускает цепочку роутеров.

`Router` хранит handlers для выбранной функциональной области. Большой бот
может иметь отдельные роутеры для пользователей, администраторов и платежей.

`Command("start")` — фильтр. Он принимает `/start` и `/start 123`; во втором
случае аргумент `123` доступен через `CommandObject.args`.

`Message` — модель сообщения MAX. `message.answer()` выбирает `chat_id` или
`user_id`, отправляет сообщение через связанный `Bot` и применяет rate limits.

Пример использует Long Polling, чтобы локальный запуск не требовал публичного
HTTPS endpoint. В production перейдите на [Webhook](webhook.md).

## Inline-клавиатура

```python
from aiomax2.utils.keyboard import InlineKeyboardBuilder

builder = InlineKeyboardBuilder()
builder.button(text="Подтвердить", callback_data="confirm")
builder.button(text="Отменить", callback_data="cancel")
builder.adjust(2)

await message.answer("Выберите действие", reply_markup=builder.as_markup())
```

`reply_markup` — удобный слой над настоящим inline-keyboard attachment MAX.
Подробности и все семь типов кнопок: [Inline-клавиатуры](keyboards.md).

## Одна кодовая база для двух режимов

Выбирать режим можно через deployment configuration, не создавая отдельный
`Bot`/`Dispatcher`/`Router` stack:

```bash
MAX_MODE=polling python examples/modes.py
```

```bash
MAX_MODE=webhook uvicorn examples.modes:app --host 127.0.0.1 --port 8000
```

Готовый application pattern находится в `examples/modes.py`. Он использует
существующие `start_polling()` и `webhook_router()` и намеренно не запускает
Polling и Webhook одновременно. Переключение переменной не удаляет уже
зарегистрированную на стороне MAX Webhook-подписку: перед переходом на Polling
удалите её отдельным setup-командой через `bot.unsubscribe(webhook_url)`.
