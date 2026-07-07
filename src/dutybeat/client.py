"""The DutyBeat public API client."""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

import httpx

from .errors import (
    APIError,
    AuthenticationError,
    DutyBeatError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
)
from .models import User

DEFAULT_BASE_URL = "https://api.dutybeat.com"
_RETRYABLE = {429, 500, 502, 503, 504}


def _parse_retry_after(response: httpx.Response) -> Optional[float]:
    value = response.headers.get("retry-after")
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _raise_for_status(response: httpx.Response) -> None:
    """Map a non-2xx response to a typed error, reading the API's error envelope when present."""
    code: Optional[str] = None
    message = f"HTTP {response.status_code}"
    try:
        body = response.json()
        err = body.get("error") if isinstance(body, dict) else None
        if isinstance(err, dict):
            code = err.get("code")
            message = err.get("message") or message
    except Exception:  # noqa: BLE001 - a non-JSON error body must not mask the HTTP error
        pass

    status = response.status_code
    if status == 401:
        raise AuthenticationError(message, status=status, code=code)
    if status == 403:
        raise ForbiddenError(message, status=status, code=code)
    if status == 404:
        raise NotFoundError(message, status=status, code=code)
    if status == 429:
        raise RateLimitError(message, status=status, code=code, retry_after=_parse_retry_after(response))
    raise APIError(message, status=status, code=code)


class _Users:
    """The ``users`` resource."""

    def __init__(self, client: "DutyBeat"):
        self._client = client

    def get(self, user_id: str, *, include_folders: bool = False) -> User:
        """``GET /api/v1/users/:user_id`` — fetch a user's full record.

        Set ``include_folders=True`` to also receive the employee's document folders (metadata only).
        """
        params: Dict[str, str] = {}
        if include_folders:
            params["include_folders"] = "true"
        body = self._client._request("GET", f"/api/v1/users/{user_id}", params=params)
        return User.from_dict(body["data"])


class DutyBeat:
    """Client for the DutyBeat public API.

    Example::

        from dutybeat import DutyBeat

        client = DutyBeat(api_key="db_live_...")        # or env DUTYBEAT_API_KEY
        user = client.users.get("9f1c...", include_folders=True)
        print(user.full_name, user.profile.iban)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        max_retries: int = 2,
    ):
        key = api_key or os.environ.get("DUTYBEAT_API_KEY")
        if not key:
            raise DutyBeatError(
                "An API key is required: pass api_key=... or set the DUTYBEAT_API_KEY environment variable."
            )
        self._base_url = base_url.rstrip("/")
        self._max_retries = max_retries
        self._client = httpx.Client(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {key}",
                "Accept": "application/json",
                "User-Agent": "dutybeat-python",
            },
        )
        self.users = _Users(self)

    # -- lifecycle -------------------------------------------------------------------------------

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "DutyBeat":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # -- transport -------------------------------------------------------------------------------

    def _request(self, method: str, path: str, *, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        url = self._base_url + path
        for attempt in range(self._max_retries + 1):
            response = self._client.request(method, url, params=params)
            if response.status_code < 400:
                return response.json()
            if response.status_code in _RETRYABLE and attempt < self._max_retries:
                retry_after = _parse_retry_after(response)
                delay = retry_after if retry_after is not None else min(2 ** attempt, 8)
                time.sleep(delay)
                continue
            _raise_for_status(response)
        # Unreachable: the loop either returns or raises.
        raise APIError("Request failed after retries")
