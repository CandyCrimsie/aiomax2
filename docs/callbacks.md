# Callback-кнопки и клавиатура

В MAX inline keyboard передаётся как attachment. Кнопка `callback` содержит
payload, который приходит в событии `message_callback`.

```python
from aiomax2 import F, Router
from aiomax2.types import (
    CallbackButton,
    CallbackQuery,
    InlineKeyboardAttachmentRequest,
    Keyboard,
    Message,
)

router = Router()


@router.message(F.text == "buttons")
async def buttons(message: Message) -> None:
    keyboard = InlineKeyboardAttachmentRequest(
        payload=Keyboard(
            buttons=[
                [
                    CallbackButton(
                        text="Подтвердить",
                        payload="confirm",
                    )
                ]
            ]
        )
    )
    await message.answer("Выберите действие", attachments=[keyboard])


@router.callback_query(F.payload == "confirm")
async def confirm(callback_query: CallbackQuery) -> None:
    await callback_query.answer(notification="Готово")
```

`callback_query.answer()` вызывает `POST /answers`. Он может показать
одноразовое уведомление, изменить исходное сообщение или сделать оба действия:

```python
await callback_query.answer(
    notification="Сохранено",
    text="Статус: подтверждено",
)
```

Shortcut передаёт `chat_id`/`user_id` из callback message в единый target
limiter. Если исходное сообщение уже удалено, используется пользователь из
callback.

MAX также определяет `LinkButton`, `MessageButton`, `ClipboardButton`,
`OpenAppButton`, `RequestContactButton` и `RequestGeoLocationButton`. Их поля
соответствуют официальным моделям MAX.
