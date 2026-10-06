# Roadmap

## `0.1.0a3` — stabilization и live coverage

- [x] Повторная сверка OpenAPI `0.0.33` и живой документации MAX
- [x] Conformance matrix всех 19 update discriminators
- [x] Полный typed Dispatcher и FastAPI Webhook round-trip для каждого update
- [x] Forward-compatible unknown update и extra-fields tests
- [x] Audit high-level Bot endpoint shapes и response models
- [x] Исправление `get_admins()` под `ChatMembersList.members`
- [x] Исключение неподдерживаемого `notify` из comment wire payload
- [x] Controlled HTTP 400 для malformed Webhook payload
- [x] Получение и logging исключений background polling handlers
- [x] Live Webhook/API harness и воспроизводимый smoke-test plan
- [ ] Ручная live-проверка всех update types и ещё не покрытых endpoints

Версия может перейти к release candidate после ручного smoke-test; пункты live
не помечаются выполненными автоматическими tests.

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
