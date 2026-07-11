import json

import httpx
import respx

from dutybeat import DutyBeat, User

BASE = "https://api.dutybeat.com"

CREATED_PAYLOAD = {
    "data": {
        "id": "u-nuevo",
        "full_name": "Lucía Prieto Vega",
        "email": "lucia.prieto@empresa.com",
        "role": "member",
        "status": "active",
        "has_photo": False,
        "department": {"id": "dept-estm", "name": "Estructuras – Madrid"},
        "work_center": {"id": "wc-madrid", "name": "Madrid – Sede central"},
        "profile": {},
        "folders": None,
    }
}


def client() -> DutyBeat:
    return DutyBeat(api_key="db_live_test", max_retries=1)


@respx.mock
def test_create_posts_body_and_returns_user():
    route = respx.post(f"{BASE}/api/v1/users").mock(
        return_value=httpx.Response(201, json=CREATED_PAYLOAD)
    )

    user = client().users.create(
        email="lucia.prieto@empresa.com",
        full_name="Lucía Prieto Vega",
        department_id="dept-estm",
        work_center_id="wc-madrid",
    )

    assert isinstance(user, User)
    assert user.id == "u-nuevo"
    assert user.full_name == "Lucía Prieto Vega"

    sent = json.loads(route.calls.last.request.content)
    # Only the fields passed are sent — optional None values are omitted (no password → forgot flow).
    assert sent == {
        "email": "lucia.prieto@empresa.com",
        "full_name": "Lucía Prieto Vega",
        "department_id": "dept-estm",
        "work_center_id": "wc-madrid",
    }


@respx.mock
def test_create_includes_password_when_given():
    route = respx.post(f"{BASE}/api/v1/users").mock(
        return_value=httpx.Response(201, json=CREATED_PAYLOAD)
    )

    client().users.create(
        email="lucia.prieto@empresa.com",
        full_name="Lucía Prieto Vega",
        password="s3cretpass",
        role="admin",
    )

    sent = json.loads(route.calls.last.request.content)
    assert sent["password"] == "s3cretpass"
    assert sent["role"] == "admin"
