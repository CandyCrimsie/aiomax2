from __future__ import annotations

import asyncio
import time
from collections import deque
from collections.abc import Awaitable, Callable

Clock = Callable[[], float]
Sleeper = Callable[[float], Awaitable[None]]


class AsyncRateLimiter:
    """A cancellation-safe sliding-window limiter."""

    def __init__(
        self,
        limit: int,
        period: float = 1.0,
        *,
        clock: Clock = time.monotonic,
        sleep: Sleeper = asyncio.sleep,
    ) -> None:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        if period <= 0:
            raise ValueError("period must be greater than zero")
        self.limit = limit
        self.period = period
        self._clock = clock
        self._sleep = sleep
        self._timestamps: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        while True:
            delay = 0.0
            async with self._lock:
                now = self._clock()
                threshold = now - self.period
                while self._timestamps and self._timestamps[0] <= threshold:
                    self._timestamps.popleft()
                if len(self._timestamps) < self.limit:
                    self._timestamps.append(now)
                    return
                delay = self.period - (now - self._timestamps[0])
            await self._sleep(max(delay, 0.0))

    async def __aenter__(self) -> AsyncRateLimiter:
        await self.acquire()
        return self

    async def __aexit__(self, *_: object) -> None:
        return None


class KeyedRateLimiter:
    """Creates independent sliding windows for MAX chat/user targets."""

    def __init__(
        self,
        limit: int,
        period: float = 1.0,
        *,
        clock: Clock = time.monotonic,
        sleep: Sleeper = asyncio.sleep,
    ) -> None:
        self.limit = limit
        self.period = period
        self._clock = clock
        self._sleep = sleep
        self._limiters: dict[str, AsyncRateLimiter] = {}
        self._lock = asyncio.Lock()

    async def acquire(self, key: str) -> None:
        limiter = self._limiters.get(key)
        if limiter is None:
            async with self._lock:
                limiter = self._limiters.setdefault(
                    key,
                    AsyncRateLimiter(
                        self.limit,
                        self.period,
                        clock=self._clock,
                        sleep=self._sleep,
                    ),
                )
        await limiter.acquire()
