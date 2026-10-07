from __future__ import annotations

import asyncio
import ssl
import warnings
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import Mock

import aiohttp
import pytest
import pytest_asyncio
from aiohttp import web

from aiomax2 import Bot, InsecureTLSWarning
from aiomax2.client import AiohttpSession, AsyncRateLimiter
from aiomax2.exceptions import RateLimitError, RequestTimeoutError, UnauthorizedError


class StubResponse:
    status = 200

    def __init__(self) -> None:
        self.headers: dict[str, str] = {}

    async def read(self) -> bytes:
        return b'{"success": true}'


class StubRequestContext:
    async def __aenter__(self) -> StubResponse:
        return StubResponse()

    async def __aexit__(self, *_: object) -> None:
        return None


def test_insecure_custom_ssl_context_is_rejected() -> None:
    insecure_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    insecure_context.check_hostname = False
    insecure_context.verify_mode = ssl.CERT_NONE

    with pytest.raises(ValueError, match="must verify certificates"):
        AiohttpSession("token", ssl_context=insecure_context)


def test_bot_uses_secure_context_by_default() -> None:
    bot = Bot("token")
    context = bot.transport._ssl_context

    assert context.check_hostname is True
    assert context.verify_mode == ssl.CERT_REQUIRED


def test_ca_file_is_loaded_into_default_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = Mock(spec=ssl.SSLContext)
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    monkeypatch.setattr(ssl, "create_default_context", lambda: context)

    transport = AiohttpSession("token", ca_file="max-ca.pem")

    assert transport._ssl_context is context
    context.load_verify_locations.assert_called_once_with(cafile="max-ca.pem")


def test_verify_ssl_false_builds_unverified_context_and_warns_once() -> None:
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        bot = Bot("token", verify_ssl=False)

    context = bot.transport._ssl_context
    insecure_warnings = [
        item for item in captured if item.category is InsecureTLSWarning
    ]
    assert context.check_hostname is False
    assert context.verify_mode == ssl.CERT_NONE
    assert len(insecure_warnings) == 1


@pytest.mark.parametrize(
    "kwargs",
    [
        {"verify_ssl": False, "ca_file": "max-ca.pem"},
        {"verify_ssl": False, "ssl_context": ssl.create_default_context()},
    ],
)
def test_verify_ssl_false_rejects_other_tls_configuration(
    kwargs: dict[str, Any],
) -> None:
    with pytest.raises(ValueError, match="cannot be combined"):
        AiohttpSession("token", **kwargs)


def test_ca_file_and_ssl_context_remain_mutually_exclusive() -> None:
    with pytest.raises(ValueError, match="either ssl_context or ca_file"):
        AiohttpSession(
            "token",
            ca_file="max-ca.pem",
            ssl_context=ssl.create_default_context(),
        )


