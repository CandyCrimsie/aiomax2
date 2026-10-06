# Handlers и события

Handler — функция, которая вызывается `Dispatcher`, когда входящий MAX update
соответствует observer и всем зарегистрированным фильтрам.

`aiomax2` поддерживает отдельные observers для всех актуальных типов событий
MAX API. Основные aliases сделаны в стиле aiogram:

```python
router.message
router.callback_query
```

При этом они соответствуют настоящим MAX update types:

```text
router.message        -> message_created
router.callback_query -> message_callback
```

Handlers могут быть как `async`, так и обычными функциями. Для ботов обычно
рекомендуется `async def`, поскольку MAX API, FSM и большинство внешних
операций асинхронны.

## Базовый handler

```python
from aiomax2 import Router
from aiomax2.types import Message

router = Router()


@router.message()
async def on_message(message: Message) -> None:
    await message.answer("Получено")
```

`router.message` — alias для `router.message_created`:

```python
router.message is router.message_created
```

Поэтому следующие регистрации относятся к одному и тому же observer:

```python
@router.message()
async def first(message: Message) -> None: ...


@router.message_created()
async def second(message: Message) -> None: ...
```

Обычно рекомендуется использовать более короткий `router.message`.

## Все observers

`Router` предоставляет observers для всех 19 актуальных MAX update types, а
также общий `router.update`.

| Observer | MAX `update_type` | Объект в handler |
|---|---|---|
| `router.message` | `message_created` | `Message` |
| `router.message_created` | `message_created` | `Message` |
| `router.callback_query` | `message_callback` | `CallbackQuery` |
| `router.message_callback` | `message_callback` | `CallbackQuery` |
| `router.message_edited` | `message_edited` | `Message` |
| `router.message_removed` | `message_removed` | `MessageRemovedUpdate` |
| `router.comment_created` | `comment_created` | `Message` |
| `router.comment_edited` | `comment_edited` | `Message` |
| `router.comment_removed` | `comment_removed` | `CommentRemovedUpdate` |
| `router.bot_added` | `bot_added` | `BotAddedToChatUpdate` |
| `router.bot_removed` | `bot_removed` | `BotRemovedFromChatUpdate` |
| `router.user_added` | `user_added` | `UserAddedToChatUpdate` |
| `router.user_removed` | `user_removed` | `UserRemovedFromChatUpdate` |
| `router.bot_started` | `bot_started` | `BotStartedUpdate` |
| `router.bot_stopped` | `bot_stopped` | `BotStoppedUpdate` |
| `router.dialog_cleared` | `dialog_cleared` | `DialogClearedUpdate` |
| `router.dialog_removed` | `dialog_removed` | `DialogRemovedUpdate` |
| `router.dialog_muted` | `dialog_muted` | `DialogMutedUpdate` |
| `router.dialog_unmuted` | `dialog_unmuted` | `DialogUnmutedUpdate` |
| `router.chat_title_changed` | `chat_title_changed` | `ChatTitleChangedUpdate` |
| `router.bot_admin_permissions_changed` | `bot_admin_permissions_changed` | `BotAdminPermissionsChangedUpdate` |
| `router.update` | любой update | соответствующий `Update` |

`router.callback_query` является alias для `router.message_callback`:

```python
router.callback_query is router.message_callback
```

Для обычной разработки рекомендуется использовать `message` и
`callback_query`, а имена `message_created` и `message_callback` полезны, когда
нужно явно сопоставить код с названиями событий MAX API.

## Message

Событие `message_created` преобразуется из `MessageCreatedUpdate` в удобный
`Message`.

```python
from aiomax2.types import Message


@router.message()
async def message_handler(message: Message) -> None:
    print(message.text)
    print(message.message_id)
    print(message.chat_id)

    await message.answer("Ответ")
```

В handler не нужно обращаться к дополнительному `update.message` — объект
`Message` передаётся напрямую.

Для MAX используются поля:

```python
message.chat_id
message.user_id
message.sender
message.recipient
message.body
message.text
message.message_id
```

Не используйте Telegram-specific обращения вроде:

```python
message.chat.id
message.from_user.id
```

