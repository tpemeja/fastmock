# Mock Data Configuration

## Overview

This documentation describes the configuration options available for defining mock data in your application.
The configuration is defined using the `MockData` model, which allows you to specify various parameters for generating mock responses.

## Enumeration: GenerationTypeEnum

The `GenerationTypeEnum` is an enumeration that specifies the type of generation for mock data. It includes the following options:

- **default**: Represents default data.
- **example**: Represents example data.
- **generated**: Represents data generated dynamically.

```python
class GenerationTypeEnum(str, Enum):
    """
    Enumeration for the type of generation for mock data.

    Attributes:
        default (str): Represents default data.
        example (str): Represents example data.
        generated (str): Represents data generated dynamically.
    """
    default = 'default'
    example = 'example'
    generated = 'generated'
```

## Model: MockData
The MockData model is used to define the configuration for mock data generation. It includes the following attributes:

* **activate (bool)**: Flag to activate or deactivate mock responses. Defaults to `True`.
* **element_size (int)**: Number of elements to be included in the mock response. Defaults to `2`.
* **type (GenerationTypeEnum)**: The type of data generation. Defaults to `GenerationTypeEnum.default`.
* **response_status_code (int | None)**: HTTP status code for the mock response. If None, a default status code is used.
* **delay (float)**: Number of seconds to wait before returning the mock response. Defaults to `0`.
* **fail_rate (float)**: Probability, between `0` and `1`, that a request returns `fail_status_code` instead of the normal mock response. Defaults to `0`.
* **fail_status_code (int | None)**: HTTP status code to return when a request fails per `fail_rate`. Required if `fail_rate` is greater than `0`.
* **validate_request (bool)**: Whether to validate the request's path, query, header, cookie, and body parameters against the endpoint's declared types before mocking a response. Defaults to `True`.
* **seed (int | None)**: Base seed making responses reproducible. Set to `None` for freshly generated data on every request. Defaults to `1`.
* **factory (Any)**: A polyfactory factory used to build the response instead of deriving one from the response model. Defaults to `None`.

```python
class MockData(BaseModel):
    """
    Model for defining mock data configurations.

    Attributes:
        activate (bool): Flag to activate or deactivate mock responses. Defaults to True.
        element_size (int): Number of elements to be included in the mock response. Defaults to 2.
        type (GenerationTypeEnum): The type of data generation. Defaults to GenerationTypeEnum.default.
        response_status_code (int | None): HTTP status code for the mock response. If None, a default status code is used.
        delay (float): Number of seconds to wait before returning the mock response. Defaults to 0.
        fail_rate (float): Probability (0-1) of returning `fail_status_code` instead of the normal
            mock response. Defaults to 0.
        fail_status_code (int | None): HTTP status code to return when a request fails per
            `fail_rate`. Required if `fail_rate` is greater than 0.
        validate_request (bool): Whether to validate the request's path, query, header, cookie,
            and body parameters against the endpoint's declared types before mocking a response,
            returning a 422 on mismatch just like a real FastAPI implementation would. Defaults
            to True.
        seed (int | None): Base seed making responses reproducible. With a seed set, a response
            is a pure function of the request. Set to None for a freshly generated response every
            time. Defaults to 1.
        factory (Any): A polyfactory factory used to build the response instead of deriving one
            from the response model. Takes precedence over `type`. Defaults to None.
    """
    activate: bool = True
    element_size: int = 2
    type: GenerationTypeEnum = GenerationTypeEnum.default
    response_status_code: int | None = None
    delay: float = 0
    fail_rate: float = Field(default=0, ge=0, le=1)
    fail_status_code: int | None = None
    validate_request: bool = True
    seed: int | None = 1
    factory: Any = None
```

### Usage Example
Here is an example of how you can use the MockData model to configure mock data generation:
```python
mock_data_config = MockData(
    activate=True,
    element_size=5,
    type=GenerationTypeEnum.generated,
    response_status_code=200
)

print(mock_data_config)
```

In this example, the mock data generation is activated, five elements will be included in the mock response,
the data type is set to generated, and the HTTP response status code is set to 200.

## Fault Injection

`delay` and `fail_rate` let you simulate an unreliable or slow upstream API without writing any extra code, which is useful for testing how your frontend or downstream services handle latency and failures.

* **delay** adds a fixed, deterministic wait (in seconds) before every mocked response.
* **fail_rate** is the probability that a request is answered with `fail_status_code` instead of its normal mock response. `fail_status_code` must be one of the route's declared `responses`, the same rule that applies to `response_status_code`.

