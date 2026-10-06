# aiomax2

[![CI](https://github.com/CandyCrimsie/aiomax2/actions/workflows/ci.yml/badge.svg)](https://github.com/CandyCrimsie/aiomax2/actions/workflows/ci.yml)

`aiomax2` — асинхронный Python-фреймворк для
[MAX Bot API](https://dev.max.ru/docs-api) с developer experience, знакомым по
aiogram 3.x. Библиотека предоставляет `Bot`, `Dispatcher`, вложенные `Router`,
фильтры, middleware, FSM, Webhook и Long Polling, но сохраняет реальные
сущности и ограничения MAX.

> **Статус: Alpha (`0.1.0a2`).** Публичный API ещё может меняться до стабильной
> версии. Модели сверены с официальной OpenAPI-схемой `0.0.33` 5 октября 2026
> года.

## Возможности

- типизированные модели событий и ответов MAX на Pydantic 2;
- `Router`/`Dispatcher`, вложенные роутеры и первый подходящий handler;
- `Command`, `CommandStart` и magic filters через `F`;
- outer/inner middleware и context injection по сигнатуре;
- shortcuts `answer`, `reply`, `edit_text`, `delete` и callback `answer`;
- FSM с `MemoryStorage`;
- production-oriented Webhook и адаптер для FastAPI;
- Long Polling для разработки и тестирования;
- единая `aiohttp`-сессия API, connection pooling, TLS, безопасные retries;
- автоматическая обработка `429`, глобальный лимит 30 rps и target-лимиты;
- загрузка изображений, видео, аудио и файлов;
- низкоуровневый доступ через методы `Bot` и `Bot.request()`.

## Установка

Требуется Python 3.12 или новее.

```bash
pip install "aiomax2 @ git+https://github.com/CandyCrimsie/aiomax2.git"
```

Для FastAPI-интеграции:

```bash
pip install "aiomax2[fastapi] @ git+https://github.com/CandyCrimsie/aiomax2.git"
```

Локальная установка для разработки:

```bash
git clone https://github.com/CandyCrimsie/aiomax2.git
cd aiomax2
python -m pip install -e ".[dev]"
```

## Быстрый старт

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

- `Bot` выполняет типизированные запросы к MAX API.
- `Dispatcher` принимает updates и управляет их обработкой.
- `Router` группирует handlers, фильтры и middleware.
- `Command("start")` пропускает сообщения `/start` и `/start аргументы`.
- `Message` — реальная модель сообщения MAX с удобными shortcuts.

Long Polling ограничен MAX по скорости и сроку хранения событий, поэтому
предназначен для разработки и тестов. Для production используйте Webhook.

## Webhook

```python
from contextlib import asynccontextmanager
import os

from fastapi import FastAPI

from aiomax2 import Bot, Dispatcher, Router

bot = Bot(os.environ["MAX_BOT_TOKEN"])
dp = Dispatcher()
router = Router()
dp.include_router(router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await bot.close()
    await dp.close()


app = FastAPI(lifespan=lifespan)
app.include_router(
    dp.webhook_router(
        "/webhook",
        bot=bot,
        secret=os.environ["MAX_WEBHOOK_SECRET"],
    )
)
```

Зарегистрируйте HTTPS endpoint в MAX:

```python
await bot.subscribe(
    "https://bot.example.ru/webhook",
    secret="replace-with-a-random-secret",
    update_types=["message_created", "message_callback", "bot_started"],
)
```

MAX передаёт secret в `X-Max-Bot-Api-Secret` и ожидает `200 OK` не позднее
30 секунд. Подробности — в [руководстве по Webhook](docs/webhook.md).

## Команды и фильтры

```python
from aiomax2 import F
from aiomax2.filters import Command, CommandObject


@router.message(Command("start"))
async def start(message: Message, command: CommandObject) -> None:
    await message.answer(f"Аргументы: {command.args!r}")


@router.message(F.text.startswith("hello"))
async def hello(message: Message) -> None:
    await message.reply("Привет!")
```

## Callback-кнопки

Клавиатура MAX является attachment сообщения, а не Telegram reply markup:

```python
from aiomax2 import F
from aiomax2.types import (
    CallbackButton,
    CallbackQuery,
    InlineKeyboardAttachmentRequest,
    Keyboard,
)

keyboard = InlineKeyboardAttachmentRequest(
    payload=Keyboard(buttons=[[CallbackButton(text="Подтвердить", payload="confirm")]])
)


@router.callback_query(F.payload == "confirm")
async def confirm(callback_query: CallbackQuery) -> None:
    await callback_query.answer(notification="Готово")
```

## FSM и Middleware

FSM включает `State`, `StatesGroup`, `FSMContext` и process-local
`MemoryStorage`. Middleware разделены на outer (до фильтров) и inner (после
фильтров). Практические сценарии находятся в [FSM guide](docs/fsm.md) и
[middleware guide](docs/middleware.md).

## Работа с MAX API

```python
me = await bot.get_my_info()
message = await bot.send_message("Привет", chat_id=123)
same_message = await bot.get_message(message.message_id)

# Для ещё не обёрнутого endpoint остаётся низкоуровневый вызов:
payload = await bot.request("GET", "/me")
```

## Rate limits

`AiohttpSession` централизованно ограничивает все исходящие запросы к API до
30 rps. Для `POST /messages`, `PUT /messages`, `DELETE /messages` и
`POST /answers` aiomax2 консервативно использует единый локальный лимит
2 операции/с на target. Это соблюдает документированные ограничения MAX,
но в смешанных сценариях может ограничивать throughput сильнее сервера.
Входящий поток `MAX -> webhook` в API limiter не входит.

Limiter локален для одного процесса и одного transport instance. Несколько
workers требуют внешнего shared limiter или ручного распределения общего
лимита. См. [подробное описание](docs/rate-limits.md).

## Сертификаты Минцифры

Проверка TLS никогда не отключается, в том числе при передаче custom
`aiohttp.ClientSession`: transport явно применяет свой `SSLContext` к API
requests. Дополнительный CA bundle можно передать одним из способов:

```python
bot = Bot(token, ca_file="/path/to/russian_trusted_ca.pem")
```

```python
bot = Bot(token, ssl_context=context)
```

Подробнее: [TLS и сертификаты](docs/certificates.md).

## Документация

- [Установка](docs/installation.md)
- [Быстрый старт](docs/quickstart.md)
- [Long Polling](docs/polling.md)
- [Webhook](docs/webhook.md)
- [Router и Dispatcher](docs/router.md)
- [Фильтры и команды](docs/filters.md)
- [Callback-кнопки](docs/callbacks.md)
- [FSM](docs/fsm.md)
- [Загрузки](docs/uploads.md)
- [Покрытие MAX API](docs/api-coverage.md)
- [Миграция с aiogram](docs/migration-from-aiogram.md)
- [Roadmap](docs/roadmap.md)

## Миграция с aiogram

Знакомые концепции намеренно имеют похожие имена, но Telegram-поля и сущности
не эмулируются. Например, в MAX используется `message.chat_id`, объект
`message.recipient` и attachment-клавиатура. Сравнения и примеры собраны в
[руководстве по миграции](docs/migration-from-aiogram.md).

## Статус проекта

Проект находится в alpha-стадии. Перед production-внедрением зафиксируйте
версию зависимости, используйте Webhook, общий limiter для multi-worker
deployment и внешнее FSM-хранилище. Сообщения об ошибках и pull requests
приветствуются.
