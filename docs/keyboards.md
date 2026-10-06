# Inline-клавиатуры

MAX передаёт inline-клавиатуру как attachment сообщения. `aiomax2` сохраняет
эту wire-модель и добавляет короткий builder API.

## Быстрый старт

```python
from aiomax2.utils.keyboard import InlineKeyboardBuilder

builder = InlineKeyboardBuilder()
builder.button(text="Подтвердить", callback_data="confirm")
builder.button(text="Отменить", callback_data="cancel")
builder.adjust(2)

await message.answer(
    "Выберите действие",
    reply_markup=builder.as_markup(),
)
```

`callback_data` — только удобный alias aiomax2. На wire он становится полем
MAX `payload`; поле `callback_data` в API не отправляется.

`reply_markup` также является только Python convenience: библиотека добавляет
`InlineKeyboardAttachmentRequest` в `attachments`. Это работает в
`Bot.send_message()`, `Message.answer()`, `Message.reply()`,
`Bot.edit_message()`, `Message.edit_text()` и при изменении сообщения через
callback answer. Если `attachments` уже содержит `inline_keyboard`, передача
`reply_markup` вызывает `ValidationError`, чтобы не создать две клавиатуры
неявно.

## Типы кнопок MAX

```python
builder = InlineKeyboardBuilder()
builder.callback(text="Подтвердить", payload="confirm")
builder.link(text="Документация", url="https://dev.max.ru")
builder.message(text="/help")
builder.clipboard(text="Скопировать", payload="ABC-123")
builder.request_contact(text="Поделиться контактом")
builder.request_geo_location(text="Отправить геопозицию", quick=False)
builder.open_app(
    text="Открыть приложение",
    web_app="your-web-app-id",
    payload="start-screen",
)
```

Builder поддерживает все актуальные типы кнопок MAX: `callback`, `link`,
`request_contact`, `request_geo_location`, `open_app`, `message` и
`clipboard`. Telegram Reply Keyboard, `ReplyKeyboardRemove` и `ForceReply` в
MAX API отсутствуют и не эмулируются.

## Компоновка

- `add(*buttons)` добавляет готовые typed-кнопки и заполняет текущий ряд;
- `row(*buttons, width=...)` начинает новые ряды;
- `adjust(*sizes, repeat=False)` перекладывает все кнопки по размерам рядов;
- `attach(other)` присоединяет строки другого builder;
- `as_markup()` возвращает `InlineKeyboardAttachmentRequest`;
- `from_markup(markup)` создаёт builder из low-level attachment.

## Low-level API

Исходные модели остаются доступны без builder:

```python
from aiomax2.types import (
    CallbackButton,
    InlineKeyboardAttachmentRequest,
    Keyboard,
)

keyboard = InlineKeyboardAttachmentRequest(
    payload=Keyboard(buttons=[[CallbackButton(text="Да", payload="yes")]])
)

await message.answer("Выберите", attachments=[keyboard])
```

## Ограничения

Локальная Pydantic-валидация применяет ограничения актуальной документации и
OpenAPI MAX:

- до 30 рядов и до 210 кнопок всего;
- до 7 обычных кнопок в ряду;
- до 3 кнопок в ряду, содержащем `link`, `open_app`,
  `request_geo_location` или `request_contact`;
- текст кнопки — от 1 до 128 символов;
- callback payload — до 1024 символов;
- link URL — до 2048 символов;
- clipboard payload — до 1024 символов;
- open_app payload — до 512 символов и только символы, допустимые OpenAPI
  pattern `^[\w-]*$`.

## Callback answer

```python
@router.callback_query(F.payload == "confirm")
async def confirm(callback: CallbackQuery) -> None:
    await callback.answer(
        notification="Подтверждено",
        text="Готово",
    )


@router.callback_query(F.payload == "cancel")
async def cancel(callback: CallbackQuery) -> None:
    await callback.answer(notification="Отменено")
```

Notification-only сериализуется как `{"notification": "Отменено"}` — без
`message: null` и без пустого message object. Это соответствует официальному
контракту «изменённое сообщение и/или уведомление». Пустой `answer()` сейчас
не запрещён локально, потому что OpenAPI не делает ни одно из двух полей
обязательным; практического эффекта от такого запроса ожидать не следует.

Обычный `answer_callback()` сохраняет совместимый результат `bool`. Для
диагностики ответа `{"success": false, "message": "..."}` используйте
`answer_callback_result()`:

```python
result = await bot.answer_callback_result(
    callback.callback_id,
    notification="Готово",
)
if not result.success:
    print(result.message)
```

См. [официальное руководство по клавиатурам](https://dev.max.ru/docs-api/use-cases/sending-messages/keyboard)
и [`POST /answers`](https://dev.max.ru/docs-api/methods/POST/answers).
