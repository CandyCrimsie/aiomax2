from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aiomax2.types import Message

from .base import Filter


@dataclass(frozen=True, slots=True)
class CommandObject:
    prefix: str
    command: str
    args: str | None = None


class Command(Filter):
    def __init__(
        self,
        *commands: str,
        prefix: str = "/",
        ignore_case: bool = False,
    ) -> None:
        if not commands:
            raise ValueError("at least one command is required")
        normalized: set[str] = set()
        for command in commands:
            command = command.removeprefix(prefix)
            if not command or any(char.isspace() for char in command):
                raise ValueError("command must be non-empty and contain no whitespace")
            normalized.add(command.casefold() if ignore_case else command)
        self.commands = frozenset(normalized)
        self.prefix = prefix
        self.ignore_case = ignore_case

    async def __call__(self, event: Any, **_: Any) -> bool | dict[str, CommandObject]:
        if not isinstance(event, Message) or not event.text:
            return False
        text = event.text
        if not text.startswith(self.prefix):
            return False
        raw = text[len(self.prefix) :]
        if not raw:
            return False
        parts = raw.split(maxsplit=1)
        command = parts[0]
        args = parts[1] if len(parts) == 2 else None
        checked = command.casefold() if self.ignore_case else command
        if checked not in self.commands:
            return False
        command_object = CommandObject(
            prefix=self.prefix,
            command=command,
            args=args,
        )
        return {"command": command_object}


class CommandStart(Command):
    def __init__(self, *, prefix: str = "/", ignore_case: bool = False) -> None:
        super().__init__("start", prefix=prefix, ignore_case=ignore_case)
