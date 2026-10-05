from __future__ import annotations

import asyncio
import time

import pytest

from aiomax2.client import AsyncRateLimiter, KeyedRateLimiter


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


@pytest.mark.asyncio
async def test_sliding_window_releases_exact_boundary() -> None:
    now = 0.0

    def clock() -> float:
        return now

    async def unexpected_sleep(_: float) -> None:
        pytest.fail("the oldest entry must expire exactly at the boundary")

    limiter = AsyncRateLimiter(1, clock=clock, sleep=unexpected_sleep)
    await limiter.acquire()
    now = 1.0
    await limiter.acquire()


@pytest.mark.asyncio
async def test_concurrent_acquire_does_not_break_window() -> None:
    limiter = AsyncRateLimiter(2, period=0.03)
    acquired_at: list[float] = []

    async def worker() -> None:
        await limiter.acquire()
        acquired_at.append(time.monotonic())

    await asyncio.gather(*(worker() for _ in range(6)))

    assert len(acquired_at) == 6
    assert acquired_at[-1] - acquired_at[0] >= 0.05


@pytest.mark.asyncio
async def test_waiting_acquire_is_cancellation_safe() -> None:
    now = 0.0
    sleep_started = asyncio.Event()
    release_sleep = asyncio.Event()

    def clock() -> float:
        return now

    async def sleep(_: float) -> None:
        sleep_started.set()
        await release_sleep.wait()

    limiter = AsyncRateLimiter(1, clock=clock, sleep=sleep)
    await limiter.acquire()
    waiting = asyncio.create_task(limiter.acquire())
    await sleep_started.wait()
    waiting.cancel()

    with pytest.raises(asyncio.CancelledError):
        await waiting

    now = 1.0
    await limiter.acquire()


@pytest.mark.asyncio
async def test_keyed_limiter_enforces_two_operations_for_one_target() -> None:
    limiter = KeyedRateLimiter(2, period=0.03)
    started = time.monotonic()

    await asyncio.gather(*(limiter.acquire("chat:1") for _ in range(3)))

    assert time.monotonic() - started >= 0.025


@pytest.mark.asyncio
async def test_keyed_limiter_keeps_chat_windows_independent() -> None:
    limiter = KeyedRateLimiter(2, period=0.03)

    await asyncio.gather(
        limiter.acquire("chat:A"),
        limiter.acquire("chat:A"),
        limiter.acquire("chat:B"),
        limiter.acquire("chat:B"),
    )
    completion_order: list[str] = []

    async def acquire(key: str) -> None:
        await limiter.acquire(key)
        completion_order.append(key)

    await asyncio.gather(acquire("chat:A"), acquire("chat:C"))

    assert completion_order[0] == "chat:C"
    assert completion_order[1] == "chat:A"
