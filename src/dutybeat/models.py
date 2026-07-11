"""Typed models for the public API responses.

Models are lenient by design (forward-compatible): unknown fields are ignored and missing fields
default to ``None``, so a new field added to the API never breaks an older client.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any, Dict, List, Optional


@dataclass
class Profile:
    """The employee's profile (Mi Perfil) fields, from ``GET /api/v1/users/:id``.

    Every field is declared and typed, so editors (VS Code / Pylance) autocomplete them and show help.
    Item access (``profile["iban"]``) and ``profile.get("iban")`` also work; unknown keys return ``None``.
    Fields the API may add in the future are ignored gracefully instead of raising.
    """

    phone_company: Optional[str] = None
    phone_personal: Optional[str] = None
    personal_email: Optional[str] = None
    birth_date: Optional[str] = None
    nationality: Optional[str] = None
    dni: Optional[str] = None
    dni_expiry: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    passport_number: Optional[str] = None
    passport_issue: Optional[str] = None
    passport_expiry: Optional[str] = None
    health_insurance: Optional[str] = None
    iban: Optional[str] = None
    swift: Optional[str] = None
    country: Optional[str] = None
    company_name: Optional[str] = None
    company_cif: Optional[str] = None
    work_location: Optional[str] = None
    work_address: Optional[str] = None
    ssn: Optional[str] = None
    qualifications: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "Profile":
        data = dict(data or {})
        known = {f.name for f in fields(cls)}
        quals = data.get("qualifications")
        return cls(
            qualifications=[q for q in quals if isinstance(q, str)] if isinstance(quals, list) else [],
            **{k: data[k] for k in known & data.keys() if k != "qualifications"},
        )

    def __getitem__(self, name: str) -> Any:
        return getattr(self, name, None)

    def get(self, name: str, default: Any = None) -> Any:
        return getattr(self, name, default)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Ref:
    """A lightweight {id, name} reference (department, work center)."""

    id: Optional[str] = None
    name: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "Optional[Ref]":
        if not data:
            return None
        return cls(id=data.get("id"), name=data.get("name"))


@dataclass
class GeoRef:
    """A location level as {code, name}: the internal slug plus its human name (region/province/…)."""

    code: Optional[str] = None
    name: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "Optional[GeoRef]":
        if not data:
            return None
        return cls(code=data.get("code"), name=data.get("name"))


@dataclass
class ActingUser:
    """The user an API key acts as, from ``GET /api/v1/me`` (``acts_as_user``).

    Its permissions authorize the key's writes. ``None`` for a legacy key with no bound user.
    """

    id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "Optional[ActingUser]":
        if not data:
            return None
        return cls(id=data.get("id"), email=data.get("email"), name=data.get("name"))


@dataclass
class Identity:
    """Who an API key is, from ``GET /api/v1/me``.

    ``tenant`` is the company the key belongs to (a :class:`Ref` with ``id``/``name``); ``scopes`` are
    the method ids the key can call (e.g. ``"users.list"``); ``acts_as_user`` is the user whose
    permissions authorize the key's writes (an :class:`ActingUser`, or ``None`` for a legacy key).
    """

    tenant: Optional["Ref"] = None
    scopes: List[str] = field(default_factory=list)
    acts_as_user: Optional["ActingUser"] = None

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "Identity":
        data = dict(data or {})
        scopes = data.get("scopes")
        return cls(
            tenant=Ref.from_dict(data.get("tenant")),
            scopes=[s for s in scopes if isinstance(s, str)] if isinstance(scopes, list) else [],
            acts_as_user=ActingUser.from_dict(data.get("acts_as_user")),
        )


@dataclass
class Folder:
    """A document folder of the employee (metadata only)."""

    id: Optional[str] = None
    name: Optional[str] = None
    document_count: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Folder":
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            document_count=data.get("document_count", 0),
        )


@dataclass
class User:
    """A user as returned by ``GET /api/v1/users/:id``."""

    id: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    hire_date: Optional[str] = None
    vacation_days: Optional[int] = None
    works_holidays: bool = False
    remote_work_allowed: bool = False
    overtime_compensation: Optional[str] = None
    overtime_comp_expiry: Optional[str] = None
    created_at: Optional[str] = None
    has_photo: bool = False
    department: Optional[Ref] = None
    work_center: Optional[Ref] = None
    profile: Profile = field(default_factory=Profile)
    folders: Optional[List[Folder]] = None
    # `profile=` is populated via Profile.from_dict in User.from_dict below.

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        folders = data.get("folders")
        return cls(
            id=data.get("id"),
            full_name=data.get("full_name"),
            email=data.get("email"),
            role=data.get("role"),
            status=data.get("status"),
            hire_date=data.get("hire_date"),
            vacation_days=data.get("vacation_days"),
            works_holidays=bool(data.get("works_holidays", False)),
            remote_work_allowed=bool(data.get("remote_work_allowed", False)),
            overtime_compensation=data.get("overtime_compensation"),
            overtime_comp_expiry=data.get("overtime_comp_expiry"),
            created_at=data.get("created_at"),
            has_photo=bool(data.get("has_photo", False)),
            department=Ref.from_dict(data.get("department")),
            work_center=Ref.from_dict(data.get("work_center")),
            profile=Profile.from_dict(data.get("profile")),
            folders=[Folder.from_dict(f) for f in folders] if isinstance(folders, list) else None,
        )


@dataclass
class UserPage:
    """A page of users from ``GET /api/v1/users`` (List Users).

    ``items`` holds the users on this page (``User`` models). ``total`` is the full count across all
    pages, so you can iterate ``page=1, 2, …`` until you've seen ``total`` users.
    """

    items: List[User] = field(default_factory=list)
    page: int = 1
    page_size: int = 25
    total: int = 0

    @classmethod
    def from_response(cls, body: Dict[str, Any]) -> "UserPage":
        data = body.get("data")
        meta = body.get("meta") or {}
        return cls(
            items=[User.from_dict(u) for u in data] if isinstance(data, list) else [],
            page=meta.get("page", 1),
            page_size=meta.get("page_size", 25),
            total=meta.get("total", 0),
        )

    def __iter__(self):
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)


@dataclass
class AbsenceType:
    """An absence type from the company's catalogue (``GET /api/v1/absence-types``).

    A stable ``key`` to branch on (the same one ``Absence.type.key`` carries), the ``label`` the company
    sees, and the attributes that let you interpret an absence: ``paid``, ``consumes_vacation``,
    ``requires_approval``, ``requires_justification``, ``allows_hourly`` and ``day_count_mode``
    (``"working"`` | ``"natural"``). ``active`` tells a live type from a retired one.

    The catalogue is per-tenant and editable, so treat ``key`` as the contract and ``label`` as text.
    When this object is the nested ``type`` of an :class:`Absence`, only ``key``/``label`` are populated
    (the absence payload carries just those); the rest default to ``None``/``False``.
    """

    key: Optional[str] = None
    label: Optional[str] = None
    paid: Optional[bool] = None
    consumes_vacation: Optional[bool] = None
    requires_approval: Optional[bool] = None
    requires_justification: Optional[bool] = None
    allows_hourly: Optional[bool] = None
    day_count_mode: Optional[str] = None
    active: Optional[bool] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AbsenceType":
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class AbsenceTypePage:
    """A page of absence types from ``GET /api/v1/absence-types`` (List Absence Types).

    ``items`` holds the types on this page. ``total`` is the full count of the catalogue, so you can
    iterate ``page=1, 2, …`` until you've seen them all (though the catalogue is small).
    """

    items: List[AbsenceType] = field(default_factory=list)
    page: int = 1
    page_size: int = 25
    total: int = 0

    @classmethod
    def from_response(cls, body: Dict[str, Any]) -> "AbsenceTypePage":
        data = body.get("data")
        meta = body.get("meta") or {}
        return cls(
            items=[AbsenceType.from_dict(t) for t in data] if isinstance(data, list) else [],
            page=meta.get("page", 1),
            page_size=meta.get("page_size", 25),
            total=meta.get("total", 0),
        )

    def __iter__(self):
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)


@dataclass
class Absence:
    """A single absence (holiday, sick leave, …).

    ``start_time``/``end_time`` are only set on hourly absences — a slice of one day — and are ``None``
    for whole-day ones. ``status`` is ``pending``, ``approved``, ``rejected`` or ``cancelled``;
    ``decided_at`` is ``None`` while it is still pending.
    """

    id: Optional[str] = None
    user_id: Optional[str] = None
    type: Optional[AbsenceType] = None
    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    created_at: Optional[str] = None
    decided_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Absence":
        known = {f.name for f in fields(cls)} - {"type"}
        absence_type = data.get("type")
        return cls(
            **{k: v for k, v in data.items() if k in known},
            type=AbsenceType.from_dict(absence_type) if isinstance(absence_type, dict) else None,
        )


@dataclass
class AbsencePage:
    """A page of absences from ``GET /api/v1/absences`` (List Absences).

    ``items`` holds the absences on this page. ``total`` is the full count across all pages, so you can
    iterate ``page=1, 2, …`` until you've seen them all.
    """

    items: List[Absence] = field(default_factory=list)
    page: int = 1
    page_size: int = 25
    total: int = 0

    @classmethod
    def from_response(cls, body: Dict[str, Any]) -> "AbsencePage":
        data = body.get("data")
        meta = body.get("meta") or {}
        return cls(
            items=[Absence.from_dict(a) for a in data] if isinstance(data, list) else [],
            page=meta.get("page", 1),
            page_size=meta.get("page_size", 25),
            total=meta.get("total", 0),
        )

    def __iter__(self):
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)


@dataclass
class Department:
    """A department as returned by ``GET /api/v1/departments``.

    ``employee_count`` is how many users belong to it. ``supervisor`` is the department directly above
    it in the org tree — a ``Ref`` ({id, name}) — or ``None`` when the department is a root.
    """

    id: Optional[str] = None
    name: Optional[str] = None
    employee_count: int = 0
    supervisor: Optional[Ref] = None
    created_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Department":
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            employee_count=data.get("employee_count", 0),
            supervisor=Ref.from_dict(data.get("supervisor")),
            created_at=data.get("created_at"),
        )


@dataclass
class DepartmentPage:
    """A page of departments from ``GET /api/v1/departments`` (List Departments).

    ``items`` holds the departments on this page. ``total`` is the full count across all pages, so you
    can iterate ``page=1, 2, …`` until you've seen them all.
    """

    items: List[Department] = field(default_factory=list)
    page: int = 1
    page_size: int = 25
    total: int = 0

    @classmethod
    def from_response(cls, body: Dict[str, Any]) -> "DepartmentPage":
        data = body.get("data")
        meta = body.get("meta") or {}
        return cls(
            items=[Department.from_dict(d) for d in data] if isinstance(data, list) else [],
            page=meta.get("page", 1),
            page_size=meta.get("page_size", 25),
            total=meta.get("total", 0),
        )

    def __iter__(self):
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)


@dataclass
class WorkCenter:
    """A work center (sede) as returned by ``GET /api/v1/work-centers``.

    ``country`` is a slug (``"es"``). ``region``, ``province`` and ``municipality`` are each a ``GeoRef``
    ({code, name}) or ``None`` when unset.
    """

    id: Optional[str] = None
    name: Optional[str] = None
    country: Optional[str] = None
    region: Optional[GeoRef] = None
    province: Optional[GeoRef] = None
    municipality: Optional[GeoRef] = None
    created_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkCenter":
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            country=data.get("country"),
            region=GeoRef.from_dict(data.get("region")),
            province=GeoRef.from_dict(data.get("province")),
            municipality=GeoRef.from_dict(data.get("municipality")),
            created_at=data.get("created_at"),
        )


@dataclass
class WorkCenterPage:
    """A page of work centers from ``GET /api/v1/work-centers`` (List Work Centers).

    ``items`` holds the work centers on this page. ``total`` is the full count across all pages, so you
    can iterate ``page=1, 2, …`` until you've seen them all.
    """

    items: List[WorkCenter] = field(default_factory=list)
    page: int = 1
    page_size: int = 25
    total: int = 0

    @classmethod
    def from_response(cls, body: Dict[str, Any]) -> "WorkCenterPage":
        data = body.get("data")
        meta = body.get("meta") or {}
        return cls(
            items=[WorkCenter.from_dict(w) for w in data] if isinstance(data, list) else [],
            page=meta.get("page", 1),
            page_size=meta.get("page_size", 25),
            total=meta.get("total", 0),
        )

    def __iter__(self):
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)


@dataclass
class Expense:
    """An expense receipt (Mis Gastos) as returned by ``GET /api/v1/expenses``.

    ``status`` is ``"processing"`` (OCR/AI pending), ``"imported"`` (fields extracted) or ``"error"``.
    The money/OCR fields are ``None`` until ``"imported"``. ``amount_eur``/``fx_rate`` normalise a
    foreign-currency receipt to euros. ``reconciled`` is ``True`` when a bank transaction is matched to
    it. ``error_reason`` is set only on ``"error"``.
    """

    id: Optional[str] = None
    user_id: Optional[str] = None
    status: Optional[str] = None
    merchant: Optional[str] = None
    expense_date: Optional[str] = None
    total_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    currency: Optional[str] = None
    amount_eur: Optional[float] = None
    fx_rate: Optional[float] = None
    category: Optional[str] = None
    reconciled: bool = False
    error_reason: Optional[str] = None
    created_at: Optional[str] = None
    processed_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Expense":
        known = {f.name for f in fields(cls)} - {"reconciled"}
        return cls(
            **{k: v for k, v in data.items() if k in known},
            reconciled=bool(data.get("reconciled", False)),
        )


@dataclass
class ExpensePage:
    """A page of expenses from ``GET /api/v1/expenses`` (List Expenses).

    ``items`` holds the expenses on this page. ``total`` is the full count across all pages, so you can
    iterate ``page=1, 2, …`` until you've seen them all.
    """

    items: List[Expense] = field(default_factory=list)
    page: int = 1
    page_size: int = 25
    total: int = 0

    @classmethod
    def from_response(cls, body: Dict[str, Any]) -> "ExpensePage":
        data = body.get("data")
        meta = body.get("meta") or {}
        return cls(
            items=[Expense.from_dict(e) for e in data] if isinstance(data, list) else [],
            page=meta.get("page", 1),
            page_size=meta.get("page_size", 25),
            total=meta.get("total", 0),
        )

    def __iter__(self):
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)


@dataclass
class Holiday:
    """A public holiday (festivo) of a work center, from ``GET /api/v1/holidays``.

    ``date`` is ``YYYY-MM-DD``. ``type`` is ``"national"``, ``"regional"`` or ``"local"``.
    """

    date: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Holiday":
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class HolidayPage:
    """A page of holidays from ``GET /api/v1/holidays`` (List Holidays).

    ``items`` holds the holidays on this page. ``total`` is the full count for the work center (and year,
    if filtered), so you can iterate ``page=1, 2, …`` until you've seen them all.
    """

    items: List[Holiday] = field(default_factory=list)
    page: int = 1
    page_size: int = 25
    total: int = 0

    @classmethod
    def from_response(cls, body: Dict[str, Any]) -> "HolidayPage":
        data = body.get("data")
        meta = body.get("meta") or {}
        return cls(
            items=[Holiday.from_dict(h) for h in data] if isinstance(data, list) else [],
            page=meta.get("page", 1),
            page_size=meta.get("page_size", 25),
            total=meta.get("total", 0),
        )

    def __iter__(self):
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)


@dataclass
class Punch:
    """A single attendance mark.

    ``type`` is one of ``in``, ``out``, ``break_start``, ``break_end``. ``at`` is the UTC instant of
    the mark (ISO-8601). ``edited`` is ``True`` when the mark's time was changed by an approved
    correction. Voided marks are never returned.
    """

    type: Optional[str] = None
    at: Optional[str] = None
    edited: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Punch":
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class AttendanceDay:
    """One calendar day of an employee's attendance.

    ``worked_minutes`` already discounts pauses. ``balance_minutes`` is ``worked - expected``, and is
    ``None`` on days where no balance applies (non-working days and holidays). ``modality`` is the
    day's check-in modality (``onsite`` / ``remote``), or ``None`` when it was not recorded.
    """

    user_id: Optional[str] = None
    date: Optional[str] = None
    is_workday: Optional[bool] = None
    holiday: Optional[str] = None
    modality: Optional[str] = None
    punches: List[Punch] = field(default_factory=list)
    worked_minutes: Optional[int] = None
    expected_minutes: Optional[int] = None
    balance_minutes: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AttendanceDay":
        known = {f.name for f in fields(cls)} - {"punches"}
        punches = data.get("punches")
        return cls(
            **{k: v for k, v in data.items() if k in known},
            punches=[Punch.from_dict(p) for p in punches] if isinstance(punches, list) else [],
        )


@dataclass
class AttendanceSummary:
    """One employee's consolidated attendance over a range, from ``GET /api/v1/attendance/summary``.

    ``worked_minutes`` already discounts pauses. ``expected_minutes``/``balance_minutes`` and
    ``expected_days`` count only settled days (a corrected or future day with no balance yet is
    excluded), so the totals match the in-app monthly summary. ``worked_days`` is how many days the
    employee registered any time.
    """

    user_id: Optional[str] = None
    full_name: Optional[str] = None
    worked_minutes: Optional[int] = None
    expected_minutes: Optional[int] = None
    balance_minutes: Optional[int] = None
    worked_days: Optional[int] = None
    expected_days: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AttendanceSummary":
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class AttendanceSummaryPage:
    """A page of per-employee attendance summaries from ``GET /api/v1/attendance/summary``.

    ``items`` holds the employees on this page. ``total`` is the number of employees matching the
    filters, so you can iterate ``page=1, 2, …`` until you've seen them all.
    """

    items: List[AttendanceSummary] = field(default_factory=list)
    page: int = 1
    page_size: int = 25
    total: int = 0

    @classmethod
    def from_response(cls, body: Dict[str, Any]) -> "AttendanceSummaryPage":
        data = body.get("data")
        meta = body.get("meta") or {}
        return cls(
            items=[AttendanceSummary.from_dict(s) for s in data] if isinstance(data, list) else [],
            page=meta.get("page", 1),
            page_size=meta.get("page_size", 25),
            total=meta.get("total", 0),
        )

    def __iter__(self):
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)


@dataclass
class AttendancePage:
    """A page of attendance days from ``GET /api/v1/attendance`` (List Attendance).

    ``items`` holds the days on this page (``AttendanceDay`` models). ``total`` is the number of days
    in the requested range, so you can iterate ``page=1, 2, …`` until you've seen them all.
    """

    items: List[AttendanceDay] = field(default_factory=list)
    page: int = 1
    page_size: int = 25
    total: int = 0

    @classmethod
    def from_response(cls, body: Dict[str, Any]) -> "AttendancePage":
        data = body.get("data")
        meta = body.get("meta") or {}
        return cls(
            items=[AttendanceDay.from_dict(d) for d in data] if isinstance(data, list) else [],
            page=meta.get("page", 1),
            page_size=meta.get("page_size", 25),
            total=meta.get("total", 0),
        )

    def __iter__(self):
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)
