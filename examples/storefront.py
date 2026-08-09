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

from fastapi import Depends, FastAPI, HTTPException, Request, status
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel, EmailStr, Field

from fastmock.decorator import FastMockDecorator
from fastmock.middleware import FastMockMiddleware
from fastmock.tools import get_data_from_decorator_route, get_data_from_header


class Customer(BaseModel):
    customer_id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    city: str
    country: str

    # Returned verbatim under the `example` generation type, for when a screenshot or a test
    # needs one specific, hand-chosen payload.
    model_config = {
        "json_schema_extra": {
            "example": {
                "customer_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "first_name": "Ada",
                "last_name": "Lovelace",
                "email": "ada@example.com",
                "city": "London",
                "country": "United Kingdom",
            }
        }
    }


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


#: Named bundles of settings, so a tester can reach a whole situation with one query parameter
#: instead of remembering which combination of headers produces it.
SCENARIOS = {
    "empty": {"element_size": 0},
    "bulk": {"element_size": 25},
    "slow": {"delay": 1.5},
    "alt": {"seed": 99},
}


def get_data_from_scenario(request: Request) -> dict:
    """
    A custom retrieval function: reads `?scenario=` and expands it into mock settings.

    Retrieval functions are plain callables taking the request and returning a dict of MockData
    fields. Returning an empty dict means "no opinion", leaving earlier sources untouched.
    """
    return SCENARIOS.get(request.query_params.get("scenario", ""), {})


app = FastAPI(title="Storefront")
app.add_middleware(
    FastMockMiddleware,
    provider_map={"sku": lambda faker: faker.bothify("???-####").upper()},
    # Ordered least to most important. Slotting scenarios between the decorator and the header
    # keeps headers as the final say.
    retrieve_data_function_list=[
        get_data_from_decorator_route,
        get_data_from_scenario,
        get_data_from_header,
    ],
)

#: Defaults shared by every decorated route, overridable per route and per request.
mock = FastMockDecorator(validate_request=True)


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
