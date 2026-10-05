# aiomax2

`aiomax2` is an asynchronous Python 3.12+ framework for the
[MAX Bot API](https://dev.max.ru/docs-api). It borrows the developer experience
of aiogram 3.x while keeping MAX entities, events, limitations, and transport
semantics explicit.

> The project is currently alpha. Its models follow the official MAX OpenAPI
> schema `0.0.33`, reviewed on 5 October 2026.

```python
from aiomax2 import Bot, Dispatcher, F, Router
from aiomax2.filters import Command, CommandObject
from aiomax2.types import Message

router = Router()


@router.message(Command("start"))
async def start(message: Message, command: CommandObject) -> None:
    await message.answer(f"Hello! args={command.args!r}")


@router.message(F.text == "hello")
async def hello(message: Message) -> None:
    await message.reply("Hello from MAX")


async def main() -> None:
    bot = Bot("MAX_BOT_TOKEN")
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    await dispatcher.start_polling(bot)  # development/testing only
```

For production, use a webhook. MAX explicitly limits long polling to
development and testing:

```python
from fastapi import FastAPI

app = FastAPI()
app.include_router(
    dispatcher.webhook_router(
        "/webhook",
        bot=bot,
        secret="the-secret-used-for-the-MAX-subscription",
    )
)
```

The client uses one pooled `aiohttp.ClientSession`, TLS verification, a global
30 rps limiter, `429` handling, and retries only when a request can be retried
safely. To add a Ministry of Digital Development CA without disabling TLS,
pass a CA bundle path or a preconfigured `ssl.SSLContext`:

```python
bot = Bot(token, ca_file="/path/to/russian_trusted_root_ca.pem")
```

See [research](docs/research.md), [architecture](docs/architecture.md),
[API coverage](docs/api-coverage.md), [roadmap](docs/roadmap.md), and the
[aiogram migration guide](docs/migration-from-aiogram.md).
