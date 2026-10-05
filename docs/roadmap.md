# Roadmap

## MVP (`0.1.0a1`)

- [x] Research official API, `aiomax`, and aiogram 3.x
- [x] Record mapping, incompatibilities, and architecture
- [x] Pooled HTTP transport with TLS, retries, 429 handling, and 30 rps limiter
- [x] Typed core MAX models and all official update variants
- [x] Core Bot methods for messages, callbacks, subscriptions, and updates
- [x] Nested Router, Dispatcher, filters, middleware, and context injection
- [x] `Command`, `CommandObject`, and magic `F`
- [x] Bound message and callback shortcuts
- [x] Async FSM with memory storage and MAX-aware key strategies
- [x] Webhook core plus FastAPI integration
- [x] Development-only long polling
- [x] Multipart media upload helpers
- [x] Unit and mock-server integration tests
- [x] Examples and aiogram migration guide

## `0.2`

- Attachment-readiness polling with explicit bounded backoff
- Resumable/chunked upload in addition to the MVP multipart helper
- Redis FSM storage and configurable event isolation
- aiohttp/Starlette webhook adapters and deployment recipes
- Recorded contract fixtures from real MAX responses

## `0.3`

- Schema-diff CI against the official repository
- Generated conformance tests for all request/response models
- Callback-data factory and keyboard builder
- Structured API client middleware and observability hooks

## Before stable `1.0`

- Validate real webhook round trips for every update discriminator
- Establish compatibility and deprecation policy
- Publish complete API reference and security guide
- Load-test domain and per-chat limiters
