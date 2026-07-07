"""Typed models for the public API responses.

Models are lenient by design (forward-compatible): unknown fields are ignored and missing fields
default to ``None``, so a new field added to the API never breaks an older client.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class Profile:
    """The employee's profile (Mi Perfil) fields.

    Backed by the raw dict so new profile fields are available immediately. Supports both attribute
    access (``profile.iban``) and item access (``profile["iban"]``); unknown keys return ``None``.
    """

    def __init__(self, data: Optional[Dict[str, Any]] = None):
        self._data: Dict[str, Any] = dict(data or {})

    def __getattr__(self, name: str) -> Any:
        # Only reached for names not set as real attributes.
        return self._data.get(name)

    def __getitem__(self, name: str) -> Any:
        return self._data.get(name)

    def get(self, name: str, default: Any = None) -> Any:
        return self._data.get(name, default)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._data)

    def __repr__(self) -> str:
        return f"Profile({self._data!r})"


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
            profile=Profile(data.get("profile") or {}),
            folders=[Folder.from_dict(f) for f in folders] if isinstance(folders, list) else None,
        )
