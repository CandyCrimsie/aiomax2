from __future__ import annotations

import re
from typing import Any

import pytest

from aiomax2 import F
from aiomax2.filters import Command
from aiomax2.types import MessageCreatedUpdate, parse_update


@pytest.fixture
def message(message_update: dict[str, Any]) -> Any:
    update = parse_update(message_update)
    assert isinstance(update, MessageCreatedUpdate)
    return update.message


@pytest.mark.asyncio
async def test_command_extracts_args(message: Any) -> None:
    result = await Command("start")(message)

    assert isinstance(result, dict)
    assert result["command"].command == "start"
    assert result["command"].args == "123"


@pytest.mark.asyncio
async def test_command_without_args(message: Any) -> None:
    message.body.text = "/start"
    result = await Command("start")(message)

    assert isinstance(result, dict)
    assert result["command"].args is None


def test_magic_filter_paths_and_composition(message: Any) -> None:
    assert (F.text == "/start 123").resolve(message) is True
    assert (F.sender.user_id == 42).resolve(message) is True
    assert ((F.text.startswith("/start")) & (F.chat_id == 100)).resolve(message)
    assert not (F.sender.user_id == 1).resolve(message)


def test_magic_filter_capture(message: Any) -> None:
    result = F.text.regexp(r"(\d+)$").as_("digits").resolve(message)

    assert isinstance(result, dict)
    assert isinstance(result["digits"], re.Match)
    assert result["digits"].group(1) == "123"
