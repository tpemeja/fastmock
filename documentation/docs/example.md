# A Complete Example

This page walks through a storefront API that is **entirely mocked**. Every endpoint has an empty
body, there is no database, and no dependency is ever called — yet the API answers with plausible,
reproducible data, validates incoming requests, and can be made slow or unreliable on demand.

The full source is at [`examples/storefront.py`](https://github.com/tpemeja/fastmock/blob/main/examples/storefront.py). Run it with:

```console
$ uvicorn examples.storefront:app --reload
```

## The setup

The only fastmock-specific lines are the middleware and the decorator:

```python
app = FastAPI(title="Storefront")
app.add_middleware(
    FastMockMiddleware,
    provider_map={"sku": lambda faker: faker.bothify("???-####").upper()},
)

mock = FastMockDecorator()
```

The `provider_map` entry teaches fastmock what a `sku` looks like in this domain. Everything else
is inferred from the models.

## Plausible data, for free

```python
class Customer(BaseModel):
    customer_id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    city: str
    country: str


@app.get("/customers",
         status_code=status.HTTP_200_OK,
         responses={status.HTTP_200_OK: {"model": list[Customer]}})
def list_customers(page: int = 1):
    return []
```

```console
$ curl http://127.0.0.1:8000/customers
```

```json
[
  {
    "customer_id": "29513b5f-6571-4a6f-8c4c-d0f46b431a46",
    "first_name": "Oscar",
    "last_name": "Gutierrez",
    "email": "charles35@yahoo.com",
    "city": "Cookhaven",
    "country": "Swaziland"
  },
  {
    "customer_id": "b087c2e9-0ba7-4e04-8d89-b6e369b09604",
    "first_name": "Joseph",
    "last_name": "Simmons",
    "email": "justin41@yahoo.com",
    "city": "East Maryville",
    "country": "Seychelles"
  }
]
```

Note where the values come from. `first_name`, `city` and `country` are resolved from the **field
name**. `email` and `customer_id` are resolved from their **types** — `EmailStr` and `UUID` need no
help. Nothing here was configured.

## Every response is addressable

The query string is part of the seed, so pagination behaves like real pagination — page 2 is
different from page 1, and both are stable:

```console
$ curl "http://127.0.0.1:8000/customers?page=2"
```

```json
[
  {
    "customer_id": "50e7433d-40fa-43c0-b8a7-cb726c48365e",
    "first_name": "Jennifer",
    "last_name": "Brown",
    "email": "brandilamb@hotmail.com",
    "city": "Austinburgh",
    "country": "Congo"
  },
  {
    "customer_id": "39077d45-6c87-4fdf-9c09-1e6bb7bccf85",
    "first_name": "Brenda",
    "last_name": "Jackson",
    "email": "wagnerdarlene@gmail.com",
    "city": "Robbinsmouth",
    "country": "North Macedonia"
  }
]
```

Refresh either page as often as you like and the rows stay put. That is what makes this usable for
a demo you present, a screenshot you paste into a ticket, or a test that asserts on a literal
value.

## Invariants a schema cannot express

An order has rules no type annotation captures: the total must match the line items, and a
tracking number should exist exactly when the order has shipped. fastmock does not guess at these
— you supply a factory:

```python
class OrderFactory(ModelFactory[Order]):
    @classmethod
    def build(cls, **kwargs) -> Order:
        order = super().build(**kwargs)

        for item in order.line_items:
            item.unit_price = round(item.unit_price, 2)

        order.total = round(sum(item.unit_price * item.quantity for item in order.line_items), 2)
        order.tracking_number = f"TRK-{cls.__faker__.numerify('########')}" \
            if order.status == "shipped" else None

        return order


@mock(factory=OrderFactory, element_size=3)
@app.get("/orders",
         status_code=status.HTTP_200_OK,
         responses={status.HTTP_200_OK: {"model": list[Order]}})
def list_orders():
    return []
```

```json
[
  {
    "order_id": "b8b66c37-791c-42d5-a13e-7e1560c795b9",
    "line_items": [
      {"sku": "RCN-2182", "quantity": 3, "unit_price": 58.52}
    ],
    "total": 175.56,
    "status": "pending",
    "tracking_number": null
  },
  {
    "order_id": "2427ab24-be2e-4426-969f-b2af1f577dc5",
    "line_items": [
      {"sku": "YNW-8861", "quantity": 3, "unit_price": 341.2}
    ],
    "total": 1023.6,
    "status": "shipped",
    "tracking_number": "TRK-14280550"
  }
]
```

`3 × 58.52 = 175.56`. The pending order has no tracking number; the shipped one does. The `sku`
values follow the `provider_map` rule from the setup. Note that the factory only had to express
what the schema *couldn't* — quantities, prices and statuses are still generated for you, within
the `Field(ge=..., le=...)` constraints declared on the model.

## Real validation, without real dependencies

```python
@app.get("/customers/{customer_id}",
         status_code=status.HTTP_200_OK,
         responses={
             status.HTTP_200_OK: {"model": Customer},
             status.HTTP_404_NOT_FOUND: {"model": CustomerNotFound},
         })
def get_customer(customer_id: UUID, user: dict = Depends(get_current_user)):
    return {}
```

`get_current_user` raises if it is ever called. It never is — mocking a route never resolves
`Depends(...)`, so no auth, database or network call fires.

Validation still happens. Posting a malformed body returns the same `422` a real FastAPI app
would, without `422` being declared in `responses` at all:

```console
$ curl -X POST http://127.0.0.1:8000/orders \
       -H 'content-type: application/json' \
       -d '{"customer_id": "nope", "line_items": []}'
```

```json
{
  "detail": [
    {
      "type": "uuid_parsing",
      "loc": ["body", "customer_id"],
      "msg": "Input should be a valid UUID, invalid character: found `n` at 1",
      "input": "nope",
      "ctx": {"error": "invalid character: found `n` at 1"}
    }
  ]
}
```

## Driving the mock from the client side

Any scalar setting can be overridden per request with an `X-FASTMOCK-` header, which means your
frontend can exercise an error path without anyone touching the server:

```console
$ curl -H "X-FASTMOCK-RESPONSE-STATUS-CODE: 404" \
       http://127.0.0.1:8000/customers/3fa85f64-5717-4562-b3fc-2c963f66afa6
```

```json
{"message": "Customer not found"}
```

That message is not random. `CustomerNotFound.message` declares a default, and the `default`
generation type returns field defaults verbatim — so error payloads read like real ones.

## Latency and failure

```python
@mock(delay=0.3, fail_rate=0.3, fail_status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
@app.get("/inventory/{sku}",
         status_code=status.HTTP_200_OK,
         responses={
             status.HTTP_200_OK: {"model": dict[str, int]},
             status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ServiceUnavailable},
         })
def get_inventory(sku: str):
    ...
```

Every call waits 300ms, and roughly three in ten fail with a `503`. Twenty calls in one run gave
thirteen `200`s and seven `503`s; another gave nineteen and one. That variation is deliberate —
**fault injection stays genuinely random even though payloads are deterministic**, so you can
exercise retry and error-handling logic that a fixed outcome would never reach.

!!! note "Reproducibility and time"
    Seeding fixes every generated value except `datetime` and `date` fields, which are produced
    relative to the current clock and therefore drift between runs. Two identical requests a
    minute apart return the same names, prices and identifiers, but timestamps that differ by
    about a minute. Pin them with a custom factory if a test needs to assert on them.

## What this replaces

Nothing in this example required writing a payload, a fixture file, or a handler body. The API
description *is* the mock. When the real implementation lands, delete the `@mock` decorators and
the middleware — the route signatures, response models and status codes were the contract all
along.
