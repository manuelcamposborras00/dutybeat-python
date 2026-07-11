import httpx
import respx

from dutybeat import DutyBeat, User

BASE = "https://api.dutybeat.com"

DISABLED_PAYLOAD = {
    "data": {
        "id": "u-nuevo",
        "full_name": "Lucía Prieto Vega",
        "email": "lucia.prieto@empresa.com",
        "role": "member",
        "status": "disabled",
        "has_photo": False,
        "department": None,
        "work_center": None,
        "profile": {},
        "folders": None,
    }
}


def client() -> DutyBeat:
    return DutyBeat(api_key="db_live_test", max_retries=1)


@respx.mock
def test_deactivate_posts_to_action_route_and_returns_disabled_user():
    route = respx.post(f"{BASE}/api/v1/users/u-nuevo/deactivate").mock(
        return_value=httpx.Response(200, json=DISABLED_PAYLOAD)
    )

    user = client().users.deactivate("u-nuevo")

    assert isinstance(user, User)
    assert user.id == "u-nuevo"
    assert user.status == "disabled"
    # No body is sent for the action.
    assert route.calls.last.request.content == b""
