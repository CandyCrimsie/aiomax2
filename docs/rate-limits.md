# Rate limits

Актуальная документация MAX задаёт два уровня ограничений, а реализация
`aiomax2` добавляет важную локальную границу.

```text
application -> platform-api2.max.ru
               30 запросов/с на API domain

chat A -> 2 message operations/с
chat B -> 2 message operations/с (независимое окно)
```

## 1. Глобальный лимит MAX API

Для стабильной работы MAX требует не превышать 30 requests/sec к
`platform-api2.max.ru`. `AiohttpSession` применяет один sliding-window limiter
ко всем исходящим API requests, включая повторные попытки.

Входящий запрос `MAX -> application` на Webhook не является запросом к MAX API
и не проходит через этот limiter. Вызовы API из Webhook handlers проходят.

## 2. Лимит на target

Документация явно устанавливает до 2 операций/с в один диалог, групповой чат
или канал для:

- `POST /messages` — отправка;
- `PUT /messages` — редактирование;
- `DELETE /messages` — удаление;
- `POST /answers` — callback answer.

`aiomax2` консервативно использует для этих методов один `KeyedRateLimiter`:
2 операции/с на один target для отправки, редактирования, удаления сообщений
и callback answers. Это гарантирует соблюдение документированных ограничений
MAX, хотя официальная документация не утверждает, что все четыре endpoint
используют один общий серверный budget. Поэтому в смешанных сценариях
библиотека может ограничивать throughput сильнее сервера. Chat A и chat B
при этом используют независимые локальные окна.

Shortcuts передают target автоматически:

```python
await message.answer("Ответ")
await message.reply("Ответ со ссылкой")
await message.edit_text("Новый текст")
await message.delete()
await callback_query.answer(notification="Готово")
```

В low-level `edit_message`, `delete_message` и `answer_callback` можно передать
`chat_id` или `user_id`. Если target неизвестен, вызов попадает в общий
консервативный `unknown` bucket: лимит не нарушается, но независимые диалоги
могут быть ограничены сильнее.

Специальные повторы после `attachment.not.ready` также считаются реальными
операциями: каждая попытка повторно acquire-ит тот же target bucket. Первый
attempt при этом не учитывается дважды.

Для comment endpoints отдельный лимит 2 operations/sec в актуальной
документации не указан, поэтому библиотека его не придумывает; действует
только глобальный API limiter.

## 3. Ограничение одного процесса

Оба limiter хранят состояние в памяти одного `AiohttpSession`/`Bot` instance.
Команда:

```bash
uvicorn main:app --workers 4
```

создаёт четыре независимых набора limiter. Суммарно они способны превысить
ограничение MAX. Для нескольких workers пользователь должен обеспечить общий
лимит внешним shared limiter, распределением нагрузки или одним API worker.
Встроенный limiter не является distributed limiter и не гарантирует общий
лимит между процессами или контейнерами. Redis-backed distributed rate limiter
находится в roadmap.

## HTTP 429

Если MAX всё же возвращает `429`, transport читает `Retry-After`, ждёт и
повторяет запрос. Каждая повторная попытка снова проходит глобальный limiter.
После `max_retries` выбрасывается `RateLimitError` с `retry_after`.
