# Обработка ошибок

Все исключения библиотеки наследуются от `Aiomax2Error`.

| Исключение | Значение |
|---|---|
| `UnauthorizedError` | MAX вернул HTTP 401 |
| `ForbiddenError` | HTTP 403 |
| `NotFoundError` | HTTP 404 |
| `RateLimitError` | HTTP 429 после исчерпания retries |
| `NetworkError` | ошибка сети или timeout |
| `ServerError` | HTTP 5xx |
| `ValidationError` | локальная проверка параметров не пройдена |
| `WebhookSecretError` | secret Webhook отсутствует или неверен |

```python
from aiomax2.exceptions import NotFoundError, RateLimitError

try:
    message = await bot.get_message("mid.unknown")
except NotFoundError:
    print("Сообщение не найдено")
except RateLimitError as exc:
    print(f"MAX всё ещё ограничивает запросы: retry_after={exc.retry_after}")
```

Обычно ловить `RateLimitError` вокруг каждого вызова не нужно: transport
централизованно применяет limiter, учитывает `Retry-After` и автоматически
повторяет `429` до `max_retries`. Исключение возникает, только если все попытки
исчерпаны.

Network/5xx retries по умолчанию выполняются только для idempotent HTTP
методов. Неидемпотентный `POST` не повторяется после неоднозначного сетевого
сбоя, чтобы не создать дубликат.

Исключение — официальный ответ HTTP 400 с точным кодом
`attachment.not.ready`: MAX сообщает, что attachment ещё обрабатывается, и
рекомендует повторить отправку с увеличением интервала. Этот bounded retry
работает только для message send/edit и callback message update с attachment;
остальные HTTP 400 и binary upload не повторяются.

Ошибки handler сейчас передаются вызывающему pipeline. В Long Polling они
логируются на уровне polling loop; в Webhook приводят к неуспешному HTTP
ответу framework. Добавляйте application-level middleware для logging и
наблюдаемости.
