# Покрытие MAX API

Покрытие повторно сверено 7 октября 2026 года с официальной OpenAPI-схемой
`0.0.33` (`max-messenger/api-schema`, commit `1a4a502`; сам `schema.yaml`
последний раз изменён в commit `5af13bd` от 17 сентября 2026 года) и живой
документацией MAX. Behavioral audit выполнен также по официальному Go SDK
ветки `v2`, commit `13264f8` (`v2.4.3`). Подробности и осознанные различия —
в разделе [сверки с upstream](upstream-conformance.md).

Версия и содержимое schema не изменились относительно предыдущей проверки:
новых или удалённых paths, update discriminators, моделей и enum в репозитории
schema нет. Живая документация содержит более свежие эксплуатационные
уточнения, перечисленные ниже.

## Методы

| MAX endpoint | Метод `Bot` | Статус | Ограничения и примечания |
|---|---|---|---|
| `GET /me` | `get_my_info` | Поддерживается | Возвращает `BotInfo`, запоминает `bot.id` |
| `PATCH /me/commands` | `edit_my_commands` | Поддерживается | `None` совместимо означает очистку через `commands=[]` |
| `GET /chats/{chatId}` | `get_chat` | Поддерживается | Типизированный `Chat` |
| `PATCH /chats/{chatId}` | `edit_chat` | Поддерживается | `icon`, `title`, `description`, `pin`, `notify` |
| `POST /chats/{chatId}/actions` | `send_action` | Поддерживается | Все значения `SenderAction` из schema |
| `GET /chats/{chatId}/pin` | `get_pinned_message` | Поддерживается | Возвращённый `Message` bind-ится к Bot |
| `PUT /chats/{chatId}/pin` | `pin_message` | Поддерживается | `message_id`, optional `notify` |
| `DELETE /chats/{chatId}/pin` | `unpin_message` | Поддерживается | — |
| `GET /chats/{chatId}/members/me` | `get_membership` | Поддерживается | `ChatMember` |
| `DELETE /chats/{chatId}/members/me` | `leave_chat` | Поддерживается | Изменяющая состояние операция |
| `GET /chats/{chatId}/members/admins` | `get_admins` | Поддерживается | MAX возвращает `ChatMembersList.members`, метод возвращает `list[ChatMember]` |
| `POST /chats/{chatId}/members/admins` | `set_admins` | Поддерживается | Полностью заменяет набор прав для переданных admins |
| `DELETE /chats/{chatId}/members/admins/{userId}` | `revoke_admin` | Поддерживается | Не удаляет участника из чата |
| `GET /chats/{chatId}/members` | `get_members` | Поддерживается | `user_ids`, `marker`, `count`; возвращает marker |
| `DELETE /chats/{chatId}/members` | `remove_member` | Поддерживается | Required `user_id`, optional `block` |
| `GET /subscriptions` | `get_subscriptions` | Поддерживается | — |
| `POST /subscriptions` | `subscribe` | Поддерживается | URL, secret, `update_types` |
| `DELETE /subscriptions` | `unsubscribe` | Поддерживается | URL передаётся query-параметром |
| `POST /uploads` | `get_upload_url`, `upload_media` | Поддерживается | Multipart upload поддерживается; resumable upload helper пока отсутствует |
| `GET /messages` | `get_messages` | Поддерживается | Ровно один из `chat_id`/`message_ids`; все query-параметры pagination/filter schema |
| `POST /messages` | `send_message` | Поддерживается | Один target; 2 операции/с на target |
| `PUT /messages` | `edit_message` | Поддерживается | `attachments=None` не меняет вложения, `[]` удаляет все |
| `DELETE /messages` | `delete_message` | Поддерживается | 2 операции/с на target |
| `GET /messages/{messageId}` | `get_message` | Поддерживается | Возвращённый `Message` bind-ится к Bot |
| comment endpoints | `get_comments`, `send_comment`, `edit_comment`, `delete_comment`, `get_comment` | Поддерживается | Response — `CommentMessage`; `NewCommentBody` не содержит `notify` |
| `GET /videos/{videoToken}` | `get_video_attachment_details` | Поддерживается | `VideoAttachmentDetails` |
| `POST /answers` | `answer_callback`, `answer_callback_result` | Поддерживается | Второй метод сохраняет diagnostic `message`; 2 операции/с на target |
| `GET /updates` | `get_updates` | Поддерживается | Только разработка/тесты; `bot_admin_permissions_changed` пока Webhook-only |

