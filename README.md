<p align="center">
  <a href="https://tpemeja.github.io/fastmock"><img src="https://github.com/tpemeja/fastmock/blob/main/documentation/docs/img/title.png?raw=true" alt="fastmock" style="width: 300px; height: 300px;"></a>
</p>
<p align="center">
    FastMock framework, mock your FastAPI APIs
</p>
<p align="center">
<a href="https://github.com/tpemeja/fastmock/actions/workflows/test.yml" target="_blank">
    <img src="https://github.com/tpemeja/fastmock/workflows/Test/badge.svg" alt="Test">
</a>
<a href="https://coveralls.io/github/tpemeja/fastmock?branch=main" target="_blank">
    <img src="https://coveralls.io/repos/github/tpemeja/fastmock/badge.svg?branch=main" alt="Coverage">
</a>
<a href="https://pypi.org/project/fastmock" target="_blank">
    <img src="https://img.shields.io/pypi/v/fastmock?color=%2334D058&label=pypi%20package" alt="Package version">
</a>
</p>

---

**Documentation**: <a href="https://tpemeja.github.io/fastmock" target="_blank">https://tpemeja.github.io/fastmock</a>

**Source Code**: <a href="https://github.com/tpemeja/fastmock" target="_blank">https://github.com/tpemeja/fastmock</a>

---

FastMock is a Python framework designed to mock FastAPI APIs based on response models.

Key features of this project include:

- **Ease of Use**: Simply add the middleware to start mocking your APIs.
- **Flexibility**: Mocking can be customized through various parameters, such as activation, data generation, length, status codes, and more.
- **Modularity**: The package includes default functions to retrieve mocking parameters from API declarations to request headers. However, all these functions can be modified, allowing you to create your own custom functions.

## Requirements

This package is build to be used with FastAPI, please learn on to use it on their well documented website - <a href="https://fastapi.tiangolo.com/" class="external-link" target="_blank">FastAPI Documentation</a>


To mock an API, you need to describe the API using FastAPI's decorator key `responses`. 

For example:
```python
@app.get("/",
         status_code=status.HTTP_200_OK,
         responses={
             status.HTTP_200_OK: {"model": list[int]},
             status.HTTP_404_NOT_FOUND: {"model": str}
         })
```


## Installation

<div class="termy">

```console
$ pip install fastmock

---> 100%
```

</div>

## Example

### Create it

* Create a file `main.py` with:
```Python hl_lines="4-5  8  11  28"
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


@app.get("/",
         status_code=status.HTTP_200_OK,
         responses={
             status.HTTP_200_OK: {"model": dict[str, str]}
         })
def read_root():
    return {"Hello": "World"}


@mock(element_size=3)
@app.get("/items",
         status_code=status.HTTP_200_OK,
         responses={
             status.HTTP_200_OK: {"model": list[Item]}
         })
def read_items():
    return []
```

* Start the server with `uvicorn main:app` 
### Check it

Open your browser at <a href="http://127.0.0.1:8000/items" class="external-link" target="_blank">http://127.0.0.1:8000/items</a>.

You will see the JSON response as:

```JSON
[
  {
    "name": "fuquvERvYTfWVEbYRKgi",
    "price": 18164954265977.8,
    "is_offer": null
  },
  {
    "name": "akMCejCxOhMjgGMPMrcb",
    "price": 40.3130726635657,
    "is_offer": null
  },
  {
    "name": "uEONHBXGCirPDrLJKgXu",
    "price": -9.23356705084994,
    "is_offer": null
  }
]
```

You just created an API using FastAPI that:

* Return value generated from defined response model
* Modify output list size using decorator


## Inspiration

* A project idea that came from my use of [FastAPI](https://github.com/tiangolo/fastapi) by **tiangolo**, the GitHub project inspired me for the structure and documentation of this project.
* Ideas and code for data generation with Faker inspired by **NiyazNz** in the [fastapi-mock-middleware project](https://github.com/NiyazNz/fastapi-mock-middleware).


## License

This project is licensed under the terms of the MIT license.
