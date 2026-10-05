from __future__ import annotations

from typing import Any

from aiomax2.fsm.state import State

from .base import Filter


class StateFilter(Filter):
    def __init__(self, *states: State | str | None) -> None:
        self.states = frozenset(
            state.state if isinstance(state, State) else state for state in states
        )

    async def __call__(
        self, event: Any, raw_state: str | None = None, **_: Any
    ) -> bool:
        return raw_state in self.states
