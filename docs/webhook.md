# Webhook

Webhook — основной режим доставки событий MAX для production. MAX выполняет
HTTPS POST на endpoint приложения, а `aiomax2` проверяет secret, парсит `Update`
и передаёт его в `Dispatcher`.

## Полный пример FastAPI

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import os

from fastapi import FastAPI

from aiomax2 import Bot, Dispatcher, Router
from aiomax2.filters import Command
from aiomax2.types import Message

bot = Bot(os.environ["MAX_BOT_TOKEN"])
dp = Dispatcher()
router = Router()


@router.message(Command("start"))
async def start(message: Message) -> None:
    await message.answer("Webhook работает")


dp.include_router(router)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
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

Запуск локального приложения:

```bash
uvicorn main:app --host 127.0.0.1 --port 8000
```

## Регистрация подписки

Публичный URL должен начинаться с `https://` и быть доступен на порту 443:

```python
await bot.subscribe(
    "https://bot.example.ru/webhook",
    secret="replace-with-a-random-secret",
    update_types=["message_created", "message_callback", "bot_started"],
)
```

`secret` имеет длину 5–256 символов и состоит из `A-Z`, `a-z`, `0-9`, `_` и
`-`. MAX передаёт его в заголовке `X-Max-Bot-Api-Secret`. Adapter сравнивает
значение в constant time и возвращает `403` при несовпадении.

Webhook и Long Polling нельзя использовать одновременно. Управлять подписками
можно через `get_subscriptions()`, `subscribe()` и `unsubscribe()`.

## HTTPS и reverse proxy

MAX принимает только HTTPS endpoint на порту 443 с сертификатом доверенного CA
или сертификатом Минцифры. Самоподписанные сертификаты не поддерживаются;
домен должен совпадать с CN/SAN, сервер обязан отдавать полную цепочку.

Минимальный `Caddyfile`:

```caddyfile
bot.example.ru {
    reverse_proxy 127.0.0.1:8000
}
```

Caddy получает публичный сертификат и проксирует запросы в Uvicorn. Ограничьте
прямой доступ к порту 8000 на уровне firewall.

## Время ответа и семантика обработки

MAX ожидает строго `200 OK` в течение 30 секунд. Любой другой status или
превышение timeout считается ошибкой доставки. MAX делает до 10 повторных
попыток с растущим интервалом и может удалить подписку, если за 8 часов не
получит успешный ответ.

Текущий FastAPI adapter сначала полностью выполняет handlers и только затем
возвращает `200 OK`. Эта семантика предсказуема: успешный ответ означает, что
update разобран и передан pipeline. Не выполняйте долгие CPU-bound или внешние
blocking операции прямо в webhook handler. Выносите тяжёлую работу в
собственную очередь и завершайте handler раньше 30 секунд.
Background/queue-backed webhook processing входит в roadmap.

## Завершение приложения

FastAPI `lifespan` должен закрыть оба ресурса:

```python
await bot.close()
await dp.close()
```

Первый вызов закрывает принадлежащие библиотеке HTTP-сессии, второй — FSM
storage. Переданная пользователем `aiohttp.ClientSession` остаётся его
ответственностью.
