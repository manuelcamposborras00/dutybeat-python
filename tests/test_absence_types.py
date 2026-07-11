import httpx
import pytest
import respx

from dutybeat import AbsenceType, AbsenceTypePage, DutyBeat, ForbiddenError

BASE = "https://api.dutybeat.com"

TYPES_PAYLOAD = {
    "data": [
        {
            "key": "vacation",
            "label": "Vacaciones",
            "paid": True,
            "consumes_vacation": True,
            "requires_approval": True,
            "requires_justification": False,
            "allows_hourly": False,
            "day_count_mode": "working",
            "active": True,
        },
        {
            "key": "old",
            "label": "Tipo retirado",
            "paid": False,
            "consumes_vacation": False,
            "requires_approval": True,
            "requires_justification": False,
            "allows_hourly": False,
            "day_count_mode": "working",
            "active": False,
        },
    ],
    "meta": {"page": 1, "page_size": 25, "total": 2},
}


def client() -> DutyBeat:
    return DutyBeat(api_key="db_live_test", max_retries=1)


@respx.mock
def test_list_returns_typed_absence_types_with_attributes():
    respx.get(f"{BASE}/api/v1/absence-types").mock(
        return_value=httpx.Response(200, json=TYPES_PAYLOAD)
    )

    page = client().absence_types.list()

    assert isinstance(page, AbsenceTypePage)
    assert page.total == 2
    assert len(page) == 2

    vacation = page.items[0]
    assert isinstance(vacation, AbsenceType)
    assert vacation.key == "vacation"
    assert vacation.paid is True
    assert vacation.consumes_vacation is True
    assert vacation.day_count_mode == "working"
    assert vacation.active is True


@respx.mock
def test_list_includes_retired_types():
    respx.get(f"{BASE}/api/v1/absence-types").mock(
        return_value=httpx.Response(200, json=TYPES_PAYLOAD)
    )

    retired = client().absence_types.list().items[1]

    assert retired.key == "old"
    assert retired.active is False


@respx.mock
def test_list_sends_pagination_as_query_params():
    route = respx.get(f"{BASE}/api/v1/absence-types").mock(
        return_value=httpx.Response(200, json=TYPES_PAYLOAD)
    )

    client().absence_types.list(page=2, page_size=50)

    params = route.calls.last.request.url.params
    assert params["page"] == "2"
    assert params["page_size"] == "50"


def test_absence_type_is_lenient_when_nested_in_an_absence():
    # When AbsenceType is the nested `type` of an Absence, only key/label arrive; the rest default.
    t = AbsenceType.from_dict({"key": "vacation", "label": "Vacaciones"})
    assert t.key == "vacation"
    assert t.paid is None  # absent → None, never a KeyError


@respx.mock
def test_list_maps_errors():
    respx.get(f"{BASE}/api/v1/absence-types").mock(
        return_value=httpx.Response(
            403, json={"error": {"code": "forbidden_scope", "message": "no scope"}}
        )
    )
    with pytest.raises(ForbiddenError):
        client().absence_types.list()
