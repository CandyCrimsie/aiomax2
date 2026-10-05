from __future__ import annotations

import asyncio
import json as json_module
import random
import ssl
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import aiohttp

from aiomax2.exceptions import (
    BadRequestError,
    ForbiddenError,
    MaxAPIError,
    MethodNotAllowedError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ResponseDecodeError,
    ServerError,
    UnauthorizedError,
)

from .rate_limiter import AsyncRateLimiter

DEFAULT_API_URL = "https://platform-api2.max.ru"
IDEMPOTENT_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


class AiohttpSession:
    """Pooled asynchronous transport for the MAX Bot API."""

    def __init__(
        self,
        token: str,
        *,
        base_url: str = DEFAULT_API_URL,
        timeout: float = 30.0,
        max_retries: int = 3,
        rate_limit: int = 30,
        ssl_context: ssl.SSLContext | None = None,
        ca_file: str | Path | None = None,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        if not token:
            raise ValueError("token must not be empty")
        if ssl_context is not None and ca_file is not None:
            raise ValueError("pass either ssl_context or ca_file, not both")
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limiter = AsyncRateLimiter(rate_limit)
        self._provided_session = session
        self._session = session
        self._owns_session = session is None
        self._ssl_context = ssl_context or self._build_ssl_context(ca_file)

    @staticmethod
    def _build_ssl_context(ca_file: str | Path | None) -> ssl.SSLContext:
        # create_default_context always verifies the certificate and hostname.
        context = ssl.create_default_context()
        if ca_file is not None:
            context.load_verify_locations(cafile=str(ca_file))
        return context

    @property
    def session(self) -> aiohttp.ClientSession | None:
        return self._session

    async def open(self) -> aiohttp.ClientSession:
        if self._session is not None and not self._session.closed:
            return self._session
        connector = aiohttp.TCPConnector(ssl=self._ssl_context)
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={"Authorization": self.token},
        )
        self._owns_session = True
        return self._session

    async def close(self) -> None:
        if self._owns_session and self._session is not None:
            await self._session.close()
        self._session = self._provided_session

    async def __aenter__(self) -> AiohttpSession:
        await self.open()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        data: Any = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | aiohttp.ClientTimeout | None = None,
        retry_safe: bool | None = None,
    ) -> Any:
        session = await self.open()
        normalized_method = method.upper()
        can_retry = (
            normalized_method in IDEMPOTENT_METHODS
            if retry_safe is None
            else retry_safe
        )
        url = f"{self.base_url}/{path.lstrip('/')}"
        request_timeout: aiohttp.ClientTimeout | None
        if isinstance(timeout, (int, float)):
            request_timeout = aiohttp.ClientTimeout(total=float(timeout))
        else:
            request_timeout = timeout

        for attempt in range(self.max_retries + 1):
            await self.rate_limiter.acquire()
            try:
                async with session.request(
                    normalized_method,
                    url,
                    params=self._clean_params(params),
                    json=json,
                    data=data,
                    headers=headers,
                    timeout=request_timeout,
                ) as response:
                    raw = await response.read()
                    payload = self._decode_payload(response.status, raw)
                    if 200 <= response.status < 300:
                        return payload

                    retry_after = self._retry_after(response)
                    if response.status == 429 and attempt < self.max_retries:
                        await asyncio.sleep(
                            retry_after
                            if retry_after is not None
                            else self._backoff(attempt)
                        )
                        continue
                    if (
                        response.status >= 500
                        and can_retry
                        and attempt < self.max_retries
                    ):
                        await asyncio.sleep(self._backoff(attempt))
                        continue
                    raise self._api_error(
                        response.status, payload, retry_after=retry_after
                    )
            except (aiohttp.ClientError, TimeoutError) as exc:
                if can_retry and attempt < self.max_retries:
                    await asyncio.sleep(self._backoff(attempt))
                    continue
                raise NetworkError(
                    f"MAX request {normalized_method} {path!r} failed: {exc}"
                ) from exc
        raise AssertionError("retry loop exhausted without returning or raising")

    async def upload(
        self,
        url: str,
        file_data: Any,
        *,
        filename: str,
        content_type: str | None = None,
    ) -> Any:
        """Upload one file to a URL previously returned by `POST /uploads`.

        Upload URLs are single-use, so ambiguous failures are deliberately not
        retried. The pooled session and verified TLS connector are reused.
        """

        session = await self.open()
        form = aiohttp.FormData()
        form.add_field(
            "data",
            file_data,
            filename=filename,
            content_type=content_type or "application/octet-stream",
        )
        try:
            async with session.post(url, data=form) as response:
                raw = await response.read()
                if 200 <= response.status < 300:
                    return self._decode_upload_payload(raw)
                payload = self._decode_payload(response.status, raw)
                raise self._api_error(
                    response.status,
                    payload,
                    retry_after=self._retry_after(response),
                )
        except (aiohttp.ClientError, TimeoutError) as exc:
            raise NetworkError(f"MAX upload to {url!r} failed: {exc}") from exc

    @staticmethod
    def _clean_params(params: Mapping[str, Any] | None) -> dict[str, Any] | None:
        if params is None:
            return None
        cleaned: dict[str, Any] = {}
        for key, value in params.items():
            if value is None:
                continue
            if isinstance(value, (list, tuple, set, frozenset)):
                cleaned[key] = ",".join(str(item) for item in value)
            elif isinstance(value, bool):
                cleaned[key] = "true" if value else "false"
            else:
                cleaned[key] = value
        return cleaned

    @staticmethod
    def _decode_payload(status: int, raw: bytes) -> Any:
        if not raw:
            return None
        text = raw.decode("utf-8", errors="replace")
        try:
            return json_module.loads(text)
        except json_module.JSONDecodeError as exc:
            if 200 <= status < 300:
                raise ResponseDecodeError(status, text) from exc
            return {"message": text}

    @staticmethod
    def _decode_upload_payload(raw: bytes) -> Any:
        if not raw:
            return None
        text = raw.decode("utf-8", errors="replace")
        try:
            return json_module.loads(text)
        except json_module.JSONDecodeError:
            # Some MAX upload hosts return XML or plain text on success.
            return text

    @staticmethod
    def _retry_after(response: aiohttp.ClientResponse) -> float | None:
        value = response.headers.get("Retry-After")
        if value is None:
            return None
        try:
            return max(float(value), 0.0)
        except ValueError:
            return None

    @staticmethod
    def _backoff(attempt: int) -> float:
        return float(min(0.25 * (2**attempt) + random.uniform(0, 0.1), 5.0))

    @staticmethod
    def _api_error(
        status: int, payload: Any, *, retry_after: float | None
    ) -> MaxAPIError:
        if isinstance(payload, dict):
            message = str(
                payload.get("message")
                or payload.get("error")
                or payload.get("code")
                or payload
            )
        else:
            message = str(payload)
        error_type: type[MaxAPIError]
        error_type = {
            400: BadRequestError,
            401: UnauthorizedError,
            403: ForbiddenError,
            404: NotFoundError,
            405: MethodNotAllowedError,
            429: RateLimitError,
        }.get(status, ServerError if status >= 500 else MaxAPIError)
        return error_type(status, message, payload=payload, retry_after=retry_after)
