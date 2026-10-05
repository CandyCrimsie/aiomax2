# Command filter

`Command` разбирает текст MAX-сообщения и добавляет `CommandObject` в context.

```python
from aiomax2.filters import Command, CommandObject
from aiomax2.types import Message


@router.message(Command("start"))
async def start(message: Message, command: CommandObject) -> None:
    await message.answer(f"args={command.args!r}")
```

Для `/start` значение `command.args` равно `None`. Для `/start 123` оно равно
`"123"`. Объект также содержит `prefix` и исходное имя `command`.

Несколько команд можно объединить:

```python
@router.message(Command("help", "about"))
async def information(message: Message, command: CommandObject) -> None: ...
```

`CommandStart()` — краткая запись для `Command("start")`:

```python
from aiomax2.filters import CommandStart


@router.message(CommandStart())
async def start(message: Message) -> None: ...
```

Доступны `prefix` и `ignore_case`. Упоминания Telegram-бота вида
`/start@botname` специально не эмулируются: фильтр соответствует модели MAX.

