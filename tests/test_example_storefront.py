"""
Guards the storefront example and the values quoted in documentation/docs/example.md.

If these fail, the example page is lying to readers.
"""

import time

import pytest
from fastapi.testclient import TestClient

from examples.storefront import app

CUSTOMER_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"


@pytest.fixture(name="client")
def client_fixture() -> TestClient:
    return TestClient(app)


def test_customers_are_plausible(client):
    body = client.get("/customers").json()

    assert body[0]["first_name"] == "Oscar"
    assert body[0]["city"] == "Cookhaven"
    assert body[0]["country"] == "Swaziland"
    assert "@" in body[0]["email"]


def test_pages_are_distinct_and_stable(client):
    page_one = client.get("/customers").json()
    page_two = client.get("/customers?page=2").json()

    assert page_one != page_two
    assert page_one == client.get("/customers").json()
    assert page_two == client.get("/customers?page=2").json()


def test_orders_satisfy_their_invariants(client):
    orders = client.get("/orders").json()

    assert len(orders) == 3
    for order in orders:
        expected = round(sum(i["unit_price"] * i["quantity"] for i in order["line_items"]), 2)
        assert order["total"] == pytest.approx(expected)
        assert (order["tracking_number"] is not None) == (order["status"] == "shipped")


def test_skus_follow_the_custom_provider(client):
    orders = client.get("/orders").json()

    for order in orders:
        for item in order["line_items"]:
            assert len(item["sku"]) == 8 and item["sku"][3] == "-"
            assert item["sku"][:3].isalpha() and item["sku"][:3].isupper()


def test_documented_order_values(client):
    """The exact figures quoted on the example page."""
    first = client.get("/orders").json()[0]

    assert first["line_items"][0]["sku"] == "RCN-2182"
    assert first["line_items"][0]["unit_price"] == 58.52
    assert first["total"] == 175.56
    assert first["status"] == "pending"
    assert first["tracking_number"] is None


def test_dependencies_are_never_resolved(client):
    """get_current_user raises if called; a 200 proves it was not."""
    assert client.get(f"/customers/{CUSTOMER_ID}").status_code == 200


def test_invalid_body_is_rejected_without_declaring_422(client):
    response = client.post("/orders", json={"customer_id": "nope", "line_items": []})

    assert response.status_code == 422
    error = response.json()["detail"][0]
    assert error["type"] == "uuid_parsing"
    assert error["loc"] == ["body", "customer_id"]


def test_status_code_override_returns_the_default_message(client):
    response = client.get(f"/customers/{CUSTOMER_ID}",
                          headers={"X-FASTMOCK-RESPONSE-STATUS-CODE": "404"})

    assert response.status_code == 404
    assert response.json() == {"message": "Customer not found"}


def test_inventory_is_flaky(client):
    # The route declares delay=0.3; override it so 60 samples do not cost 18 seconds.
    statuses = {client.get("/inventory/ABC-1234",
                           headers={"X-FASTMOCK-DELAY": "0"}).status_code
                for _ in range(60)}

    assert statuses == {200, 503}


def test_inventory_is_slow(client):
    """The declared delay applies when it is not overridden."""
    start = time.perf_counter()
    client.get("/inventory/ABC-1234")

    assert time.perf_counter() - start >= 0.3
