# A Complete Example

This page walks through a storefront API that is **entirely mocked**. Every endpoint has an empty
body, there is no database, and no dependency is ever called — yet the API answers with plausible,
reproducible data, validates incoming requests, and can be made slow or unreliable on demand.

The full source is at [`examples/storefront.py`](https://github.com/tpemeja/fastmock/blob/main/examples/storefront.py). Run it from the repository root with:

```console
$ uv sync --group examples
$ uv run uvicorn examples.storefront:app --reload
```

!!! tip "Use `uv run`"
    A bare `uvicorn` can resolve to a system-wide install even with the project virtualenv
    activated, because `PATH` finds that copy first. It then runs under a different interpreter
    and fails with `ModuleNotFoundError: No module named 'polyfactory'`. `uv run` always uses the
    project environment.

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

Every scalar setting can be overridden **per request** with a header. The rule is
`X-FASTMOCK-<PARAMETER>`, with dashes standing in for underscores — `element_size` becomes
`X-FASTMOCK-ELEMENT-SIZE`. Matching is case-insensitive.

Headers sit at the top of the precedence chain, so they beat the decorator *and* the middleware
configuration. That means a frontend developer can reshape the API from the client side without
anyone restarting a server or editing Python.

| Header | Effect |
| --- | --- |
| `X-FASTMOCK-ELEMENT-SIZE` | How many items a list response contains |
| `X-FASTMOCK-SEED` | Switch to a different, equally stable data set |
| `X-FASTMOCK-RESPONSE-STATUS-CODE` | Return a specific declared response |
| `X-FASTMOCK-DELAY` | Add or remove latency |
| `X-FASTMOCK-FAIL-RATE` | Force or suppress failures |
| `X-FASTMOCK-TYPE` | Switch between `default`, `example` and `generated` |
| `X-FASTMOCK-VALIDATE-REQUEST` | Turn request validation off |
| `X-FASTMOCK-ACTIVATE` | Turn mocking off entirely for this request |

### Ask for more rows

```console
$ curl -H "X-FASTMOCK-ELEMENT-SIZE: 5" http://127.0.0.1:8000/customers
```

```
Oscar, Joseph, Jasmine, Lisa, Patricia
```

The baseline response was `Oscar, Joseph`. Asking for five did not reshuffle anything — it
extended the same sequence, because the seed depends on the request, not on how much of the
result you asked for.

### Switch to a different data set

```console
$ curl -H "X-FASTMOCK-SEED: 99" http://127.0.0.1:8000/customers
```

```json
[
  {
    "customer_id": "46b32ea5-21f2-418f-bcd7-0b6e1503afbe",
    "first_name": "Tiffany",
    "last_name": "Romero",
    "email": "amber56@gmail.com",
    "city": "South Jenny",
    "country": "Djibouti"
  },
  {
    "customer_id": "645cb376-e384-43cc-9744-a4928d75a69b",
    "first_name": "Christina",
    "last_name": "Mendoza",
    "email": "bthomas@gmail.com",
    "city": "Johnsonbury",
    "country": "China"
  }
]
```

Different people, but just as stable: send that header again and Tiffany and Christina come back.
This is how you keep several fixed data sets on hand — one per seed — without configuring any of
them in advance.

### Exercise an error path

```console
$ curl -H "X-FASTMOCK-RESPONSE-STATUS-CODE: 404" \
       http://127.0.0.1:8000/customers/3fa85f64-5717-4562-b3fc-2c963f66afa6
```

```json
{"message": "Customer not found"}
```

That message is not random. `CustomerNotFound.message` declares a default, and the `default`
generation type returns field defaults verbatim — so error payloads read like real ones.

### Override what the decorator asked for

`/inventory/{sku}` is decorated with `delay=0.3, fail_rate=0.3`. Headers outrank that, so you can
force the failure you want to test instead of retrying until chance delivers it:

```console
$ curl -H "X-FASTMOCK-FAIL-RATE: 1" -H "X-FASTMOCK-DELAY: 0" \
       http://127.0.0.1:8000/inventory/ABC-1234
```

```json
{"message": "Inventory service unavailable"}
```

Returned as `503`, instantly — the declared 300ms wait drops to under a millisecond. The same
works in reverse: `X-FASTMOCK-FAIL-RATE: 0` gives you a reliable endpoint while you work on
something else.

### Skip validation, or stop mocking altogether

`X-FASTMOCK-VALIDATE-REQUEST: false` accepts a body that would otherwise be rejected, which is
useful while a client is still being written:

```console
$ curl -X POST -H "X-FASTMOCK-VALIDATE-REQUEST: false" \
       -H 'content-type: application/json' \
       -d '{"customer_id": "nope", "line_items": []}' \
       http://127.0.0.1:8000/orders
```

Returns `201` with a generated order rather than the `422` shown earlier.

`X-FASTMOCK-ACTIVATE: false` goes further and takes fastmock out of the way entirely, so the
request reaches your real handler. On this example that returns `[]`, since `list_customers` has
an empty body — which is a quick way to check which endpoints are genuinely implemented yet.

!!! note "One parameter has no header"
    `factory` is a callable, and a header can only carry text. It is the single setting that must
    be applied through the decorator or the middleware.

## Choosing how values are generated

`type` selects where a value comes from, and the three modes answer different needs.

**`default`** — the default — honours field defaults. That is why the `404` above reads
`{"message": "Customer not found"}`: `CustomerNotFound.message` declares that default, and it is
returned verbatim.

**`generated`** ignores defaults and generates everything, which is how you check that a client
does not quietly depend on a default:

```console
$ curl -H "X-FASTMOCK-RESPONSE-STATUS-CODE: 404" -H "X-FASTMOCK-TYPE: generated" \
       http://127.0.0.1:8000/customers/3fa85f64-5717-4562-b3fc-2c963f66afa6
```

```json
{"message": "ViooIuwICvLeOqKnuUUQ"}
```

**`example`** returns a hand-written payload from the model's `json_schema_extra`, for when a
screenshot or an assertion needs one specific set of values:

```python
class Customer(BaseModel):
    ...
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
```

```console
$ curl -H "X-FASTMOCK-TYPE: example" \
       http://127.0.0.1:8000/customers/3fa85f64-5717-4562-b3fc-2c963f66afa6
```

```json
{
  "customer_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "first_name": "Ada",
  "last_name": "Lovelace",
  "email": "ada@example.com",
  "city": "London",
  "country": "United Kingdom"
}
```

The example lives in the schema, so it also shows up in your OpenAPI docs — it is documentation
and mock data at once, rather than a fixture file that drifts out of sync.

## Teaching fastmock your own vocabulary

Headers are flexible but low-level: reproducing "the empty state, but slow" means remembering
which combination to send. `retrieve_data_function_list` lets you add your own source of settings.

A retrieval function is a plain callable that takes the request and returns a dict of `MockData`
fields. Returning an empty dict means "no opinion". Here one expands a `?scenario=` parameter
into a bundle:

```python
SCENARIOS = {
    "empty": {"element_size": 0},
    "bulk": {"element_size": 25},
    "slow": {"delay": 1.5},
    "alt": {"seed": 99},
}


def get_data_from_scenario(request: Request) -> dict:
    return SCENARIOS.get(request.query_params.get("scenario", ""), {})


app.add_middleware(
    FastMockMiddleware,
    retrieve_data_function_list=[
        get_data_from_decorator_route,
        get_data_from_scenario,
        get_data_from_header,
    ],
)
```

```console
$ curl "http://127.0.0.1:8000/customers?scenario=empty"   # []            - empty-state UI
$ curl "http://127.0.0.1:8000/customers?scenario=bulk"    # 25 customers  - pagination, overflow
$ curl "http://127.0.0.1:8000/customers?scenario=slow"    # 1.5s          - spinners, timeouts
$ curl "http://127.0.0.1:8000/customers?scenario=alt"     # different people
```

Now a bug report can say *"open `?scenario=bulk`"* instead of listing headers. The same hook can
read settings from a cookie, a JWT claim, or a per-tenant config — anywhere a request carries
information you want to mock by.

!!! note "Query strings feed the seed"
    `?scenario=alt` sets `seed=99`, but its data differs from sending `X-FASTMOCK-SEED: 99` with
    no query string, because the query string is itself part of the seed. Both are perfectly
    stable; they are simply two different stable data sets.

## Where settings come from

Four sources are consulted in order, each overriding the last:

| # | Source | Scope |
| --- | --- | --- |
| 1 | `FastMockMiddleware(mock_data=...)` | Every route |
| 2 | `FastMockDecorator(...)` | Every route using that decorator |
| 3 | `@mock(...)` on a route | That route |
| 4 | `X-FASTMOCK-` headers | That request |

The example inserts scenarios between 3 and 4, so a header still has the final say — which is why
`?scenario=bulk` with `X-FASTMOCK-ELEMENT-SIZE: 2` returns two customers, not twenty-five.

Level 2 is easy to overlook. `mock = FastMockDecorator(validate_request=True)` sets a house style
once, and every `@mock` route inherits it:

```python
mock = FastMockDecorator(validate_request=True)

@mock(factory=OrderFactory, element_size=3)   # inherits validate_request
@app.get("/orders", ...)
def list_orders():
    return []
```

!!! warning "The decorator carries a full MockData"
    A decorated route supplies *every* field, not only the ones you named — so its defaults
    override the middleware. If `@mock(factory=...)` sits on a route, that route uses the
    decorator's `element_size`, not the middleware's. Set the value on the decorator, or override
    it per request with a header.

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
