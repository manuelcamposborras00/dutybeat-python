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
from .models import Folder, Profile, Ref, User

__version__ = "0.2.1"

__all__ = [
    "DutyBeat",
    "DEFAULT_BASE_URL",
    "User",
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
