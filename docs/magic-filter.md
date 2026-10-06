# Magic filter `F`

`F` — встроенный декларативный фильтр aiomax2.

Он использует тот же механизм фильтрации, что `Filter`, `Command` и FSM state,
но позволяет описывать простые условия прямо при регистрации handler без
создания отдельного класса.

Например:

```python
from aiomax2 import F


@router.message(F.text == "hello")
async def hello(message: Message) -> None:
    await message.answer("Привет")
```

Handler будет вызван только в том случае, если `message.text == "hello"`.

Для аналогичной проверки через собственный фильтр пришлось бы написать:

```python
from aiomax2.filters import Filter
from aiomax2.types import Message


class HelloFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.text == "hello"
```

Для большинства простых проверок `F` позволяет избежать таких небольших
одноразовых классов.

Подробнее об общей системе фильтрации:
[Фильтры](filters.md).

## Как работает `F`

`F` не содержит заранее определённого списка полей.

Когда записывается выражение:

```python
F.sender.user_id == 123
```

aiomax2 строит путь:

```text
event
└── sender
    └── user_id
```

Само значение будет получено только тогда, когда фильтр будет применён
к реальному событию.

Поэтому выражение:

```python
F.sender.user_id == 123
```

можно воспринимать примерно как:

```python
event.sender.user_id == 123
```

но с безопасной обработкой отсутствующих значений.

## Простая проверка значения

Если не использовать оператор сравнения, значение проверяется на truthiness:

```python
@router.message(F.text)
async def text_message(message: Message) -> None: ...
```

Такой handler подходит только для сообщений, у которых `text` содержит
непустое значение.

Например:

```text
"hello"  -> True
""       -> False
None     -> False
```

Это удобно для проверки наличия значения:

```python
router.message(F.text)
```

## Доступ к вложенным полям

Можно обращаться к вложенным атрибутам события:

```python
F.sender.user_id
F.recipient.chat_id
F.body.mid
```

Например:

```python
ADMIN_ID = 123456


@router.message(F.sender.user_id == ADMIN_ID)
async def admin(message: Message) -> None:
    await message.answer("Привет, администратор")
```

Для `Message` также доступны удобные свойства верхнего уровня:

```python
F.text
F.chat_id
F.user_id
F.message_id
```

Поэтому вместо:

```python
F.body.text == "hello"
```

обычно удобнее писать:

```python
F.text == "hello"
```

## Отсутствующие поля

Magic filter безопасно обрабатывает отсутствующие поля.

Например:

```python
F.sender.user_id == 123
```

не приведёт к исключению, если `sender` отсутствует.

В таком случае выражение просто не пройдёт фильтрацию.

То же относится к несовместимым операциям. Например, если строковая операция
применяется к значению неподходящего типа, handler не будет выбран вместо
падения dispatcher.

## Сравнения

Поддерживаются обычные операторы сравнения:

```python
F.user_id == 123
F.user_id != 123

F.timestamp > 1000
F.timestamp >= 1000

F.timestamp < 2000
F.timestamp <= 2000
```

Например:

```python
@router.message(F.chat_id == 100)
async def selected_chat(message: Message) -> None: ...
```

## Работа со строками

### `startswith`

Проверяет начало строки:

```python
F.text.startswith("hello")
```

Пример:

```python
@router.message(F.text.startswith("order:"))
async def order(message: Message) -> None: ...
```

### `endswith`

Проверяет конец строки:

```python
F.text.endswith(".jpg")
```

Пример:

```python
@router.message(F.text.endswith("!"))
async def exclamation(message: Message) -> None: ...
```

### `contains`

Проверяет наличие значения внутри объекта:

```python
F.text.contains("max")
```

Для строки это соответствует:

```python
"max" in text
```

Например:

```python
@router.message(F.text.contains("aiomax2"))
async def mention(message: Message) -> None: ...
```

`contains()` может использоваться и с другими объектами, поддерживающими
оператор `in`.

## Проверка в наборе значений

Метод `in_()` проверяет, содержится ли значение поля в переданном контейнере:

```python
F.user_id.in_({1, 2, 3})
```

Например:

```python
ADMIN_IDS = {100, 200, 300}


@router.message(F.user_id.in_(ADMIN_IDS))
async def admin(message: Message) -> None: ...
```

