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
| `errors.py` | типизированные API/network ошибки |
| `custom_session.py` | пользовательская `aiohttp.ClientSession` |
| `custom_ca.py` | дополнительный CA bundle |

Для `fastapi_webhook.py`:

```bash
python -m pip install -e ".[fastapi]"
uvicorn examples.fastapi_webhook:app --host 127.0.0.1 --port 8000
```

Для полной проверки repository examples вместе со всеми необязательными
интеграциями можно установить development extra:

```bash
python -m pip install -e ".[dev]"
```

Установите `MAX_WEBHOOK_URL` для автоматической регистрации подписки при
startup и `MAX_WEBHOOK_SECRET` для проверки входящих запросов.
