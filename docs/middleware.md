# Middleware

Middleware получает следующий handler, event и изменяемый context. Наследование
от `BaseMiddleware` делает контракт явным.

```python
import logging
from typing import Any

from aiomax2 import BaseMiddleware
from aiomax2.dispatcher import NextMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: NextMiddleware,
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        logger.info("event=%s", type(event).__name__)
        data["request_id"] = "example-request-id"
        return await handler(event, data)
```

Регистрация:

```python
router.message.outer_middleware(LoggingMiddleware())
router.message.middleware(LoggingMiddleware())
```

Порядок обработки event observer:

```text
Update
  -> outer middleware
  -> root filters и handler filters
  -> inner middleware
  -> handler
```

Outer middleware удобно использовать для логирования, tracing, transaction и
загрузки зависимостей до фильтров. Inner middleware запускается только после
успешных фильтров и подходит для логики вокруг конкретного handler.

Значения, добавленные в `data`, можно запросить по имени аргумента:

```python
@router.message()
async def handler(message: Message, request_id: str) -> None: ...
```

