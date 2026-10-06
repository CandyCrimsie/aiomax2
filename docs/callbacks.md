# Callback-события

Callback позволяет боту обработать нажатие на inline-кнопку без отправки
пользователем отдельного текстового сообщения.

Общий поток выглядит так:

```text
CallbackButton
      │
      ▼
пользователь нажимает кнопку
      │
      ▼
MAX отправляет message_callback
      │
      ▼
router.callback_query
      │
      ▼
CallbackQuery
      │
      ▼
callback.answer(...)
```

В aiomax2 для обработки таких событий используется observer:

```python
router.callback_query
```

Он является удобным alias для MAX-события:

```text
message_callback
```

## Быстрый пример

Создадим кнопку:

```python
from aiomax2 import F, Router
from aiomax2.types import CallbackQuery, Message
from aiomax2.utils.keyboard import InlineKeyboardBuilder


router = Router()


@router.message(F.text == "buttons")
async def buttons(message: Message) -> None:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Подтвердить",
        callback_data="confirm",
    )

    await message.answer(
        "Выберите действие",
        reply_markup=builder.as_markup(),
    )
```

После нажатия кнопки MAX отправит событие `message_callback`.

Обработать его можно так:

```python
@router.callback_query(F.payload == "confirm")
async def confirm(callback: CallbackQuery) -> None:
    await callback.answer(
        notification="Готово",
    )
```

`callback_data="confirm"` в builder является удобным alias aiomax2.

На уровне MAX API значение передаётся как:

```text
payload
```

и приходит в:

```python
callback.payload
```

Подробнее о создании кнопок и клавиатур:
[Inline-клавиатуры](keyboards.md).

## `CallbackQuery`

Handler `router.callback_query` получает объект `CallbackQuery`.

```python
from aiomax2.types import CallbackQuery


@router.callback_query()
async def callback_handler(callback: CallbackQuery) -> None:
    print(callback.callback_id)
    print(callback.payload)
    print(callback.timestamp)
    print(callback.user)
    print(callback.message)
    print(callback.user_locale)
```

Основные поля:

| Поле | Назначение |
| --- | --- |
| `callback_id` | идентификатор callback для ответа через `POST /answers` |
| `payload` | значение, указанное в callback-кнопке |
| `timestamp` | время callback-события |
| `user` | пользователь, нажавший кнопку |
| `message` | исходное сообщение, если оно доступно |
| `user_locale` | locale пользователя, если MAX передал его |

`CallbackQuery` создаётся aiomax2 из MAX-события `message_callback`.

## `payload`

Основной способ определить, какая кнопка была нажата — поле `payload`.

Например, клавиатура:

```python
builder = InlineKeyboardBuilder()

builder.button(
    text="Да",
    callback_data="confirm",
)

builder.button(
    text="Нет",
    callback_data="cancel",
)

builder.adjust(2)
```

может обрабатываться двумя handlers:

```python
@router.callback_query(F.payload == "confirm")
async def confirm(callback: CallbackQuery) -> None:
    await callback.answer(notification="Подтверждено")


@router.callback_query(F.payload == "cancel")
async def cancel(callback: CallbackQuery) -> None:
    await callback.answer(notification="Отменено")
```

Или одним:

```python
@router.callback_query(F.payload.in_({"confirm", "cancel"}))
async def action(callback: CallbackQuery) -> None:
    if callback.payload == "confirm":
        await callback.answer(notification="Подтверждено")
        return

    await callback.answer(notification="Отменено")
```

Подробнее о `F`:
[Magic filter](magic-filter.md).

## `callback_id`

Не следует путать:

```python
callback.payload
```

и:

```python
callback.callback_id
```

`payload` задаётся разработчиком при создании кнопки:

```python
builder.button(
    text="Удалить",
    callback_data="delete",
)
```

и используется для маршрутизации:

```python
F.payload == "delete"
```

`callback_id` создаётся MAX и идентифицирует конкретное callback-событие.

Именно `callback_id` используется при отправке ответа в:

```text
POST /answers
```

При использовании:

```python
await callback.answer(...)
```

aiomax2 передаёт `callback.callback_id` автоматически.

## Пользователь

Пользователь, нажавший кнопку, доступен через:

```python
callback.user
```

