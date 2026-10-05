from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Filter(ABC):
    @abstractmethod
    async def __call__(self, event: Any, **data: Any) -> bool | dict[str, Any]:
        raise NotImplementedError
