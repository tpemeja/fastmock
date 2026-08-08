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
    """
    activate: bool = True
    element_size: int = 2
    type: GenerationTypeEnum = GenerationTypeEnum.default
    response_status_code: int | None = None
    delay: float = 0
    fail_rate: float = Field(default=0, ge=0, le=1)
    fail_status_code: int | None = None
    validate_request: bool = True
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

