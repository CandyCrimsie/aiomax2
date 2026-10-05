from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from pydantic import BaseModel, ConfigDict, PrivateAttr

from aiomax2.exceptions import BotNotBoundError

if TYPE_CHECKING:
    from aiomax2.bot import Bot


class MAXObject(BaseModel):
    """Base for MAX objects, tolerant to forward-compatible response fields."""

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        use_enum_values=True,
    )

    _bot: Bot | None = PrivateAttr(default=None)

    def bind(self, bot: Bot) -> Self:
        self._bot = bot
        return self

    def require_bot(self) -> Bot:
        if self._bot is None:
            raise BotNotBoundError(
                f"{type(self).__name__} is not bound to a Bot; "
                "objects parsed by Dispatcher and Bot methods are bound automatically"
            )
        return self._bot

    def api_dump(self) -> dict[str, Any]:
        return self.model_dump(mode="json", by_alias=True, exclude_none=True)
