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

Все эти методы используют один `KeyedRateLimiter`, потому что ограничение
относится к target, а не к endpoint. Поэтому отправка и редактирование одного
чата делят одно окно, а chat A и chat B обрабатываются независимо.

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
Distributed/Redis-backed limiter находится в roadmap.

## HTTP 429

Если MAX всё же возвращает `429`, transport читает `Retry-After`, ждёт и
повторяет запрос. Каждая повторная попытка снова проходит глобальный limiter.
После `max_retries` выбрасывается `RateLimitError` с `retry_after`.

