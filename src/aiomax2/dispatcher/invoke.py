from __future__ import annotations

import inspect
import types
from collections.abc import Callable, Mapping
from typing import Any, get_args, get_origin, get_type_hints


async def invoke(
    callback: Callable[..., Any], event: Any, data: Mapping[str, Any]
) -> Any:
    """Call a filter/handler with event and named context dependencies."""

    signature = inspect.signature(callback)
    try:
        hints = get_type_hints(callback)
    except (NameError, TypeError):
        hints = {}

    positional: list[Any] = []
    keyword: dict[str, Any] = {}
    consumed: set[str] = set()
    event_used = False
    has_var_keyword = False
    parameter_index = 0

    for parameter in signature.parameters.values():
        if parameter.kind is inspect.Parameter.VAR_POSITIONAL:
            continue
        if parameter.kind is inspect.Parameter.VAR_KEYWORD:
            has_var_keyword = True
            continue

        value = _missing
        if parameter.name in data:
            value = data[parameter.name]
            consumed.add(parameter.name)
            if value is event:
                event_used = True
        elif parameter.name == "event":
            value = event
            event_used = True
        else:
            annotation = hints.get(parameter.name, parameter.annotation)
            if not event_used and _annotation_matches(annotation, event):
                value = event
                event_used = True
            elif (
                not event_used
                and parameter_index == 0
                and parameter.kind
                in (
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                )
            ):
                value = event
                event_used = True

        if value is _missing:
            if parameter.default is not inspect.Parameter.empty:
                continue
            raise TypeError(
                f"Cannot resolve parameter {parameter.name!r} for "
                f"{getattr(callback, '__qualname__', repr(callback))}"
            )

        if parameter.kind is inspect.Parameter.POSITIONAL_ONLY:
            positional.append(value)
        else:
            keyword[parameter.name] = value
        parameter_index += 1

    if has_var_keyword:
        keyword.update(
            {key: value for key, value in data.items() if key not in consumed}
        )

    result = callback(*positional, **keyword)
    if inspect.isawaitable(result):
        return await result
    return result


_missing = object()


def _annotation_matches(annotation: Any, event: Any) -> bool:
    if annotation is inspect.Parameter.empty or annotation is Any:
        return False
    origin = get_origin(annotation)
    if origin in (types.UnionType,):
        return any(_annotation_matches(item, event) for item in get_args(annotation))
    try:
        return isinstance(event, annotation)
    except TypeError:
        return False