## Callback query

`message_callback` преобразуется в `CallbackQuery`.

```python
from aiomax2.types import CallbackQuery


@router.callback_query()
async def callback_handler(callback_query: CallbackQuery) -> None:
    print(callback_query.callback_id)
    print(callback_query.payload)
    print(callback_query.user.user_id)

    await callback_query.answer(
        notification="Готово",
        text="Callback обработан",
    )
```

Исходный `Message` может отсутствовать, например если сообщение уже было
удалено:

```python
@router.callback_query()
async def callback_handler(callback_query: CallbackQuery) -> None:
    if callback_query.message is not None:
        print(callback_query.message.message_id)
```

## Редактирование сообщений

`message_edited` также передаёт непосредственно `Message`:

```python
from aiomax2.types import Message


@router.message_edited()
async def edited(message: Message) -> None:
    print(message.message_id)
    print(message.text)
```

## Удаление сообщений

Для удалённого сообщения полноценного объекта `Message` уже нет, поэтому
handler получает `MessageRemovedUpdate`.

```python
from aiomax2.types import MessageRemovedUpdate


@router.message_removed()
async def removed(update: MessageRemovedUpdate) -> None:
    print(update.message_id)
    print(update.chat_id)
    print(update.user_id)
```

Не рассчитывайте на `update.message` для removed events.

## Комментарии

MAX предоставляет три события комментариев:

```python
router.comment_created
router.comment_edited
router.comment_removed
```

Согласно актуальной MAX schema, `comment_created` и `comment_edited` содержат
`Message`, поэтому именно он передаётся напрямую в handler:

```python
from aiomax2.types import Message


@router.comment_created()
async def comment_created(message: Message) -> None:
    print(message.message_id)
    print(message.text)


@router.comment_edited()
async def comment_edited(message: Message) -> None:
    print(message.message_id)
    print(message.text)
```

Это отличается от ответов comment API методов, которые используют
`CommentMessage`.

Для удаления комментария используется отдельный update:

```python
from aiomax2.types import CommentRemovedUpdate


@router.comment_removed()
async def comment_removed(update: CommentRemovedUpdate) -> None:
    print(update.message_id)
    print(update.post_id)
    print(update.chat_id)
    print(update.user_id)
```

## Добавление и удаление бота

```python
from aiomax2.types import (
    BotAddedToChatUpdate,
    BotRemovedFromChatUpdate,
)


@router.bot_added()
async def bot_added(update: BotAddedToChatUpdate) -> None:
    print(update.chat_id)
    print(update.user.user_id)
    print(update.is_channel)


@router.bot_removed()
async def bot_removed(update: BotRemovedFromChatUpdate) -> None:
    print(update.chat_id)
    print(update.user.user_id)
```

## Добавление и удаление пользователей

```python
from aiomax2.types import (
    UserAddedToChatUpdate,
    UserRemovedFromChatUpdate,
)


@router.user_added()
async def user_added(update: UserAddedToChatUpdate) -> None:
    print(update.chat_id)
    print(update.user.user_id)
    print(update.inviter_id)


@router.user_removed()
async def user_removed(update: UserRemovedFromChatUpdate) -> None:
    print(update.chat_id)
    print(update.user.user_id)
    print(update.admin_id)
```

`inviter_id` и `admin_id` могут отсутствовать.

## Запуск и остановка бота пользователем

```python
from aiomax2.types import BotStartedUpdate, BotStoppedUpdate


@router.bot_started()
async def bot_started(update: BotStartedUpdate) -> None:
    print(update.chat_id)
    print(update.user.user_id)
    print(update.payload)
    print(update.user_locale)


@router.bot_stopped()
async def bot_stopped(update: BotStoppedUpdate) -> None:
    print(update.chat_id)
    print(update.user.user_id)
```

`BotStartedUpdate.payload` может использоваться для start payload и ограничен
MAX schema длиной 512 символов.

## События диалога

Доступны observers:

```python
router.dialog_cleared
router.dialog_removed
router.dialog_muted
router.dialog_unmuted
```

Пример:

```python
from aiomax2.types import (
    DialogClearedUpdate,
    DialogMutedUpdate,
    DialogRemovedUpdate,
    DialogUnmutedUpdate,
)


@router.dialog_cleared()
async def dialog_cleared(update: DialogClearedUpdate) -> None:
    print(update.chat_id)


@router.dialog_removed()
async def dialog_removed(update: DialogRemovedUpdate) -> None:
    print(update.chat_id)


@router.dialog_muted()
async def dialog_muted(update: DialogMutedUpdate) -> None:
    print(update.chat_id)
    print(update.muted_until)


@router.dialog_unmuted()
async def dialog_unmuted(update: DialogUnmutedUpdate) -> None:
    print(update.chat_id)
```

## Изменение названия чата

```python
from aiomax2.types import ChatTitleChangedUpdate


@router.chat_title_changed()
async def title_changed(update: ChatTitleChangedUpdate) -> None:
    print(update.chat_id)
    print(update.title)
    print(update.user.user_id)
```

## Изменение прав бота-администратора

```python
from aiomax2.types import BotAdminPermissionsChangedUpdate


@router.bot_admin_permissions_changed()
async def permissions_changed(
    update: BotAdminPermissionsChangedUpdate,
) -> None:
    print(update.chat_id)
    print(update.bot_id)
    print(update.is_admin)
    print(update.permissions)
```

На текущем MAX API событие `bot_admin_permissions_changed` доступно через
Webhook и не доставляется через Long Polling.

## Общий `router.update`

`router.update` работает с исходным типизированным объектом update до
конкретного event observer.

```python
from aiomax2.types import Update


@router.update()
async def any_update(update: Update) -> None:
    print(update.update_type)
```

!!! warning

    `router.update()` — не пассивный logger.

    Если handler общего `update` observer успешно обработал событие, конкретный
    observer (`message`, `callback_query`, `user_added` и т. д.) для этого
    Router уже не будет вызван.

    Для общего логирования всех событий лучше использовать outer middleware.

Например, общий handler удобно использовать как fallback только для неизвестных
будущих update types:

```python
from aiomax2.types import Update


def unknown_update(update: Update) -> bool:
    return type(update) is Update


@router.update(unknown_update)
async def handle_unknown_update(update: Update) -> None:
    print(f"Unknown MAX update: {update.update_type}")
```

Известные update types парсятся в конкретные классы, а неизвестный будущий
`update_type` остаётся обычным `Update`. Дополнительные неизвестные поля также
сохраняются для forward compatibility.

## Доступ к исходному Update

Даже когда handler получает `Message` или `CallbackQuery`, исходный update
доступен через context как `event_update` или `update`.

```python
from aiomax2.types import Message, MessageCreatedUpdate


@router.message()
async def handler(
    message: Message,
    event_update: MessageCreatedUpdate,
) -> None:
    print(message.text)
    print(event_update.timestamp)
    print(event_update.user_locale)
```

Это удобно, если нужны поля envelope, которые не входят в объект события.

## Dependency injection

Аргументы handler автоматически разрешаются из context.

Например:

```python
from aiomax2 import Bot
from aiomax2.filters import Command, CommandObject
from aiomax2.fsm import FSMContext
from aiomax2.types import Message


@router.message(Command("start"))
async def start(
    message: Message,
    command: CommandObject,
    bot: Bot,
    state: FSMContext,
) -> None:
    print(command.args)
    print(bot.id)

    await state.clear()
    await message.answer("Готово")
```

Стандартный context включает, в частности:

- `bot`;
- `dispatcher`;
- `router`;
- `update` / `event_update`;
- текущий event;
- `state` и `raw_state`, если FSM включён;
- значения, добавленные filters и middleware;
- пользовательские workflow data из `Dispatcher`.

Событие можно получить по имени параметра, по аннотации типа или как первый
позиционный аргумент handler.

## Фильтры

Фильтры передаются непосредственно observer:

```python
from aiomax2 import F
from aiomax2.filters import Command
from aiomax2.types import Message


@router.message(Command("start"))
async def start(message: Message) -> None:
    await message.answer("Start")


@router.message(F.sender.user_id == 123)
async def specific_user(message: Message) -> None:
    await message.answer("Привет")
```