Например:

```python
@router.callback_query(F.payload == "profile")
async def profile(callback: CallbackQuery) -> None:
    user_id = callback.user.user_id

    await callback.answer(
        notification=f"Ваш ID: {user_id}",
    )
```

Фильтровать callback можно непосредственно по пользователю:

```python
ADMIN_ID = 123456


@router.callback_query(
    F.payload == "admin",
    F.user.user_id == ADMIN_ID,
)
async def admin(callback: CallbackQuery) -> None:
    await callback.answer(notification="Доступ разрешён")
```

Несколько filters одного handler работают как логическое `AND`.

## Исходное сообщение

Если MAX передал исходное сообщение, оно доступно через:

```python
callback.message
```

Например:

```python
@router.callback_query()
async def callback_handler(callback: CallbackQuery) -> None:
    if callback.message is not None:
        print(callback.message.message_id)
        print(callback.message.text)
        print(callback.message.chat_id)
```

Поле:

```python
callback.message
```

имеет тип:

```python
Message | None
```

Поэтому нельзя считать, что исходное сообщение присутствует всегда.

Например, оно может отсутствовать, если MAX прислал callback без доступного
объекта сообщения.

Правильно:

```python
if callback.message is not None:
    message_id = callback.message.message_id
```

Не следует без проверки писать:

```python
callback.message.message_id
```

## Ответ на callback

Основной shortcut:

```python
await callback.answer(...)
```

Он вызывает MAX endpoint:

```text
POST /answers
```

и возвращает:

```python
bool
```

Простейший вариант:

```python
@router.callback_query(F.payload == "confirm")
async def confirm(callback: CallbackQuery) -> None:
    success = await callback.answer(
        notification="Готово",
    )

    print(success)
```

## Уведомление

Через `notification` можно передать текст одноразового уведомления:

```python
await callback.answer(
    notification="Сохранено",
)
```

На wire aiomax2 отправит:

```json
{
  "notification": "Сохранено"
}
```

без искусственного пустого `message`.

Это соответствует текущей модели MAX API.

!!! note

    Фактическое отображение notification-only зависит от поведения клиента
    MAX.

    Во время live smoke-test MAX API успешно принимал такой ответ и возвращал
    `success=true`, но отдельное notification-only не отображалось в
    протестированных Web, Android и iOS клиентах.

    При одновременном изменении сообщения callback answer отображался
    корректно.

    aiomax2 не подменяет это поведение и не добавляет фиктивное сообщение
    автоматически.

## Изменение сообщения через callback

Ответ на callback может одновременно изменить сообщение.

Для простого случая можно передать новый текст:

```python
@router.callback_query(F.payload == "confirm")
async def confirm(callback: CallbackQuery) -> None:
    await callback.answer(
        text="Статус: подтверждено",
    )
```

`text` — convenience-параметр aiomax2.

Библиотека автоматически создаст MAX `NewMessageBody`.

Можно одновременно передать notification:

```python
await callback.answer(
    notification="Сохранено",
    text="Статус: подтверждено",
)
```

То есть один callback answer может:

```text
показать notification
        +
изменить сообщение
```

## Изменение клавиатуры

Через callback answer можно передать новую inline-клавиатуру:

```python
from aiomax2.utils.keyboard import InlineKeyboardBuilder


@router.callback_query(F.payload == "next")
async def next_page(callback: CallbackQuery) -> None:
    builder = InlineKeyboardBuilder()

    builder.button(
        text="Назад",
        callback_data="back",
    )

    await callback.answer(
        text="Страница 2",
        reply_markup=builder.as_markup(),
    )
```

`reply_markup` является удобным Python API.

На уровне MAX клавиатура остаётся attachment типа:

```text
inline_keyboard
```

Подробнее:
[Inline-клавиатуры](keyboards.md).

## Attachments

При изменении сообщения через callback answer также можно передать
attachments:

```python
await callback.answer(
    text="Обновлено",
    attachments=[attachment],
)
```

`attachments` использует те же `AttachmentRequest`, что и:

```python
Bot.send_message()
Message.answer()
Message.reply()
Bot.edit_message()
```

Нельзя одновременно передавать inline keyboard через:

```python
attachments
```

и:

```python
reply_markup
```

