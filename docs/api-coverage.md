# Покрытие MAX API

Покрытие основано на официальной OpenAPI-схеме `0.0.33` и актуальной
документации, проверенных 5 октября 2026 года.

| MAX endpoint | Метод `Bot` | Статус | Ограничения и примечания |
|---|---|---|---|
| `GET /me` | `get_my_info` | Поддерживается | Запоминает `bot.id` |
| `PATCH /me/commands` | `edit_my_commands` | Поддерживается | Актуальный commands API |
| `GET /chats/{chatId}` | `get_chat` | Поддерживается | Типизированный `Chat` |
| `PATCH /chats/{chatId}` | `edit_chat` | Поддерживается | Включая `description` |
| `POST /chats/{chatId}/actions` | `send_action` | Поддерживается | `SenderAction` |
| `GET/PUT/DELETE /chats/{chatId}/pin` | `get_pinned_message`, `pin_message`, `unpin_message` | Поддерживается | Права проверяет MAX |
| `GET/DELETE /chats/{chatId}/members/me` | `get_membership`, `leave_chat` | Поддерживается | — |
| admin endpoints | `get_admins`, `set_admins`, `revoke_admin` | Поддерживается | — |
| `GET/DELETE /chats/{chatId}/members` | `get_members`, `remove_member` | Поддерживается | Добавление участников исключено |
| subscriptions | `get_subscriptions`, `subscribe`, `unsubscribe` | Поддерживается | Webhook — production transport |
| `POST /uploads` | `get_upload_url`, `upload_media` | Частично | One-shot multipart; без resumable upload |
| `GET /messages` | `get_messages` | Поддерживается | — |
| `POST /messages` | `send_message` | Поддерживается | 2 операции/с на target |
| `PUT /messages` | `edit_message` | Поддерживается | 2 операции/с на target |
| `DELETE /messages` | `delete_message` | Поддерживается | 2 операции/с на target |
| `GET /messages/{messageId}` | `get_message` | Поддерживается | — |
| comment endpoints | `get_comments`, `send_comment`, `edit_comment`, `delete_comment`, `get_comment` | Поддерживается | События комментариев пока только Webhook |
| `GET /videos/{videoToken}` | `get_video_attachment_details` | Поддерживается | — |
| `POST /answers` | `answer_callback`, `answer_callback_result` | Поддерживается | Второй метод сохраняет diagnostic `message`; 2 операции/с на target |
| `GET /updates` | `get_updates` | Поддерживается | Только разработка и тесты |

## Осознанные исключения

`GET /chats` перестал поддерживаться в июне 2026 года и отсутствует в схеме
`0.0.33`, поэтому метода совместимости нет.

Схема `0.0.33` ещё содержит `POST /chats/{chatId}/members`, но живая
документация указывает ограничение с 9 сентября и удаление с 30 сентября 2026.
`aiomax2` не предоставляет устаревший `add_members`. Низкоуровневый
`Bot.request()` остаётся для диагностики и будущих endpoints, но удалённая
возможность не заявляется поддерживаемой.

`upload_media` реализует документированный one-shot multipart workflow.
`attachment.not.ready` обрабатывается bounded retry при последующей отправке
или правке сообщения; binary upload не повторяется. Resumable/chunked вариант
отложен: протокол зависит от upload host и не описан полностью в OpenAPI.

## Версия источников

- MAX OpenAPI: `0.0.33`;
- API host: `https://platform-api2.max.ru`;
- token: чистое значение в `Authorization`, без `Bearer`;
- дата ручной сверки: 6 октября 2026.
