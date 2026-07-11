import httpx
import pytest
import respx

from dutybeat import DutyBeat, ForbiddenError, User, UserPage

BASE = "https://api.dutybeat.com"

LIST_PAYLOAD = {
    "data": [
        {
            "id": "u1",
            "full_name": "Ana Uno",
            "email": "ana@empresa.com",
            "role": "member",
            "status": "active",
            "has_photo": True,
            "department": {"id": "dep-ing", "name": "Ingeniería"},
            "work_center": {"id": "wc-cor", "name": "A Coruña"},
        },
        {
            "id": "u2",
            "full_name": "Bruno Dos",
            "email": "bruno@empresa.com",
            "role": "admin",
            "status": "active",
            "has_photo": False,
            "department": None,
            "work_center": None,
        },
    ],
    "meta": {"page": 1, "page_size": 25, "total": 42},
}


def client() -> DutyBeat:
    return DutyBeat(api_key="db_live_test", max_retries=1)


@respx.mock
def test_list_parses_page_and_items():
    respx.get(f"{BASE}/api/v1/users").mock(return_value=httpx.Response(200, json=LIST_PAYLOAD))
    page = client().users.list()
    assert isinstance(page, UserPage)
    assert page.total == 42
    assert page.page == 1
    assert page.page_size == 25
    assert len(page) == 2
    assert [u.full_name for u in page] == ["Ana Uno", "Bruno Dos"]
    assert isinstance(page.items[0], User)
    assert page.items[0].department.name == "Ingeniería"


@respx.mock
def test_list_sends_pagination_and_filter_params():
    route = respx.get(
        f"{BASE}/api/v1/users",
        params={
            "page": "2",
            "page_size": "50",
            "detail": "full",
            "status": "active",
            "role": "member",
            "department_id": "dep-ing",
            "work_center_id": "wc-cor",
            "q": "ana",
        },
    ).mock(return_value=httpx.Response(200, json=LIST_PAYLOAD))
    client().users.list(
        page=2,
        page_size=50,
        detail="full",
        status="active",
        role="member",
        department_id="dep-ing",
        work_center_id="wc-cor",
        q="ana",
    )
    assert route.called


@respx.mock
def test_list_sends_email_filter():
    route = respx.get(
        f"{BASE}/api/v1/users",
        params={"page": "1", "page_size": "25", "detail": "reduced", "email": "ana@empresa.com"},
    ).mock(return_value=httpx.Response(200, json=LIST_PAYLOAD))
    client().users.list(email="ana@empresa.com")
    assert route.called


@respx.mock
def test_list_omits_unset_filters():
    route = respx.get(f"{BASE}/api/v1/users").mock(
        return_value=httpx.Response(200, json=LIST_PAYLOAD)
    )
    client().users.list()
    sent = route.calls.last.request.url
    # Only the always-present pagination/detail params are sent; optional filters are absent.
    assert "status=" not in str(sent)
    assert "role=" not in str(sent)
    assert "email=" not in str(sent)
    assert "q=" not in str(sent)
    assert "page=1" in str(sent)


@respx.mock
def test_list_403_raises_forbidden():
    respx.get(f"{BASE}/api/v1/users").mock(
        return_value=httpx.Response(403, json={"error": {"code": "forbidden_scope", "message": "no"}})
    )
    with pytest.raises(ForbiddenError):
        client().users.list()


def test_userpage_lenient_empty():
    # Missing data/meta must not crash — forward-compatible like the other models.
    page = UserPage.from_response({})
    assert page.items == []
    assert page.total == 0
