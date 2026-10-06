# aiomax2

[![PyPI](https://img.shields.io/pypi/v/aiomax2?label=PyPI&color=3775A9)](https://pypi.org/project/aiomax2/)
[![Python](https://img.shields.io/pypi/pyversions/aiomax2)](https://pypi.org/project/aiomax2/)
[![CI](https://github.com/CandyCrimsie/aiomax2/actions/workflows/ci.yml/badge.svg)](https://github.com/CandyCrimsie/aiomax2/actions/workflows/ci.yml)
[![Documentation](https://github.com/CandyCrimsie/aiomax2/actions/workflows/docs.yml/badge.svg)](https://candycrimsie.github.io/aiomax2/)
[![License](https://img.shields.io/github/license/CandyCrimsie/aiomax2)](https://github.com/CandyCrimsie/aiomax2/blob/main/LICENSE)

**aiomax2** — асинхронный Python-фреймворк для разработки ботов на
[MAX Bot API](https://dev.max.ru/docs-api).

Фреймворк предоставляет `Bot`, `Dispatcher`, `Router`, фильтры, middleware,
FSM, inline-клавиатуры, Long Polling и Webhook, сохраняя модели и семантику
оригинального MAX API.

Архитектура и developer experience используют знакомые подходы из aiogram 3.x,
но MAX API остаётся источником истины для методов, событий, моделей и
ограничений.

**[Документация](https://candycrimsie.github.io/aiomax2/) ·
[PyPI](https://pypi.org/project/aiomax2/) ·
[Releases](https://github.com/CandyCrimsie/aiomax2/releases) ·
[MAX Bot API](https://dev.max.ru/docs-api)**

> [!NOTE]
> Проект находится в стадии Alpha. До стабильного релиза публичный API может
> изменяться.

---

## Установка

Требуется **Python 3.12+**.

```bash
pip install aiomax2
```

Проверить установленную версию:

```bash
python -c "import aiomax2; print(aiomax2.__version__)"
```

---

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
export MAX_BOT_TOKEN="..."
python bot.py
```

На Windows PowerShell:

```powershell
$env:MAX_BOT_TOKEN="..."
python bot.py
```

---

## Возможности

- полностью асинхронная работа на `asyncio` и `aiohttp`;
- типизированные модели MAX API на Pydantic 2;
- `Dispatcher`, вложенные `Router` и dependency injection;
- команды, фильтры и magic filter `F`;
- middleware и FSM;
- shortcuts для сообщений и callback;
- `InlineKeyboardBuilder` и все актуальные типы inline-кнопок MAX;
- HTML и MAX Markdown через `TextFormat`;
- Long Polling и Webhook;
- интеграция Webhook с FastAPI;
- загрузка изображений, видео, аудио и файлов;
- работа с подписками, чатами, сообщениями и комментариями;
- автоматическая обработка rate limits и `Retry-After`;
- безопасная по умолчанию TLS verification;
- дополнительный CA bundle через `ca_file`;
- низкоуровневый доступ к API через `Bot.request()`.

---

## Inline-клавиатуры

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
async def confirm(callback: CallbackQuery) -> None:
    await callback.answer(text="Подтверждено")
```

Подробнее:
[Inline-клавиатуры](https://candycrimsie.github.io/aiomax2/keyboards/) и
[Callback](https://candycrimsie.github.io/aiomax2/callbacks/).

---

## Форматирование текста

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

Подробнее:
[форматирование текста](https://candycrimsie.github.io/aiomax2/formatting/).

---

## Long Polling и Webhook

Для локальной разработки можно использовать Long Polling:

```python
await dp.start_polling(bot)
```

Для production доступен Webhook с FastAPI:

```python
app.include_router(
    dp.webhook_router(
        "/webhook",
        bot=bot,
        secret=WEBHOOK_SECRET,
    )
)
```

Регистрация публичного URL выполняется через:

```python
await bot.subscribe(
    "https://bot.example.ru/webhook",
    secret=WEBHOOK_SECRET,
    update_types=dp.resolve_used_update_types(),
)
```

Подробнее:

- [Long Polling](https://candycrimsie.github.io/aiomax2/polling/)
- [Webhook](https://candycrimsie.github.io/aiomax2/webhook/)
- [Subscriptions](https://candycrimsie.github.io/aiomax2/subscriptions/)

---

## TLS и сертификаты

По умолчанию `aiomax2` проверяет TLS-сертификаты и hostname.

Если системное хранилище сертификатов не доверяет цепочке MAX, можно передать
дополнительный CA bundle:

```python
bot = Bot(
    os.environ["MAX_BOT_TOKEN"],
    ca_file="/path/to/ca.pem",
)
```

Сертификаты Минцифры и инструкции по их установке доступны на
[Госуслугах](https://www.gosuslugi.ru/landing/tls).

Для диагностики существует явный небезопасный режим:

```python
bot = Bot(
    os.environ["MAX_BOT_TOKEN"],
    verify_ssl=False,
)
```

> [!WARNING]
> `verify_ssl=False` отключает проверку подлинности TLS-сертификата для
> исходящих HTTPS-соединений бота. Не используйте этот режим в production без
> понимания последствий.

Подробнее:
[TLS и сертификаты](https://candycrimsie.github.io/aiomax2/certificates/).

---

## Документация

Полная документация:

**https://candycrimsie.github.io/aiomax2/**

Основные разделы:

- [Установка](https://candycrimsie.github.io/aiomax2/installation/)
- [Быстрый старт](https://candycrimsie.github.io/aiomax2/quickstart/)
- [Dispatcher и Router](https://candycrimsie.github.io/aiomax2/router/)
- [Команды и фильтры](https://candycrimsie.github.io/aiomax2/commands/)
- [FSM](https://candycrimsie.github.io/aiomax2/fsm/)
- [Inline-клавиатуры](https://candycrimsie.github.io/aiomax2/keyboards/)
- [Загрузка файлов](https://candycrimsie.github.io/aiomax2/uploads/)
- [Обработка ошибок](https://candycrimsie.github.io/aiomax2/errors/)
- [Покрытие MAX API](https://candycrimsie.github.io/aiomax2/api-coverage/)

Готовые примеры находятся в каталоге
[`examples`](https://github.com/CandyCrimsie/aiomax2/tree/main/examples).

---

## Разработка

```bash
git clone https://github.com/CandyCrimsie/aiomax2.git
cd aiomax2

python -m pip install -e ".[dev]"
```

Перед отправкой изменений:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy src/aiomax2
python -m pytest
python -m mkdocs build --strict
```

Правила участия в разработке:
[CONTRIBUTING.md](https://github.com/CandyCrimsie/aiomax2/blob/main/CONTRIBUTING.md).

---

## Проект

- [PyPI](https://pypi.org/project/aiomax2/)
- [Документация](https://candycrimsie.github.io/aiomax2/)
- [GitHub Releases](https://github.com/CandyCrimsie/aiomax2/releases)
- [Changelog](https://github.com/CandyCrimsie/aiomax2/blob/main/CHANGELOG.md)
- [Roadmap](https://candycrimsie.github.io/aiomax2/roadmap/)
- [Security Policy](https://github.com/CandyCrimsie/aiomax2/blob/main/SECURITY.md)

---

## Лицензия

`aiomax2` распространяется по лицензии
[MIT](https://github.com/CandyCrimsie/aiomax2/blob/main/LICENSE).
