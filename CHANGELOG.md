# Changelog

Все заметные изменения проекта документируются в этом файле. Формат основан
на [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/), версии следуют
Semantic Versioning с pre-release суффиксами.

## [Unreleased]

## [0.1.0] - 2026-10-07

### Исправлено

- multipart filename больше не раскрывает локальные компоненты пути;
- token после upload извлекается из документированного для каждого media type
  источника: upload response для image/file и `POST /uploads` для video/audio;
- `GET /messages` локально требует ровно один источник: `chat_id` либо
  непустой `message_ids`;
- timeouts API и upload отделены от остальных сетевых ошибок через совместимый
  `RequestTimeoutError`;
- response-модели photo/video и исходящие attachment combinations приведены к
  актуальной OpenAPI и ограничениям MAX.

### Добавлено

- conformance tests на основе минимальных wire contracts официального Go SDK
  v2, включая comments, callbacks, uploads и deprecated `User.name`;
- локальная проверка HTTPS URL и формата secret для Webhook-подписки;
- [страница upstream conformance](docs/upstream-conformance.md) с точными
  revisions OpenAPI и Go SDK, осознанными различиями и runtime quirks;
- project metadata URLs для документации, исходников и issue tracker.

### Изменено

- весь публичный API повторно сверён с OpenAPI `0.0.33` и официальным Go SDK
  v2 `v2.4.3` от 7 октября 2026 года;
- documented attachment combinations проверяются до отправки без ограничения
  будущих неизвестных attachment types;
- upload, polling, subscriptions, keyboards и errors guides уточнены по
  результатам conformance-аудита;
- release metadata подготовлена для первого stable-релиза `0.1.0`.

## [0.1.0a3] - 2026-10-06

### Исправлено

- `get_admins()` приведён к фактическому ответу MAX
  `ChatMembersList.members`;
- неподдерживаемый schema параметр `notify` больше не попадает в comment
  requests; совместимый аргумент 0.1.x временно сохранён с
  `DeprecationWarning`;
- malformed Webhook JSON и невалидные update payload получают контролируемый
  HTTP `400`, при этом исключения пользовательских handlers по-прежнему дают
  `500`;
- исключения фоновых polling handlers извлекаются и логируются без
  `Task exception was never retrieved`;
- очистка команд через `edit_my_commands(None)` сериализуется как
  `commands=[]`;
- модели принимают документированные legacy admin permissions, а
  `BotStartedUpdate.payload` ограничен 512 символами согласно OpenAPI;
- timing-проверки `Retry-After` и глобального limiter сделаны
  детерминированными для Windows/Python 3.12.

### Добавлено

- параметризованные parsing, bind, nested Router, dependency context, FSM и
  FastAPI Webhook round-trip tests для всех 19 официальных update types;
- tests forward compatibility для неизвестных update types и дополнительных
  полей, а также Webhook secret и malformed payload;
- conformance tests high-level Bot API serialization и response binding;
- `examples/live_updates.py` с безопасными handlers для ручной проверки
  updates, API методов, uploads, keyboards и formatting;
- подробный manual smoke-test plan без ложных отметок о live-прохождении.

### Изменено

- покрытие API повторно сверено с актуальной OpenAPI `0.0.33`, schema commit
  `5af13bd` и живой документацией MAX от 6 октября 2026 года;
- документация фиксирует удалённый `POST /chats/{chatId}/members`, Webhook-only
  статус `bot_admin_permissions_changed`, ограничения uploads и известное
  поведение notification-only callbacks;
- уточнена настройка TLS для MAX API: системный trust store, отдельный CA
  bundle и диагностический `verify_ssl=False`;
- указано, что собственный сертификат для исходящих MAX API-запросов выпускать
  не требуется;
- обновлена ссылка на страницу сертификатов Минцифры:
  https://www.gosuslugi.ru/crt;
- документация установки обновлена после публикации `aiomax2` на PyPI.

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
- FastAPI и Uvicorn включены в стандартную установку, optional extra удалён;
- Webhook configuration упрощена до public base URL и локального route path;
- lifespan annotations обновлены с `AsyncIterator` на `AsyncGenerator`;
- пользовательская документация и примеры переведены на русский язык;
- добавлен удобный `reply_markup` поверх настоящего MAX keyboard attachment;
- HTML и MAX Markdown оформлены как документированный public API через
  `TextFormat` без неподдерживаемого `MARKDOWN_V2`;
- `attachment.not.ready` обрабатывается отдельным bounded retry только при
  отправке/изменении сообщения с attachment;
- исправлена ASCII-валидация `open_app` payload;
- documentation notification-only callback уточнена с учётом необходимости
  live verification;
- каждый attachment retry теперь повторно учитывается per-target limiter;
- уточнено, что `reply_markup=None` не удаляет клавиатуру, а `attachments=[]`
  удаляет все вложения;
- добавлен явный небезопасный режим `verify_ssl=False` с
  `InsecureTLSWarning`, безопасный default сохранён;
- расширено руководство по сертификатам Минцифры и добавлен официальный
  источник: https://www.gosuslugi.ru/crt.

### Добавлено

- конкурентные и cancellation tests rate limiter;
- tests для нескольких targets, 30 concurrent requests и повторных `429`;
- transport tests для TLS override, custom sessions, upload authorization и
  исчерпания повторов после `429`;
- полное руководство по Webhook, Long Polling, FSM, middleware и rate limits;
- пример выбора Polling или Webhook через `MAX_MODE` для одной кодовой базы;
- MkDocs configuration, официальный GitHub Pages workflow и community files;
- `InlineKeyboardBuilder` для всех семи актуальных MAX button types;
- typed `answer_callback_result()` для сохранения diagnostic message при
  `success=false` без изменения совместимого `answer_callback() -> bool`;
- keyboard/formatting examples, TLS troubleshooting и расширенные tests для
  callback serialization, keyboard limits и attachment readiness.

## [0.1.0a1] - 2026-10-05

### Добавлено

- первый alpha-релиз `Bot`, `Dispatcher`, `Router`, filters, FSM и Webhook;
- типизированные модели MAX OpenAPI `0.0.33`;
- aiohttp transport, TLS validation, retries и базовые rate limits;
- unit и mock-server integration tests.
