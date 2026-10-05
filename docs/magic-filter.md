# Magic filter `F`

`F` строит выражение, которое безопасно проходит по атрибутам объекта и
возвращает `False`, если путь отсутствует.

```python
from aiomax2 import F

router.message(F.text == "hello")
router.message(F.text.startswith("hello"))
router.message(F.text.contains("max"))
router.callback_query(F.payload == "confirm")
router.message(F.sender.user_id == 123)
```

Путь должен соответствовать реальной модели event. Для `Message` доступны
удобные свойства `text`, `chat_id`, `user_id`, а также исходные
`sender`, `recipient` и `body`.

## Операции

- сравнения `==`, `!=`, `<`, `<=`, `>`, `>=`;
- `startswith`, `endswith`, `contains`, `in_`;
- `regexp`;
- transforms `lower`, `upper`, `len`;
- композиция `&`, `|`, `~`.

```python
@router.message((F.text.lower() == "привет") & (F.chat_id == 100))
async def greeting(message: Message) -> None: ...
```

`as_(name)` добавляет найденное значение в context. Для `regexp` передаётся
объект `re.Match`:

```python
@router.message(F.text.regexp(r"^order:(\d+)$").as_("match"))
async def order(message: Message, match: re.Match[str]) -> None:
    order_id = int(match.group(1))
```