Это соответствует проверке:

```python
message.user_id in ADMIN_IDS
```

## Преобразование регистра

### `lower`

Преобразует строку в нижний регистр перед дальнейшей проверкой:

```python
F.text.lower() == "hello"
```

Теперь подойдут, например:

```text
hello
Hello
HELLO
```

Пример:

```python
@router.message(F.text.lower() == "привет")
async def greeting(message: Message) -> None: ...
```

### `upper`

Аналогично преобразует строку в верхний регистр:

```python
F.text.upper() == "HELLO"
```

Преобразования выполняются до проверки условия.

Их можно комбинировать с другими возможностями `F`.

## Длина значения

Метод `len()` применяет встроенный Python `len()` к найденному значению:

```python
F.text.len() > 10
```

Например:

```python
@router.message(F.text.len() >= 100)
async def long_message(message: Message) -> None: ...
```

Если значение не поддерживает `len()`, фильтр просто не пройдёт.

## Регулярные выражения

Для поиска по регулярному выражению используется `regexp()`:

```python
F.text.regexp(r"^order:\d+$")
```

Внутри используется поиск через `re.search()`.

Например:

```python
@router.message(F.text.regexp(r"^order:(\d+)$"))
async def order(message: Message) -> None: ...
```

Подойдёт сообщение:

```text
order:123
```

и не подойдёт:

```text
hello
```

В `regexp()` можно передать как строку:

```python
F.text.regexp(r"\d+")
```

так и заранее скомпилированный pattern:

```python
import re


ORDER_PATTERN = re.compile(r"^order:(\d+)$")

router.message(F.text.regexp(ORDER_PATTERN))
```

## Передача найденного значения через `as_()`

Magic filter может добавить найденное значение в context.

Для этого используется `as_()`:

```python
F.user_id.as_("sender_id")
```

После успешной проверки значение станет доступно handler:

```python
@router.message(F.user_id.as_("sender_id"))
async def handler(
    message: Message,
    sender_id: int,
) -> None:
    print(sender_id)
```

Это позволяет передавать значения в handler без отдельного класса `Filter`.

## `regexp()` вместе с `as_()`

При использовании `regexp()` в context передаётся объект `re.Match`.

Например:

```python
import re

from aiomax2 import F
from aiomax2.types import Message


@router.message(F.text.regexp(r"^order:(\d+)$").as_("match"))
async def order(
    message: Message,
    match: re.Match[str],
) -> None:
    order_id = int(match.group(1))

    await message.answer(f"Номер заказа: {order_id}")
```

Для сообщения:

```text
order:123
```

значение:

```python
match.group(1)
```

будет равно:

```text
123
```

## Несколько условий через `&`

Оператор `&` объединяет два выражения как логическое `AND`.

Например:

```python
@router.message((F.text.startswith("hello")) & (F.chat_id == 100))
async def hello(message: Message) -> None: ...
```

Оба условия должны быть истинными:

```text
text начинается с "hello"
AND
chat_id == 100
```

Если первое условие не проходит, второе уже не требуется для успешного
результата.

## Несколько вариантов через `|`

Оператор `|` работает как логическое `OR`.

Например:

```python
@router.message((F.text == "yes") | (F.text == "да"))
async def confirm(message: Message) -> None: ...
```

Handler будет вызван, если выполняется хотя бы одно условие.

## Скобки при использовании `&` и `|`

При композиции magic filters рекомендуется всегда заключать отдельные
выражения в скобки:

```python
((F.text == "hello") & (F.user_id == 123))
```

и:

```python
((F.text == "yes") | (F.text == "да"))
```

Это делает порядок вычисления очевидным и предотвращает проблемы с
приоритетом операторов Python.

Не следует писать:

```python
F.text == "hello" & F.user_id == 123
```

## Не используйте Python `and` и `or`

Magic filter нельзя объединять обычными Python-операторами `and` и `or`:

```python
# Неправильно
F.text == "hello" and F.user_id == 123
```

Magic filter специально запрещает преобразование выражения в обычный
Python `bool`.

Используйте:

```python
# Правильно
(F.text == "hello") & (F.user_id == 123)
```

или:

```python
(F.text == "hello") | (F.text == "hi")
```

## `as_()` и составные выражения

