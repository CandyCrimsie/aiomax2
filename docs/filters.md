# Фильтры

Фильтры определяют, должен ли конкретный handler обрабатывать событие.

Они выполняются **до handler** и позволяют отсеивать события по тексту,
отправителю, состоянию FSM, команде и любым другим условиям.

Например:

```python
from aiomax2 import F


@router.message(F.text == "hello")
async def hello(message: Message) -> None:
    await message.answer("Привет")
```

Этот handler будет вызван только для сообщений, у которых `text == "hello"`.

## Как работают фильтры

Каждый фильтр вызывается перед handler и может вернуть:

- `False` или другое ложное значение — handler не подходит;
- `True` — handler подходит;
- `dict[str, Any]` — handler подходит, а значения из словаря добавляются
  в context и могут быть переданы следующим фильтрам, middleware или handler.

Фильтр может быть как синхронным, так и асинхронным.

Например, собственный асинхронный фильтр:

```python
from aiomax2.filters import Filter
from aiomax2.types import Message


class HasText(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.text is not None


@router.message(HasText())
async def text_message(message: Message) -> None:
    await message.answer("Сообщение содержит текст")
```

Для простых условий обычно не требуется создавать отдельный класс.
Вместо этого удобнее использовать [magic filter `F`](magic-filter.md):

```python
from aiomax2 import F


@router.message(F.text)
async def text_message(message: Message) -> None:
    await message.answer("Сообщение содержит текст")
```

## Несколько фильтров

Одному handler можно передать несколько фильтров:

```python
from aiomax2 import F
from aiomax2.filters import Command


ADMIN_ID = 123456


@router.message(
    Command("admin"),
    F.sender.user_id == ADMIN_ID,
)
async def admin(message: Message) -> None:
    await message.answer("Панель администратора")
```

Фильтры выполняются последовательно в порядке, в котором были переданы.

Между ними действует логическое `AND`:

```text
Command("admin")
        AND
F.sender.user_id == ADMIN_ID
```

Если какой-либо фильтр не проходит, оставшиеся фильтры этого handler не
выполняются и dispatcher переходит к следующему подходящему handler.

## Передача данных из фильтра в handler

Фильтр может вернуть словарь.

Его значения будут добавлены в context и затем доступны handler по имени
аргумента.

```python
from aiomax2.filters import Filter
from aiomax2.types import Message


class ExtractName(Filter):
    async def __call__(self, message: Message) -> bool | dict[str, str]:
        if message.text is None:
            return False

        prefix = "hello "

        if not message.text.startswith(prefix):
            return False

        name = message.text[len(prefix) :].strip()

        if not name:
            return False

        return {"name": name}


@router.message(ExtractName())
async def greeting(message: Message, name: str) -> None:
    await message.answer(f"Привет, {name}")
```

Если пользователь отправит:

```text
hello Alex
```

фильтр вернёт:

```python
{"name": "Alex"}
```

и `name` будет автоматически передан в handler.

Таким способом фильтры могут не только проверять событие, но и извлекать из
него данные для дальнейшей обработки.

## Context между несколькими фильтрами

Данные, возвращённые одним фильтром, становятся доступны следующим фильтрам
того же handler.

Например:

```python
from aiomax2.filters import Filter
from aiomax2.types import Message


class ExtractNumber(Filter):
    async def __call__(self, message: Message) -> bool | dict[str, int]:
        if message.text is None:
            return False

        if not message.text.isdigit():
            return False

        return {"number": int(message.text)}


class PositiveNumber(Filter):
    async def __call__(self, number: int) -> bool:
        return number > 0


@router.message(
    ExtractNumber(),
    PositiveNumber(),
)
async def number_handler(message: Message, number: int) -> None:
    await message.answer(f"Число: {number}")
```

Сначала `ExtractNumber` добавит `number` в context, после чего
`PositiveNumber` сможет получить его как аргумент.

## Observer-level фильтры

Фильтр можно применить не к одному handler, а сразу ко всему observer.

Например:

```python
router.message.filter(F.text)
```

