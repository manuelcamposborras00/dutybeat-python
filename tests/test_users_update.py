import json

import httpx
import respx

from dutybeat import DutyBeat, User

BASE = "https://api.dutybeat.com"

UPDATED_PAYLOAD = {
    "data": {
        "id": "u-estm1",
        "full_name": "Andrés Molina Prieto",
        "email": "andres.molina@empresa.com",
        "role": "member",
        "status": "active",
        "has_photo": False,
        "remote_work_allowed": True,
        "department": None,
        "work_center": None,
        "profile": {"iban": "ES9121000418450200051332"},
        "folders": None,
    }
}


def client() -> DutyBeat:
    return DutyBeat(api_key="db_live_test", max_retries=1)


@respx.mock
def test_update_patches_only_given_fields_account_and_profile():
    route = respx.patch(f"{BASE}/api/v1/users/u-estm1").mock(
        return_value=httpx.Response(200, json=UPDATED_PAYLOAD)
    )

    user = client().users.update(
        "u-estm1",
        remote_work_allowed=True,
        iban="ES9121000418450200051332",
    )

    assert isinstance(user, User)
    assert user.remote_work_allowed is True
    assert user.profile.iban == "ES9121000418450200051332"

    sent = json.loads(route.calls.last.request.content)
    # Only the fields passed are sent (account field + profile field); nothing else.
    assert sent == {
        "remote_work_allowed": True,
        "iban": "ES9121000418450200051332",
    }


@respx.mock
def test_update_omits_none_values():
    route = respx.patch(f"{BASE}/api/v1/users/u-estm1").mock(
        return_value=httpx.Response(200, json=UPDATED_PAYLOAD)
    )

    client().users.update("u-estm1", full_name="Nuevo Nombre", role=None, dni=None)

    sent = json.loads(route.calls.last.request.content)
    assert sent == {"full_name": "Nuevo Nombre"}
