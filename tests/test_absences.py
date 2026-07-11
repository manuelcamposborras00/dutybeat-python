import httpx
import pytest
import respx

from dutybeat import Absence, AbsencePage, DutyBeat, ForbiddenError, NotFoundError

ABSENCE_PAYLOAD = {
    "data": {
        "id": "abs-008",
        "user_id": "u-delm",
        "type": {"key": "vacation", "label": "Vacaciones"},
        "status": "approved",
        "start_date": "2026-06-22",
        "end_date": "2026-06-26",
        "start_time": None,
        "end_time": None,
        "created_at": "2026-06-08T00:00:00Z",
        "decided_at": "2026-06-09T09:00:00Z",
    }
}

BASE = "https://api.dutybeat.com"

ABSENCES_PAYLOAD = {
    "data": [
        {
            "id": "abs-008",
            "user_id": "u-delm",
            "type": {"key": "vacation", "label": "Vacaciones"},
            "status": "approved",
            "start_date": "2026-06-22",
            "end_date": "2026-06-26",
            "start_time": None,
            "end_time": None,
            "created_at": "2026-06-08T00:00:00Z",
            "decided_at": "2026-06-09T09:00:00Z",
        },
        {
            "id": "abs-010",
            "user_id": "u-delm",
            "type": {"key": "personal", "label": "Asuntos propios"},
            "status": "approved",
            "start_date": "2026-06-11",
            "end_date": "2026-06-11",
            "start_time": "10:00",
            "end_time": "12:00",
            "created_at": "2026-06-05T00:00:00Z",
            "decided_at": "2026-06-05T15:00:00Z",
        },
    ],
    "meta": {"page": 1, "page_size": 25, "total": 2},
}


def client() -> DutyBeat:
    return DutyBeat(api_key="db_live_test", max_retries=1)


@respx.mock
def test_list_returns_typed_absences_with_a_nested_type():
    respx.get(f"{BASE}/api/v1/absences").mock(
        return_value=httpx.Response(200, json=ABSENCES_PAYLOAD)
    )

    page = client().absences.list(from_="2026-06-01", to="2026-06-30")

    assert isinstance(page, AbsencePage)
    assert page.total == 2
    assert len(page) == 2

    holiday = page.items[0]
    assert isinstance(holiday, Absence)
    assert holiday.type.key == "vacation"
    assert holiday.type.label == "Vacaciones"
    assert holiday.start_time is None  # whole-day


@respx.mock
def test_list_exposes_the_time_slice_of_an_hourly_absence():
    respx.get(f"{BASE}/api/v1/absences").mock(
        return_value=httpx.Response(200, json=ABSENCES_PAYLOAD)
    )

    hourly = client().absences.list(from_="2026-06-01", to="2026-06-30").items[1]

    assert (hourly.start_time, hourly.end_time) == ("10:00", "12:00")
    assert hourly.type.key == "personal"


@respx.mock
def test_list_sends_the_range_and_filters_as_query_params():
    route = respx.get(f"{BASE}/api/v1/absences").mock(
        return_value=httpx.Response(200, json=ABSENCES_PAYLOAD)
    )

    client().absences.list(
        from_="2026-06-01",
        to="2026-06-30",
        user_id="u-delm",
        status="approved",
        type="vacation",
        page=2,
        page_size=50,
    )

    params = route.calls.last.request.url.params
    assert params["from"] == "2026-06-01"  # `from_` is sent as `from`
    assert params["to"] == "2026-06-30"
    assert params["user_id"] == "u-delm"
    assert params["status"] == "approved"
    assert params["type"] == "vacation"
    assert params["page"] == "2"
    assert params["page_size"] == "50"


@respx.mock
def test_list_omits_optional_filters_when_not_given():
    route = respx.get(f"{BASE}/api/v1/absences").mock(
        return_value=httpx.Response(200, json=ABSENCES_PAYLOAD)
    )

    client().absences.list(from_="2026-06-01", to="2026-06-30")

    params = route.calls.last.request.url.params
    for absent in ("user_id", "status", "type"):
        assert absent not in params


@respx.mock
def test_list_is_forward_compatible_with_unknown_fields():
    payload = {
        "data": [{"id": "a1", "brand_new_field": "ignored", "type": {"key": "sick", "extra": 1}}],
        "meta": {"page": 1, "page_size": 25, "total": 1},
    }
    respx.get(f"{BASE}/api/v1/absences").mock(return_value=httpx.Response(200, json=payload))

    absence = client().absences.list(from_="2026-06-01", to="2026-06-30").items[0]

    assert absence.id == "a1"
    assert absence.type.key == "sick"
    assert absence.status is None  # absent → None, never a KeyError


@respx.mock
def test_list_handles_a_null_type_without_crashing():
    payload = {
        "data": [{"id": "a1", "type": None}],
        "meta": {"page": 1, "page_size": 25, "total": 1},
    }
    respx.get(f"{BASE}/api/v1/absences").mock(return_value=httpx.Response(200, json=payload))

    assert client().absences.list(from_="2026-06-01", to="2026-06-30").items[0].type is None


@respx.mock
def test_list_maps_errors():
    respx.get(f"{BASE}/api/v1/absences").mock(
        return_value=httpx.Response(
            403, json={"error": {"code": "forbidden_scope", "message": "no scope"}}
        )
    )
    with pytest.raises(ForbiddenError):
        client().absences.list(from_="2026-06-01", to="2026-06-30")


@respx.mock
def test_list_maps_unknown_employee_to_not_found():
    respx.get(f"{BASE}/api/v1/absences").mock(
        return_value=httpx.Response(
            404, json={"error": {"code": "not_found", "message": "Usuario no encontrado"}}
        )
    )
    with pytest.raises(NotFoundError):
        client().absences.list(from_="2026-06-01", to="2026-06-30", user_id="nope")


@respx.mock
def test_get_returns_a_typed_absence():
    respx.get(f"{BASE}/api/v1/absences/abs-008").mock(
        return_value=httpx.Response(200, json=ABSENCE_PAYLOAD)
    )

    absence = client().absences.get("abs-008")

    assert isinstance(absence, Absence)
    assert absence.id == "abs-008"
    assert absence.type.key == "vacation"
    assert absence.type.label == "Vacaciones"
    assert absence.status == "approved"
    assert absence.start_time is None


@respx.mock
def test_get_maps_an_unknown_id_to_not_found():
    respx.get(f"{BASE}/api/v1/absences/nope").mock(
        return_value=httpx.Response(
            404, json={"error": {"code": "not_found", "message": "Ausencia no encontrada"}}
        )
    )
    with pytest.raises(NotFoundError):
        client().absences.get("nope")
