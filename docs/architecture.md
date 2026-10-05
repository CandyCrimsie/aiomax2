# Архитектура

Пакет разделён по ответственности, а не по количеству endpoints:

```text
src/aiomax2/
├── client/          aiohttp transport, TLS, retries, rate limiting
├── types/           Pydantic-модели и parsing MAX updates
├── dispatcher/      observers, routers, middleware, DI, dispatcher
├── filters/         Filter, Command, magic F, StateFilter
├── fsm/             states, context, strategies, storage
├── webhook/         независимый handler и adapters
├── bot.py           типизированный facade MAX API
├── enums.py         значения актуальной MAX-схемы
└── exceptions.py    ошибки transport/API/framework
```

Pipeline обработки:

```text
raw JSON
  -> parse_update (discriminator-aware, unknown-update tolerant)
  -> bind Bot to shortcut-capable objects
  -> Dispatcher context + FSM context
  -> root update middleware/observer
  -> matching event observer on each Router
  -> outer middleware
  -> filters (may enrich context)
  -> inner middleware
  -> signature-based handler invocation
```

## Границы ответственности

`AiohttpSession` отвечает за HTTP, pooling, TLS, retries, `429` и глобальный
лимит. `Bot` знает semantics endpoints, target limits и преобразование моделей.
Dispatcher не создаёт HTTP-запросы. Модели обращаются к связанному `Bot` только
через явные shortcuts.

Parser `Update` использует явную таблицу discriminator вместо полной
зависимости от сгенерированного OpenAPI union. Это учитывает ограничения
генераторов, описанные MAX, и сохраняет неизвестные будущие события как общий
`Update`, не ломая Webhook.

Context — изменяемый словарь в пределах одного update. Filters и middleware
могут добавлять значения; invocation передаёт callable только запрошенные по
имени аргументы. Это даёт aiogram-like DI без глобального service container.

## Доставка и подтверждение

Webhook secret сравнивается в constant time. Успешный HTTP-ответ означает, что
update разобран и pipeline handler завершён. Framework не обещает durable или
exactly-once обработку. Для таких требований application должна записать event
в собственную очередь или транзакционное хранилище.

HTTP layer повторяет `429` согласно `Retry-After`. Network и 5xx retries по
умолчанию разрешены только для idempotent methods. Неидемпотентные операции MAX
не повторяются после неоднозначного сетевого сбоя.

## Локальное состояние

Rate limiters и `MemoryStorage` находятся в памяти одного процесса. Несколько
workers не разделяют эти данные. Distributed limiter, Redis FSM storage и
queue-based Webhook processing запланированы отдельно.
