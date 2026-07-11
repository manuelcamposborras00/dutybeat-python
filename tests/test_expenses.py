import httpx
import pytest
import respx

from dutybeat import DutyBeat, Expense, ExpensePage, ForbiddenError, NotFoundError

BASE = "https://api.dutybeat.com"

EXPENSES_PAYLOAD = {
    "data": [
        {
            "id": "exp-dem-4",
            "user_id": "u-civm1",
            "status": "imported",
            "merchant": "Taxi Madrid",
            "expense_date": "2026-06-05",
            "total_amount": 18,
            "tax_amount": 1.64,
            "currency": "EUR",
            "amount_eur": 18,
            "fx_rate": 1,
            "category": "Desplazamiento",
            "reconciled": False,
            "error_reason": None,
            "created_at": "2026-06-05T09:30:00Z",
            "processed_at": "2026-06-05T09:31:00Z",
        },
        {
            "id": "exp-dem-1",
            "user_id": "u-civm1",
            "status": "imported",
            "merchant": "Mercadona",
            "expense_date": "2026-06-01",
            "total_amount": 23.4,
            "tax_amount": 2.13,
            "currency": "EUR",
            "amount_eur": 23.4,
            "fx_rate": 1,
            "category": "Dietas",
            "reconciled": True,
            "error_reason": None,
            "created_at": "2026-06-01T12:00:00Z",
            "processed_at": "2026-06-01T12:01:00Z",
        },
    ],
    "meta": {"page": 1, "page_size": 25, "total": 2},
}


def client() -> DutyBeat:
    return DutyBeat(api_key="db_live_test", max_retries=1)


@respx.mock
def test_list_returns_typed_expenses():
    respx.get(f"{BASE}/api/v1/expenses").mock(
        return_value=httpx.Response(200, json=EXPENSES_PAYLOAD)
    )

    page = client().expenses.list(user_id="u-civm1")

    assert isinstance(page, ExpensePage)
    assert page.total == 2
    assert len(page) == 2

    taxi = page.items[0]
    assert isinstance(taxi, Expense)
    assert taxi.merchant == "Taxi Madrid"
    assert taxi.amount_eur == 18
    assert taxi.category == "Desplazamiento"
    assert taxi.reconciled is False


@respx.mock
def test_list_exposes_the_reconciled_flag_as_bool():
    respx.get(f"{BASE}/api/v1/expenses").mock(
        return_value=httpx.Response(200, json=EXPENSES_PAYLOAD)
    )

    reconciled = client().expenses.list().items[1]

    assert reconciled.merchant == "Mercadona"
    assert reconciled.reconciled is True


@respx.mock
def test_list_sends_filters_and_pagination_as_query_params():
    route = respx.get(f"{BASE}/api/v1/expenses").mock(
        return_value=httpx.Response(200, json=EXPENSES_PAYLOAD)
    )

    client().expenses.list(user_id="u-civm1", status="imported", page=2, page_size=50)

    params = route.calls.last.request.url.params
    assert params["user_id"] == "u-civm1"
    assert params["status"] == "imported"
    assert params["page"] == "2"
    assert params["page_size"] == "50"


@respx.mock
def test_list_omits_optional_filters_when_not_given():
    route = respx.get(f"{BASE}/api/v1/expenses").mock(
        return_value=httpx.Response(200, json=EXPENSES_PAYLOAD)
    )

    client().expenses.list()

    params = route.calls.last.request.url.params
    for absent in ("user_id", "status"):
        assert absent not in params


@respx.mock
def test_list_is_forward_compatible_with_unknown_fields():
    payload = {
        "data": [{"id": "e1", "merchant": "X", "brand_new_field": "ignored"}],
        "meta": {"page": 1, "page_size": 25, "total": 1},
    }
    respx.get(f"{BASE}/api/v1/expenses").mock(return_value=httpx.Response(200, json=payload))

    expense = client().expenses.list().items[0]

    assert expense.id == "e1"
    assert expense.merchant == "X"
    assert expense.reconciled is False  # absent → default, never a KeyError
    assert expense.total_amount is None


@respx.mock
def test_list_maps_errors():
    respx.get(f"{BASE}/api/v1/expenses").mock(
        return_value=httpx.Response(
            403, json={"error": {"code": "forbidden_scope", "message": "no scope"}}
        )
    )
    with pytest.raises(ForbiddenError):
        client().expenses.list()


@respx.mock
def test_list_maps_unknown_employee_to_not_found():
    respx.get(f"{BASE}/api/v1/expenses").mock(
        return_value=httpx.Response(
            404, json={"error": {"code": "not_found", "message": "Usuario no encontrado"}}
        )
    )
    with pytest.raises(NotFoundError):
        client().expenses.list(user_id="nope")


@respx.mock
def test_get_returns_a_typed_expense():
    respx.get(f"{BASE}/api/v1/expenses/exp-dem-1").mock(
        return_value=httpx.Response(200, json={"data": EXPENSES_PAYLOAD["data"][1]})
    )

    expense = client().expenses.get("exp-dem-1")

    assert isinstance(expense, Expense)
    assert expense.id == "exp-dem-1"
    assert expense.merchant == "Mercadona"
    assert expense.amount_eur == 23.4
    assert expense.reconciled is True


@respx.mock
def test_get_maps_an_unknown_id_to_not_found():
    respx.get(f"{BASE}/api/v1/expenses/nope").mock(
        return_value=httpx.Response(
            404, json={"error": {"code": "not_found", "message": "Gasto no encontrado"}}
        )
    )
    with pytest.raises(NotFoundError):
        client().expenses.get("nope")
