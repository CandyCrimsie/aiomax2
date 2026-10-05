from __future__ import annotations

from typing import Any


class State:
    def __init__(self, state: str | None = None) -> None:
        self._state = state
        self._group: str | None = None
        self._name: str | None = None

    def __set_name__(self, owner: type[StatesGroup], name: str) -> None:
        self._group = owner.__name__
        self._name = name

    @property
    def state(self) -> str:
        if self._state is not None:
            return self._state
        if self._group is None or self._name is None:
            raise RuntimeError("State must be declared on a StatesGroup")
        return f"{self._group}:{self._name}"

    def __str__(self) -> str:
        return self.state

    def __repr__(self) -> str:
        return f"<State {self.state!r}>"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, State):
            return self.state == other.state
        if isinstance(other, str):
            return self.state == other
        return False

    def __hash__(self) -> int:
        return hash(self.state)


class StatesGroupMeta(type):
    @property
    def states(cls) -> tuple[State, ...]:
        return tuple(value for value in vars(cls).values() if isinstance(value, State))


class StatesGroup(metaclass=StatesGroupMeta):
    def __new__(cls, *_: object, **__: object) -> StatesGroup:
        raise TypeError(
            "StatesGroup classes are declarative and cannot be instantiated"
        )