@pytest.mark.asyncio
async def test_insecure_context_is_reused_for_api_and_upload_without_new_warnings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def request_spy(
        _: aiohttp.ClientSession,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> StubRequestContext:
        captured.update(api_method=method, api_url=url, api_ssl=kwargs["ssl"])
        return StubRequestContext()

    def post_spy(
        _: aiohttp.ClientSession,
        url: str,
        **kwargs: Any,
    ) -> StubRequestContext:
        captured.update(upload_url=url, upload_ssl=kwargs["ssl"])
        return StubRequestContext()

    monkeypatch.setattr(aiohttp.ClientSession, "request", request_spy)
    monkeypatch.setattr(aiohttp.ClientSession, "post", post_spy)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        transport = AiohttpSession("token", verify_ssl=False)
        await transport.request("GET", "/me")
        await transport.upload(
            "https://uploads.example.test/media",
            b"file data",
            filename="file.bin",
        )

    try:
        insecure_warnings = [
            item for item in caught if item.category is InsecureTLSWarning
        ]
        assert len(insecure_warnings) == 1
        assert captured["api_ssl"] is transport._ssl_context
        assert captured["upload_ssl"] is transport._ssl_context
        assert transport._ssl_context.verify_mode == ssl.CERT_NONE
    finally:
        await transport.close()


@pytest_asyncio.fixture
async def api_server() -> AsyncIterator[tuple[str, dict[str, int]]]:
    state = {
        "limited": 0,
        "limited_many": 0,
        "limited_always": 0,
        "connections": 0,
        "concurrent": 0,
    }

    async def me(request: web.Request) -> web.Response:
        assert request.headers["Authorization"] == "token"
        state["client_header"] = int(request.headers.get("X-Client") == "custom")
        state["request_header"] = int(request.headers.get("X-Request") == "value")
        state["connections"] += 1
        return web.json_response({"user_id": 1, "first_name": "Bot", "is_bot": True})

    async def limited(_: web.Request) -> web.Response:
        state["limited"] += 1
        if state["limited"] == 1:
            return web.json_response(
                {"message": "slow down"},
                status=429,
                headers={"Retry-After": "0"},
            )
        return web.json_response({"success": True})

    async def limited_many(_: web.Request) -> web.Response:
        state["limited_many"] += 1
        if state["limited_many"] <= 2:
            return web.json_response(
                {"message": "slow down again"},
                status=429,
                headers={"Retry-After": "0.01"},
            )
        return web.json_response({"success": True})

    async def limited_always(_: web.Request) -> web.Response:
        state["limited_always"] += 1
        return web.json_response(
            {"message": "still limited"},
            status=429,
            headers={"Retry-After": "0"},
        )

    async def concurrent(_: web.Request) -> web.Response:
        state["concurrent"] += 1
        await asyncio.sleep(0)
        return web.json_response({"success": True})

    async def unauthorized(_: web.Request) -> web.Response:
        return web.json_response({"message": "bad token"}, status=401)

    async def upload(request: web.Request) -> web.Response:
        state["upload_authorized"] = int("Authorization" in request.headers)
        reader = await request.multipart()
        field = await reader.next()
        assert field is not None and field.name == "data"
        state["uploaded_bytes"] = len(await field.read())
        return web.json_response({"photos": {"photoIds": {"token": "image-token"}}})

    app = web.Application()
    app.router.add_get("/me", me)
    app.router.add_get("/limited", limited)
    app.router.add_get("/limited-many", limited_many)
    app.router.add_get("/limited-always", limited_always)
    app.router.add_get("/concurrent", concurrent)
    app.router.add_get("/unauthorized", unauthorized)
    app.router.add_post("/upload", upload)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    sockets = site._server.sockets  # type: ignore[union-attr]
    port = sockets[0].getsockname()[1]
    try:
        yield f"http://127.0.0.1:{port}", state
    finally:
        await runner.cleanup()


@pytest.mark.asyncio
async def test_transport_reuses_session_and_retries_429(
    api_server: tuple[str, dict[str, int]],
) -> None:
    base_url, state = api_server
    transport = AiohttpSession("token", base_url=base_url, max_retries=1, rate_limit=30)

    await transport.request("GET", "/me")
    first_session = transport.session
    result = await transport.request("GET", "/limited")

    assert result == {"success": True}
    assert state["limited"] == 2
    assert transport.session is first_session
    await transport.close()
    assert first_session is not None and first_session.closed


@pytest.mark.asyncio
async def test_transport_maps_api_errors(
    api_server: tuple[str, dict[str, int]],
) -> None:
    base_url, _ = api_server
    async with AiohttpSession("token", base_url=base_url) as transport:
        with pytest.raises(UnauthorizedError) as error:
            await transport.request("GET", "/unauthorized")

    assert error.value.status == 401
    assert error.value.message == "bad token"


@pytest.mark.asyncio
async def test_external_session_is_not_closed(
    api_server: tuple[str, dict[str, int]],
) -> None:
    base_url, _ = api_server
    external = aiohttp.ClientSession()
    transport = AiohttpSession("token", base_url=base_url, session=external)
    await transport.request("GET", "/me")
    await transport.close()

    assert not external.closed
    await external.close()


@pytest.mark.asyncio
async def test_custom_session_without_authorization_receives_library_header(
    api_server: tuple[str, dict[str, int]],
) -> None:
    base_url, state = api_server
    external = aiohttp.ClientSession(headers={"X-Client": "custom"})
    transport = AiohttpSession("token", base_url=base_url, session=external)

    await transport.request(
        "GET",
        "/me",
        headers={"Authorization": "must-not-win", "X-Request": "value"},
    )
    await transport.close()

    assert state["client_header"] == 1
    assert state["request_header"] == 1
    assert not external.closed
    await external.close()


@pytest.mark.asyncio
async def test_custom_session_with_ssl_disabled_gets_library_ssl_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def request_spy(
        _: aiohttp.ClientSession,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> StubRequestContext:
        captured.update(method=method, url=url, **kwargs)
        return StubRequestContext()

    monkeypatch.setattr(aiohttp.ClientSession, "request", request_spy)
    secure_context = ssl.create_default_context()
    external = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False))
    transport = AiohttpSession(
        "token",
        session=external,
        ssl_context=secure_context,
    )

    try:
        result = await transport.request("GET", "/me")
        await transport.close()

        assert result == {"success": True}
        assert captured["url"] == "https://platform-api2.max.ru/me"
        assert captured["ssl"] is secure_context
        assert secure_context.check_hostname
        assert secure_context.verify_mode == ssl.CERT_REQUIRED
        assert captured["headers"]["Authorization"] == "token"
        assert not external.closed
    finally:
        await external.close()


