from __future__ import annotations

from typing import Any

from aiomax2.exceptions import RouterError
from aiomax2.types import (
    CommentCreatedUpdate,
    CommentEditedUpdate,
    MessageCallbackUpdate,
    MessageCreatedUpdate,
    MessageEditedUpdate,
    Update,
)

from .event import UNHANDLED, EventObserver
from .middleware import wrap_middlewares

EVENT_NAMES = (
    "message_created",
    "message_callback",
    "message_edited",
    "message_removed",
    "comment_created",
    "comment_edited",
    "comment_removed",
    "bot_added",
    "bot_removed",
    "user_added",
    "user_removed",
    "bot_started",
    "bot_stopped",
    "dialog_cleared",
    "dialog_removed",
    "dialog_muted",
    "dialog_unmuted",
    "chat_title_changed",
    "bot_admin_permissions_changed",
)


class Router:
    def __init__(self, *, name: str | None = None) -> None:
        self.name = name or hex(id(self))
        self.parent_router: Router | None = None
        self.sub_routers: list[Router] = []
        self.observers = {
            name: EventObserver(self, name) for name in ("update", *EVENT_NAMES)
        }
        self.update = self.observers["update"]
        self.message = self.observers["message_created"]
        self.message_created = self.message
        self.callback_query = self.observers["message_callback"]
        self.message_callback = self.callback_query
        self.message_edited = self.observers["message_edited"]
        self.message_removed = self.observers["message_removed"]
        self.comment_created = self.observers["comment_created"]
        self.comment_edited = self.observers["comment_edited"]
        self.comment_removed = self.observers["comment_removed"]
        self.bot_added = self.observers["bot_added"]
        self.bot_removed = self.observers["bot_removed"]
        self.user_added = self.observers["user_added"]
        self.user_removed = self.observers["user_removed"]
        self.bot_started = self.observers["bot_started"]
        self.bot_stopped = self.observers["bot_stopped"]
        self.dialog_cleared = self.observers["dialog_cleared"]
        self.dialog_removed = self.observers["dialog_removed"]
        self.dialog_muted = self.observers["dialog_muted"]
        self.dialog_unmuted = self.observers["dialog_unmuted"]
        self.chat_title_changed = self.observers["chat_title_changed"]
        self.bot_admin_permissions_changed = self.observers[
            "bot_admin_permissions_changed"
        ]

    def include_router(self, router: Router) -> Router:
        if router is self:
            raise RouterError("a router cannot include itself")
        if router.parent_router is not None:
            raise RouterError("router is already attached")
        parent: Router | None = self
        while parent is not None:
            if parent is router:
                raise RouterError("circular router inclusion is not allowed")
            parent = parent.parent_router
        router.parent_router = self
        self.sub_routers.append(router)
        return router

    def include_routers(self, *routers: Router) -> None:
        for router in routers:
            self.include_router(router)

    def resolve_used_update_types(self) -> list[str]:
        used = {
            event_name
            for event_name in EVENT_NAMES
            if self.observers[event_name].handlers
        }
        for router in self.sub_routers:
            used.update(router.resolve_used_update_types())
        return sorted(used)

    async def propagate_event(self, update: Update, data: dict[str, Any]) -> Any:
        event_name, event, event_context_name = extract_event(update)

        async def route(_: Any, update_data: dict[str, Any]) -> Any:
            local_data = dict(update_data)
            local_data["router"] = self
            update_result = await self.update.trigger(
                update, local_data, with_outer=False
            )
            if update_result is not UNHANDLED:
                return update_result

            observer = self.observers.get(event_name)
            if observer is not None:
                event_data = dict(local_data)
                event_data["event"] = event
                event_data[event_context_name] = event
                event_data[event_name] = event
                result = await observer.trigger(event, event_data)
                if result is not UNHANDLED:
                    return result

            for child in self.sub_routers:
                result = await child.propagate_event(update, local_data)
                if result is not UNHANDLED:
                    return result
            return UNHANDLED

        wrapped = wrap_middlewares(self.update.outer_middleware.items, route)
        return await wrapped(update, data)


def extract_event(update: Update) -> tuple[str, Any, str]:
    if isinstance(update, MessageCreatedUpdate):
        return update.update_type, update.message, "message"
    if isinstance(update, MessageCallbackUpdate):
        return update.update_type, update.as_callback_query(), "callback_query"
    if isinstance(update, MessageEditedUpdate):
        return update.update_type, update.message, "message_edited"
    if isinstance(update, (CommentCreatedUpdate, CommentEditedUpdate)):
        return update.update_type, update.message, update.update_type
    return update.update_type, update, update.update_type
