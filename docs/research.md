# Research and API mapping

Research date: 5 October 2026. Sources are ordered by authority:

1. [Official MAX Bot API documentation](https://dev.max.ru/docs-api)
2. [Official OpenAPI schema](https://github.com/max-messenger/api-schema)
3. Observable API behaviour (to be captured as integration fixtures)
4. Archived [dpnspn/aiomax](https://github.com/dpnspn/aiomax)
5. [aiogram 3.x](https://github.com/aiogram/aiogram)

The reviewed official schema is OpenAPI 3.0, version `0.0.33`. The API base URL
is `https://platform-api2.max.ru`; the bot token is sent verbatim in the
`Authorization` header (there is no `Bearer` prefix).

## Constraints that shape the framework

- Webhook is the production transport. Long polling (`GET /updates`) is only
  suitable for development and testing, and cannot be used while a webhook
  subscription is active.
- Webhook endpoints must use HTTPS with a trusted certificate. When a
  subscription has a `secret`, MAX sends it in `X-Max-Bot-Api-Secret`.
- The documented domain limit is 30 requests per second.
- Message sending is additionally limited to two messages per second per
  dialog/chat/channel. Similar two-per-second constraints apply to callback
  answers and several mutating message operations.
- A message body carries its id as `message.body.mid`; a message recipient is a
  MAX `Recipient`, not a Telegram `Chat` object.
- Update polymorphism is determined by `update_type`. Unknown future update
  types must remain parseable as a generic `Update` rather than crashing the
  webhook.
- The archived `aiomax` repository does not cover all current events and
  contains `message_chat_created`, which is absent from the current official
  schema. It is not implemented here.

## Correspondence matrix

| MAX API entity/event | archived `aiomax` | aiogram-like abstraction | `aiomax2` |
|---|---|---|---|
| `Message` | `Message` with manual parsing | `Message` and bound shortcuts | typed `Message`; `answer`, `reply`, `edit_text`, `delete` |
| `message_created` | `on_message` | `router.message(...)` | `router.message(...)` receives `Message` |
| `message_callback` + `Callback` | `on_button_callback` | `router.callback_query(...)` | `router.callback_query(...)` receives `CallbackQuery` |
| `message_edited` | `on_message_edit` | edited-message observer | `router.message_edited(...)` |
| `message_removed` | `on_message_delete` | deleted-message observer | `router.message_removed(...)` with the MAX update object |
| comment created/edited/removed | not covered | no direct Telegram equivalent | observers with exact MAX event names |
| `bot_started` | `on_bot_start` | no exact Telegram equivalent | `router.bot_started(...)` |
| `bot_stopped` | not covered | no exact Telegram equivalent | `router.bot_stopped(...)` |
| bot/user added/removed | partial | chat-member observers | exact MAX observers, no Telegram status emulation |
| dialog cleared/removed/muted/unmuted | not covered | no direct equivalent | exact MAX observers |
| chat title changed | `on_chat_title_change` | service/chat update | `router.chat_title_changed(...)` |
| bot admin permissions changed | not covered | chat-member update | exact MAX observer |
| `GET /updates` + marker | Bot-owned polling loop | `Dispatcher.start_polling` | dispatcher-owned polling; documented as non-production |
| `POST /subscriptions` | no first-class adapter | webhook adapters | generic handler plus optional FastAPI router |
| command text | separate command registry | `Command` filter | `Command` returns `CommandObject` into context |
| arbitrary object predicates | simple content filters | magic filter `F` | local typed path-expression implementation |
| handler context | name-based cursor injection | context data injection | signature-aware event/context injection |
| FSM | synchronous user-only dictionary | async storage and `FSMContext` | async storage keyed by MAX user/chat strategy |
| API errors | hand-written exceptions | typed API exceptions | status-aware hierarchy with retry metadata |
| TLS/Ministry CA | bundled opt-in CA | normal TLS session | verified TLS; user CA file or `SSLContext`, never `ssl=False` |

## Concepts intentionally not copied from Telegram

- There are no Telegram `Update` fields, inline queries, payments, polls,
  topics, Telegram reply markup classes, or `getMe`-derived chat semantics.
- MAX callback answers use `POST /answers` and can replace a message and/or
  show a notification; this is modelled directly.
- MAX subscriptions are API resources. A webhook adapter does not silently
  create or delete a subscription.
- MAX message attachments and keyboard buttons retain their official
  discriminator values and payload shapes.
- Long polling is exposed for developer convenience but is not presented as a
  production-equivalent alternative to webhooks.

## Concepts carried over from aiogram

- `Dispatcher` is the root `Router`.
- Event observers support decorator and explicit registration styles.
- Routers can be nested once and have a single parent.
- Filters return `bool` or a context dictionary.
- Outer middleware runs before filters; inner middleware runs after filters.
- Handler arguments are selected from context data by signature.
- FSM storage and state declarations are independent of the transport.

