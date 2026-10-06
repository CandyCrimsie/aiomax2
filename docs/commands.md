# Command filter

`Command` — встроенный фильтр aiomax2 для обработки текстовых команд.

Он проверяет текст входящего `Message`, разбирает имя команды и её аргументы,
а затем добавляет объект `CommandObject` в context handler.

Например:

```python
from aiomax2.filters import Command
from aiomax2.types import Message


@router.message(Command("start"))
async def start(message: Message) -> None:
    await message.answer("Бот запущен")
```

Этот handler будет вызван для сообщения:

```text
/start
```

Подробнее об общей системе фильтрации:
[Фильтры](filters.md).

## Как разбирается команда

По умолчанию команды начинаются с `/`.

Например, для сообщения:

```text
/start hello world
```

фильтр:

```python
Command("start")
```

разбирает строку на две части:

```text
command = "start"
args    = "hello world"
```

Имя команды заканчивается на первом пробельном символе.

Поэтому:

```text
/start one two three
```

даёт:

```python
command.command == "start"
command.args == "one two three"
```

Аргументы не разбиваются фильтром на отдельные значения. Их дальнейший разбор
остаётся приложению.

## `CommandObject`

Если команда подходит, `Command` добавляет в context объект `CommandObject`.

```python
from aiomax2.filters import Command, CommandObject
from aiomax2.types import Message


@router.message(Command("start"))
async def start(
    message: Message,
    command: CommandObject,
) -> None:
    print(command.prefix)
    print(command.command)
    print(command.args)
```

`CommandObject` содержит три поля:

```python
@dataclass
class CommandObject:
    prefix: str
    command: str
    args: str | None
```

Для сообщения:

```text
/start hello
```

значения будут следующими:

```python
command.prefix == "/"
command.command == "start"
command.args == "hello"
```

## Команда без аргументов

Если после команды ничего нет:

```text
/start
```

то:

```python
command.args is None
```

Например:

```python
@router.message(Command("start"))
async def start(
    message: Message,
    command: CommandObject,
) -> None:
    if command.args is None:
        await message.answer("Команда вызвана без аргументов")
        return

    await message.answer(f"Аргументы: {command.args}")
```

Важно отличать `None` от пустой строки: при отсутствии аргументов используется
именно `None`.

## Команда с аргументами

Аргументы можно получить через `command.args`:

```python
@router.message(Command("echo"))
async def echo(
    message: Message,
    command: CommandObject,
) -> None:
    if command.args is None:
        await message.answer("Укажите текст")
        return

    await message.answer(command.args)
```

Например:

```text
/echo hello MAX
```

даст:

```python
command.command == "echo"
command.args == "hello MAX"
```

## Несколько команд

Один фильтр `Command` может обрабатывать сразу несколько имён:

```python
@router.message(Command("help", "about"))
async def information(
    message: Message,
    command: CommandObject,
) -> None:
    await message.answer(f"Команда: {command.command}")
```

Handler подойдёт как для:

```text
/help
```

так и для:

```text
/about
```

Это удобно, когда несколько команд должны запускать один и тот же handler.

## `CommandStart`

Для наиболее распространённой команды `/start` существует сокращение
`CommandStart`.

```python
from aiomax2.filters import CommandStart
from aiomax2.types import Message


@router.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer("Привет")
```

Это эквивалентно:

```python
@router.message(Command("start"))
async def start(message: Message) -> None:
    await message.answer("Привет")
```

`CommandStart` также поддерживает `prefix` и `ignore_case`.

## Префикс команды

По умолчанию используется:

```text
/
```

Но его можно изменить через `prefix`.

Например:

```python
@router.message(Command("help", prefix="!"))
async def help_command(message: Message) -> None:
    await message.answer("Помощь")
```

Теперь handler ожидает:

```text
!help
```

а не:

```text
/help
```

Другой пример:

```python
@router.message(Command("ping", prefix="."))
async def ping(message: Message) -> None:
    await message.answer("pong")
```

Для сообщения:

```text
.ping
```

## Префикс можно указать и в имени команды

При создании фильтра aiomax2 удаляет переданный `prefix` из начала имени
команды.

Поэтому при стандартном префиксе `/`:

```python
Command("start")
```

и:

```python
Command("/start")
```

эквивалентны.

То же относится к собственному префиксу:

```python
Command("help", prefix="!")
```

и:

```python
Command("!help", prefix="!")
```

будут проверять команду:

```text
!help
```

Для единообразия в приложении обычно проще передавать имя команды без
префикса:

```python
Command("start")
Command("help")
Command("admin")
```

## Регистрозависимость

По умолчанию имя команды регистрозависимо:

```python
Command("start")
```

подойдёт для:

```text
/start
```

но не для:

```text
/START
/Start
```

Чтобы отключить зависимость от регистра, используется `ignore_case=True`:

