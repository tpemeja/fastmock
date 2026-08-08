# Mock Data Middleware

## Overview

The Mock Data Middleware allows you to easily configure and manage mock responses for your FastAPI application. This document provides a comprehensive guide on how to use decorators to specify mocking behavior for your APIs.

## Decorator Usage

You can use the decorator to describe the mocking behavior for specific APIs. The default parameters will be derived from the `FastMockDecorator` declaration using `@mock` or `@mock()`. However, you can also specify parameter values for each API individually.

To utilize the decorator, initialize it and apply it to your API endpoint as shown in the following example:

```python hl_lines="4  10  17"
from fastapi import FastAPI, status
from pydantic import BaseModel

from fastmock.decorator import FastMockDecorator
from fastmock.middleware import FastMockMiddleware

app = FastAPI()
app.add_middleware(FastMockMiddleware)

mock = FastMockDecorator()

class Item(BaseModel):
    name: str
    price: float
    is_offer: bool | None = None

@mock(element_size=3)
@app.get("/items",
         status_code=status.HTTP_200_OK,
         responses={
             status.HTTP_200_OK: {"model": list[Item]}
         })
def read_items():
    return []
```

In the code above, the decorator `@mock(element_size=3)` overrides the default middleware parameters, setting the element size of the API output to 3.

## Request Header
You can override the default middleware parameters using request headers.
Each parameter can be overridden by using the `X-FASTMOCK-<PARAMETER>` format.
For example, to set the element size of the API output to 3, you can send the header `X-FASTMOCK-ELEMENT-SIZE: 3` as shown below:
```
curl -H "X-FASTMOCK-ELEMENT-SIZE: 3" http://127.0.0.1:8000/items
```

Note that `factory` is the one parameter without a header equivalent, since a header can only carry text.

## Field Name Providers

Polyfactory picks values from a field's *type*, never its name, so a field called `country` would otherwise hold a random string. fastmock ships a small map from common field names to Faker providers — `first_name`, `city`, `country`, `email`, `url` and similar — so that generated data reads like real data.

The map is deliberately conservative and matched exactly, never by substring. A plausible-looking but wrong value is worse than obvious gibberish: gibberish tells you to reach for a custom factory, whereas a country name where your client expects an ISO code quietly misleads. For the same reason a bare `name` is absent, being as likely to describe a product or a company as a person.

A provider is only applied when the value it produces exactly matches the field's declared type, so a `city` field annotated as an `int` still generates an int. Semantically typed fields such as `EmailStr` are left to polyfactory, which already handles them.

Extend or override the map with `provider_map`:

```python
app.add_middleware(
    FastMockMiddleware,
    provider_map={"sku": lambda faker: faker.bothify("???-####")},
)
```

Entries are merged over the defaults, so the example above adds `sku` while leaving everything else in place. Pass an empty mapping to switch name-based inference off entirely:

```python
app.add_middleware(FastMockMiddleware, provider_map={})
```

`provider_map` is global policy rather than per-request state, which is why it lives on the middleware rather than on `MockData`. If a single route needs different values, use a [custom factory](mock-data.md#custom-factories) instead.

## Data Retrieval Order
During middleware initialization, you can provide custom functions to override the default data retrieval functions or their order with the attribute `retrieve_data_function_list`.
The default order of operations is as follows, with each step potentially overriding the data from the previous step if parameters are defined:

1.  Middleware initialization
2.  Decorator initialization
3.  API Decorator
4.  Header request

This structure ensures that headers can dynamically adjust the behavior of the middleware on a per-request basis.