# MAX API coverage

Coverage is based on the official OpenAPI schema `0.0.33` and the live
documentation reviewed on 5 October 2026.

| MAX endpoint | `Bot` method |
|---|---|
| `GET /me` | `get_my_info` |
| `PATCH /me/commands` | `edit_my_commands` |
| `GET /chats/{chatId}` | `get_chat` |
| `PATCH /chats/{chatId}` | `edit_chat` |
| `POST /chats/{chatId}/actions` | `send_action` |
| `GET/PUT/DELETE /chats/{chatId}/pin` | `get_pinned_message`, `pin_message`, `unpin_message` |
| `GET/DELETE /chats/{chatId}/members/me` | `get_membership`, `leave_chat` |
| admin member endpoints | `get_admins`, `set_admins`, `revoke_admin` |
| `GET/DELETE /chats/{chatId}/members` | `get_members`, `remove_member` |
| subscription endpoints | `get_subscriptions`, `subscribe`, `unsubscribe` |
| `POST /uploads` | `get_upload_url`; `upload_media` completes multipart upload |
| `GET/POST/PUT/DELETE /messages` | `get_messages`, `send_message`, `edit_message`, `delete_message` |
| `GET /messages/{messageId}` | `get_message` |
| comment endpoints | `get_comments`, `send_comment`, `edit_comment`, `delete_comment`, `get_comment` |
| `GET /videos/{videoToken}` | `get_video_attachment_details` |
| `POST /answers` | `answer_callback` |
| `GET /updates` | `get_updates`; normally driven by `Dispatcher.start_polling` |

## Deliberate exclusions

The documentation says `GET /chats` stopped being supported in June 2026; it
is also absent from schema `0.0.33`. It is not exposed.

Although schema `0.0.33` still contains `POST /chats/{chatId}/members`, the
live documentation says the method was restricted on 9 September 2026 and
removed on 30 September 2026. `aiomax2` therefore does not expose an
`add_members` compatibility method. The generic `Bot.request` remains
available for diagnostics and future API changes, but removed functionality is
not presented as supported.

`upload_media` implements the documented one-shot multipart workflow. The
resumable/chunked upload variant is deferred because its protocol varies by the
upload host and is not fully specified by OpenAPI.

