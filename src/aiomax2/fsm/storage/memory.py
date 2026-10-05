from __future__ import annotations

import asyncio
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from .base import BaseStorage, StorageKey


@dataclass(slots=True)
class MemoryStorageRecord:
    state: str | None = None
    data: dict[str, Any] = field(default_factory=dict)


class MemoryStorage(BaseStorage):
    """Process-local storage intended for tests and single-process bots."""

    def __init__(self) -> None:
        self._records: dict[StorageKey, MemoryStorageRecord] = {}
        self._lock = asyncio.Lock()

    async def get_state(self, key: StorageKey) -> str | None:
        async with self._lock:
            record = self._records.get(key)
            return record.state if record is not None else None

    async def set_state(self, key: StorageKey, state: str | None) -> None:
        async with self._lock:
            record = self._records.setdefault(key, MemoryStorageRecord())
            record.state = state
            self._discard_empty(key, record)

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        async with self._lock:
            record = self._records.get(key)
            return deepcopy(record.data) if record is not None else {}

    async def set_data(self, key: StorageKey, data: dict[str, Any]) -> None:
        async with self._lock:
            record = self._records.setdefault(key, MemoryStorageRecord())
            record.data = deepcopy(data)
            self._discard_empty(key, record)

    async def update_data(
        self, key: StorageKey, data: dict[str, Any]
    ) -> dict[str, Any]:
        async with self._lock:
            record = self._records.setdefault(key, MemoryStorageRecord())
            record.data.update(deepcopy(data))
            return deepcopy(record.data)

    async def clear(self) -> None:
        async with self._lock:
            self._records.clear()

    def _discard_empty(self, key: StorageKey, record: MemoryStorageRecord) -> None:
        if record.state is None and not record.data:
            self._records.pop(key, None)
