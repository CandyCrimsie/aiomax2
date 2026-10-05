# Фильтры

Фильтры выполняются до handler. Они могут вернуть:

- `False` — handler не подходит;
- `True` — handler подходит;
- словарь — handler подходит, а значения добавляются в context.

```python
from aiomax2.filters import Filter


class HasText(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.text is not None


@router.message(HasText())
async def text_message(message: Message) -> None: ...
```

Несколько фильтров одного handler применяются последовательно как логическое
`AND`:

```python
@router.message(Command("admin"), F.sender.user_id == ADMIN_ID)
async def admin(message: Message) -> None: ...
```

Observer-level фильтр применяется ко всем handlers observer:

```python
router.message.filter(F.text)
```

Готовые фильтры: [команды](commands.md), [magic filter `F`](magic-filter.md) и
FSM state filter, который автоматически создаётся при передаче `State`.

