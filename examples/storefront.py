"""
A storefront API that is entirely mocked by fastmock.

Every endpoint below has an empty body. Nothing is implemented, there is no database, and no
dependency is ever called -- yet the API answers with plausible, reproducible data, validates
incoming requests, and can be made slow or unreliable on demand.

Run it from the repository root with:

    uv sync --group examples
    uv run uvicorn examples.storefront:app --reload

Use `uv run` rather than a bare `uvicorn`: activating the virtualenv is not enough if uvicorn is
also installed system-wide, since PATH may resolve to that copy and its unrelated interpreter.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel, EmailStr, Field

from fastmock.decorator import FastMockDecorator
from fastmock.middleware import FastMockMiddleware


class Customer(BaseModel):
    customer_id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    city: str
    country: str


class LineItem(BaseModel):
    sku: str
    quantity: int = Field(ge=1, le=5)
    unit_price: float = Field(ge=1, le=500)


class Order(BaseModel):
    order_id: UUID
    line_items: list[LineItem]
    total: float
    status: Literal["pending", "shipped"]
    tracking_number: str | None
    created_at: datetime


class NewOrder(BaseModel):
    customer_id: UUID
    line_items: list[LineItem]


class CustomerNotFound(BaseModel):
    # A field default is returned verbatim under the default generation type, so error payloads
    # read like real ones instead of random strings.
    message: str = "Customer not found"


class ServiceUnavailable(BaseModel):
    message: str = "Inventory service unavailable"


class OrderFactory(ModelFactory[Order]):
    """
    Encodes the invariants a schema cannot express: prices are rounded to cents, the total
    matches the line items, and a tracking number exists exactly when the order has shipped.
    """

    @classmethod
    def build(cls, **kwargs) -> Order:
        order = super().build(**kwargs)

        for item in order.line_items:
            item.unit_price = round(item.unit_price, 2)

        order.total = round(sum(item.unit_price * item.quantity for item in order.line_items), 2)
        order.tracking_number = f"TRK-{cls.__faker__.numerify('########')}" \
            if order.status == "shipped" else None

        return order


def get_current_user() -> dict:
    """A dependency that would hit a real identity provider. fastmock never calls it."""
    raise RuntimeError("this dependency must never run while mocking")


app = FastAPI(title="Storefront")
app.add_middleware(
    FastMockMiddleware,
    provider_map={"sku": lambda faker: faker.bothify("???-####").upper()},
)

mock = FastMockDecorator()


@app.get("/customers",
         status_code=status.HTTP_200_OK,
         responses={status.HTTP_200_OK: {"model": list[Customer]}})
def list_customers(page: int = 1):
    return []


@app.get("/customers/{customer_id}",
         status_code=status.HTTP_200_OK,
         responses={
             status.HTTP_200_OK: {"model": Customer},
             status.HTTP_404_NOT_FOUND: {"model": CustomerNotFound},
         })
def get_customer(customer_id: UUID, user: dict = Depends(get_current_user)):
    return {}


@mock(factory=OrderFactory, element_size=3)
@app.get("/orders",
         status_code=status.HTTP_200_OK,
         responses={status.HTTP_200_OK: {"model": list[Order]}})
def list_orders():
    return []


@mock(factory=OrderFactory)
@app.post("/orders",
          status_code=status.HTTP_201_CREATED,
          # No 422 is declared: request validation returns a real FastAPI-shaped one regardless.
          responses={status.HTTP_201_CREATED: {"model": Order}})
def create_order(new_order: NewOrder):
    return {}


@mock(delay=0.3, fail_rate=0.3, fail_status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
@app.get("/inventory/{sku}",
         status_code=status.HTTP_200_OK,
         responses={
             status.HTTP_200_OK: {"model": dict[str, int]},
             status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ServiceUnavailable},
         })
def get_inventory(sku: str):
    raise HTTPException(status_code=500, detail="not implemented")
