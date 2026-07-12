import json

import httpx
import respx

from dutybeat import DutyBeat, PunchRecord

BASE = "https://api.dutybeat.com"

PUNCH_PAYLOAD = {
    "data": {
        "id": "punch-nueva",
        "user_id": "u-delm",
        "type": "in",
        "ts": "2026-07-10T09:00:00.000Z",
        "modality": "onsite",
    }
}


def client() -> DutyBeat:
    return DutyBeat(api_key="db_live_test", max_retries=1)


@respx.mock
def test_create_posts_mark_and_returns_punch_record():
    route = respx.post(f"{BASE}/api/v1/attendance").mock(
        return_value=httpx.Response(201, json=PUNCH_PAYLOAD)
    )

    punch = client().attendance.create(user_id="u-delm", type="in", ts="2026-07-10T09:00:00Z")

    assert isinstance(punch, PunchRecord)
    assert punch.id == "punch-nueva"
    assert punch.type == "in"
    assert punch.modality == "onsite"

    sent = json.loads(route.calls.last.request.content)
    assert sent == {"user_id": "u-delm", "type": "in", "ts": "2026-07-10T09:00:00Z"}


@respx.mock
def test_create_includes_modality_when_given():
    route = respx.post(f"{BASE}/api/v1/attendance").mock(
        return_value=httpx.Response(201, json=PUNCH_PAYLOAD)
    )

    client().attendance.create(
        user_id="u-delm", type="in", ts="2026-07-10T09:00:00Z", modality="remote"
    )

    sent = json.loads(route.calls.last.request.content)
    assert sent["modality"] == "remote"
