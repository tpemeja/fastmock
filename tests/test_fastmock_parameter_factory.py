from typing import Literal

from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel

from fastmock.decorator import FastMockDecorator
from fastmock.middleware import FastMockMiddleware
from fastmock.model import MockData


class LineItem(BaseModel):
    price: float


class Order(BaseModel):
    line_items: list[LineItem]
    total: float
    status: Literal["pending", "shipped"]
    tracking_number: str | None


class CoherentOrderFactory(ModelFactory[Order]):
    """Encodes the cross-field invariants fastmock deliberately does not infer from a schema."""

    @classmethod
    def build(cls, **kwargs) -> Order:
        line_items = [LineItem(price=10.0), LineItem(price=5.5)]
        return Order(
            line_items=line_items,
            total=sum(item.price for item in line_items),
            status="shipped",
            tracking_number="TRACK-123",
        )


def get_client(**kwargs) -> TestClient:
    # Recreate the app to reset the middleware for each test
    test_app = FastAPI()
    test_app.add_middleware(FastMockMiddleware, mock_data=MockData(**kwargs))
    mock = FastMockDecorator()

    @test_app.get("/order",
                  status_code=status.HTTP_200_OK,
                  responses={status.HTTP_200_OK: {"model": Order}})
    async def get_order():
        return {}

    @mock(factory=CoherentOrderFactory)
    @test_app.get("/decorated-order",
                  status_code=status.HTTP_200_OK,
                  responses={status.HTTP_200_OK: {"model": Order}})
    async def get_decorated_order():
        return {}

    @mock(factory=CoherentOrderFactory)
    @test_app.get("/decorated-orders",
                  status_code=status.HTTP_200_OK,
                  responses={status.HTTP_200_OK: {"model": list[Order]}})
    async def get_decorated_orders():
        return []

    return TestClient(test_app)


def assert_is_coherent(order: dict):
    assert order["total"] == sum(item["price"] for item in order["line_items"])
    assert (order["tracking_number"] is not None) == (order["status"] == "shipped")


def test_schema_generation_does_not_guarantee_invariants():
    """
    Documents the fidelity ceiling: without a factory, fields are individually plausible but
    unrelated. This is why the escape hatch exists.
    """
    order = get_client(type="generated").get("/order").json()

    assert order["total"] != sum(item["price"] for item in order["line_items"])


def test_factory_supplies_invariants_the_schema_cannot():
    order = get_client().get("/decorated-order").json()

    assert_is_coherent(order)
    assert order["total"] == 15.5


def test_factory_applies_to_every_element_of_a_list():
    # element_size comes from the header rather than the middleware, since the decorator carries
    # a complete MockData and its default element_size would otherwise take precedence.
    orders = get_client().get("/decorated-orders",
                              headers={"X-FASTMOCK-ELEMENT-SIZE": "3"}).json()

    assert len(orders) == 3
    for order in orders:
        assert_is_coherent(order)


def test_factory_takes_precedence_over_type():
    """`factory` is the most specific instruction available, so it wins over `type=example`."""
    order = get_client(type="example").get("/decorated-order").json()

    assert_is_coherent(order)


def test_factory_can_be_set_globally_on_the_middleware():
    order = get_client(factory=CoherentOrderFactory).get("/order").json()

    assert_is_coherent(order)


def test_routes_without_a_factory_are_unaffected():
    order = get_client(type="generated").get("/order").json()

    assert set(order) == {"line_items", "total", "status", "tracking_number"}
