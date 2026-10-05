from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class StorageKey:
    bot_id: int | str
    chat_id: int | None
    user_id: int | None


class BaseStorage(ABC):
    @abstractmethod
    async def get_state(self, key: StorageKey) -> str | None:
        raise NotImplementedError

    @abstractmethod
    async def set_state(self, key: StorageKey, state: str | None) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def set_data(self, key: StorageKey, data: dict[str, Any]) -> None:
        raise NotImplementedError

    async def update_data(
        self, key: StorageKey, data: dict[str, Any]
    ) -> dict[str, Any]:
        current = await self.get_data(key)
        current.update(data)
        await self.set_data(key, current)
        return current

    async def close(self) -> None:
        return None
