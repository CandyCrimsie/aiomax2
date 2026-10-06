from __future__ import annotations

import asyncio
import logging
from typing import Any

import pytest

from aiomax2 import Bot, Dispatcher, F, Router
from aiomax2.dispatcher import BaseMiddleware
from aiomax2.filters import Command, CommandObject
from aiomax2.fsm import FSMContext
from aiomax2.types import CallbackQuery, Message, UpdateList
from tests.update_cases import ALL_UPDATE_CASES, ALL_UPDATE_TYPES


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


@pytest.mark.asyncio
async def test_callback_without_message_uses_user_for_fsm_identifiers() -> None:
    case = next(
        item for item in ALL_UPDATE_CASES if item.update_type == "message_callback"
    )
    raw = case.raw()
    raw["message"] = None
    bot = Bot("token")
    dispatcher = Dispatcher()
    seen: list[tuple[CallbackQuery, FSMContext]] = []

    @dispatcher.callback_query()
    async def handler(callback_query: CallbackQuery, state: FSMContext) -> None:
        seen.append((callback_query, state))

    await dispatcher.feed_raw_update(bot, raw)

    callback_query, state = seen[0]
    assert callback_query.message is None
    assert callback_query.user_locale == "ru"
    assert callback_query.require_bot() is bot
    assert state.key.chat_id == 42
    assert state.key.user_id == 42
    await dispatcher.close()
    await bot.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ALL_UPDATE_CASES, ids=ALL_UPDATE_TYPES)
async def test_every_update_runs_typed_dispatch_pipeline(case: Any) -> None:
    bot = Bot("token")
    dispatcher = Dispatcher()
    router = Router(name=f"test-{case.update_type}")
    dispatcher.include_router(router)
    seen: list[tuple[object, dict[str, Any], FSMContext]] = []

    async def handler(
        event: object,
        state: FSMContext,
        **data: Any,
    ) -> None:
        seen.append((event, data, state))

    getattr(router, case.observer).register(handler)

    await dispatcher.feed_raw_update(bot, case.raw())

    assert len(seen) == 1
    event, data, state = seen[0]
    assert isinstance(event, case.event_type)
    assert isinstance(data["event_update"], case.model_type)
    assert data[case.context_name] is event
    assert data[case.update_type] is event
    assert data["event_update"].require_bot() is bot
    assert event.require_bot() is bot
    assert state.key.chat_id == case.fsm_chat_id
    assert state.key.user_id == case.fsm_user_id
    await dispatcher.close()
    await bot.close()


def test_resolve_used_update_types_is_nested_unique_and_deterministic() -> None:
    dispatcher = Dispatcher()
    first = Router(name="first")
    second = Router(name="second")
    nested = Router(name="nested")
    dispatcher.include_routers(first, second)
    first.include_router(nested)

    async def handler(event: object) -> None:
        return None

    dispatcher.message.register(handler)
    first.message.register(handler)
    nested.bot_removed.register(handler)
    nested.comment_edited.register(handler)
    second.callback_query.register(handler)
    second.update.register(handler)

    assert dispatcher.resolve_used_update_types() == [
        "bot_removed",
        "comment_edited",
        "message_callback",
        "message_created",
    ]


@pytest.mark.asyncio
async def test_polling_background_handler_exception_is_retrieved_and_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    dispatcher = Dispatcher()

    async def failing_handler() -> None:
        raise RuntimeError("handler failed")

    task = asyncio.create_task(failing_handler())
    dispatcher._handle_update_tasks.add(task)
    task.add_done_callback(dispatcher._polling_task_done)

    with caplog.at_level(logging.ERROR, logger="aiomax2.dispatcher.dispatcher"):
        await asyncio.sleep(0)
        await asyncio.sleep(0)

    assert task not in dispatcher._handle_update_tasks
    assert "MAX polling update handler failed" in caplog.text


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