На текущем этапе значения из `as_()` лучше не захватывать внутри выражения,
объединённого через `&` или `|`.

Вместо:

```python
F.text.regexp(r"^order:(\d+)$").as_("match") & (F.chat_id == 100)
```

передайте условия как отдельные фильтры:

```python
@router.message(
    F.text.regexp(r"^order:(\d+)$").as_("match"),
    F.chat_id == 100,
)
async def order(
    message: Message,
    match: re.Match[str],
) -> None: ...
```

Это также хорошо показывает разницу между двумя механизмами:

```text
filter 1 AND filter 2
```

на уровне handler и:

```text
expression A & expression B
```

внутри одного magic filter.

## Несколько magic filters у одного handler

Часто отдельные условия удобнее передавать независимо:

```python
@router.message(
    F.text,
    F.sender.user_id == ADMIN_ID,
    F.text.startswith("/"),
)
async def handler(message: Message) -> None: ...
```

Как и любые другие filters, они выполняются последовательно и работают как
логическое `AND`.

Это особенно удобно, если один из фильтров использует `as_()`.

## Callback query

`F` работает не только с сообщениями.

Для callback query можно фильтровать `payload`:

```python
@router.callback_query(F.payload == "confirm")
async def confirm(callback: CallbackQuery) -> None:
    await callback.answer()
```

Или использовать другие поля callback:

```python
F.callback_id
F.user.user_id
F.payload
```

Путь всегда строится относительно объекта события, который получает
конкретный observer.

## Примеры

Точное совпадение:

```python
@router.message(F.text == "hello")
async def exact(message: Message) -> None: ...
```

Начало строки:

```python
@router.message(F.text.startswith("/"))
async def command_like(message: Message) -> None: ...
```

Регистронезависимая проверка:

```python
@router.message(F.text.lower() == "hello")
async def hello(message: Message) -> None: ...
```

Проверка пользователя:

```python
@router.message(F.user_id == ADMIN_ID)
async def admin(message: Message) -> None: ...
```

Несколько разрешённых пользователей:

```python
@router.message(F.user_id.in_(ADMIN_IDS))
async def admins(message: Message) -> None: ...
```

Проверка текста и пользователя:

```python
@router.message((F.text == "admin") & (F.user_id == ADMIN_ID))
async def admin_command(message: Message) -> None: ...
```

Регулярное выражение с извлечением значения:

```python
@router.message(F.text.regexp(r"^order:(\d+)$").as_("match"))
async def order(
    message: Message,
    match: re.Match[str],
) -> None:
    order_id = int(match.group(1))
```

Callback:

```python
@router.callback_query(F.payload == "confirm")
async def confirm(callback: CallbackQuery) -> None: ...
```

## Поддерживаемые операции

| Возможность | Пример |
| --- | --- |
| Проверка значения | `F.text` |
| Равенство | `F.text == "hello"` |
| Неравенство | `F.text != "hello"` |
| Больше | `F.timestamp > 1000` |
| Больше или равно | `F.timestamp >= 1000` |
| Меньше | `F.timestamp < 2000` |
| Меньше или равно | `F.timestamp <= 2000` |
| Начало строки | `F.text.startswith("hello")` |
| Конец строки | `F.text.endswith("!")` |
| Содержит значение | `F.text.contains("max")` |
| Значение входит в набор | `F.user_id.in_({1, 2, 3})` |
| Нижний регистр | `F.text.lower()` |
| Верхний регистр | `F.text.upper()` |
| Длина | `F.text.len()` |
| Регулярное выражение | `F.text.regexp(r"\d+")` |
| Логическое AND | `(F.text) & (F.user_id == 1)` |
| Логическое OR | `(F.text == "yes") \| (F.text == "да")` |
| Передача в context | `F.user_id.as_("sender_id")` |

## Когда использовать `F`

Magic filter хорошо подходит для компактных декларативных проверок:

```python
F.text == "hello"
F.user_id == ADMIN_ID
F.payload == "confirm"
F.text.startswith("order:")
```

Если фильтрация содержит сложную бизнес-логику, обращения к внешним сервисам,
несколько вычислений или должна переиспользоваться как самостоятельный
компонент, лучше создать собственный класс `Filter`.

Подробнее:
[Фильтры](filters.md).