# Changelog

Все заметные изменения проекта документируются в этом файле. Формат основан
на [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/), версии следуют
Semantic Versioning с pre-release суффиксами.

## [Unreleased]

## [0.1.0a2] - 2026-10-06

### Изменено

- target rate limiter распространён на отправку, редактирование и удаление
  сообщений, а также callback answers;
- shortcuts передают `chat_id`/`user_id` в low-level методы;
- token гарантированно добавляется к API requests с custom `ClientSession`;
- внешние upload requests изолированы от headers API session;
- проверяющий `SSLContext` принудительно применяется к каждому API request,
  включая requests через custom session с небезопасным connector;
- custom `SSLContext` без проверки hostname или сертификата отклоняется;
- единый per-target limiter документирован как консервативная клиентская
  политика, а process-local и multi-worker ограничения описаны явно;
- пользовательская документация и примеры переведены на русский язык.

### Добавлено

- конкурентные и cancellation tests rate limiter;
- tests для нескольких targets, 30 concurrent requests и повторных `429`;
- transport tests для TLS override, custom sessions, upload authorization и
  исчерпания повторов после `429`;
- полное руководство по Webhook, Long Polling, FSM, middleware и rate limits;
- MkDocs configuration, официальный GitHub Pages workflow и community files.

## [0.1.0a1] - 2026-10-05

### Добавлено

- первый alpha-релиз `Bot`, `Dispatcher`, `Router`, filters, FSM и Webhook;
- типизированные модели MAX OpenAPI `0.0.33`;
- aiohttp transport, TLS validation, retries и базовые rate limits;
- unit и mock-server integration tests.