```python
@mock(delay=0.5, fail_rate=0.2, fail_status_code=503)
@app.get("/items",
         status_code=status.HTTP_200_OK,
         responses={
             status.HTTP_200_OK: {"model": list[Item]},
             status.HTTP_503_SERVICE_UNAVAILABLE: {"model": str}
         })
def read_items():
    return []
```

In this example, every call to `/items` waits half a second, and roughly 20% of requests return a `503` instead of the item list.

Setting `fail_rate` to `1` always fails (useful for deterministically testing an error path), and the default `fail_rate` of `0` never does.

## Request Validation

By default, fastmock validates an incoming request's path, query, header, cookie, and body parameters against the endpoint's declared types before generating a mock response, exactly like a real FastAPI implementation would. A mismatch returns a standard FastAPI `422` validation error, without needing you to declare `422` in the route's `responses`.

```python
@app.post("/items",
          status_code=status.HTTP_200_OK,
          responses={
              status.HTTP_200_OK: {"model": Item}
          })
def create_item(item: Item, quantity: int) -> Item:
    return item
```

Calling `POST /items` with a body that doesn't match `Item`, or without the required `quantity` query parameter, returns a `422` with the same error shape a real FastAPI app would produce — without you writing `create_item`'s body at all.

Only the parameters declared directly on the endpoint are validated. Any `Depends(...)` dependencies are never resolved or called, so mocking a route never triggers real authentication, database access, or other side-effecting dependencies.

Set `validate_request=False` to disable this and go back to accepting any request, useful for quick prototyping when you don't want to match the schema exactly yet.

## Reproducible Responses

By default, a mocked response is a **pure function of the request**. The same method, path, query string and body always produce the same data — across page refreshes, server restarts and machines.

```console
$ curl http://127.0.0.1:8000/customers/1
{"first_name": "Patricia", "last_name": "Burgess", "city": "New Erichaven", "country": "Paraguay", "is_active": null}

$ curl http://127.0.0.1:8000/customers/1   # same request, same data
{"first_name": "Patricia", "last_name": "Burgess", "city": "New Erichaven", "country": "Paraguay", "is_active": null}

$ curl http://127.0.0.1:8000/customers/2   # different resource, different data
{"first_name": "Tyler", "last_name": "Weber", "city": "New Melissaburgh", "country": "Trinidad and Tobago", "is_active": null}
```

This is what makes generated data usable beyond a placeholder: a demo doesn't reshuffle every time someone refreshes, an integration test can assert on a literal payload, and a colleague reproducing a bug sees the values you saw.

The `seed` acts as a base mixed into every request. Change it to shift the entire data set at once:

```python
@mock(seed=42)
```

Because `seed` is a plain integer, it can also be overridden per request through the `X-FASTMOCK-SEED` header, which is handy for flipping between data sets without restarting.

Set `seed=None` to generate fresh data on every request instead.

!!! note "Fault injection stays random"
    `fail_rate` is deliberately unaffected by seeding, so a flaky endpoint stays genuinely flaky while its payloads remain stable. If you want an endpoint to fail *predictably*, use `fail_rate=1` or `response_status_code`.

Form and multipart bodies are excluded from the seed, since upload boundaries would make it unstable, and only the first 64KB of any body contributes.

Temporal fields are covered by this too. `datetime`, `date`, `time` and `timedelta` values are drawn from a fixed window rather than relative to the current clock, so a timestamp generated today is the same one you get next week. Without that, a seed would only fix the *offset* from "now" and every timestamp would quietly drift between runs.

## Custom Factories

fastmock generates data that is plausible **field by field**. It does not infer relationships *between* fields — that a `total` should equal the sum of its line items, or that a `tracking_number` should be present exactly when `status` is `"shipped"`. Those invariants live in your domain, not in the schema.

When they matter, hand fastmock a [polyfactory](https://polyfactory.litestar.dev/) factory and it will use that instead of deriving one from the response model:

```python
from polyfactory.factories.pydantic_factory import ModelFactory

class OrderFactory(ModelFactory[Order]):
    @classmethod
    def build(cls, **kwargs) -> Order:
        line_items = [LineItem(price=10.0), LineItem(price=5.5)]
        return Order(
            line_items=line_items,
            total=sum(item.price for item in line_items),
            status="shipped",
            tracking_number="TRACK-123",
        )

@mock(factory=OrderFactory)
@app.get("/orders",
         status_code=status.HTTP_200_OK,
         responses={
             status.HTTP_200_OK: {"model": list[Order]}
         })
def list_orders():
    return []
```

The factory is applied per element for list responses, and takes precedence over `type`. Being a callable, it is the one parameter that cannot be set through a request header.

