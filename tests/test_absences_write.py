import json

import httpx
import respx

from dutybeat import Absence, DutyBeat

BASE = "https://api.dutybeat.com"


def _absence(status: str) -> dict:
    return {
        "data": {
            "id": "abs-nueva",
            "user_id": "u-delm",
            "type": {"key": "vacation", "label": "Vacaciones"},
            "status": status,
            "start_date": "2026-08-10",
            "end_date": "2026-08-14",
            "start_time": None,
            "end_time": None,
            "created_at": "2026-07-12T10:00:00.000Z",
            "decided_at": None,
        }
    }


def client() -> DutyBeat:
    return DutyBeat(api_key="db_live_test", max_retries=1)


@respx.mock
def test_create_posts_subject_and_returns_absence():
    route = respx.post(f"{BASE}/api/v1/absences").mock(
        return_value=httpx.Response(201, json=_absence("pending"))
    )

    absence = client().absences.create(
        user_id="u-delm",
        type="vacation",
        start_date="2026-08-10",
        end_date="2026-08-14",
    )

    assert isinstance(absence, Absence)
    assert absence.id == "abs-nueva"
    assert absence.status == "pending"

    sent = json.loads(route.calls.last.request.content)
    assert sent == {
        "user_id": "u-delm",
        "type": "vacation",
        "start_date": "2026-08-10",
        "end_date": "2026-08-14",
    }


@respx.mock
def test_decide_posts_to_action_route():
    route = respx.post(f"{BASE}/api/v1/absences/abs-nueva/decide").mock(
        return_value=httpx.Response(200, json=_absence("approved"))
    )

    absence = client().absences.decide("abs-nueva", "approved")

    assert absence.status == "approved"
    sent = json.loads(route.calls.last.request.content)
    assert sent == {"decision": "approved"}
