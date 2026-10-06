# Live smoke-test 0.1.0a3

Автоматические tests проверяют parsing, Dispatcher и Webhook round-trip без
реального MAX. Эта страница описывает отдельную ручную проверку на настоящем
боте. Ни один пункт таблиц ниже не считается пройденным самим code pass.

## Запуск harness

Используйте отдельного тестового бота, тестовую группу/канал и отдельные
учётные записи участников. Не используйте production chat.

```bash
export MAX_BOT_TOKEN="..."
export MAX_WEBHOOK_BASE_URL="https://bot.example.ru"
export MAX_WEBHOOK_SECRET="replace-with-random-secret"

# Необязательно для upload-команд:
export MAX_TEST_IMAGE="/path/to/image.png"
export MAX_TEST_FILE="/path/to/file.pdf"
export MAX_TEST_AUDIO="/path/to/audio.mp3"
export MAX_TEST_VIDEO="/path/to/video.mp4"

uvicorn examples.live_updates:app --host 127.0.0.1 --port 8000
```

Публичный reverse proxy должен направлять
`https://bot.example.ru/webhook` на `127.0.0.1:8000/webhook` и иметь
сертификат, которому доверяет MAX. Harness подписывается на все известные
update types в FastAPI lifespan. Для multi-worker запуска регистрацию
подписки вынесите в отдельный setup step: каждый worker выполняет lifespan.

В stdout для каждого события выводятся:

- `update_type`;
- имя Pydantic-класса;
- ключевые `chat_id`, `user_id`, `message_id`, `callback_id`;
- payload с удалёнными token/secret/authorization и обрезанными длинными
  строками.

Bot token и Webhook secret в лог не выводятся.

## Проверка update types

Во всех сценариях ожидается HTTP `200` от Webhook, одна JSON-запись в stdout и
вызов указанного observer. `FAIL`: запросы повторяются из-за 5xx, отсутствует
лог, выбран другой observer, payload не парсится либо ключевые ID неверны.

| `update_type` | Prerequisite и действие | Ожидаемый handler | Live в этом pass |
|---|---|---|---|
| `message_created` | Написать боту или отправить сообщение/пост в тестовом чате | `router.message`, объект `Message` | Не проверено |
| `message_callback` | Выполнить `/buttons`, нажать Callback | `router.callback_query`, объект `CallbackQuery` | Не проверено |
| `message_edited` | Другому пользователю изменить своё сообщение/пост | `router.message_edited`, объект `Message` | Не проверено |
| `message_removed` | Другому пользователю удалить своё сообщение/пост | `router.message_removed`, `MessageRemovedUpdate` | Не проверено |
| `comment_created` | В канале с комментариями другому пользователю создать комментарий; действия самого бота update не дают | `router.comment_created`, schema payload `Message` | Не проверено |
| `comment_edited` | Другому пользователю изменить комментарий | `router.comment_edited`, schema payload `Message` | Не проверено |
| `comment_removed` | Другому пользователю удалить комментарий | `router.comment_removed`, `CommentRemovedUpdate` | Не проверено |
| `bot_added` | Добавить тестового бота в тестовую группу/канал | `router.bot_added`, `BotAddedToChatUpdate` | Не проверено |
| `bot_removed` | Удалить тестового бота из тестовой группы/канала | `router.bot_removed`, `BotRemovedFromChatUpdate` | Не проверено |
| `user_added` | Добавить отдельного тестового пользователя или войти по ссылке | `router.user_added`, `UserAddedToChatUpdate` | Не проверено |
| `user_removed` | Удалить тестового пользователя либо выйти им самостоятельно | `router.user_removed`, `UserRemovedFromChatUpdate` | Не проверено |
| `bot_started` | Пользователю впервые запустить или возобновить бота | `router.bot_started`, `BotStartedUpdate` | Не проверено |
| `bot_stopped` | Пользователю остановить/удалить бота в настройках | `router.bot_stopped`, `BotStoppedUpdate` | Не проверено |
| `dialog_cleared` | Пользователю очистить историю диалога с ботом | `router.dialog_cleared`, `DialogClearedUpdate` | Не проверено |
| `dialog_removed` | Пользователю удалить диалог с ботом; MAX также может прислать `bot_stopped` | `router.dialog_removed`, `DialogRemovedUpdate` | Не проверено |
| `dialog_muted` | Пользователю отключить уведомления диалога | `router.dialog_muted`, `DialogMutedUpdate` | Не проверено |
| `dialog_unmuted` | Пользователю включить уведомления диалога | `router.dialog_unmuted`, `DialogUnmutedUpdate` | Не проверено |
| `chat_title_changed` | Изменить название тестовой группы/канала | `router.chat_title_changed`, `ChatTitleChangedUpdate` | Не проверено |
| `bot_admin_permissions_changed` | В Webhook-подписке изменить права бота-администратора | `router.bot_admin_permissions_changed`, `BotAdminPermissionsChangedUpdate` | Не проверено; Long Polling пока не поддерживается MAX |