Request serialization всех перечисленных high-level методов проверяется
mock transport tests. Это не означает, что endpoint был вызван на реальном
MAX в рамках данного pass.

Ответы типизированы по required/optional полям OpenAPI. Документированное
legacy-поле `User.name`, которое всё ещё присутствует в ответах MAX и fixtures
Go SDK, сохранено как optional для чтения.

## Updates

Поддержаны все 19 discriminator актуальной schema:

```text
message_created                 message_callback
message_edited                  message_removed
comment_created                 comment_edited
comment_removed                 bot_added
bot_removed                     user_added
user_removed                    bot_started
bot_stopped                     dialog_cleared
dialog_removed                  dialog_muted
dialog_unmuted                  chat_title_changed
bot_admin_permissions_changed
```

`message_created` и `message_edited` передают handler объект `Message`,
`message_callback` — `CallbackQuery`. `comment_created`/`comment_edited`
используют `Message`, поскольку именно такая модель указана для update payload
в актуальной schema, хотя ответы comment endpoints используют отдельный
`CommentMessage`. Остальные observers получают соответствующий Update.

Parsing, bind, FSM identifiers, nested Router dispatch и FastAPI Webhook
round-trip каждого discriminator покрыты tests. Неизвестный `update_type`
остаётся generic `Update`, а дополнительные будущие поля сохраняются благодаря
`MAXObject.extra="allow"`.

## Расхождения schema и живой документации

- Schema всё ещё содержит `POST /chats/{chatId}/members`, но документация
  указывает удаление метода с 30 сентября 2026 года. `add_members` намеренно
  отсутствует.
- `bot_admin_permissions_changed` есть в schema и Webhook, но живая
  документация помечает его недоступным через Long Polling.
- Живая документация предупреждает, что в ответах ещё могут встречаться
  legacy admin permissions `post_edit_delete_message`, `edit_message` и
  `delete_message`. Модели принимают их для чтения; при назначении следует
  использовать `write`, `edit`, `delete`.
- Schema и docs не содержат `notify` в `NewCommentBody`. Совместимый аргумент
  методов 0.1.x временно сохранён, выдаёт `DeprecationWarning` и не попадает в
  wire JSON.
- Notification-only callback корректно сериализуется и возвращал
  `success=true`, `message=null`, но по пользовательскому live-наблюдению не
  показывался в Web/Android/iOS. aiomax2 не подменяет его message update.

## Uploads

`upload_image()`, `upload_video()`, `upload_audio()` и `upload_file()` реализуют
multipart flow:

```text
POST /uploads -> внешний upload URL -> binary POST -> attachment -> message
```

API session и upload session разделены. Authorization добавляется к внешнему
upload только для image flow, где его явно показывает media guide; custom API
headers не наследуются. Binary upload автоматически не повторяется после
неоднозначной network failure. Каждый последующий `attachment.not.ready`
message attempt снова получает target limiter slot.

Источник token зависит от типа: image и file получают token из ответа upload
host, video и audio — из ответа `POST /uploads`. Multipart filename очищается
от локальных компонентов пути, поле формы всегда называется `data`.

Resumable/chunked upload пока не реализован как отдельный high-level helper.
Это не ограничивает поддержку `POST /uploads` и обычного multipart upload.
Отдельный resumable helper не реализуется догадками: официальный протокол
зависит от upload host и недостаточно формализован в OpenAPI.

## Осознанные исключения

- Удалённый `GET /chats` не имеет high-level compatibility method.
- `DELETE /chats/{chatId}` не реализован: метод отсутствует в актуальной
  OpenAPI и документации MAX, несмотря на сохранённую реализацию в Go SDK v2.
- `POST /chats/{chatId}/members` намеренно не реализован: OpenAPI `0.0.33`
  и Go SDK v2 всё ещё содержат метод, но официальная документация MAX
  сообщает о его удалении с 30 сентября 2026 года.
- `Bot.request()` остаётся для диагностики и будущих endpoints, но наличие
  low-level request API не означает поддержку удалённых операций.

## Версия источников

- MAX OpenAPI: `0.0.33`;
- schema repository HEAD: `1a4a502fab096aa3a15d83d7ea95667ffb44d2ac`;
- последняя правка `schema.yaml`: `5af13bddab6a16b991cbe2640c78d02e2a3047da`;
- Go SDK v2: `13264f872c743f55dcf7a8dfce43a16a055b46ab` (`v2.4.3`);
- API host: `https://platform-api2.max.ru`;
- token: чистое значение в `Authorization`, без `Bearer`;
- дата ручной сверки: 7 октября 2026 года.
