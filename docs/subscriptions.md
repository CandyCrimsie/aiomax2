# Webhook-подписки

Подписка определяет HTTPS endpoint и типы events, которые MAX отправляет боту.

```python
subscriptions = await bot.get_subscriptions()

await bot.subscribe(
    "https://bot.example.ru/webhook",
    secret="replace-with-a-random-secret",
    update_types=["message_created", "message_callback", "bot_started"],
)

await bot.unsubscribe("https://bot.example.ru/webhook")
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

