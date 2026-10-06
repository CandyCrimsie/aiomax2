from __future__ import annotations

from typing import Any


class Aiomax2Error(Exception):
    """Base exception for aiomax2."""


class ConfigurationError(Aiomax2Error):
    """The framework or client was configured incorrectly."""


class ClientError(Aiomax2Error):
    """An error occurred before a valid MAX API response was received."""


class NetworkError(ClientError):
    """A network or timeout error occurred."""


class ResponseDecodeError(ClientError):
    """MAX returned a response that could not be decoded as JSON."""

    def __init__(self, status: int, body: str) -> None:
        self.status = status
        self.body = body
        super().__init__(f"Could not decode MAX response (HTTP {status}): {body[:200]}")


class MaxAPIError(Aiomax2Error):
    """MAX returned a non-success HTTP response."""

    def __init__(
        self,
        status: int,
        message: str,
        *,
        payload: Any = None,
        retry_after: float | None = None,
    ) -> None:
        self.status = status
        self.message = message
        self.payload = payload
        self.retry_after = retry_after
        super().__init__(f"MAX API error {status}: {message}")


class BadRequestError(MaxAPIError):
    pass


class UnauthorizedError(MaxAPIError):
    pass


class ForbiddenError(MaxAPIError):
    pass


class NotFoundError(MaxAPIError):
    pass


class MethodNotAllowedError(MaxAPIError):
    pass


class RateLimitError(MaxAPIError):
    pass


class ServerError(MaxAPIError):
    pass


class ValidationError(Aiomax2Error):
    """A local framework-level validation failed."""


class BotNotBoundError(Aiomax2Error):
    """An object shortcut was called before the object was bound to a Bot."""


class RouterError(Aiomax2Error):
    pass


class UnsupportedUpdateError(Aiomax2Error):
    pass


class WebhookSecretError(Aiomax2Error):
    """A webhook request did not carry the configured MAX secret."""


class WebhookPayloadError(Aiomax2Error):
    """A webhook request body is not a valid MAX update."""


class SkipHandler(Aiomax2Error):
    """Skip the current handler and continue observer lookup."""
