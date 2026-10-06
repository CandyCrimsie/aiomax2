from __future__ import annotations

import asyncio
import hashlib
import logging
from collections.abc import Mapping, Sequence
from contextlib import suppress
from typing import Any

from aiomax2.bot import Bot
from aiomax2.fsm import BaseStorage, FSMContext, FSMStrategy, MemoryStorage, StorageKey
from aiomax2.types import (
    CallbackQuery,
    Message,
    Update,
    parse_update,
)

from .event import UNHANDLED
from .router import Router, extract_event

logger = logging.getLogger(__name__)


class Dispatcher(Router):
    def __init__(
        self,
        *,
        storage: BaseStorage | None = None,
        fsm_strategy: FSMStrategy = FSMStrategy.USER_IN_CHAT,
        disable_fsm: bool = False,
        name: str | None = None,
        **workflow_data: Any,
    ) -> None:
        super().__init__(name=name or "dispatcher")
        self.storage = storage or MemoryStorage()
        self.fsm_strategy = fsm_strategy
        self.disable_fsm = disable_fsm
        self.workflow_data = workflow_data
        self._stop_signal: asyncio.Event | None = None
        self._polling_lock = asyncio.Lock()
        self._handle_update_tasks: set[asyncio.Task[Any]] = set()

    def __getitem__(self, key: str) -> Any:
        return self.workflow_data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.workflow_data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.workflow_data.get(key, default)

    async def feed_raw_update(
        self, bot: Bot, update: Mapping[str, Any], **kwargs: Any
    ) -> Any:
        return await self.feed_update(bot, parse_update(update), **kwargs)

    async def feed_update(self, bot: Bot, update: Update, **kwargs: Any) -> Any:
        update.bind(bot)
        data = dict(self.workflow_data)
        data.update(kwargs)
        data.update(
            {
                "bot": bot,
                "dispatcher": self,
                "event_update": update,
                "update": update,
            }
        )
        if not self.disable_fsm:
            state = await self._fsm_context(bot, update)
            data["state"] = state
            data["raw_state"] = await state.get_state()
        result = await self.propagate_event(update, data)
        return None if result is UNHANDLED else result

    async def _fsm_context(self, bot: Bot, update: Update) -> FSMContext:
        _, event, _ = extract_event(update)
        chat_id, user_id = _event_ids(event, update)
        if self.fsm_strategy is FSMStrategy.CHAT:
            user_id = None
        elif self.fsm_strategy is FSMStrategy.GLOBAL_USER:
            chat_id = None
        bot_id: int | str = (
            bot.id or hashlib.sha256(bot.token.encode("utf-8")).hexdigest()[:16]
        )
        return FSMContext(
            self.storage,
            StorageKey(bot_id=bot_id, chat_id=chat_id, user_id=user_id),
        )

    async def start_polling(
        self,
        bot: Bot,
        *,
        polling_timeout: int = 30,
        limit: int = 100,
        handle_as_tasks: bool = True,
        close_bot_session: bool = True,
        allowed_updates: Sequence[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Run MAX long polling for development and testing only."""

        async with self._polling_lock:
            logger.warning(
                "MAX long polling is intended only for development/testing; "
                "use a webhook in production"
            )
            self._stop_signal = asyncio.Event()
            marker: int | None = None
            update_types = (
                list(allowed_updates)
                if allowed_updates is not None
                else self.resolve_used_update_types() or None
            )
            backoff = 0.5
            try:
                while not self._stop_signal.is_set():
                    try:
                        batch = await bot.get_updates(
                            limit=limit,
                            timeout=polling_timeout,
                            marker=marker,
                            types=update_types,
                        )
                        marker = batch.marker
                        backoff = 0.5
                        for update in batch.updates:
                            coroutine = self.feed_update(bot, update, **kwargs)
                            if handle_as_tasks:
                                task = asyncio.create_task(coroutine)
                                self._handle_update_tasks.add(task)
                                task.add_done_callback(self._polling_task_done)
                            else:
                                await coroutine
                    except asyncio.CancelledError:
                        raise
                    except Exception:
                        logger.exception("MAX polling request failed")
                        try:
                            await asyncio.wait_for(
                                self._stop_signal.wait(), timeout=backoff
                            )
                        except TimeoutError:
                            pass
                        backoff = min(backoff * 2, 5.0)
            finally:
                if self._handle_update_tasks:
                    await asyncio.gather(
                        *self._handle_update_tasks, return_exceptions=True
                    )
                self._stop_signal = None
                if close_bot_session:
                    await bot.close()

    def _polling_task_done(self, task: asyncio.Task[Any]) -> None:
        self._handle_update_tasks.discard(task)
        if task.cancelled():
            return
        exception = task.exception()
        if exception is not None:
            logger.error(
                "MAX polling update handler failed",
                exc_info=(
                    type(exception),
                    exception,
                    exception.__traceback__,
                ),
            )

    async def stop_polling(self) -> None:
        if self._stop_signal is None:
            raise RuntimeError("polling is not running")
        self._stop_signal.set()

    def run_polling(self, bot: Bot, **kwargs: Any) -> None:
        with suppress(KeyboardInterrupt):
            asyncio.run(self.start_polling(bot, **kwargs))

    async def close(self) -> None:
        await self.storage.close()

    def webhook_router(
        self,
        path: str,
        *,
        bot: Bot,
        secret: str | None = None,
        **feed_data: Any,
    ) -> Any:
        from aiomax2.webhook.fastapi import create_webhook_router

        return create_webhook_router(self, bot, path=path, secret=secret, **feed_data)


def _event_ids(event: Any, update: Update) -> tuple[int | None, int | None]:
    if isinstance(event, Message):
        chat_id = event.chat_id
        user_id = event.sender.user_id if event.sender is not None else event.user_id
        return chat_id or user_id, user_id
    if isinstance(event, CallbackQuery):
        chat_id = event.message.chat_id if event.message is not None else None
        return chat_id or event.user.user_id, event.user.user_id
    chat_id = getattr(update, "chat_id", None)
    user = getattr(update, "user", None)
    user_id = getattr(update, "user_id", None)
    if user_id is None and user is not None:
        user_id = user.user_id
    return chat_id or user_id, user_id
