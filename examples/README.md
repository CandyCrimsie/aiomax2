# Примеры

Базовые примеры работают после локальной установки:

```bash
python -m pip install -e .
```

Все примеры используют `MAX_BOT_TOKEN`. Polling examples запускаются так:

```bash
python examples/basic_bot.py
```

| Файл | Сценарий |
|---|---|
| `basic_bot.py` | минимальный бот, `Command` и `F` |
| `commands.py` | `Command`, `CommandStart`, `CommandObject.args` |
| `filters.py` | сравнение, `startswith` и `contains` |
| `callbacks.py` | inline keyboard и callback answer |
| `message_actions.py` | `answer`, `reply`, `edit_text`, `delete` |
| `fsm.py` | диалог имя → возраст |
| `middleware.py` | outer middleware и context injection |
| `routers.py` | вложенные routers и пользовательская dependency |
| `send_action.py` | `typing_on` через `send_action` |
| `uploads.py` | image, video, audio и file upload |
| `comments.py` | отправка комментария к посту |
| `subscriptions.py` | регистрация Webhook-подписки |
| `fastapi_webhook.py` | FastAPI, lifespan и Webhook adapter |
| `modes.py` | выбор Polling/Webhook через `MAX_MODE` |
| `errors.py` | типизированные API/network ошибки |
| `custom_session.py` | пользовательская `aiohttp.ClientSession` |
| `custom_ca.py` | дополнительный CA bundle |

Для `fastapi_webhook.py`:

```bash
export MAX_BOT_TOKEN="..."
export MAX_WEBHOOK_BASE_URL="https://bot.example.ru"
export MAX_WEBHOOK_SECRET="replace-with-random-secret"
uvicorn examples.fastapi_webhook:app --host 127.0.0.1 --port 8000
```

Для полной проверки repository examples вместе со всеми необязательными
интеграциями можно установить development extra:

```bash
python -m pip install -e ".[dev]"
```

В `fastapi_webhook.py` локальный `WEBHOOK_PATH = "/webhook"` добавляется к
`MAX_WEBHOOK_BASE_URL` при регистрации подписки. Для переключаемого примера:

```bash
MAX_MODE=polling python examples/modes.py
MAX_MODE=webhook uvicorn examples.modes:app --host 127.0.0.1 --port 8000
```

Polling и Webhook нельзя запускать одновременно для одного бота.
Перед переходом с Webhook на Polling удалите активную MAX-подписку через
`bot.unsubscribe(webhook_url)`; одна смена `MAX_MODE` не меняет состояние MAX.
