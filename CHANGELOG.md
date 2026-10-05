# Changelog

Все заметные изменения проекта документируются в этом файле. Формат основан
на [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/), версии следуют
Semantic Versioning с pre-release суффиксами.

## [Unreleased]

### Изменено

- target rate limiter распространён на отправку, редактирование и удаление
  сообщений, а также callback answers;
- shortcuts передают `chat_id`/`user_id` в low-level методы;
- token гарантированно добавляется к API requests с custom `ClientSession`;
- внешние upload requests изолированы от headers API session;
- пользовательская документация и примеры переведены на русский язык.

### Добавлено

- конкурентные и cancellation tests rate limiter;
- tests для нескольких targets, 30 concurrent requests и повторных `429`;
- полное руководство по Webhook, Long Polling, FSM, middleware и rate limits;
- MkDocs configuration и GitHub community files.

## [0.1.0a1] - 2026-10-05

### Добавлено

- первый alpha-релиз `Bot`, `Dispatcher`, `Router`, filters, FSM и Webhook;
- типизированные модели MAX OpenAPI `0.0.33`;
- aiohttp transport, TLS validation, retries и базовые rate limits;
- unit и mock-server integration tests.

