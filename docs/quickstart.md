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

