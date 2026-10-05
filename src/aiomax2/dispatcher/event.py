from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Final

from aiomax2.exceptions import SkipHandler
from aiomax2.filters import StateFilter
from aiomax2.fsm import State

from .invoke import invoke
from .middleware import MiddlewareManager, wrap_middlewares


class _Unhandled:
    pass


UNHANDLED: Final = _Unhandled()


@dataclass(slots=True)
class HandlerObject:
    callback: Callable[..., Any]
    filters: tuple[Callable[..., Any], ...]

    async def check(
        self, event: Any, data: dict[str, Any]
    ) -> tuple[bool, dict[str, Any]]:
        context = dict(data)
        for event_filter in self.filters:
            result = await invoke(event_filter, event, context)
            if not result:
                return False, context
            if isinstance(result, Mapping):
                context.update(result)
        return True, context


class EventObserver:
    def __init__(self, router: Any, event_name: str) -> None:
        self.router = router
        self.event_name = event_name
        self.handlers: list[HandlerObject] = []
        self.root_filters: list[Callable[..., Any]] = []
        self.outer_middleware = MiddlewareManager()
        self.middleware = MiddlewareManager()

    def register(
        self,
        callback: Callable[..., Any],
        *filters: Callable[..., Any] | State,
    ) -> Callable[..., Any]:
        prepared: list[Callable[..., Any]] = []
        for event_filter in filters:
            if isinstance(event_filter, State):
                prepared.append(StateFilter(event_filter))
            elif callable(event_filter):
                prepared.append(event_filter)
            else:
                raise TypeError(f"Unsupported filter: {event_filter!r}")
        self.handlers.append(HandlerObject(callback, tuple(prepared)))
        return callback

    def __call__(
        self, *filters: Callable[..., Any] | State
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(callback: Callable[..., Any]) -> Callable[..., Any]:
            return self.register(callback, *filters)

        return decorator

    def filter(self, *filters: Callable[..., Any]) -> None:
        self.root_filters.extend(filters)

    async def trigger(
        self, event: Any, data: dict[str, Any], *, with_outer: bool = True
    ) -> Any:
        async def core(current_event: Any, current_data: dict[str, Any]) -> Any:
            context = dict(current_data)
            for event_filter in self.root_filters:
                result = await invoke(event_filter, current_event, context)
                if not result:
                    return UNHANDLED
                if isinstance(result, Mapping):
                    context.update(result)

            for handler in self.handlers:
                passed, handler_data = await handler.check(current_event, context)
                if not passed:
                    continue

                async def call_handler(
                    inner_event: Any,
                    inner_data: dict[str, Any],
                    *,
                    current_handler: HandlerObject = handler,
                ) -> Any:
                    return await invoke(
                        current_handler.callback, inner_event, inner_data
                    )

                wrapped = wrap_middlewares(self.middleware.items, call_handler)
                try:
                    return await wrapped(current_event, handler_data)
                except SkipHandler:
                    continue
            return UNHANDLED

        if not with_outer:
            return await core(event, data)
        wrapped = wrap_middlewares(self.outer_middleware.items, core)
        return await wrapped(event, data)