если в `attachments` уже присутствует `inline_keyboard`.

aiomax2 в таком случае выбросит `ValidationError`, чтобы не создать две
клавиатуры неявно.

## Форматирование текста

При изменении сообщения можно указать формат:

```python
from aiomax2 import TextFormat


await callback.answer(
    text="<b>Готово</b>",
    format=TextFormat.HTML,
)
```

Или Markdown:

```python
await callback.answer(
    text="**Готово**",
    format=TextFormat.MARKDOWN,
)
```

Подробнее:
[Форматирование сообщений](formatting.md).

## Отключение preview ссылок

При изменении текста можно передать:

```python
await callback.answer(
    text="https://example.com",
    disable_link_preview=True,
)
```

Этот параметр передаётся MAX при обработке callback answer.

## `NewMessageBody`

Вместо convenience-параметров можно сформировать объект сообщения вручную:

```python
from aiomax2.types import NewMessageBody


body = NewMessageBody(
    text="Статус: подтверждено",
)

await callback.answer(
    message=body,
)
```

Это low-level вариант.

Обычно проще использовать:

```python
await callback.answer(
    text="Статус: подтверждено",
)
```

## `message` и convenience-параметры

Нельзя одновременно передавать:

```python
message = NewMessageBody(...)
```

и поля, из которых aiomax2 сам создаёт сообщение:

```python
text=
attachments=
reply_markup=
format=
```

Например, неправильно:

```python
await callback.answer(
    message=NewMessageBody(text="Hello"),
    text="World",
)
```

aiomax2 выбросит `ValidationError`.

Используйте один из двух вариантов.

Высокоуровневый:

```python
await callback.answer(
    text="Hello",
)
```

или low-level:

```python
await callback.answer(
    message=NewMessageBody(
        text="Hello",
    ),
)
```

## Диагностический ответ MAX

Обычный:

```python
await callback.answer(...)
```

возвращает только:

```python
bool
```

Этого достаточно для большинства handlers.

Если требуется получить диагностическое сообщение MAX при:

```text
success=false
```

можно использовать:

```python
bot.answer_callback_result(...)
```

Например:

```python
result = await bot.answer_callback_result(
    callback.callback_id,
    notification="Готово",
)

if not result.success:
    print(result.message)
```

Метод возвращает:

```python
SimpleQueryResult
```

вместо одного `bool`.

Для обычного приложения предпочтительнее:

```python
callback.answer()
```

а `answer_callback_result()` полезен для диагностики и низкоуровневой
обработки ошибок API.

## Ответ через `Bot`

Shortcut:

```python
callback.answer(...)
```

в конечном итоге использует:

```python
Bot.answer_callback(...)
```

Низкоуровневый вызов также доступен напрямую:

```python
await bot.answer_callback(
    callback.callback_id,
    notification="Готово",
)
```

Но внутри callback handler обычно лучше использовать:

```python
await callback.answer(...)
```

потому что `CallbackQuery` уже содержит необходимые данные события и
автоматически передаёт идентификатор callback.

## Target rate limit

Callback shortcut передаёт в `Bot` target исходного сообщения.

Если доступен:

```python
callback.message.chat_id
```

он используется как target.

Если исходного сообщения нет, aiomax2 использует:

```python
callback.user.user_id
```

Это позволяет callback operations участвовать в общей клиентской
per-target rate limiting политике aiomax2 вместе с операциями над сообщениями.

Для обычного пользовательского кода дополнительная настройка не требуется.

## Пустой `answer()`

Технически текущая модель MAX API не требует обязательного наличия
`notification` или `message`, поэтому aiomax2 локально не запрещает:

```python
await callback.answer()
```

Однако такой запрос не содержит полезного действия.

Для реального callback обычно следует передать хотя бы:

```python
notification=
```

или изменение сообщения:

```python
text=
message=
attachments=
reply_markup=
```

## Low-level callback-кнопка

Builder является рекомендуемым способом создания клавиатур:

```python
builder.button(
    text="Подтвердить",
    callback_data="confirm",
)
```

Но low-level MAX-модель также доступна напрямую:

```python
from aiomax2.types import (
    CallbackButton,
    InlineKeyboardAttachmentRequest,
    Keyboard,
)


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

await message.answer(
    "Выберите действие",
    attachments=[keyboard],
)
```

