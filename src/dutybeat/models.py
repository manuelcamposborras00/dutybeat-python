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
