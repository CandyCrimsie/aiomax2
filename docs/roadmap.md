# Roadmap

## MVP (`0.1.0a2`)

- [x] Исследование официального API, архивного `aiomax` и aiogram 3.x
- [x] Таблица соответствий, различия и архитектура
- [x] HTTP transport с pooling, TLS, retries, `429` и лимитом 30 rps
- [x] Target limiter 2 operations/sec для message mutations и callbacks
- [x] Типизированные модели MAX и актуальные варианты updates
- [x] Методы Bot для messages, callbacks, subscriptions и updates
- [x] Вложенные Router, Dispatcher, filters, middleware и context injection
- [x] `Command`, `CommandObject` и magic `F`
- [x] Shortcuts сообщений и callbacks с передачей target
- [x] Async FSM с memory storage и MAX-aware стратегиями ключей
- [x] Webhook core и FastAPI integration
- [x] Long Polling для разработки
- [x] Multipart media upload helpers
- [x] Inline keyboard builder и `reply_markup` convenience
- [x] Bounded retry для `attachment.not.ready`
- [x] Документация HTML и MAX Markdown
- [x] Unit и mock-server integration tests
- [x] Русскоязычная документация, примеры и migration guide

## `0.2`

- Redis-backed distributed rate limiter для multi-worker deployments
- Redis FSM storage и настраиваемая event isolation
- Background Webhook processing и queue-backed production strategy
- Resumable/chunked upload в дополнение к multipart helper
- aiohttp/Starlette adapters и дополнительные deployment recipes
- Contract fixtures из реальных ответов MAX

## `0.3`

- Schema-diff CI относительно официального репозитория
- Сгенерированные conformance tests request/response моделей
- Callback-data factory
- API client middleware и observability hooks

## Before stable `1.0`

- Проверить реальные Webhook round trips каждого update discriminator
- Зафиксировать compatibility/deprecation policy
- Опубликовать полную API reference и security guide
- Провести load tests глобального и target limiter
