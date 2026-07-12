"""Official Python client for the DutyBeat public API.

    from dutybeat import DutyBeat

    client = DutyBeat(api_key="db_live_...")
    user = client.users.get("9f1c...", include_folders=True)
"""

from .client import DEFAULT_BASE_URL, DutyBeat
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
    AbsenceType,
    AbsenceTypePage,
    AttendanceDay,
    AttendancePage,
    AttendanceSummary,
    AttendanceSummaryPage,
    ActingUser,
    Department,
    DepartmentPage,
    Expense,
    ExpensePage,
    Folder,
    GeoRef,
    Holiday,
    HolidayPage,
    Identity,
    Profile,
    Punch,
    Ref,
    User,
    UserPage,
    WorkCenter,
    WorkCenterPage,
)

__version__ = "0.20.0"

__all__ = [
    "DutyBeat",
    "DEFAULT_BASE_URL",
    "User",
    "UserPage",
    "AttendanceDay",
    "AttendancePage",
    "AttendanceSummary",
    "AttendanceSummaryPage",
    "Punch",
    "Absence",
    "AbsencePage",
    "AbsenceType",
    "AbsenceTypePage",
    "Department",
    "DepartmentPage",
    "WorkCenter",
    "WorkCenterPage",
    "Expense",
    "ExpensePage",
    "Holiday",
    "HolidayPage",
    "Identity",
    "ActingUser",
    "GeoRef",
    "Profile",
    "Ref",
    "Folder",
    "DutyBeatError",
    "AuthenticationError",
    "ForbiddenError",
    "NotFoundError",
    "RateLimitError",
    "APIError",
    "__version__",
]
