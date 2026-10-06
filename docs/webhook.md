# Webhook

Webhook — основной режим доставки событий MAX для production. MAX выполняет
HTTPS POST на endpoint приложения, а `aiomax2` проверяет secret, парсит `Update`
и передаёт его в `Dispatcher`.

## Полный пример FastAPI

```python
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import os

from fastapi import FastAPI

from aiomax2 import Bot, Dispatcher, Router
from aiomax2.filters import Command
from aiomax2.types import Message

WEBHOOK_PATH = "/webhook"
MAX_WEBHOOK_BASE_URL = os.environ["MAX_WEBHOOK_BASE_URL"].rstrip("/")
MAX_WEBHOOK_SECRET = os.environ["MAX_WEBHOOK_SECRET"]
WEBHOOK_URL = f"{MAX_WEBHOOK_BASE_URL}{WEBHOOK_PATH}"

bot = Bot(os.environ["MAX_BOT_TOKEN"])
dp = Dispatcher()
router = Router()


@router.message(Command("start"))
async def start(message: Message) -> None:
    await message.answer("Webhook работает")


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

Переменные окружения:

```bash
export MAX_BOT_TOKEN="..."
export MAX_WEBHOOK_BASE_URL="https://bot.example.ru"
export MAX_WEBHOOK_SECRET="replace-with-random-secret"
```

`WEBHOOK_PATH` остаётся в коде и одновременно используется для локального
route и формирования публичного URL. Это исключает рассинхронизацию между
FastAPI и подпиской MAX.

## Локальный path и публичный URL

`webhook_router()` получает только локальный path:

```text
/webhook
```

`subscribe()` получает полный публичный HTTPS URL:

```text
https://bot.example.ru/webhook
```

Полный маршрут запроса выглядит так:

```text
MAX
  -> https://bot.example.ru/webhook
  -> reverse proxy / Caddy / nginx
  -> 127.0.0.1:8000/webhook
  -> FastAPI
  -> aiomax2 Dispatcher
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

Локальный Uvicorn запускается так:

```bash
uvicorn main:app --host 127.0.0.1 --port 8000
```

Caddy принимает публичный запрос к `https://bot.example.ru/webhook`,
обслуживает TLS на порту 443 и проксирует тот же path `/webhook` в Uvicorn.
Uvicorn не обязан сам слушать порт 443 или обслуживать публичный TLS. Ограничьте
прямой доступ к локальному порту 8000 на уровне firewall.

## Регистрация подписки в lifespan

Автоматический `subscribe()` в lifespan удобен для простого single-process
deployment. При запуске:

```bash
uvicorn main:app --workers 4
```

создаются четыре процесса, и каждый выполняет свой lifespan. Это не означает,
что подписка MAX обязательно сломается, но в multi-worker production лучше
регистрировать Webhook отдельным setup/deploy step или гарантировать, что
registration выполняется ровно один раз.

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
