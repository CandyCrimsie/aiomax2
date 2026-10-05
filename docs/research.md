# Исследование и соответствие API

Дата исследования: 5 октября 2026. Источники в порядке приоритета:

1. [Официальная документация MAX Bot API](https://dev.max.ru/docs-api)
2. [Официальная OpenAPI-схема](https://github.com/max-messenger/api-schema)
3. Наблюдаемое поведение API, фиксируемое integration fixtures
4. Архивный [dpnspn/aiomax](https://github.com/dpnspn/aiomax)
5. [aiogram 3.x](https://github.com/aiogram/aiogram) только как ориентир DX

Проверенная схема — OpenAPI 3.0 версии `0.0.33`. Base URL:
`https://platform-api2.max.ru`. Токен передаётся без изменений в заголовке
`Authorization`, без префикса `Bearer`.

## Ограничения, определяющие архитектуру

- Webhook — production transport. Long Polling (`GET /updates`) подходит только
  для разработки и тестов и не работает при активной Webhook-подписке.
- Webhook требует HTTPS с доверенным сертификатом. При наличии `secret` MAX
  передаёт его в `X-Max-Bot-Api-Secret` и ждёт `200 OK` не более 30 секунд.
- Документированный лимит API domain — 30 requests/sec.
- Отправка, редактирование, удаление сообщений и callback answers ограничены
  двумя операциями/с на dialog/chat/channel.
- ID сообщения находится в `message.body.mid`; получатель — MAX `Recipient`, а
  не Telegram `Chat`.
- Полиморфизм updates определяется `update_type`. Неизвестный будущий event
  парсится как общий `Update`, а не ломает Webhook.
- Архивный `aiomax` не покрывает актуальные события и содержит
  `message_chat_created`, отсутствующий в официальной схеме. Эта устаревшая
  сущность не реализована.

## Таблица соответствия

| MAX API entity/event | архивный `aiomax` | aiogram-like abstraction | `aiomax2` |
|---|---|---|---|
| `Message` | `Message` с ручным parsing | `Message` и bound shortcuts | типизированный `Message`; `answer`, `reply`, `edit_text`, `delete` |
| `message_created` | `on_message` | `router.message(...)` | `router.message(...)` receives `Message` |
| `message_callback` + `Callback` | `on_button_callback` | `router.callback_query(...)` | `router.callback_query(...)` receives `CallbackQuery` |
| `message_edited` | `on_message_edit` | edited-message observer | `router.message_edited(...)` |
| `message_removed` | `on_message_delete` | observer удаления | `router.message_removed(...)` с MAX update object |
| comment created/edited/removed | не покрыты | нет прямого Telegram-аналога | observers с точными именами MAX |
| `bot_started` | `on_bot_start` | нет точного Telegram-аналога | `router.bot_started(...)` |
| `bot_stopped` | не покрыт | нет точного Telegram-аналога | `router.bot_stopped(...)` |
| bot/user added/removed | частично | chat-member observers | точные MAX observers без эмуляции Telegram |
| dialog cleared/removed/muted/unmuted | не покрыты | нет прямого аналога | точные MAX observers |
| chat title changed | `on_chat_title_change` | service/chat update | `router.chat_title_changed(...)` |
| bot admin permissions changed | не покрыт | chat-member update | точный MAX observer |
| `GET /updates` + marker | polling внутри Bot | `Dispatcher.start_polling` | polling Dispatcher только для разработки |
| `POST /subscriptions` | нет first-class adapter | webhook adapters | общий handler и FastAPI router |
| command text | separate command registry | `Command` filter | `Command` returns `CommandObject` into context |
| произвольные предикаты объекта | простые content filters | magic filter `F` | собственные typed path expressions |
| handler context | name-based cursor injection | context data injection | signature-aware event/context injection |
| FSM | sync-словарь по user | async storage и `FSMContext` | async storage с MAX user/chat strategy |
| API errors | ручные exceptions | типизированные API exceptions | иерархия по HTTP status и retry metadata |
| TLS/сертификаты Минцифры | bundled opt-in CA | стандартная TLS session | проверяемый TLS; CA file или `SSLContext`, без `ssl=False` |

## Что намеренно не копируется из Telegram

- Нет Telegram-полей `Update`, inline queries, payments, polls, topics,
  Telegram reply markup и chat semantics на основе `getMe`.
- Callback answer MAX использует `POST /answers` и может изменить сообщение,
  показать notification или сделать оба действия.
- MAX subscriptions — самостоятельные API resources. Adapter не создаёт и не
  удаляет подписку неявно.
- Attachments и кнопки сохраняют официальные discriminator и payload shapes.
- Long Polling доступен для удобства разработки, но не представлен как
  production-эквивалент Webhook.

## Концепции, перенесённые из aiogram

- `Dispatcher` является корневым `Router`.
- Observers поддерживают decorator и явную регистрацию.
- Routers вкладываются и имеют одного родителя.
- Filters возвращают `bool` или словарь context.
- Outer middleware выполняется до фильтров, inner — после.
- Аргументы handler выбираются из context по сигнатуре.
- FSM storage и объявления states не зависят от transport.
