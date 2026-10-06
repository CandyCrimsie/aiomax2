# Webhook-подписки

Подписка определяет HTTPS endpoint и типы events, которые MAX отправляет боту.

```python
import os

WEBHOOK_PATH = "/webhook"
webhook_base_url = os.environ["MAX_WEBHOOK_BASE_URL"].rstrip("/")
webhook_secret = os.environ["MAX_WEBHOOK_SECRET"]
webhook_url = f"{webhook_base_url}{WEBHOOK_PATH}"

subscriptions = await bot.get_subscriptions()

await bot.subscribe(
    webhook_url,
    secret=webhook_secret,
    update_types=["message_created", "message_callback", "bot_started"],
)

await bot.unsubscribe(webhook_url)
```

Указывайте только events, для которых приложение зарегистрировало handlers.
Список можно получить через `dispatcher.resolve_used_update_types()`:

```python
await bot.subscribe(
    webhook_url,
    secret=secret,
    update_types=dispatcher.resolve_used_update_types(),
)
```

Активная Webhook-подписка несовместима с `GET /updates`. Перед локальным Long
Polling удалите подписку. Требования к HTTPS, secret и timeout описаны в
[Webhook guide](webhook.md).

Актуальная документация MAX помечает `bot_admin_permissions_changed` как
Webhook-only: в `resolve_used_update_types()` событие учитывается, но через
Long Polling пока не доставляется. Полная таблица событий и ручных способов
воспроизведения приведена в [live smoke-test](live-testing.md).
