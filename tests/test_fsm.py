from __future__ import annotations

from typing import Any

import pytest

from aiomax2 import Bot, Dispatcher
from aiomax2.fsm import FSMContext, State, StatesGroup
from aiomax2.types import Message


class Form(StatesGroup):
    name = State()
    age = State()


@pytest.mark.asyncio
async def test_fsm_state_filter_and_context(
    message_update: dict[str, Any],
) -> None:
    bot = Bot("token")
    dispatcher = Dispatcher()
    calls: list[str] = []

    @dispatcher.message(Form.name)
    async def name_handler(message: Message, state: FSMContext) -> None:
        calls.append(message.text or "")
        await state.update_data(name=message.text)
        await state.set_state(Form.age)

    update = await dispatcher._fsm_context(
        bot,
        __import__("aiomax2.types", fromlist=["parse_update"]).parse_update(
            message_update
        ),
    )
    await update.set_state(Form.name)

    await dispatcher.feed_raw_update(bot, message_update)

    assert calls == ["/start 123"]
    assert await update.get_state() == Form.age.state
    assert await update.get_data() == {"name": "/start 123"}
    await bot.close()


def test_state_names_are_stable() -> None:
    assert Form.name.state == "Form:name"
    assert Form.age.state == "Form:age"
