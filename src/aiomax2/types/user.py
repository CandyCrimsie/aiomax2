from __future__ import annotations

from pydantic import Field

from aiomax2.enums import ChatAdminPermission

from .base import MAXObject


class User(MAXObject):
    user_id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    is_bot: bool
    last_activity_time: int | None = None

    @property
    def full_name(self) -> str:
        return " ".join(part for part in (self.first_name, self.last_name) if part)


class UserWithPhoto(User):
    description: str | None = None
    avatar_url: str | None = None
    full_avatar_url: str | None = None


class BotCommand(MAXObject):
    name: str = Field(min_length=1, max_length=64)
    description: str | None = Field(default=None, min_length=1, max_length=128)


class BotInfo(UserWithPhoto):
    commands: list[BotCommand] | None = Field(default=None, max_length=32)


class ChatMember(UserWithPhoto):
    last_access_time: int
    is_owner: bool
    is_admin: bool
    join_time: int
    permissions: list[ChatAdminPermission] | None = None
    alias: str | None = None


class ChatAdmin(MAXObject):
    user_id: int
    permissions: list[ChatAdminPermission]
    alias: str | None = None
