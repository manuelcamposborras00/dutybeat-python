import dataclasses

import httpx
import pytest
import respx

from dutybeat import (
    AuthenticationError,
    DutyBeat,
    ForbiddenError,
    NotFoundError,
    Profile,
    RateLimitError,
)

BASE = "https://api.dutybeat.com"

USER_PAYLOAD = {
    "data": {
        "id": "9f1c",
        "full_name": "Daniel Castro",
        "email": "daniel@empresa.com",
        "role": "member",
        "status": "active",
        "has_photo": True,
        "department": {"id": "dep-ing", "name": "Ingeniería"},
        "work_center": {"id": "wc-cor", "name": "A Coruña"},
        "profile": {"dni": "12345678Z", "iban": "ES91...", "qualifications": ["Ing"]},
        "folders": None,
    }
}


def client() -> DutyBeat:
    return DutyBeat(api_key="db_live_test", max_retries=1)


@respx.mock
def test_get_user_parses_payload():
    respx.get(f"{BASE}/api/v1/users/9f1c").mock(return_value=httpx.Response(200, json=USER_PAYLOAD))
    user = client().users.get("9f1c")
    assert user.full_name == "Daniel Castro"
    assert user.department.name == "Ingeniería"
    assert user.profile.iban == "ES91..."
    assert user.has_photo is True


@respx.mock
def test_include_folders_passes_query():
    route = respx.get(f"{BASE}/api/v1/users/9f1c", params={"include_folders": "true"}).mock(
        return_value=httpx.Response(200, json=USER_PAYLOAD)
    )
    client().users.get("9f1c", include_folders=True)
    assert route.called


@respx.mock
def test_401_raises_authentication_error():
    respx.get(f"{BASE}/api/v1/users/9f1c").mock(
        return_value=httpx.Response(401, json={"error": {"code": "unauthorized", "message": "no"}})
    )
    with pytest.raises(AuthenticationError) as exc:
        client().users.get("9f1c")
    assert exc.value.code == "unauthorized"


@respx.mock
def test_403_raises_forbidden_error():
    respx.get(f"{BASE}/api/v1/users/9f1c").mock(
        return_value=httpx.Response(403, json={"error": {"code": "forbidden_scope", "message": "no"}})
    )
    with pytest.raises(ForbiddenError):
        client().users.get("9f1c")


@respx.mock
def test_404_raises_not_found():
    respx.get(f"{BASE}/api/v1/users/9f1c").mock(return_value=httpx.Response(404, json={}))
    with pytest.raises(NotFoundError):
        client().users.get("9f1c")


@respx.mock
def test_429_retries_then_raises():
    respx.get(f"{BASE}/api/v1/users/9f1c").mock(
        return_value=httpx.Response(429, headers={"Retry-After": "0"}, json={"error": {"code": "rate_limited", "message": "slow"}})
    )
    with pytest.raises(RateLimitError):
        client().users.get("9f1c")


def test_profile_is_typed_dataclass_with_declared_fields():
    # Guards the autocomplete contract: profile fields are real declared dataclass fields (not a dict
    # proxy), so editors can complete them. If a field is renamed/removed here, this breaks.
    assert dataclasses.is_dataclass(Profile)
    names = {f.name for f in dataclasses.fields(Profile)}
    assert {"dni", "iban", "ssn", "phone_personal", "qualifications"} <= names


def test_profile_parsing_and_leniency():
    p = Profile.from_dict({"iban": "ES91...", "qualifications": ["Ing"], "brand_new_field": "x"})
    assert p.iban == "ES91..."          # typed attribute access
    assert p["iban"] == "ES91..."        # item access still works
    assert p.qualifications == ["Ing"]
    assert p.dni is None                 # missing field defaults to None
    assert p.get("brand_new_field") is None  # unknown/newer API field ignored, no crash


def test_missing_api_key_raises():
    import os

    old = os.environ.pop("DUTYBEAT_API_KEY", None)
    try:
        with pytest.raises(Exception):
            DutyBeat()
    finally:
        if old is not None:
            os.environ["DUTYBEAT_API_KEY"] = old