После этого фильтр `F.text` будет применяться ко всем handlers,
зарегистрированным через `router.message`.

```python
router.message.filter(F.text)


@router.message(F.text == "hello")
async def hello(message: Message) -> None: ...


@router.message(F.text == "bye")
async def bye(message: Message) -> None: ...
```

Сначала будет выполнен observer-level фильтр `F.text`, и только после него
dispatcher начнёт проверять фильтры конкретных handlers.

Это удобно, когда у группы handlers есть общее условие.

## Magic filter `F`

`F` — встроенный декларативный фильтр aiomax2.

Он использует тот же механизм фильтрации, что и обычные классы `Filter`,
но позволяет описывать большинство простых условий без создания отдельного
класса.

Например:

```python
@router.message(F.text == "hello")
async def hello(message: Message) -> None: ...
```

вместо отдельного класса:

```python
class HelloFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.text == "hello"
```

`F` поддерживает сравнения, работу со строками, регулярные выражения,
преобразования, логические операции и передачу найденных значений в context.

Подробнее: [Magic filter `F`](magic-filter.md).

## Command

Для обработки команд используется встроенный фильтр `Command`.

```python
from aiomax2.filters import Command


@router.message(Command("start"))
async def start(message: Message) -> None:
    await message.answer("Бот запущен")
```

`Command` умеет разбирать аргументы команды и добавляет `CommandObject`
в context.

Например:

```python
from aiomax2.filters import Command, CommandObject


@router.message(Command("start"))
async def start(
    message: Message,
    command: CommandObject,
) -> None:
    await message.answer(f"args={command.args!r}")
```

Подробнее: [Command filter](commands.md).

## FSM state

Объект `State` можно передавать в observer так же, как обычный фильтр.

aiomax2 автоматически преобразует его во внутренний `StateFilter`.

```python
from aiomax2.fsm import State, StatesGroup


class Form(StatesGroup):
    name = State()


@router.message(Form.name)
async def process_name(message: Message) -> None: ...
```

Такой handler будет вызван только тогда, когда текущий FSM state соответствует
`Form.name`.

Подробнее: [FSM](fsm.md).

## Когда использовать `F`, а когда собственный `Filter`

Для простых проверок предпочтительнее использовать `F`:

```python
F.text == "hello"
F.text.startswith("order:")
F.sender.user_id == ADMIN_ID
F.payload == "confirm"
```

Собственный `Filter` полезнее, когда условие:

- содержит несколько шагов;
- использует внешние зависимости;
- выполняет более сложную бизнес-логику;
- должно переиспользоваться в разных routers;
- должно извлекать или подготавливать данные для handler.

Например:

```python
class IsAdmin(Filter):
    async def __call__(
        self,
        message: Message,
        admin_service: AdminService,
    ) -> bool:
        if message.user_id is None:
            return False

        return await admin_service.is_admin(message.user_id)
```

Таким образом, `F` лучше подходит для компактных декларативных условий,
а `Filter` — для отдельной переиспользуемой логики.

## Порядок обработки

Для handler с несколькими фильтрами обработка выглядит примерно так:

```text
event
  │
  ▼
observer-level filters
  │
  ▼
filter 1
  │
  ▼
filter 2
  │
  ▼
filter 3
  │
  ▼
handler
```

Если какой-либо фильтр возвращает ложное значение, текущий handler
пропускается.

Если фильтр возвращает словарь, его значения добавляются в context перед
выполнением следующего фильтра.

## Встроенные фильтры

В aiomax2 доступны:

| Фильтр | Назначение |
| --- | --- |
| [`F`](magic-filter.md) | декларативные проверки полей события |
| [`Command`](commands.md) | обработка команд |
| `CommandStart` | сокращение для `Command("start")` |
| `StateFilter` | проверка текущего состояния FSM |
| `Filter` | базовый класс для собственных фильтров |

В большинстве приложений основными будут `F`, `Command` и FSM states.
Собственные классы `Filter` стоит создавать для более сложной или
переиспользуемой логики.