Несколько фильтров одного handler работают как логическое `AND`:

```python
@router.message(Command("admin"), F.sender.user_id == ADMIN_ID)
async def admin(message: Message) -> None: ...
```

Подробнее см. разделы [Фильтры](filters.md),
[Command](commands.md) и [Magic filter](magic-filter.md).

## Observer-level фильтры

Фильтр можно применить ко всему observer:

```python
router.message.filter(F.text)
```

После этого он будет проверяться перед всеми handlers
`router.message` / `router.message_created`.

## Регистрация без декоратора

Любой handler можно зарегистрировать через `.register()`:

```python
async def hello(message: Message) -> None:
    await message.answer("Hello")


router.message.register(hello, F.text == "hello")
```

То же относится к остальным observers:

```python
router.user_added.register(on_user_added)
router.comment_removed.register(on_comment_removed)
router.dialog_muted.register(on_dialog_muted)
```

## Порядок handlers

Handlers одного observer проверяются в порядке регистрации.

```python
@router.message(F.text == "hello")
async def first(message: Message) -> None: ...


@router.message()
async def fallback(message: Message) -> None: ...
```

Если фильтры первого handler не прошли, проверяется следующий.

Как только подходящий handler обработал событие, дальнейший поиск для этого
observer прекращается.

Поэтому более специфичные handlers обычно следует регистрировать раньше
общих fallback handlers.

## `SkipHandler`

Если фильтр уже прошёл, но handler во время выполнения решил отказаться от
события, можно выбросить `SkipHandler`.

```python
from aiomax2.exceptions import SkipHandler
from aiomax2.types import Message


@router.message()
async def maybe_handle(message: Message) -> None:
    if message.text != "expected":
        raise SkipHandler

    await message.answer("Обработано")


@router.message()
async def fallback(message: Message) -> None:
    await message.answer("Fallback")
```

После `SkipHandler` observer продолжит проверять следующий handler.

## Sync handlers

Обычные функции также поддерживаются:

```python
@router.message()
def sync_handler(message: Message) -> None:
    print(message.text)
```

Если handler возвращает awaitable, `aiomax2` автоматически ожидает его.

Для реальных ботов предпочтительнее `async def`, поскольку вызовы API выглядят
так:

```python
@router.message()
async def async_handler(message: Message) -> None:
    await message.answer("Ответ")
```

## Nested routers

Observers работают одинаково и во вложенных `Router`.

```python
from aiomax2 import Dispatcher, Router

dispatcher = Dispatcher()
messages = Router(name="messages")
callbacks = Router(name="callbacks")

dispatcher.include_routers(messages, callbacks)


@messages.message()
async def message_handler(message: Message) -> None: ...


@callbacks.callback_query()
async def callback_handler(callback_query: CallbackQuery) -> None: ...
```

`Dispatcher.resolve_used_update_types()` собирает используемые MAX update types
также из вложенных routers. Это позволяет использовать фактически
зарегистрированные observers при настройке Webhook или Long Polling.

## Краткий пример

```python
from aiomax2 import Bot, Dispatcher, F, Router
from aiomax2.filters import Command
from aiomax2.types import (
    CallbackQuery,
    Message,
    MessageRemovedUpdate,
    UserAddedToChatUpdate,
)

bot = Bot("TOKEN")
dispatcher = Dispatcher()
router = Router()


@router.message(Command("start"))
async def start(message: Message) -> None:
    await message.answer("Бот запущен")


@router.callback_query(F.payload == "confirm")
async def confirm(callback_query: CallbackQuery) -> None:
    await callback_query.answer(
        notification="Готово",
        text="Подтверждено",
    )


@router.message_removed()
async def message_removed(update: MessageRemovedUpdate) -> None:
    print(f"Удалено сообщение {update.message_id}")


@router.user_added()
async def user_added(update: UserAddedToChatUpdate) -> None:
    print(f"Пользователь {update.user.user_id} добавлен в {update.chat_id}")


dispatcher.include_router(router)
```

Полный список событий MAX и их соответствие моделям также приведён в
[покрытии MAX API](api-coverage.md).