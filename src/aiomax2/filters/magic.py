from __future__ import annotations

import operator
import re
from collections.abc import Callable, Container
from dataclasses import dataclass, replace
from typing import Any

_MISSING = object()
Predicate = Callable[[Any], Any]
Transform = Callable[[Any], Any]


@dataclass(frozen=True, slots=True, eq=False)
class MagicFilter:
    _path: tuple[str, ...] = ()
    _transforms: tuple[Transform, ...] = ()
    _predicate: Predicate | None = None
    _alias: str | None = None
    _left: MagicFilter | None = None
    _right: MagicFilter | None = None
    _boolean_operator: str | None = None

    def __getattr__(self, name: str) -> MagicFilter:
        if name.startswith("_"):
            raise AttributeError(name)
        if self._predicate is not None or self._boolean_operator is not None:
            raise AttributeError("cannot extend a completed magic-filter expression")
        return replace(self, _path=(*self._path, name))

    def _compare(self, func: Predicate) -> MagicFilter:
        return replace(self, _predicate=func)

    def __eq__(self, other: object) -> MagicFilter:  # type: ignore[override]
        return self._compare(lambda value: operator.eq(value, other))

    def __ne__(self, other: object) -> MagicFilter:  # type: ignore[override]
        return self._compare(lambda value: operator.ne(value, other))

    def __lt__(self, other: Any) -> MagicFilter:
        return self._compare(lambda value: operator.lt(value, other))

    def __le__(self, other: Any) -> MagicFilter:
        return self._compare(lambda value: operator.le(value, other))

    def __gt__(self, other: Any) -> MagicFilter:
        return self._compare(lambda value: operator.gt(value, other))

    def __ge__(self, other: Any) -> MagicFilter:
        return self._compare(lambda value: operator.ge(value, other))

    def __and__(self, other: MagicFilter) -> MagicFilter:
        return MagicFilter(_left=self, _right=other, _boolean_operator="and")

    def __or__(self, other: MagicFilter) -> MagicFilter:
        return MagicFilter(_left=self, _right=other, _boolean_operator="or")

    def __invert__(self) -> MagicFilter:
        return self._compare(lambda value: not bool(value))

    def __bool__(self) -> bool:
        raise TypeError("MagicFilter expressions cannot be used as Python booleans")

    def startswith(self, prefix: str) -> MagicFilter:
        return self._compare(lambda value: value.startswith(prefix))

    def endswith(self, suffix: str) -> MagicFilter:
        return self._compare(lambda value: value.endswith(suffix))

    def contains(self, item: Any) -> MagicFilter:
        return self._compare(lambda value: item in value)

    def in_(self, container: Container[Any]) -> MagicFilter:
        return self._compare(lambda value: value in container)

    def regexp(self, pattern: str | re.Pattern[str]) -> MagicFilter:
        compiled = re.compile(pattern)
        return self._compare(lambda value: compiled.search(value))

    def lower(self) -> MagicFilter:
        return replace(self, _transforms=(*self._transforms, str.lower))

    def upper(self) -> MagicFilter:
        return replace(self, _transforms=(*self._transforms, str.upper))

    def len(self) -> MagicFilter:
        return replace(self, _transforms=(*self._transforms, len))

    def as_(self, name: str) -> MagicFilter:
        if not name:
            raise ValueError("alias must not be empty")
        return replace(self, _alias=name)

    def _value(self, obj: Any) -> Any:
        value = obj
        for part in self._path:
            if isinstance(value, dict):
                value = value.get(part, _MISSING)
            else:
                value = getattr(value, part, _MISSING)
            if value is _MISSING:
                return _MISSING
        try:
            for transform in self._transforms:
                value = transform(value)
        except (AttributeError, TypeError, ValueError):
            return _MISSING
        return value

    def resolve(self, obj: Any) -> bool | dict[str, Any]:
        if self._boolean_operator is not None:
            assert self._left is not None and self._right is not None
            left = bool(self._left.resolve(obj))
            if self._boolean_operator == "and":
                return left and bool(self._right.resolve(obj))
            return left or bool(self._right.resolve(obj))

        value = self._value(obj)
        if value is _MISSING:
            return False
        try:
            result = self._predicate(value) if self._predicate else value
        except (AttributeError, TypeError, ValueError, re.error):
            return False
        if not result:
            return False
        if self._alias is not None:
            captured = result if not isinstance(result, bool) else value
            return {self._alias: captured}
        return True

    def __call__(self, event: Any) -> bool | dict[str, Any]:
        return self.resolve(event)


F = MagicFilter()
