# aiomax2

[![CI](https://github.com/CandyCrimsie/aiomax2/actions/workflows/ci.yml/badge.svg)](https://github.com/CandyCrimsie/aiomax2/actions/workflows/ci.yml)
[![Documentation](https://github.com/CandyCrimsie/aiomax2/actions/workflows/docs.yml/badge.svg)](https://candycrimsie.github.io/aiomax2/)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/github/license/CandyCrimsie/aiomax2)](LICENSE)

**aiomax2** — асинхронный Python-фреймворк для
[MAX Bot API](https://dev.max.ru/docs-api).

Он предоставляет знакомую по aiogram 3.x архитектуру с `Bot`, `Dispatcher`,
`Router`, фильтрами, middleware, FSM и shortcuts, но работает с реальными
сущностями, методами и ограничениями MAX.

> **Статус: Alpha (`0.1.0a2`)**
>
> Библиотека находится в активной разработке. Публичный API до стабильного
> релиза может изменяться.

**Документация:** https://candycrimsie.github.io/aiomax2/

---

## Возможности

- полностью асинхронная работа через `asyncio` и `aiohttp`;
- типизированные модели MAX API на Pydantic 2;
- `Bot`, `Dispatcher` и вложенные `Router`;
- фильтры и magic filter `F`;
- `Command`, `CommandStart` и `CommandObject`;
- outer и inner middleware;
- dependency/context injection по сигнатуре handler;
- FSM с `FSMContext`, `State`, `StatesGroup` и `MemoryStorage`;
- shortcuts для сообщений и callback;
- `InlineKeyboardBuilder` и `reply_markup` для inline-клавиатур MAX;
- HTML и MAX Markdown через `TextFormat`;
- Long Polling;
- Webhook и интеграция с FastAPI;
- загрузка изображений, видео, аудио и файлов;
- управление webhook-подписками;
- типизированные исключения MAX API;
- автоматическая обработка `429` и `Retry-After`;
- встроенные rate limits;
- безопасный HTTP transport с обязательной TLS verification;
- поддержка custom `aiohttp.ClientSession`;
- поддержка дополнительного CA bundle;
- низкоуровневый доступ к MAX API через `Bot.request()`.

---

## Требования

- Python **3.12+**
- `aiohttp`
- Pydantic 2
- FastAPI
- Uvicorn

---

## Установка

Пока библиотека не опубликована на PyPI, её можно установить напрямую из
GitHub:

```bash
pip install "aiomax2 @ git+https://github.com/CandyCrimsie/aiomax2.git"
```

Эта единственная установка включает Long Polling, Webhook, FastAPI и Uvicorn.
Режим доставки updates выбирается в приложении или deployment configuration,
а не через package extra. После публикации на PyPI будет достаточно:

```bash
pip install aiomax2
```

Для локальной разработки:

```bash
git clone https://github.com/CandyCrimsie/aiomax2.git
cd aiomax2

python -m pip install -e ".[dev]"
```

---

## Быстрый старт

Создайте бота в MAX и передайте его token через переменную окружения
`MAX_BOT_TOKEN`.

```python
import asyncio
import os

from aiomax2 import Bot, Dispatcher, Router
from aiomax2.filters import Command
from aiomax2.types import Message

router = Router()


@router.message(Command("start"))
async def start(message: Message) -> None:
    await message.answer("Привет из aiomax2!")


async def main() -> None:
    bot = Bot(os.environ["MAX_BOT_TOKEN"])

    dp = Dispatcher()
    dp.include_router(router)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.close()
        await dp.close()


if __name__ == "__main__":
    asyncio.run(main())
```

Запуск:

```bash
python bot.py
```

---

## Dispatcher и Router

Обработчики группируются внутри `Router`, после чего router подключается к
`Dispatcher`.

```python
from aiomax2 import Dispatcher, Router
from aiomax2.filters import Command
from aiomax2.types import Message

router = Router()


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer("Помощь")


dp = Dispatcher()
dp.include_router(router)
```

Можно создавать несколько router и вкладывать их друг в друга для разделения
логики приложения.

---

## Фильтры

Для простых условий доступен magic filter `F`:

```python
from aiomax2 import F
from aiomax2.types import Message


@router.message(F.text == "ping")
async def ping(message: Message) -> None:
    await message.answer("pong")


@router.message(F.text.startswith("hello"))
async def hello(message: Message) -> None:
    await message.reply("Привет!")
```

Команды обрабатываются отдельными фильтрами:

```python
from aiomax2.filters import Command, CommandObject


@router.message(Command("echo"))
async def echo(message: Message, command: CommandObject) -> None:
    await message.answer(command.args or "Нет аргументов")
```

---

## Shortcuts

Типы MAX привязываются к экземпляру `Bot`, поэтому для большинства обычных
операций не требуется вручную передавать идентификаторы.

```python
@router.message(Command("test"))
async def test(message: Message) -> None:
    sent = await message.answer("Первый текст")

    await sent.edit_text("Текст изменён")
    await sent.delete()
```

Доступны, в частности:

```python
await message.answer("Ответ")
await message.reply("Ответ с привязкой к сообщению")
await message.edit_text("Новый текст")
await message.delete()
```

---

## Callback и клавиатуры

Клавиатура в MAX является attachment сообщения.

```python
from aiomax2 import F
from aiomax2.types import CallbackQuery
from aiomax2.utils.keyboard import InlineKeyboardBuilder

builder = InlineKeyboardBuilder()
builder.button(text="Подтвердить", callback_data="confirm")
builder.button(text="Отменить", callback_data="cancel")
builder.adjust(2)

await message.answer(
    "Выберите действие",
    reply_markup=builder.as_markup(),
)


@router.callback_query(F.payload == "confirm")
async def confirm(callback_query: CallbackQuery) -> None:
    await callback_query.answer(notification="Готово")
```

Builder поддерживает семь актуальных типов кнопок MAX. Low-level
`CallbackButton`, `Keyboard` и `InlineKeyboardAttachmentRequest` остаются
доступны. Подробнее: [клавиатуры](https://candycrimsie.github.io/aiomax2/keyboards/).

## Форматирование

```python
from aiomax2 import TextFormat

await message.answer(
    "<b>Жирный</b> <i>курсив</i>",
    format=TextFormat.HTML,
)

await message.answer(
    "**Жирный** _курсив_",
    format=TextFormat.MARKDOWN,
)
```

MAX поддерживает значения `html` и `markdown`; отдельного
`markdown_v2` в актуальном API нет. Подробнее:
[форматирование текста](https://candycrimsie.github.io/aiomax2/formatting/).

---

## FSM

В библиотеке есть встроенная FSM:

```python
from aiomax2.fsm.context import FSMContext
from aiomax2.fsm.state import State, StatesGroup
from aiomax2.filters import Command
from aiomax2.types import Message


class Form(StatesGroup):
    name = State()
    age = State()


@router.message(Command("form"))
async def start_form(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.name)
    await message.answer("Как вас зовут?")


@router.message(Form.name)
async def process_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await state.set_state(Form.age)
    await message.answer("Сколько вам лет?")
```

По умолчанию используется process-local `MemoryStorage`.

Для multi-worker production deployment рекомендуется внешнее общее хранилище.

---

## Webhook

Для production рекомендуется использовать Webhook.

Пример с FastAPI:

```python
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from aiomax2 import Bot, Dispatcher, Router

WEBHOOK_PATH = "/webhook"
MAX_WEBHOOK_BASE_URL = os.environ["MAX_WEBHOOK_BASE_URL"].rstrip("/")
MAX_WEBHOOK_SECRET = os.environ["MAX_WEBHOOK_SECRET"]
WEBHOOK_URL = f"{MAX_WEBHOOK_BASE_URL}{WEBHOOK_PATH}"

bot = Bot(os.environ["MAX_BOT_TOKEN"])
dp = Dispatcher()
router = Router()

dp.include_router(router)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    try:
        await bot.subscribe(
            WEBHOOK_URL,
            secret=MAX_WEBHOOK_SECRET,
            update_types=dp.resolve_used_update_types(),
        )
        yield
    finally:
        await bot.close()
        await dp.close()


app = FastAPI(lifespan=lifespan)

app.include_router(
    dp.webhook_router(
        WEBHOOK_PATH,
        bot=bot,
        secret=MAX_WEBHOOK_SECRET,
    )
)
```

```bash
export MAX_BOT_TOKEN="..."
export MAX_WEBHOOK_BASE_URL="https://bot.example.ru"
export MAX_WEBHOOK_SECRET="replace-with-random-secret"
```

`webhook_router()` получает только локальный route path `/webhook`, а
`subscribe()` — полный публичный HTTPS URL. Например:

```text
MAX -> https://bot.example.ru/webhook
    -> reverse proxy
    -> 127.0.0.1:5000/webhook
    -> FastAPI
    -> aiomax2 Dispatcher
```

Для одной кодовой базы режим можно выбрать через `MAX_MODE=polling` или
`MAX_MODE=webhook`; готовый pattern находится в
[`examples/modes.py`](examples/modes.py). Оба режима одновременно не
запускаются.

MAX ожидает `200 OK` от Webhook не позднее чем через 30 секунд, поэтому долгие
CPU-bound и blocking операции не следует выполнять непосредственно внутри
handler.

Подробнее:

https://candycrimsie.github.io/aiomax2/webhook/

---

## Загрузка файлов

`aiomax2` поддерживает загрузку изображений, видео, аудио и обычных файлов:

```python
image = await bot.upload_image("photo.png")
video = await bot.upload_video("video.mp4")
audio = await bot.upload_audio("audio.mp3")
document = await bot.upload_file("document.pdf")

await bot.send_message(
    "Файлы",
    chat_id=123,
    attachments=[image, document],
)
```

Transport отдельно обрабатывает внешние upload URL и не переносит на них
headers основной API session.

Если MAX вернул документированный `attachment.not.ready`, отправка или
редактирование сообщения с уже загруженным attachment ограниченно повторяется
с растущей паузой. Сам binary upload после неоднозначной ошибки не повторяется.

Подробнее:

https://candycrimsie.github.io/aiomax2/uploads/

---

## Работа с MAX API

Основные методы доступны непосредственно через `Bot`:

```python
me = await bot.get_my_info()

message = await bot.send_message(
    "Привет!",
    chat_id=123,
)

same_message = await bot.get_message(message.message_id)
```

Для endpoint, который ещё не получил отдельный high-level wrapper, можно
использовать:

```python
payload = await bot.request(
    "GET",
    "/me",
)
```

При этом сохраняются transport safeguards библиотеки: авторизация, TLS,
rate limiting и обработка API errors.

---

## Rate limits

`aiomax2` применяет встроенный глобальный limiter к исходящим запросам MAX API.

Для операций отправки, редактирования и удаления сообщений, а также callback
answers используется дополнительный консервативный per-target limiter:

```text
MAX API
└── до 30 requests/sec

target A
└── до 2 operations/sec

target B
└── отдельное окно до 2 operations/sec
```

Встроенные limiter хранят состояние в памяти процесса.

Например:

```bash
uvicorn main:app --workers 4
```

создаст четыре независимых limiter. Для multi-worker или multi-container
deployment необходим внешний shared/distributed limiter.

Подробнее:

https://candycrimsie.github.io/aiomax2/rate-limits/

---

## TLS и сертификаты

TLS verification в `aiomax2` не отключается.

Даже если переданная пользователем `aiohttp.ClientSession` создана с:

```python
aiohttp.TCPConnector(ssl=False)
```

для HTTPS-запросов transport явно применяет собственный проверяющий
`SSLContext`.

Дополнительный CA bundle можно передать через `ca_file`:

```python
bot = Bot(
    token,
    ca_file="/path/to/ca.pem",
)
```

Или через собственный безопасный `SSLContext`:

```python
import ssl

context = ssl.create_default_context()
context.load_verify_locations(cafile="/path/to/ca.pem")

bot = Bot(
    token,
    ssl_context=context,
)
```

Пользовательский `SSLContext` должен сохранять проверку сертификата и hostname.

Подробнее:

https://candycrimsie.github.io/aiomax2/certificates/

---

## Custom aiohttp.ClientSession

Можно использовать собственную `aiohttp.ClientSession`:

```python
import aiohttp

from aiomax2 import Bot


session = aiohttp.ClientSession(
    headers={
        "User-Agent": "my-max-bot/1.0",
    }
)

bot = Bot(
    token,
    session=session,
)
```

`Authorization` для MAX API добавляется самой библиотекой.

Переданная пользователем session принадлежит пользователю, поэтому
`Bot.close()` её не закрывает автоматически.

---

## Обработка ошибок

API и transport ошибки представлены отдельными исключениями:

```python
from aiomax2.exceptions import (
    BadRequestError,
    ForbiddenError,
    NetworkError,
    RateLimitError,
    UnauthorizedError,
)

try:
    await bot.get_my_info()
except UnauthorizedError:
    print("Неверный token")
except RateLimitError as error:
    print("Rate limit:", error.retry_after)
except NetworkError as error:
    print("Network error:", error)
```

Подробнее:

https://candycrimsie.github.io/aiomax2/errors/

---

## Миграция с aiogram

`aiomax2` использует знакомые концепции:

```text
Bot
Dispatcher
Router
Message
Command
F
FSMContext
Middleware
```

Но библиотека **не эмулирует Telegram API**.

MAX остаётся источником истины для:

- моделей;
- названий полей;
- callback;
- клавиатур;
- attachments;
- Webhook;
- rate limits;
- upload flow;
- API semantics.

Например, клавиатура MAX на wire является attachment сообщения. Параметр
`reply_markup` в aiomax2 — только convenience над этим attachment, а не
Telegram keyboard model.

Подробное руководство:

https://candycrimsie.github.io/aiomax2/migration-from-aiogram/

---

## Документация

Полная документация публикуется через MkDocs и GitHub Pages:

**https://candycrimsie.github.io/aiomax2/**

### Начало работы

- [Установка](https://candycrimsie.github.io/aiomax2/installation/)
- [Быстрый старт](https://candycrimsie.github.io/aiomax2/quickstart/)
- [Long Polling](https://candycrimsie.github.io/aiomax2/polling/)
- [Webhook](https://candycrimsie.github.io/aiomax2/webhook/)

### Обработка событий

- [Dispatcher и Router](https://candycrimsie.github.io/aiomax2/router/)
- [Handlers](https://candycrimsie.github.io/aiomax2/handlers/)
- [Фильтры](https://candycrimsie.github.io/aiomax2/filters/)
- [Команды](https://candycrimsie.github.io/aiomax2/commands/)
- [Magic filter F](https://candycrimsie.github.io/aiomax2/magic-filter/)
- [Callback и клавиатуры](https://candycrimsie.github.io/aiomax2/callbacks/)
- [Inline-клавиатуры](https://candycrimsie.github.io/aiomax2/keyboards/)
- [Форматирование текста](https://candycrimsie.github.io/aiomax2/formatting/)
- [Middleware](https://candycrimsie.github.io/aiomax2/middleware/)
- [FSM](https://candycrimsie.github.io/aiomax2/fsm/)

### MAX API

- [Загрузки](https://candycrimsie.github.io/aiomax2/uploads/)
- [Подписки](https://candycrimsie.github.io/aiomax2/subscriptions/)
- [Ошибки](https://candycrimsie.github.io/aiomax2/errors/)
- [Rate limits](https://candycrimsie.github.io/aiomax2/rate-limits/)
- [TLS и сертификаты](https://candycrimsie.github.io/aiomax2/certificates/)
- [Покрытие MAX API](https://candycrimsie.github.io/aiomax2/api-coverage/)

### Проект

- [Миграция с aiogram](https://candycrimsie.github.io/aiomax2/migration-from-aiogram/)
- [Архитектура](https://candycrimsie.github.io/aiomax2/architecture/)
- [Исследование API](https://candycrimsie.github.io/aiomax2/research/)
- [Roadmap](https://candycrimsie.github.io/aiomax2/roadmap/)

---

## Примеры

Готовые примеры находятся в каталоге [`examples`](examples).

В репозитории есть примеры для:

- Long Polling;
- Webhook с FastAPI;
- команд;
- фильтров;
- callback-кнопок;
- всех MAX inline button types и builder API;
- HTML и MAX Markdown;
- FSM;
- middleware;
- вложенных router;
- message shortcuts;
- uploads;
- subscriptions;
- custom `ClientSession`;
- custom CA;
- обработки ошибок.

---

## Разработка

Установите development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Перед commit рекомендуется запускать:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy src/aiomax2
python -m pytest
python -m mkdocs build --strict
```

CI выполняет проверки на поддерживаемых версиях Python автоматически.

Правила участия в разработке:

[CONTRIBUTING.md](CONTRIBUTING.md)

---

## Roadmap

В следующих версиях планируются, среди прочего:

- Redis-backed distributed rate limiter;
- Redis FSM storage;
- настраиваемая event isolation;
- background/queue-backed Webhook processing;
- resumable/chunked uploads;
- дополнительные production deployment recipes.

Полный roadmap:

https://candycrimsie.github.io/aiomax2/roadmap/

---

## Безопасность

Инструкции по сообщению об уязвимостях находятся в:

[SECURITY.md](SECURITY.md)

Не публикуйте реальные bot tokens в issues, logs, examples или публичных
репозиториях.

---

## Changelog

История изменений:

[CHANGELOG.md](CHANGELOG.md)

---

## Лицензия

Проект распространяется по лицензии MIT.

[LICENSE](LICENSE)
