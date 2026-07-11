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
from .models import (
    Absence,
    AbsencePage,
    AbsenceTypePage,
    AttendancePage,
    AttendanceSummaryPage,
    DepartmentPage,
    Expense,
    ExpensePage,
    HolidayPage,
    Identity,
    User,
    UserPage,
    WorkCenterPage,
)

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
        """Fetch a user's full record — ``GET /api/v1/users/:user_id``.

        Args:
            user_id: The user's id within your company.
            include_folders: If ``True``, also include the employee's document folders
                (metadata only: id, name and document count).

        Returns:
            User: The user's account and profile data (see the ``User`` model).

        Raises:
            NotFoundError: If the user does not exist or belongs to another company.
            ForbiddenError: If the API key does not have the ``users.get`` method enabled.
            AuthenticationError: If the API key is missing or invalid.
        """
        params: Dict[str, str] = {}
        if include_folders:
            params["include_folders"] = "true"
        body = self._client._request("GET", f"/api/v1/users/{user_id}", params=params)
        return User.from_dict(body["data"])

    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 25,
        detail: str = "reduced",
        status: Optional[str] = None,
        role: Optional[str] = None,
        department_id: Optional[str] = None,
        work_center_id: Optional[str] = None,
        email: Optional[str] = None,
        q: Optional[str] = None,
    ) -> UserPage:
        """List users — ``GET /api/v1/users``.

        Returns a page of users (25 per page by default, max 100). Combine the filters to narrow the
        result; iterate ``page=1, 2, …`` until you've seen ``UserPage.total`` users.

        Args:
            page: Page to fetch, 1-based.
            page_size: Users per page (default 25, max 100).
            detail: ``"reduced"`` (default; basic fields) or ``"full"`` (complete record with profile).
            status: Filter by status: ``"active"`` or ``"disabled"``.
            role: Filter by role: ``"member"`` or ``"admin"``.
            department_id: Filter by department id.
            work_center_id: Filter by work center id.
            email: Resolve an exact email (case-insensitive) to its user — at most one result. Use it to
                map your own external identifier (the email) to our id.
            q: Search by full name or email (substring). For an exact email, use ``email``.

        Returns:
            UserPage: The page of users (``.items``) plus ``.page``, ``.page_size`` and ``.total``.

        Raises:
            ForbiddenError: If the API key does not have the ``users.list`` method enabled.
            AuthenticationError: If the API key is missing or invalid.
        """
        params: Dict[str, Any] = {"page": page, "page_size": page_size, "detail": detail}
        if status is not None:
            params["status"] = status
        if role is not None:
            params["role"] = role
        if department_id is not None:
            params["department_id"] = department_id
        if work_center_id is not None:
            params["work_center_id"] = work_center_id
        if email is not None:
            params["email"] = email
        if q is not None:
            params["q"] = q
        body = self._client._request("GET", "/api/v1/users", params=params)
        return UserPage.from_response(body)

    def create(
        self,
        *,
        email: str,
        full_name: str,
        password: Optional[str] = None,
        role: Optional[str] = None,
        department_id: Optional[str] = None,
        work_center_id: Optional[str] = None,
        hire_date: Optional[str] = None,
        vacation_days: Optional[int] = None,
        works_holidays: Optional[bool] = None,
        remote_work_allowed: Optional[bool] = None,
        dni: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> User:
        """Create an employee — ``POST /api/v1/users``.

        Only ``email`` and ``full_name`` are required. ``password`` is optional: omit it and the
        employee sets their own via "forgot password"; if given it must be at least 8 characters.
        Creating a ``role="admin"`` user requires the key to act as an administrator.

        Args:
            email: Login email (must be unique).
            full_name: The employee's full name.
            password: Optional initial password (min. 8 chars).
            role: ``"member"`` (default) or ``"admin"``.
            department_id: Department id the employee belongs to.
            work_center_id: Work center (sede) id.
            hire_date: Hire date, ``YYYY-MM-DD``.
            vacation_days: Annual vacation days (defaults to the company's).
            works_holidays: Whether they work on public holidays.
            remote_work_allowed: Whether they may clock in remotely.
            dni: DNI/NIE — the kiosk identifier is derived from its digits.
            phone: Phone — the initial kiosk PIN is derived from its last 4 digits.

        Returns:
            User: The created user (same shape as :meth:`get`).

        Raises:
            ForbiddenError: If the key lacks the ``users.create`` method or the actor can't create users.
            APIError: 400 on a malformed body, 409 if the email is already in use.
            AuthenticationError: If the API key is missing or invalid.
        """
        payload: Dict[str, Any] = {"email": email, "full_name": full_name}
        for key, value in (
            ("password", password),
            ("role", role),
            ("department_id", department_id),
            ("work_center_id", work_center_id),
            ("hire_date", hire_date),
            ("vacation_days", vacation_days),
            ("works_holidays", works_holidays),
            ("remote_work_allowed", remote_work_allowed),
            ("dni", dni),
            ("phone", phone),
        ):
            if value is not None:
                payload[key] = value
        body = self._client._request("POST", "/api/v1/users", json_body=payload)
        return User.from_dict(body["data"])

    def update(
        self,
        user_id: str,
        *,
        full_name: Optional[str] = None,
        role: Optional[str] = None,
        department_id: Optional[str] = None,
        work_center_id: Optional[str] = None,
        hire_date: Optional[str] = None,
        vacation_days: Optional[int] = None,
        works_holidays: Optional[bool] = None,
        remote_work_allowed: Optional[bool] = None,
        **profile_fields: Any,
    ) -> User:
        """Update an employee — ``PATCH /api/v1/users/:user_id`` (partial).

        Only the fields you pass are changed; anything omitted is kept. Account fields are keyword
        arguments; any profile column (``dni``, ``iban``, ``ssn``, ``address``, ``city``, …) can be
        passed via ``**profile_fields``. Changing ``role`` to ``"admin"`` requires the key to act as an
        administrator. Email and status are not editable here.

        Note: to clear a field you must send an explicit ``null`` — this SDK omits ``None`` values
        (they mean "leave unchanged"), so use the HTTP API directly for a deliberate clear.

        Args:
            user_id: The user's id within your company.
            full_name, role, department_id, work_center_id, hire_date, vacation_days, works_holidays,
                remote_work_allowed: Account fields (all optional).
            **profile_fields: Any profile column to set.

        Returns:
            User: The updated user.

        Raises:
            NotFoundError: If the user does not exist or belongs to another company.
            ForbiddenError: If the key lacks ``users.update`` or the actor can't edit / can't grant admin.
            APIError: 400 on an invalid field.
            AuthenticationError: If the API key is missing or invalid.
        """
        payload: Dict[str, Any] = {}
        for key, value in (
            ("full_name", full_name),
            ("role", role),
            ("department_id", department_id),
            ("work_center_id", work_center_id),
            ("hire_date", hire_date),
            ("vacation_days", vacation_days),
            ("works_holidays", works_holidays),
            ("remote_work_allowed", remote_work_allowed),
        ):
            if value is not None:
                payload[key] = value
        for key, value in profile_fields.items():
            if value is not None:
                payload[key] = value
        body = self._client._request("PATCH", f"/api/v1/users/{user_id}", json_body=payload)
        return User.from_dict(body["data"])

    def deactivate(self, user_id: str) -> User:
        """Deactivate an employee (offboarding) — ``POST /api/v1/users/:user_id/deactivate``.

        The employee can no longer sign in and their sessions are revoked immediately. Idempotent:
        deactivating an already-disabled user also returns 200. The last active admin can't be
        deactivated.

        Args:
            user_id: The user's id within your company.

        Returns:
            User: The user, now with ``status == "disabled"``.

        Raises:
            NotFoundError: If the user does not exist or belongs to another company.
            ForbiddenError: If the key lacks the ``users.deactivate`` method or the actor can't do it.
            APIError: 409 if the user is the last active admin.
            AuthenticationError: If the API key is missing or invalid.
        """
        body = self._client._request("POST", f"/api/v1/users/{user_id}/deactivate")
        return User.from_dict(body["data"])


class _Attendance:
    """The ``attendance`` resource."""

    def __init__(self, client: "DutyBeat"):
        self._client = client

    def list(
        self,
        user_id: str,
        *,
        from_: str,
        to: str,
        tz: Optional[str] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> AttendancePage:
        """List an employee's workdays — ``GET /api/v1/attendance``.

        One entry per calendar day of ``[from_, to]`` (both inclusive), with the day's marks, the
        minutes actually worked (pauses discounted) and the balance against their schedule.

        Args:
            user_id: The employee's id within your company.
            from_: First day of the range, ``YYYY-MM-DD``. Trailing underscore because ``from`` is a
                reserved word in Python.
            to: Last day of the range, ``YYYY-MM-DD``. Inclusive. The range cannot exceed 366 days.
            tz: IANA time zone used to bucket marks into days (default ``Europe/Madrid``).
            page: 1-based page number.
            page_size: Days per page (max 100).

        Returns:
            AttendancePage: The days on this page, plus ``total`` across the range.

        Raises:
            NotFoundError: If the employee does not exist or belongs to another company.
            ForbiddenError: If the API key does not have the ``attendance.list`` method enabled.
            AuthenticationError: If the API key is missing or invalid.
            APIError: If the range is invalid (bad dates, ``from_`` after ``to``, over 366 days) or
                the time zone is not recognised.
        """
        params: Dict[str, Any] = {
            "user_id": user_id,
            "from": from_,
            "to": to,
            "page": page,
            "page_size": page_size,
        }
        if tz is not None:
            params["tz"] = tz
        body = self._client._request("GET", "/api/v1/attendance", params=params)
        return AttendancePage.from_response(body)

    def summary(
        self,
        *,
        from_: str,
        to: str,
        tz: Optional[str] = None,
        status: Optional[str] = None,
        department_id: Optional[str] = None,
        work_center_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> AttendanceSummaryPage:
        """Company-wide attendance totals — ``GET /api/v1/attendance/summary``.

        One row per employee with their consolidated totals over ``[from_, to]``: minutes worked,
        expected and the balance, plus days. This is the payroll query ("hours per employee this
        month"); the page bounds how many employees are computed per request.

        Args:
            from_: First day of the range, ``YYYY-MM-DD``. Trailing underscore because ``from`` is a
                reserved word in Python.
            to: Last day of the range, ``YYYY-MM-DD``. Inclusive. The range cannot exceed 366 days.
            tz: IANA time zone used to bucket marks into days (default ``Europe/Madrid``).
            status: Filter employees by status: ``"active"`` or ``"disabled"``.
            department_id: Filter employees by department id.
            work_center_id: Filter employees by work center id.
            page: 1-based page number (paginates over employees).
            page_size: Employees per page (max 100).

        Returns:
            AttendanceSummaryPage: The employees on this page, plus ``total`` across the filters.

        Raises:
            ForbiddenError: If the API key does not have the ``attendance.summary`` method enabled.
            AuthenticationError: If the API key is missing or invalid.
            APIError: If the range is invalid, the time zone is not recognised or the status is invalid.
        """
        params: Dict[str, Any] = {"from": from_, "to": to, "page": page, "page_size": page_size}
        if tz is not None:
            params["tz"] = tz
        if status is not None:
            params["status"] = status
        if department_id is not None:
            params["department_id"] = department_id
        if work_center_id is not None:
            params["work_center_id"] = work_center_id
        body = self._client._request("GET", "/api/v1/attendance/summary", params=params)
        return AttendanceSummaryPage.from_response(body)


class _Absences:
    """The ``absences`` resource."""

    def __init__(self, client: "DutyBeat"):
        self._client = client

    def get(self, absence_id: str) -> Absence:
        """Fetch a single absence — ``GET /api/v1/absences/:absence_id``.

        Args:
            absence_id: The absence's id within your company.

        Returns:
            Absence: The absence, with its type (key + label), status, dates and — for hourly
            absences — the time slice.

        Raises:
            NotFoundError: If the absence does not exist or belongs to another company.
            ForbiddenError: If the API key does not have the ``absences.get`` method enabled.
            AuthenticationError: If the API key is missing or invalid.
        """
        body = self._client._request("GET", f"/api/v1/absences/{absence_id}")
        return Absence.from_dict(body["data"])

    def list(
        self,
        *,
        from_: str,
        to: str,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        type: Optional[str] = None,  # noqa: A002 - mirrors the API's query parameter name
        page: int = 1,
        page_size: int = 25,
    ) -> AbsencePage:
        """List absences overlapping a date range — ``GET /api/v1/absences``.

        Returns every absence that overlaps ``[from_, to]`` (both inclusive), newest first — including
        those that start before the window or end after it.

        Args:
            from_: First day of the range, ``YYYY-MM-DD``. Trailing underscore because ``from`` is a
                reserved word in Python.
            to: Last day of the range, ``YYYY-MM-DD``. Inclusive. The range cannot exceed 366 days.
            user_id: Only this employee's absences. Omit for the whole company.
            status: Filter by ``"pending"``, ``"approved"``, ``"rejected"`` or ``"cancelled"``.
            type: Filter by absence type key (e.g. ``"vacation"``, ``"sick"``). The catalogue is
                per-company; an unknown key simply matches nothing.
            page: 1-based page number.
            page_size: Absences per page (max 100).

        Returns:
            AbsencePage: The absences on this page (``.items``) plus ``.total`` across the range.

        Raises:
            NotFoundError: If ``user_id`` does not exist or belongs to another company.
            ForbiddenError: If the API key does not have the ``absences.list`` method enabled.
            AuthenticationError: If the API key is missing or invalid.
            APIError: If the range or the status is invalid.
        """
        params: Dict[str, Any] = {"from": from_, "to": to, "page": page, "page_size": page_size}
        if user_id is not None:
            params["user_id"] = user_id
        if status is not None:
            params["status"] = status
        if type is not None:
            params["type"] = type
        body = self._client._request("GET", "/api/v1/absences", params=params)
        return AbsencePage.from_response(body)


class _AbsenceTypes:
    """The ``absence_types`` resource."""

    def __init__(self, client: "DutyBeat"):
        self._client = client

    def list(self, *, page: int = 1, page_size: int = 25) -> AbsenceTypePage:
        """List absence types — ``GET /api/v1/absence-types``.

        Returns the company's absence-type catalogue: the `key` that :attr:`Absence.type` references,
        plus the attributes (paid, consumes_vacation, requires_approval, …) you need to interpret an
        absence. Includes retired types (``active=False``) so a historical ``type.key`` always resolves.

        Args:
            page: Page to fetch, 1-based.
            page_size: Types per page (default 25, max 100). The catalogue is small.

        Returns:
            AbsenceTypePage: The types on this page (``.items``) plus ``.page``, ``.page_size`` and
            ``.total``.

        Raises:
            ForbiddenError: If the API key does not have the ``absence-types.list`` method enabled.
            AuthenticationError: If the API key is missing or invalid.
        """
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        body = self._client._request("GET", "/api/v1/absence-types", params=params)
        return AbsenceTypePage.from_response(body)


class _Holidays:
    """The ``holidays`` resource."""

    def __init__(self, client: "DutyBeat"):
        self._client = client

    def list(
        self,
        work_center_id: str,
        *,
        year: Optional[str] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> HolidayPage:
        """List a work center's holidays — ``GET /api/v1/holidays``.

        Returns the festivo calendar of one work center (sede), oldest first. Each holiday is a date,
        a name and a type (``"national"`` / ``"regional"`` / ``"local"``).

        Args:
            work_center_id: The work center whose calendar to fetch (required). Discover ids with
                :meth:`DutyBeat.work_centers.list`.
            year: Narrow to a single year (``"YYYY"``). Omit for the full calendar.
            page: Page to fetch, 1-based.
            page_size: Holidays per page (default 25, max 100).

        Returns:
            HolidayPage: The holidays on this page (``.items``) plus ``.page``, ``.page_size`` and
            ``.total``.

        Raises:
            NotFoundError: If the work center does not exist or belongs to another company.
            ForbiddenError: If the API key does not have the ``holidays.list`` method enabled.
            AuthenticationError: If the API key is missing or invalid.
            APIError: If ``year`` is not a 4-digit year.
        """
        params: Dict[str, Any] = {
            "work_center_id": work_center_id,
            "page": page,
            "page_size": page_size,
        }
        if year is not None:
            params["year"] = year
        body = self._client._request("GET", "/api/v1/holidays", params=params)
        return HolidayPage.from_response(body)


class _Departments:
    """The ``departments`` resource."""

    def __init__(self, client: "DutyBeat"):
        self._client = client

    def list(self, *, page: int = 1, page_size: int = 25) -> DepartmentPage:
        """List departments — ``GET /api/v1/departments``.

        Returns a page of the company's departments, alphabetical, each with its employee headcount and
        its supervisor department (the org tree). Iterate ``page=1, 2, …`` until you've seen
        ``DepartmentPage.total`` departments.

        Args:
            page: Page to fetch, 1-based.
            page_size: Departments per page (default 25, max 100).

        Returns:
            DepartmentPage: The departments on this page (``.items``) plus ``.page``, ``.page_size``
            and ``.total``.

        Raises:
            ForbiddenError: If the API key does not have the ``departments.list`` method enabled.
            AuthenticationError: If the API key is missing or invalid.
        """
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        body = self._client._request("GET", "/api/v1/departments", params=params)
        return DepartmentPage.from_response(body)


class _WorkCenters:
    """The ``work_centers`` resource."""

    def __init__(self, client: "DutyBeat"):
        self._client = client

    def list(self, *, page: int = 1, page_size: int = 25) -> WorkCenterPage:
        """List work centers (sedes) — ``GET /api/v1/work-centers``.

        Returns a page of the company's work centers, alphabetical, each with its location (country and,
        when set, region/province/municipality). Iterate ``page=1, 2, …`` until you've seen
        ``WorkCenterPage.total`` work centers.

        Args:
            page: Page to fetch, 1-based.
            page_size: Work centers per page (default 25, max 100).

        Returns:
            WorkCenterPage: The work centers on this page (``.items``) plus ``.page``, ``.page_size``
            and ``.total``.

        Raises:
            ForbiddenError: If the API key does not have the ``work-centers.list`` method enabled.
            AuthenticationError: If the API key is missing or invalid.
        """
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        body = self._client._request("GET", "/api/v1/work-centers", params=params)
        return WorkCenterPage.from_response(body)


class _Expenses:
    """The ``expenses`` resource."""

    def __init__(self, client: "DutyBeat"):
        self._client = client

    def get(self, expense_id: str) -> Expense:
        """Fetch a single expense — ``GET /api/v1/expenses/:expense_id``.

        Args:
            expense_id: The expense's id within your company.

        Returns:
            Expense: The expense, with its OCR money fields, category, status and ``reconciled`` flag.

        Raises:
            NotFoundError: If the expense does not exist or belongs to another company.
            ForbiddenError: If the API key does not have the ``expenses.get`` method enabled.
            AuthenticationError: If the API key is missing or invalid.
        """
        body = self._client._request("GET", f"/api/v1/expenses/{expense_id}")
        return Expense.from_dict(body["data"])

    def list(
        self,
        *,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> ExpensePage:
        """List expenses (receipts) — ``GET /api/v1/expenses``.

        Returns a page of the company's expense receipts, newest first. Combine the filters to narrow
        the result; iterate ``page=1, 2, …`` until you've seen ``ExpensePage.total`` expenses.

        Args:
            user_id: Only this employee's expenses. Omit for the whole company.
            status: Filter by ``"processing"``, ``"imported"`` or ``"error"``.
            page: Page to fetch, 1-based.
            page_size: Expenses per page (default 25, max 100).

        Returns:
            ExpensePage: The expenses on this page (``.items``) plus ``.page``, ``.page_size`` and
            ``.total``.

        Raises:
            NotFoundError: If ``user_id`` does not exist or belongs to another company.
            ForbiddenError: If the API key does not have the ``expenses.list`` method enabled.
            AuthenticationError: If the API key is missing or invalid.
            APIError: If the status is invalid.
        """
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if user_id is not None:
            params["user_id"] = user_id
        if status is not None:
            params["status"] = status
        body = self._client._request("GET", "/api/v1/expenses", params=params)
        return ExpensePage.from_response(body)


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
        """Create a DutyBeat API client.

        Args:
            api_key: Your API key (starts with ``db_live_``). Create one in the app under
                Configuración → Claves de API. If omitted, the ``DUTYBEAT_API_KEY`` environment
                variable is used instead.
            base_url: Base URL of the API. Defaults to the production API; override only for testing.
            timeout: Per-request timeout, in seconds.
            max_retries: How many times to retry on ``429``/``5xx`` responses, honouring ``Retry-After``.

        Raises:
            DutyBeatError: If no API key is passed and ``DUTYBEAT_API_KEY`` is not set.
        """
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
        self.attendance = _Attendance(self)
        self.absences = _Absences(self)
        self.absence_types = _AbsenceTypes(self)
        self.departments = _Departments(self)
        self.work_centers = _WorkCenters(self)
        self.expenses = _Expenses(self)
        self.holidays = _Holidays(self)

    # -- introspection ---------------------------------------------------------------------------

    def me(self) -> Identity:
        """Who this API key is — ``GET /api/v1/me``.

        Returns the company (tenant) the key belongs to and the methods it can call. Not scope-gated:
        any valid key can call it, so it's a good first request to verify the key works.

        Returns:
            Identity: ``.tenant`` (a :class:`Ref` with ``id``/``name``) and ``.scopes`` (a list of
            method ids).

        Raises:
            AuthenticationError: If the API key is missing or invalid.
        """
        body = self._request("GET", "/api/v1/me")
        return Identity.from_dict(body["data"])

    # -- lifecycle -------------------------------------------------------------------------------

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "DutyBeat":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # -- transport -------------------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = self._base_url + path
        for attempt in range(self._max_retries + 1):
            response = self._client.request(method, url, params=params, json=json_body)
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
