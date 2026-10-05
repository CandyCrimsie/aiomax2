from __future__ import annotations

from collections.abc import AsyncIterator

import aiohttp
import pytest
import pytest_asyncio
from aiohttp import web

from aiomax2.client import AiohttpSession
from aiomax2.exceptions import UnauthorizedError


@pytest_asyncio.fixture
async def api_server() -> AsyncIterator[tuple[str, dict[str, int]]]:
    state = {"limited": 0, "connections": 0}

    async def me(request: web.Request) -> web.Response:
        assert request.headers["Authorization"] == "token"
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

    async def unauthorized(_: web.Request) -> web.Response:
        return web.json_response({"message": "bad token"}, status=401)

    async def upload(request: web.Request) -> web.Response:
        reader = await request.multipart()
        field = await reader.next()
        assert field is not None and field.name == "data"
        state["uploaded_bytes"] = len(await field.read())
        return web.json_response({"photos": {"photoIds": {"token": "image-token"}}})

    app = web.Application()
    app.router.add_get("/me", me)
    app.router.add_get("/limited", limited)
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
    external = aiohttp.ClientSession(headers={"Authorization": "token"})
    transport = AiohttpSession("token", base_url=base_url, session=external)
    await transport.request("GET", "/me")
    await transport.close()

    assert not external.closed
    await external.close()


@pytest.mark.asyncio
async def test_multipart_upload_reuses_verified_session(
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
