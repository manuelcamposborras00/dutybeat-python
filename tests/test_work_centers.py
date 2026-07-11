import httpx
import pytest
import respx

from dutybeat import DutyBeat, ForbiddenError, WorkCenter, WorkCenterPage

BASE = "https://api.dutybeat.com"

WORK_CENTERS_PAYLOAD = {
    "data": [
        {
            "id": "wc-coruna",
            "name": "A Coruña – Delegación",
            "country": "es",
            "region": {"code": "gal", "name": "Galicia"},
            "province": {"code": "a-coruna", "name": "A Coruña"},
            "municipality": {"code": "coruna-a", "name": "A Coruña"},
            "created_at": "2015-01-01T00:00:00Z",
        },
        {
            "id": "wc-bare",
            "name": "Sede sin ubicación",
            "country": "es",
            "region": None,
            "province": None,
            "municipality": None,
            "created_at": "2015-01-01T00:00:00Z",
        },
    ],
    "meta": {"page": 1, "page_size": 25, "total": 2},
}


def client() -> DutyBeat:
    return DutyBeat(api_key="db_live_test", max_retries=1)


@respx.mock
def test_list_returns_typed_work_centers_with_nested_location():
    respx.get(f"{BASE}/api/v1/work-centers").mock(
        return_value=httpx.Response(200, json=WORK_CENTERS_PAYLOAD)
    )

    page = client().work_centers.list()

    assert isinstance(page, WorkCenterPage)
    assert page.total == 2
    assert len(page) == 2

    coruna = page.items[0]
    assert isinstance(coruna, WorkCenter)
    assert coruna.country == "es"
    assert coruna.region.code == "gal"
    assert coruna.region.name == "Galicia"
    assert coruna.municipality.name == "A Coruña"


@respx.mock
def test_list_maps_unset_location_levels_to_none():
    respx.get(f"{BASE}/api/v1/work-centers").mock(
        return_value=httpx.Response(200, json=WORK_CENTERS_PAYLOAD)
    )

    bare = client().work_centers.list().items[1]

    assert bare.region is None
    assert bare.province is None
    assert bare.municipality is None


@respx.mock
def test_list_sends_pagination_as_query_params():
    route = respx.get(f"{BASE}/api/v1/work-centers").mock(
        return_value=httpx.Response(200, json=WORK_CENTERS_PAYLOAD)
    )

    client().work_centers.list(page=2, page_size=50)

    params = route.calls.last.request.url.params
    assert params["page"] == "2"
    assert params["page_size"] == "50"


@respx.mock
def test_list_is_forward_compatible_with_unknown_fields():
    payload = {
        "data": [{"id": "w1", "name": "Nueva", "brand_new_field": "ignored"}],
        "meta": {"page": 1, "page_size": 25, "total": 1},
    }
    respx.get(f"{BASE}/api/v1/work-centers").mock(return_value=httpx.Response(200, json=payload))

    wc = client().work_centers.list().items[0]

    assert wc.id == "w1"
    assert wc.name == "Nueva"
    assert wc.region is None  # absent → None, never a KeyError


@respx.mock
def test_list_maps_errors():
    respx.get(f"{BASE}/api/v1/work-centers").mock(
        return_value=httpx.Response(
            403, json={"error": {"code": "forbidden_scope", "message": "no scope"}}
        )
    )
    with pytest.raises(ForbiddenError):
        client().work_centers.list()
