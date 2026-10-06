from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from itertools import cycle
from typing import Self

from aiomax2.exceptions import ValidationError
from aiomax2.types import (
    Button,
    CallbackButton,
    ClipboardButton,
    InlineKeyboardAttachmentRequest,
    Keyboard,
    LinkButton,
    MessageButton,
    OpenAppButton,
    RequestContactButton,
    RequestGeoLocationButton,
)


class InlineKeyboardBuilder:
    """Build a MAX inline-keyboard attachment with an aiogram-like workflow."""

    def __init__(self, markup: Sequence[Sequence[Button]] | None = None) -> None:
        self._markup: list[list[Button]] = [list(row) for row in markup or ()]

    @property
    def buttons(self) -> Iterator[Button]:
        """Iterate over buttons in row-major order."""

        return iter(self._flatten())

    def button(
        self,
        *,
        text: str,
        callback_data: str | None = None,
        url: str | None = None,
        request_contact: bool = False,
        request_geo_location: bool = False,
        message: bool = False,
        clipboard: str | None = None,
        web_app: str | None = None,
        quick: bool | None = None,
        app_payload: str | None = None,
        contact_id: int | None = None,
    ) -> Self:
        """Add exactly one button selected by its action-specific argument.

        ``callback_data`` is an aiomax2 convenience alias. It is serialized as
        the MAX callback button's ``payload`` field.
        """

        actions = (
            callback_data is not None,
            url is not None,
            request_contact,
            request_geo_location,
            message,
            clipboard is not None,
            web_app is not None,
        )
        if sum(actions) != 1:
            raise ValidationError(
                "button() requires exactly one action: callback_data, url, "
                "request_contact, request_geo_location, message, clipboard or web_app"
            )

        if callback_data is not None:
            return self.callback(text=text, payload=callback_data)
        if url is not None:
            return self.link(text=text, url=url)
        if request_contact:
            return self.request_contact(text=text)
        if request_geo_location:
            return self.request_geo_location(text=text, quick=quick)
        if message:
            return self.message(text=text)
        if clipboard is not None:
            return self.clipboard(text=text, payload=clipboard)
        assert web_app is not None
        return self.open_app(
            text=text,
            web_app=web_app,
            payload=app_payload,
            contact_id=contact_id,
        )

    def callback(self, *, text: str, payload: str) -> Self:
        return self.add(CallbackButton(text=text, payload=payload))

    def link(self, *, text: str, url: str) -> Self:
        return self.add(LinkButton(text=text, url=url))

    def request_contact(self, *, text: str) -> Self:
        return self.add(RequestContactButton(text=text))

    def request_geo_location(self, *, text: str, quick: bool | None = None) -> Self:
        return self.add(RequestGeoLocationButton(text=text, quick=quick))

    def message(self, *, text: str) -> Self:
        return self.add(MessageButton(text=text))

    def clipboard(self, *, text: str, payload: str) -> Self:
        return self.add(ClipboardButton(text=text, payload=payload))

    def open_app(
        self,
        *,
        text: str,
        web_app: str,
        payload: str | None = None,
        contact_id: int | None = None,
    ) -> Self:
        return self.add(
            OpenAppButton(
                text=text,
                web_app=web_app,
                payload=payload,
                contact_id=contact_id,
            )
        )

    def add(self, *buttons: Button) -> Self:
        """Append buttons, filling the current row up to seven items."""

        pending = list(buttons)
        if not pending:
            return self
        if self._markup and len(self._markup[-1]) < 7:
            available = 7 - len(self._markup[-1])
            self._markup[-1].extend(pending[:available])
            del pending[:available]
        while pending:
            self._markup.append(pending[:7])
            del pending[:7]
        return self

    def row(self, *buttons: Button, width: int | None = None) -> Self:
        """Append buttons as one or more new rows."""

        if not buttons:
            raise ValidationError("row() requires at least one button")
        row_width = min(len(buttons), 7) if width is None else width
        self._validate_width(row_width)
        for offset in range(0, len(buttons), row_width):
            self._markup.append(list(buttons[offset : offset + row_width]))
        return self

    def adjust(self, *sizes: int, repeat: bool = False) -> Self:
        """Reflow all buttons into rows of the requested sizes."""

        if not sizes:
            raise ValidationError("adjust() requires at least one row size")
        for size in sizes:
            self._validate_width(size)

        flat = self._flatten()
        self._markup = []
        if not flat:
            return self

        size_iterator: Iterable[int]
        if repeat:
            size_iterator = cycle(sizes)
        else:
            size_iterator = (*sizes, *([sizes[-1]] * len(flat)))

        offset = 0
        for size in size_iterator:
            if offset >= len(flat):
                break
            self._markup.append(flat[offset : offset + size])
            offset += size
        return self

    def attach(self, builder: InlineKeyboardBuilder) -> Self:
        """Append a copy of another builder's rows."""

        self._markup.extend([list(row) for row in builder._markup])
        return self

    def as_markup(self) -> InlineKeyboardAttachmentRequest:
        """Build the existing low-level MAX inline-keyboard attachment."""

        return InlineKeyboardAttachmentRequest(
            payload=Keyboard(buttons=[list(row) for row in self._markup])
        )

    @classmethod
    def from_markup(
        cls, markup: InlineKeyboardAttachmentRequest
    ) -> InlineKeyboardBuilder:
        return cls(markup.payload.buttons)

    def _flatten(self) -> list[Button]:
        return [button for row in self._markup for button in row]

    @staticmethod
    def _validate_width(width: int) -> None:
        if not 1 <= width <= 7:
            raise ValidationError("keyboard row width must be between 1 and 7")
