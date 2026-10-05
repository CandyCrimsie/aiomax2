from __future__ import annotations

from typing import TYPE_CHECKING

from aiomax2.enums import ChatStatus, ChatType

from .base import MAXObject
from .user import UserWithPhoto

if TYPE_CHECKING:
    from .message import Message


class Image(MAXObject):
    url: str


class Chat(MAXObject):
    chat_id: int
    type: ChatType
    status: ChatStatus
    title: str | None = None
    icon: Image | None = None
    last_event_time: int
    participants_count: int
    owner_id: int | None = None
    participants: dict[str, int] | None = None
    is_public: bool
    link: str | None = None
    description: str | None = None
    dialog_with_user: UserWithPhoto | None = None
    messages_count: int | None = None
    pinned_message: Message | None = None
