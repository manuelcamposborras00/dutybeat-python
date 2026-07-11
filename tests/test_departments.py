import httpx
import pytest
import respx

from dutybeat import Department, DepartmentPage, DutyBeat, ForbiddenError

BASE = "https://api.dutybeat.com"

DEPARTMENTS_PAYLOAD = {
    "data": [
        {
            "id": "dept-admin",
            "name": "Administración y Finanzas",
            "employee_count": 2,
            "supervisor": {"id": "dept-dir", "name": "Dirección General"},
            "created_at": "2015-01-01T00:00:00Z",
        },
        {
            "id": "dept-dir",
            "name": "Dirección General",
            "employee_count": 1,
            "supervisor": None,
            "created_at": "2015-01-01T00:00:00Z",
        },
    ],
    "meta": {"page": 1, "page_size": 25, "total": 11},
}


def client() -> DutyBeat:
    return DutyBeat(api_key="db_live_test", max_retries=1)


@respx.mock
def test_list_returns_typed_departments_with_a_nested_supervisor():
    respx.get(f"{BASE}/api/v1/departments").mock(
        return_value=httpx.Response(200, json=DEPARTMENTS_PAYLOAD)
    )

    page = client().departments.list()

    assert isinstance(page, DepartmentPage)
    assert page.total == 11
    assert len(page) == 2

    admin = page.items[0]
    assert isinstance(admin, Department)
    assert admin.name == "Administración y Finanzas"
    assert admin.employee_count == 2
    assert admin.supervisor.id == "dept-dir"
    assert admin.supervisor.name == "Dirección General"


@respx.mock
def test_list_maps_a_root_departments_supervisor_to_none():
    respx.get(f"{BASE}/api/v1/departments").mock(
        return_value=httpx.Response(200, json=DEPARTMENTS_PAYLOAD)
    )

    root = client().departments.list().items[1]

    assert root.name == "Dirección General"
    assert root.supervisor is None


@respx.mock
def test_list_sends_pagination_as_query_params():
    route = respx.get(f"{BASE}/api/v1/departments").mock(
        return_value=httpx.Response(200, json=DEPARTMENTS_PAYLOAD)
    )

    client().departments.list(page=2, page_size=50)

    params = route.calls.last.request.url.params
    assert params["page"] == "2"
    assert params["page_size"] == "50"


@respx.mock
def test_list_is_forward_compatible_with_unknown_fields():
    payload = {
        "data": [{"id": "d1", "name": "Nuevo", "brand_new_field": "ignored"}],
        "meta": {"page": 1, "page_size": 25, "total": 1},
    }
    respx.get(f"{BASE}/api/v1/departments").mock(return_value=httpx.Response(200, json=payload))

    dept = client().departments.list().items[0]

    assert dept.id == "d1"
    assert dept.name == "Nuevo"
    assert dept.employee_count == 0  # absent → default, never a KeyError
    assert dept.supervisor is None


@respx.mock
def test_list_maps_errors():
    respx.get(f"{BASE}/api/v1/departments").mock(
        return_value=httpx.Response(
            403, json={"error": {"code": "forbidden_scope", "message": "no scope"}}
        )
    )
    with pytest.raises(ForbiddenError):
        client().departments.list()