Здесь используется настоящее MAX-поле:

```python
payload = "confirm"
```

Builder API:

```python
callback_data = "confirm"
```

является только удобным alias.

## Ограничение callback payload

Текущая модель aiomax2 ограничивает `CallbackButton.payload` максимум
1024 символами в соответствии с актуальным контрактом MAX.

Например:

```python
CallbackButton(
    text="Открыть",
    payload="item:123",
)
```

При проектировании payload лучше хранить только данные, необходимые для
идентификации действия.

Например:

```text
confirm
cancel
item:123
page:2
order:9182
```

а не сериализовать в кнопку большие объекты состояния приложения.

## Структурированный payload

Для небольших приложений достаточно простых строк:

```python
F.payload == "confirm"
```

Для более сложной маршрутизации удобно использовать собственный формат:

```text
order:confirm:123
order:cancel:123
```

и фильтровать его через magic filter:

```python
@router.callback_query(F.payload.regexp(r"^order:confirm:(\d+)$").as_("match"))
async def confirm_order(
    callback: CallbackQuery,
    match: re.Match[str],
) -> None:
    order_id = int(match.group(1))

    await callback.answer(
        notification=f"Заказ {order_id} подтверждён",
    )
```

Для этого примера потребуется:

```python
import re
```

Подробнее о `regexp()` и `as_()`:
[Magic filter](magic-filter.md).

## Callback без исходного сообщения

aiomax2 поддерживает callback, у которого:

```python
callback.message is None
```

Например:

```python
@router.callback_query()
async def callback_handler(callback: CallbackQuery) -> None:
    if callback.message is None:
        await callback.answer(
            notification="Исходное сообщение недоступно",
        )
        return

    await callback.answer(
        text="Сообщение обновлено",
    )
```

При отсутствии сообщения пользователь для внутреннего context и target
определяется через:

```python
callback.user
```

## FSM и callback

Callback handlers работают с тем же FSM context, что и остальные handlers.

Например:

```python
from aiomax2.fsm import FSMContext


@router.callback_query(F.payload == "confirm")
async def confirm(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await state.update_data(confirmed=True)

    await callback.answer(
        notification="Подтверждено",
    )
```

Если исходное сообщение отсутствует, aiomax2 может определить идентификаторы
FSM по пользователю callback.

Подробнее:
[FSM](fsm.md).

## Регистрация без декоратора

Callback handler можно зарегистрировать через `.register()`:

```python
async def confirm(callback: CallbackQuery) -> None:
    await callback.answer(notification="Готово")


router.callback_query.register(
    confirm,
    F.payload == "confirm",
)
```

Это эквивалентно:

```python
@router.callback_query(F.payload == "confirm")
async def confirm(callback: CallbackQuery) -> None:
    await callback.answer(notification="Готово")
```

## Alias observer

В `Router`:

```python
router.callback_query
```

является alias для:

```python
router.message_callback
```

Оба работают с MAX update type:

```text
message_callback
```

Поэтому:

```python
@router.callback_query()
async def first(callback: CallbackQuery) -> None: ...
```

и:

```python
@router.message_callback()
async def second(callback: CallbackQuery) -> None: ...
```

регистрируются в одном observer.

Для прикладного кода обычно удобнее:

```python
router.callback_query
```

а `message_callback` полезно знать при сопоставлении кода с названиями
событий MAX API.

## Краткая справка

| Задача | Пример |
| --- | --- |
| Обработать callback | `@router.callback_query()` |
| Проверить payload | `F.payload == "confirm"` |
| Получить payload | `callback.payload` |
| Получить ID callback | `callback.callback_id` |
| Получить пользователя | `callback.user` |
| Получить исходное сообщение | `callback.message` |
| Показать notification | `callback.answer(notification="Готово")` |
| Изменить текст | `callback.answer(text="Готово")` |
| Изменить клавиатуру | `callback.answer(reply_markup=...)` |
| Получить диагностический результат | `bot.answer_callback_result(...)` |

Для создания inline-клавиатур и всех типов кнопок MAX используйте:
[Inline-клавиатуры](keyboards.md).

Для фильтрации callback payload:
[Magic filter](magic-filter.md).