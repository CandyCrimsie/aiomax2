from __future__ import annotations

from typing import Any

import pytest

from aiomax2 import Bot, Dispatcher, F, Router
from aiomax2.dispatcher import BaseMiddleware
from aiomax2.filters import Command, CommandObject
from aiomax2.types import CallbackQuery, Message, UpdateList


class TraceMiddleware(BaseMiddleware):
    def __init__(self, trace: list[str], name: str) -> None:
        self.trace = trace
        self.name = name

    async def __call__(self, handler: Any, event: Any, data: dict[str, Any]) -> Any:
        self.trace.append(f"{self.name}:before")
        data[f"{self.name}_value"] = self.name
        result = await handler(event, data)
        self.trace.append(f"{self.name}:after")
        return result


@pytest.mark.asyncio
async def test_nested_router_command_and_dependency_injection(
    message_update: dict[str, Any],
) -> None:
    bot = Bot("token")
    dispatcher = Dispatcher(service="service")
    router = Router(name="feature")
    dispatcher.include_router(router)
    called: list[tuple[str, str | None, str, str]] = []

    @router.message(Command("start"))
    async def handler(
        message: Message,
        command: CommandObject,
        bot: Bot,
        service: str,
    ) -> None:
        called.append((message.text or "", command.args, bot.token, service))

    await dispatcher.feed_raw_update(bot, message_update)

    assert called == [("/start 123", "123", "token", "service")]
    await bot.close()


@pytest.mark.asyncio
async def test_outer_and_inner_middleware_order(
    message_update: dict[str, Any],
) -> None:
    bot = Bot("token")
    dispatcher = Dispatcher()
    trace: list[str] = []
    dispatcher.message.outer_middleware(TraceMiddleware(trace, "outer"))
    dispatcher.message.middleware(TraceMiddleware(trace, "inner"))

    @dispatcher.message(F.sender.user_id == 42)
    async def handler(message: Message, inner_value: str) -> None:
        assert inner_value == "inner"
        trace.append("handler")

    await dispatcher.feed_raw_update(bot, message_update)

    assert trace == [
        "outer:before",
        "inner:before",
        "handler",
        "inner:after",
        "outer:after",
    ]
    await bot.close()


@pytest.mark.asyncio
async def test_callback_observer_receives_callback_query(
    callback_update: dict[str, Any],
) -> None:
    bot = Bot("token")
    dispatcher = Dispatcher()
    seen: list[CallbackQuery] = []

    @dispatcher.callback_query(F.payload == "confirm")
    async def callback_handler(callback_query: CallbackQuery) -> None:
        seen.append(callback_query)

    await dispatcher.feed_raw_update(bot, callback_update)

    assert seen[0].callback_id == "callback.1"
    assert seen[0].message is not None
    assert seen[0].message.message_id == "mid.1"
    await bot.close()


def test_router_cannot_be_attached_twice() -> None:
    first = Router()
    second = Router()
    child = Router()
    first.include_router(child)

    with pytest.raises(Exception, match="already attached"):
        second.include_router(child)


@pytest.mark.asyncio
async def test_development_polling_tracks_marker_and_stops(
    message_update: dict[str, Any],
) -> None:
    dispatcher = Dispatcher()

    class PollingBot(Bot):
        def __init__(self) -> None:
            super().__init__("token")
            self.calls: list[dict[str, Any]] = []
            self.was_closed = False

        async def get_updates(self, **kwargs: Any) -> UpdateList:
            self.calls.append(kwargs)
            return UpdateList.model_validate(
                {"updates": [message_update], "marker": 77}
            )

        async def close(self) -> None:
            self.was_closed = True

    bot = PollingBot()
    seen: list[str | None] = []

    @dispatcher.message()
    async def handler(message: Message) -> None:
        seen.append(message.text)
        await dispatcher.stop_polling()

    await dispatcher.start_polling(bot, handle_as_tasks=False)

    assert seen == ["/start 123"]
    assert bot.calls[0]["marker"] is None
    assert bot.calls[0]["types"] == ["message_created"]
    assert bot.was_closed