```python
@router.message(Command("start", ignore_case=True))
async def start(message: Message) -> None:
    await message.answer("Команда распознана")
```

Теперь будут приняты, например:

```text
/start
/START
/Start
/sTaRt
```

Для сравнения имён используется Unicode-aware нормализация через
`casefold()`.

При этом `CommandObject.command` содержит исходное имя команды из сообщения.

Например, если пользователь отправил:

```text
/START
```

то при:

```python
Command("start", ignore_case=True)
```

фильтр пройдёт, а:

```python
command.command == "START"
```

## `CommandStart` с параметрами

Параметры доступны и для `CommandStart`:

```python
@router.message(
    CommandStart(
        prefix="!",
        ignore_case=True,
    )
)
async def start(message: Message) -> None: ...
```

Такой фильтр сможет обработать, например:

```text
!start
!START
!Start
```

## Совместное использование с другими фильтрами

`Command` можно комбинировать с любыми другими filters aiomax2.

Например, разрешить `/admin` только определённому пользователю:

```python
from aiomax2 import F
from aiomax2.filters import Command
from aiomax2.types import Message


ADMIN_ID = 123456


@router.message(
    Command("admin"),
    F.user_id == ADMIN_ID,
)
async def admin(message: Message) -> None:
    await message.answer("Панель администратора")
```

Оба фильтра должны пройти:

```text
Command("admin")
AND
F.user_id == ADMIN_ID
```

Можно комбинировать `Command` и с собственными классами `Filter`.

Подробнее:
[Фильтры](filters.md).

## `CommandObject` вместе с другими context-значениями

Поскольку результат `Command` добавляется в общий context, `CommandObject`
может использоваться вместе с другими зависимостями handler:

```python
from aiomax2 import Bot
from aiomax2.filters import Command, CommandObject
from aiomax2.types import Message


@router.message(Command("send"))
async def send(
    message: Message,
    command: CommandObject,
    bot: Bot,
) -> None:
    if command.args is None:
        await message.answer("Укажите текст")
        return

    await bot.send_message(
        chat_id=message.chat_id,
        text=command.args,
    )
```

`Command` отвечает только за распознавание команды и создание
`CommandObject`. Остальные значения разрешаются обычным механизмом context
aiomax2.

## Что считается командой

Команда должна:

- начинаться с настроенного `prefix`;
- содержать непустое имя;
- совпадать с одним из имён, переданных в `Command`;
- при наличии аргументов отделяться от них пробельным символом.

Например:

```python
Command("start")
```

пройдёт для:

```text
/start
/start hello
/start one two three
```

но не пройдёт для:

```text
start
/help
/start123
```

В последнем случае имя команды будет:

```text
start123
```

а не `start`.

`Command` следует модели сообщений MAX и не добавляет дополнительный синтаксис
команд, отсутствующий в MAX.

## Не текстовые сообщения

`Command` работает только с `Message`, содержащими непустой текст.

Если событие не является `Message` или `message.text` отсутствует, фильтр
просто возвращает `False`.

Поэтому отдельная проверка:

```python
F.text
```

перед `Command` обычно не требуется:

```python
@router.message(Command("start"))
async def start(message: Message) -> None: ...
```

достаточно.

## Валидация конфигурации

Необходимо передать хотя бы одно имя команды:

```python
Command()
```

приведёт к:

```text
ValueError: at least one command is required
```

Имя команды также не может быть пустым:

```python
Command("")
```

и не может содержать пробельные символы:

```python
Command("hello world")
```

Оба варианта являются ошибками конфигурации.

Правильно:

```python
Command("hello")
Command("hello", "world")
```

Аргументы пользователя не нужно указывать в имени фильтра.

Неправильно:

```python
Command("start 123")
```

Правильно:

```python
Command("start")
```

а значение `123` затем будет доступно через:

```python
command.args
```

## Регистрация без декоратора

`Command` можно использовать и с `.register()`:

```python
async def start(
    message: Message,
    command: CommandObject,
) -> None:
    await message.answer("Start")


router.message.register(
    start,
    Command("start"),
)
```

Это эквивалентно:

```python
@router.message(Command("start"))
async def start(
    message: Message,
    command: CommandObject,
) -> None:
    await message.answer("Start")
```

## Краткая справка

| Возможность | Пример |
| --- | --- |
| Одна команда | `Command("start")` |
| Несколько команд | `Command("help", "about")` |
| `/start` | `CommandStart()` |
| Собственный префикс | `Command("help", prefix="!")` |
| Без учёта регистра | `Command("start", ignore_case=True)` |
| Получить имя | `command.command` |
| Получить аргументы | `command.args` |
| Получить префикс | `command.prefix` |

Для простых проверок полей события вместе с командами можно использовать
[magic filter `F`](magic-filter.md).