@pytest.mark.asyncio
async def test_multiple_429_responses_honor_retry_after(
    api_server: tuple[str, dict[str, int]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base_url, state = api_server
    transport = AiohttpSession("token", base_url=base_url, max_retries=2)
    delays: list[float] = []
    original_sleep = asyncio.sleep

    async def record_sleep(delay: float) -> None:
        delays.append(delay)
        await original_sleep(0)

    monkeypatch.setattr("aiomax2.client.session.asyncio.sleep", record_sleep)

    result = await transport.request("GET", "/limited-many")

    assert result == {"success": True}
    assert state["limited_many"] == 3
    assert delays == [0.01, 0.01]
    await transport.close()


@pytest.mark.asyncio
async def test_repeated_429_raises_after_retry_budget_is_exhausted(
    api_server: tuple[str, dict[str, int]],
) -> None:
    base_url, state = api_server
    transport = AiohttpSession("token", base_url=base_url, max_retries=1)

    with pytest.raises(RateLimitError) as error:
        await transport.request("GET", "/limited-always")

    assert state["limited_always"] == 2
    assert error.value.status == 429
    assert error.value.retry_after == 0.0
    await transport.close()


@pytest.mark.asyncio
async def test_thirty_concurrent_api_requests_share_global_limiter(
    api_server: tuple[str, dict[str, int]],
) -> None:
    base_url, state = api_server
    transport = AiohttpSession("token", base_url=base_url, rate_limit=30)
    now = 0.0
    delays: list[float] = []

    def clock() -> float:
        return now

    async def sleep(delay: float) -> None:
        nonlocal now
        delays.append(delay)
        now += delay

    transport.rate_limiter = AsyncRateLimiter(
        30,
        period=0.05,
        clock=clock,
        sleep=sleep,
    )

    await asyncio.gather(*(transport.request("GET", "/concurrent") for _ in range(31)))

    assert state["concurrent"] == 31
    assert delays == [0.05]
    await transport.close()


@pytest.mark.asyncio
async def test_multipart_upload_uses_verified_session_without_api_token(
    api_server: tuple[str, dict[str, int]],
) -> None:
    base_url, state = api_server
    async with AiohttpSession("token", base_url=base_url) as transport:
        result = await transport.upload(
            f"{base_url}/upload",
            b"image data",
            filename="image.png",
            content_type="image/png",
        )

    assert result == {"photos": {"photoIds": {"token": "image-token"}}}
    assert state["uploaded_bytes"] == len(b"image data")
    assert state["upload_authorized"] == 0


@pytest.mark.asyncio
async def test_external_upload_does_not_leak_custom_session_authorization(
    api_server: tuple[str, dict[str, int]],
) -> None:
    base_url, state = api_server
    external = aiohttp.ClientSession(headers={"Authorization": "private"})
    transport = AiohttpSession("token", base_url=base_url, session=external)

    await transport.upload(
        f"{base_url}/upload",
        b"image data",
        filename="image.png",
    )
    await transport.close()

    assert state["upload_authorized"] == 0
    assert not external.closed
    await external.close()


@pytest.mark.asyncio
async def test_upload_authorization_is_explicit_when_protocol_requires_it(
    api_server: tuple[str, dict[str, int]],
) -> None:
    base_url, state = api_server
    transport = AiohttpSession("token", base_url=base_url)

    await transport.upload(
        f"{base_url}/upload",
        b"image data",
        filename="image.png",
        authorization=True,
    )
    await transport.close()

    assert state["upload_authorized"] == 1


@pytest.mark.asyncio
async def test_external_upload_request_uses_library_ssl_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def post_spy(
        _: aiohttp.ClientSession,
        url: str,
        **kwargs: Any,
    ) -> StubRequestContext:
        captured.update(url=url, **kwargs)
        return StubRequestContext()

    monkeypatch.setattr(aiohttp.ClientSession, "post", post_spy)
    secure_context = ssl.create_default_context()
    transport = AiohttpSession("token", ssl_context=secure_context)

    try:
        result = await transport.upload(
            "https://uploads.example.test/media",
            b"file data",
            filename="file.bin",
        )

        assert result == {"success": True}
        assert captured["ssl"] is secure_context
        assert captured["headers"] is None
    finally:
        await transport.close()


@pytest.mark.asyncio
async def test_api_timeout_has_specific_backward_compatible_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def timeout_request(*_: Any, **__: Any) -> StubRequestContext:
        raise TimeoutError("deadline exceeded")

    monkeypatch.setattr(aiohttp.ClientSession, "request", timeout_request)
    transport = AiohttpSession("token", max_retries=0)

    try:
        with pytest.raises(RequestTimeoutError) as error:
            await transport.request("GET", "/me")
        assert "timed out" in str(error.value)
    finally:
        await transport.close()


@pytest.mark.asyncio
async def test_upload_timeout_has_specific_backward_compatible_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def timeout_post(*_: Any, **__: Any) -> StubRequestContext:
        raise TimeoutError("deadline exceeded")

    monkeypatch.setattr(aiohttp.ClientSession, "post", timeout_post)
    transport = AiohttpSession("token")

    try:
        with pytest.raises(RequestTimeoutError) as error:
            await transport.upload(
                "https://uploads.example.test/media",
                b"file",
                filename="file.bin",
            )
        assert "timed out" in str(error.value)
    finally:
        await transport.close()
