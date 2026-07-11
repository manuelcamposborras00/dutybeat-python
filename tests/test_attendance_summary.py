import httpx
import pytest
import respx

from dutybeat import AttendanceSummary, AttendanceSummaryPage, DutyBeat, ForbiddenError

BASE = "https://api.dutybeat.com"

SUMMARY_PAYLOAD = {
    "data": [
        {
            "user_id": "u-dirg",
            "full_name": "Alberto Vázquez Romero",
            "worked_minutes": 2445,
            "expected_minutes": 10560,
            "balance_minutes": -8115,
            "worked_days": 5,
            "expected_days": 22,
        },
        {
            "user_id": "u-estm1",
            "full_name": "Andrés Molina Prieto",
            "worked_minutes": 0,
            "expected_minutes": 10560,
            "balance_minutes": -10560,
            "worked_days": 0,
            "expected_days": 22,
        },
    ],
    "meta": {"page": 1, "page_size": 25, "total": 17},
}


def client() -> DutyBeat:
    return DutyBeat(api_key="db_live_test", max_retries=1)


@respx.mock
def test_summary_returns_typed_rows():
    respx.get(f"{BASE}/api/v1/attendance/summary").mock(
        return_value=httpx.Response(200, json=SUMMARY_PAYLOAD)
    )

    page = client().attendance.summary(from_="2026-06-01", to="2026-06-30")

    assert isinstance(page, AttendanceSummaryPage)
    assert page.total == 17
    assert len(page) == 2

    row = page.items[0]
    assert isinstance(row, AttendanceSummary)
    assert row.user_id == "u-dirg"
    assert row.full_name == "Alberto Vázquez Romero"
    assert row.worked_minutes == 2445
    assert row.expected_minutes == 10560
    assert row.balance_minutes == -8115
    assert row.worked_days == 5
    assert row.expected_days == 22


@respx.mock
def test_summary_sends_range_filters_and_pagination_as_query_params():
    route = respx.get(f"{BASE}/api/v1/attendance/summary").mock(
        return_value=httpx.Response(200, json=SUMMARY_PAYLOAD)
    )

    client().attendance.summary(
        from_="2026-06-01",
        to="2026-06-30",
        tz="Europe/Madrid",
        status="active",
        department_id="dep-ing",
        work_center_id="wc-madrid",
        page=2,
        page_size=50,
    )

    params = route.calls.last.request.url.params
    assert params["from"] == "2026-06-01"  # `from_` is sent as `from`
    assert params["to"] == "2026-06-30"
    assert params["tz"] == "Europe/Madrid"
    assert params["status"] == "active"
    assert params["department_id"] == "dep-ing"
    assert params["work_center_id"] == "wc-madrid"
    assert params["page"] == "2"
    assert params["page_size"] == "50"


@respx.mock
def test_summary_omits_optional_params_when_not_given():
    route = respx.get(f"{BASE}/api/v1/attendance/summary").mock(
        return_value=httpx.Response(200, json=SUMMARY_PAYLOAD)
    )

    client().attendance.summary(from_="2026-06-01", to="2026-06-30")

    params = route.calls.last.request.url.params
    assert "tz" not in params
    assert "status" not in params
    assert "department_id" not in params
    assert "work_center_id" not in params


@respx.mock
def test_summary_is_forward_compatible_with_unknown_fields():
    payload = {
        "data": [{"user_id": "u-dirg", "worked_minutes": 2445, "brand_new_field": "ignored"}],
        "meta": {"page": 1, "page_size": 25, "total": 1},
    }
    respx.get(f"{BASE}/api/v1/attendance/summary").mock(
        return_value=httpx.Response(200, json=payload)
    )

    row = client().attendance.summary(from_="2026-06-01", to="2026-06-30").items[0]

    assert row.worked_minutes == 2445
    assert row.expected_minutes is None  # absent → None, never a KeyError


@respx.mock
def test_summary_maps_errors():
    respx.get(f"{BASE}/api/v1/attendance/summary").mock(
        return_value=httpx.Response(
            403, json={"error": {"code": "forbidden_scope", "message": "no scope"}}
        )
    )
    with pytest.raises(ForbiddenError):
        client().attendance.summary(from_="2026-06-01", to="2026-06-30")