Removed events намеренно не содержат полноценный `Message`. Проверяйте их ID
не через message shortcuts, а непосредственно в соответствующем Update.

## Безопасные API-команды

| Команда | Prerequisite / действие | Pass |
|---|---|---|
| `/start`, `/reply`, `/edit`, `/delete` | Диалог или тестовый чат | Ответ, reply, изменение и удаление только сообщения самого бота |
| `/buttons`, `/builder` | Клиент с inline keyboard | Отображаются callback и семь типов кнопок; callback приходит в stdout |
| `/fsm`, затем текст | Любой диалог | Второе сообщение получает сохранённое состояние, затем state очищается |
| `/me` | Валидный token | Возвращаются ID и имя бота |
| `/subscriptions` | Webhook уже зарегистрирован | Видна текущая подписка и её update types |
| `/image`, `/file`, `/audio`, `/video_upload` | Соответствующий `MAX_TEST_*` path | Upload завершается, attachment приходит в чат; token не попадает в stdout |
| `/ratelimit` | Любой чат | Три ответа доставлены, клиентский target limiter не превышает 2 ops/sec |
| `/request_contact`, `/clipboard` | Клиент с поддержкой кнопок | Контактное действие/копирование работают |
| `/send_contact <user_id>` | Валидный numeric MAX ID | Приходит contact attachment |
| `/sticker <code>` | Валидный sticker code | Приходит sticker attachment |
| `/html`, `/markdown` | Любой чат | MAX отображает форматирование без переписывания aiomax2 |
| `/chat`, `/action` | Бот в группе/канале | Возвращается Chat; `typing_on` принимается API |
| `/members`, `/admins` | Бот-администратор | Возвращаются `ChatMember` из поля `members` |
| `/comments <post_id>` | Канал, comments включены, нужные admin permissions | Возвращается список `CommentMessage` |
| `/video <video_token>` | Token существующего video attachment | Возвращаются dimensions и duration |

## Изменяющие состояние команды

Запускайте только в отдельной тестовой группе. Они требуют точное слово
`CONFIRM`; без него выполняется только подсказка:

```text
/pin <message_id> CONFIRM
/unpin CONFIRM
/remove_member <user_id> CONFIRM
/revoke_admin <user_id> CONFIRM
/leave_chat CONFIRM
```

Перед `/remove_member` подготовьте отдельного тестового участника. Перед
`/revoke_admin` — отдельного тестового администратора. `/leave_chat` удаляет
бота из текущего чата и должен выполняться последним. Назначение администратора
не автоматизировано: первого bot-admin MAX требует назначать через клиент, а
набор допустимых прав зависит от типа чата и субъекта.

## Что ранее проверено пользователем

По предоставленному ранее live-отчёту уже проверялись Webhook,
send/reply/edit/delete, FSM, `get_my_info`, subscriptions, image/file,
callbacks, keyboard, request_contact, clipboard, contacts, sticker, HTML,
Markdown и TLS system/custom CA setup. Этот code pass их автоматически не
переобъявляет live-проверенными; перед релизом рекомендуется короткая
регрессия соответствующих команд.

Notification-only callback отдельно остаётся runtime peculiarity: MAX API
возвращал `success=true`, `message=null`, но уведомление не отображалось в Web,
Android и iOS. Это не считается ошибкой сериализации aiomax2 и не заменяется
автоматически на message update.
