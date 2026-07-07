"""Typed exceptions for the DutyBeat client.

Every error carries the machine-readable ``code`` and human ``message`` from the API's error envelope
(``{"error": {"code", "message"}}``) when available, so callers can branch on ``err.code``.
"""

from __future__ import annotations

from typing import Optional


class DutyBeatError(Exception):
    """Base class for all client errors."""

    def __init__(self, message: str, *, status: Optional[int] = None, code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code


class AuthenticationError(DutyBeatError):
    """401 — the API key is missing, malformed, revoked or expired."""


class ForbiddenError(DutyBeatError):
    """403 — the key does not have the required method enabled.

    Named ``ForbiddenError`` (not ``PermissionError``) so it does not shadow the built-in.
    """


class NotFoundError(DutyBeatError):
    """404 — the resource does not exist (or belongs to another tenant)."""


class RateLimitError(DutyBeatError):
    """429 — too many requests. ``retry_after`` is seconds to wait, when the API provided it."""

    def __init__(self, message: str, *, status: Optional[int] = None, code: Optional[str] = None,
                 retry_after: Optional[float] = None):
        super().__init__(message, status=status, code=code)
        self.retry_after = retry_after


class APIError(DutyBeatError):
    """Any other non-2xx response (4xx not covered above, or 5xx)."""
