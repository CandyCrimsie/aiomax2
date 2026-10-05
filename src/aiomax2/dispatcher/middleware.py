from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

type NextMiddleware = Callable[[Any, dict[str, Any]], Awaitable[Any]]
type MiddlewareCallable = Callable[
    [NextMiddleware, Any, dict[str, Any]], Awaitable[Any]
]


class BaseMiddleware(ABC):
    @abstractmethod
    async def __call__(
        self,
        handler: NextMiddleware,
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        raise NotImplementedError


class MiddlewareManager:
    def __init__(self) -> None:
        self._items: list[MiddlewareCallable] = []

    @property
    def items(self) -> tuple[MiddlewareCallable, ...]:
        return tuple(self._items)

    def register(self, middleware: MiddlewareCallable) -> MiddlewareCallable:
        self._items.append(middleware)
        return middleware

    def __call__(
        self, middleware: MiddlewareCallable | None = None
    ) -> MiddlewareCallable | Callable[[MiddlewareCallable], MiddlewareCallable]:
        if middleware is not None:
            return self.register(middleware)

        def decorator(value: MiddlewareCallable) -> MiddlewareCallable:
            return self.register(value)

        return decorator


def wrap_middlewares(
    middlewares: tuple[MiddlewareCallable, ...], handler: NextMiddleware
) -> NextMiddleware:
    wrapped = handler
    for middleware in reversed(middlewares):
        next_handler = wrapped

        async def call(
            event: Any,
            data: dict[str, Any],
            *,
            current: MiddlewareCallable = middleware,
            next_: NextMiddleware = next_handler,
        ) -> Any:
            return await current(next_, event, data)

        wrapped = call
    return wrapped
