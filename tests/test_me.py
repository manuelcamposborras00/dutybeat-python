import httpx
import pytest
import respx

from dutybeat import AuthenticationError, DutyBeat, Identity

BASE = "https://api.dutybeat.com"

ME_PAYLOAD = {
    "data": {
        "tenant": {"id": "tenant-001", "name": "Atlántica Ingeniería S.L."},
        "scopes": ["users.list", "attendance.list"],
        "acts_as_user": {
            "id": "u-dirg",
            "email": "alberto.vazquez@atlantica-ing.com",
            "name": "Alberto Vázquez",
        },
    }
}


def client() -> DutyBeat:
    return DutyBeat(api_key="db_live_test", max_retries=1)


@respx.mock
def test_me_returns_identity():
    respx.get(f"{BASE}/api/v1/me").mock(return_value=httpx.Response(200, json=ME_PAYLOAD))

    identity = client().me()

    assert isinstance(identity, Identity)
    assert identity.tenant.id == "tenant-001"
    assert identity.tenant.name == "Atlántica Ingeniería S.L."
    assert identity.scopes == ["users.list", "attendance.list"]
    assert identity.acts_as_user is not None
    assert identity.acts_as_user.id == "u-dirg"
    assert identity.acts_as_user.email == "alberto.vazquez@atlantica-ing.com"
    assert identity.acts_as_user.name == "Alberto Vázquez"


@respx.mock
def test_me_is_lenient_with_missing_fields():
    respx.get(f"{BASE}/api/v1/me").mock(return_value=httpx.Response(200, json={"data": {}}))

    identity = client().me()

    assert identity.tenant is None
    assert identity.scopes == []
    assert identity.acts_as_user is None


@respx.mock
def test_me_maps_invalid_key_to_authentication_error():
    respx.get(f"{BASE}/api/v1/me").mock(
        return_value=httpx.Response(
            401, json={"error": {"code": "unauthorized", "message": "API key ausente o inválida"}}
        )
    )
    with pytest.raises(AuthenticationError):
        client().me()
