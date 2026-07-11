import httpx
import pytest
import respx

from dutybeat import DutyBeat, ForbiddenError, Holiday, HolidayPage, NotFoundError

BASE = "https://api.dutybeat.com"

HOLIDAYS_PAYLOAD = {
    "data": [
        {"date": "2026-01-01", "name": "Año Nuevo", "type": "national"},
        {"date": "2026-01-06", "name": "Epifanía del Señor", "type": "national"},
    ],
    "meta": {"page": 1, "page_size": 25, "total": 12},
}


def client() -> DutyBeat:
    return DutyBeat(api_key="db_live_test", max_retries=1)


@respx.mock
def test_list_returns_typed_holidays():
    respx.get(f"{BASE}/api/v1/holidays").mock(
        return_value=httpx.Response(200, json=HOLIDAYS_PAYLOAD)
    )

    page = client().holidays.list("wc-madrid")

    assert isinstance(page, HolidayPage)
    assert page.total == 12
    assert len(page) == 2
    first = page.items[0]
    assert isinstance(first, Holiday)
    assert first.date == "2026-01-01"
    assert first.name == "Año Nuevo"
    assert first.type == "national"


@respx.mock
def test_list_sends_work_center_year_and_pagination():
    route = respx.get(f"{BASE}/api/v1/holidays").mock(
        return_value=httpx.Response(200, json=HOLIDAYS_PAYLOAD)
    )

    client().holidays.list("wc-madrid", year="2026", page=2, page_size=50)

    params = route.calls.last.request.url.params
    assert params["work_center_id"] == "wc-madrid"
    assert params["year"] == "2026"
    assert params["page"] == "2"
    assert params["page_size"] == "50"


@respx.mock
def test_list_omits_year_when_not_given():
    route = respx.get(f"{BASE}/api/v1/holidays").mock(
        return_value=httpx.Response(200, json=HOLIDAYS_PAYLOAD)
    )

    client().holidays.list("wc-madrid")

    assert "year=" not in str(route.calls.last.request.url)


@respx.mock
def test_list_maps_unknown_work_center_to_not_found():
    respx.get(f"{BASE}/api/v1/holidays").mock(
        return_value=httpx.Response(
            404, json={"error": {"code": "not_found", "message": "Sede no encontrada"}}
        )
    )
    with pytest.raises(NotFoundError):
        client().holidays.list("nope")


@respx.mock
def test_list_maps_errors():
    respx.get(f"{BASE}/api/v1/holidays").mock(
        return_value=httpx.Response(
            403, json={"error": {"code": "forbidden_scope", "message": "no scope"}}
        )
    )
    with pytest.raises(ForbiddenError):
        client().holidays.list("wc-madrid")
