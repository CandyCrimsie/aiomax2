# Миграция с aiogram 3.x

Знакомые концепции намеренно сохраняют знакомые имена:

| aiogram | aiomax2 | Примечание |
|---|---|---|
| `Bot` | `Bot` | MAX token отправляется без `Bearer` |
| `Dispatcher` | `Dispatcher` | корневой router |
| `Router` | `Router` | observers и вложенные routers |
| `Command("start")` | `Command("start")` | добавляет `CommandObject` |
| `F.text` | `F.text` | собственный небольшой expression engine |
| `Message` | `Message` | реальные поля MAX; id хранится в `body.mid` |
| `message.answer()` | `message.answer()` | выбирает MAX `chat_id` или `user_id` |
| `FSMContext` | `FSMContext` | async storage API |
| `State`, `StatesGroup` | те же имена | похожий декларативный стиль |

## Простой handler

aiogram:

```python
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("start"))
async def start(message: Message) -> None:
    await message.answer("Hello")
```

aiomax2:

```python
from aiomax2 import F, Router
from aiomax2.filters import Command
from aiomax2.types import Message

router = Router()


@router.message(Command("start"))
async def start(message: Message) -> None:
    await message.answer("Hello")
```

Сходство заканчивается там, где различаются платформы.

## Поля Message

```python
# aiogram / Telegram
chat_id = message.chat.id
message_id = message.message_id

# aiomax2 / MAX
chat_id = message.chat_id
message_id = message.message_id  # удобное свойство поверх message.body.mid
recipient = message.recipient
```

В `aiomax2` нет искусственного `message.chat.id`. В диалоге target может быть
представлен `recipient.user_id`, а в чате/канале — `recipient.chat_id`.

## Callback

MAX-событие содержит `Callback` и иногда исходный `Message`. Router передаёт
удобный `CallbackQuery`, но операция соответствует `POST /answers`, а не
Telegram `answerCallbackQuery`:

```python
@router.callback_query(F.payload == "confirm")
async def confirm(callback: CallbackQuery) -> None:
    await callback.answer(notification="Подтверждено")


@router.bot_started()
async def started(event: BotStartedUpdate) -> None:
    # MAX передаёт chat_id, user, optional payload и locale.
    ...
```

## Клавиатуры

На wire MAX использует attachment. Для знакомого DX можно использовать
`InlineKeyboardBuilder` и convenience-параметр `reply_markup`:

```python
builder = InlineKeyboardBuilder()
builder.button(text="OK", callback_data="confirm")
await message.answer("Выберите", reply_markup=builder.as_markup())
```

Это не Telegram Reply Keyboard: внутри всё равно создаётся MAX
`inline_keyboard` attachment. Low-level вариант также сохранён:

```python
keyboard = InlineKeyboardAttachmentRequest(
    payload=Keyboard(buttons=[[CallbackButton(text="OK", payload="confirm")]])
)
await message.answer("Выберите", attachments=[keyboard])
```

Используйте реальные типы кнопок и payload MAX. Telegram Reply Keyboard,
`ReplyKeyboardRemove` и `ForceReply` не эмулируются.

## Events, которых нет в Telegram

`bot_started`, `bot_stopped`, dialog muted/cleared/removed, comments и изменение
прав администратора моделируются напрямую. Не пытайтесь преобразовывать их в
похожие Telegram updates.

## Запуск

В aiogram polling часто используют и в production. MAX ограничивает Long
Polling по скорости и хранению событий и рекомендует Webhook. Для production
перенесите startup на FastAPI/aiohttp adapter и создайте подписку через
`Bot.subscribe()`.

## FSM и storage

Объявление `StatesGroup` похоже, но встроенное `MemoryStorage` локально одному
процессу. Для нескольких workers понадобится внешнее storage. Автоматической
совместимости с aiogram Redis storage нет.
