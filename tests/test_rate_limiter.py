from __future__ import annotations

import pytest

from aiomax2.client import AsyncRateLimiter


@pytest.mark.asyncio
async def test_sliding_window_waits_when_full() -> None:
    now = 0.0
    sleeps: list[float] = []

    def clock() -> float:
        return now

    async def sleep(delay: float) -> None:
        nonlocal now
        sleeps.append(delay)
        now += delay

    limiter = AsyncRateLimiter(2, clock=clock, sleep=sleep)
    await limiter.acquire()
    await limiter.acquire()
    await limiter.acquire()

    assert sleeps == [1.0]
