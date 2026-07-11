import httpx
import pytest
import respx

from dutybeat import AttendanceDay, AttendancePage, DutyBeat, ForbiddenError, NotFoundError

BASE = "https://api.dutybeat.com"

ATTENDANCE_PAYLOAD = {
    "data": [
        {
            "user_id": "u-delm",
            "date": "2026-06-03",
            "is_workday": True,
            "holiday": None,
            "modality": "remote",
            "punches": [
                {"type": "in", "at": "2026-06-03T07:00:00.000Z", "edited": False},
                {"type": "break_start", "at": "2026-06-03T08:30:00.000Z", "edited": False},
                {"type": "break_end", "at": "2026-06-03T08:45:00.000Z", "edited": False},
                {"type": "out", "at": "2026-06-03T16:00:00.000Z", "edited": True},
            ],
            "worked_minutes": 465,
            "expected_minutes": 480,
            "balance_minutes": -15,
        }
    ],
    "meta": {"page": 1, "page_size": 25, "total": 1},
}


def client() -> DutyBeat:
    return DutyBeat(api_key="db_live_test", max_retries=1)


@respx.mock
def test_list_returns_typed_days_and_punches():
    respx.get(f"{BASE}/api/v1/attendance").mock(
        return_value=httpx.Response(200, json=ATTENDANCE_PAYLOAD)
    )

    page = client().attendance.list("u-delm", from_="2026-06-03", to="2026-06-03")

    assert isinstance(page, AttendancePage)
    assert page.total == 1
    assert len(page) == 1

    day = page.items[0]
    assert isinstance(day, AttendanceDay)
    assert day.date == "2026-06-03"
    assert day.modality == "remote"
    assert day.worked_minutes == 465
    assert day.balance_minutes == -15
    assert [p.type for p in day.punches] == ["in", "break_start", "break_end", "out"]
    assert day.punches[-1].edited is True
    assert day.punches[0].edited is False


@respx.mock
def test_list_sends_the_range_and_pagination_as_query_params():
    route = respx.get(f"{BASE}/api/v1/attendance").mock(
        return_value=httpx.Response(200, json=ATTENDANCE_PAYLOAD)
    )

    client().attendance.list(
        "u-delm", from_="2026-06-01", to="2026-06-30", tz="Europe/Madrid", page=2, page_size=50
    )

    params = route.calls.last.request.url.params
    assert params["user_id"] == "u-delm"
    assert params["from"] == "2026-06-01"  # `from_` is sent as `from`
    assert params["to"] == "2026-06-30"
    assert params["tz"] == "Europe/Madrid"
    assert params["page"] == "2"
    assert params["page_size"] == "50"


@respx.mock
def test_list_omits_tz_when_not_given():
    route = respx.get(f"{BASE}/api/v1/attendance").mock(
        return_value=httpx.Response(200, json=ATTENDANCE_PAYLOAD)
    )

    client().attendance.list("u-delm", from_="2026-06-01", to="2026-06-30")

    assert "tz" not in route.calls.last.request.url.params


@respx.mock
def test_list_is_forward_compatible_with_unknown_fields():
    payload = {
        "data": [
            {
                "user_id": "u-delm",
                "date": "2026-06-03",
                "punches": [{"type": "in", "at": "2026-06-03T07:00:00.000Z", "unknown": 1}],
                "worked_minutes": 465,
                "brand_new_field": "ignored",
            }
        ],
        "meta": {"page": 1, "page_size": 25, "total": 1},
    }
    respx.get(f"{BASE}/api/v1/attendance").mock(return_value=httpx.Response(200, json=payload))

    day = client().attendance.list("u-delm", from_="2026-06-03", to="2026-06-03").items[0]

    assert day.worked_minutes == 465
    assert day.expected_minutes is None  # absent → None, never a KeyError
    assert day.punches[0].type == "in"


@respx.mock
def test_list_maps_errors():
    respx.get(f"{BASE}/api/v1/attendance").mock(
        return_value=httpx.Response(
            403, json={"error": {"code": "forbidden_scope", "message": "no scope"}}
        )
    )
    with pytest.raises(ForbiddenError):
        client().attendance.list("u-delm", from_="2026-06-03", to="2026-06-03")


@respx.mock
def test_list_maps_unknown_employee_to_not_found():
    respx.get(f"{BASE}/api/v1/attendance").mock(
        return_value=httpx.Response(
            404, json={"error": {"code": "not_found", "message": "Usuario no encontrado"}}
        )
    )
    with pytest.raises(NotFoundError):
        client().attendance.list("nope", from_="2026-06-03", to="2026-06-03")
