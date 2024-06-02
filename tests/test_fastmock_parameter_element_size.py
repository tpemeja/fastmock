import pytest
from tests.clients import (decorator_client, decorator_initialization_client,
                           middleware_client, header_client)


@pytest.mark.parametrize("get_client", [
    middleware_client.get_client,
    decorator_client.get_client,
    decorator_initialization_client.get_client
])
@pytest.mark.parametrize("size", [1, 2, 5])
def test_fastmock_list_size_response(get_client, size: int):
    client = get_client(element_size=size, type='example')
    response = client.get("/list")
    assert response.status_code == 200
    assert response.json() == [{
        "device_uuid": "DEVX000001",
        "localisation": {
            "latitude": 35.6582,
            "longitude": 139.8752
        },
        "deployment_date": "2024-03-14",
        "owner": "tanguy.pemeja@gmail.com"
    }] * size


@pytest.mark.parametrize("get_client", [
    middleware_client.get_client,
    decorator_client.get_client,
    decorator_initialization_client.get_client,
    header_client.get_client
])
@pytest.mark.parametrize("size", [1, 2, 5])
def test_fastmock_dict_size_response(get_client, size: int):
    client = get_client(element_size=size, type='example')
    response = client.get("/dict")
    assert response.status_code == 200
    assert list(response.json().values()) == [{
        "device_uuid": "DEVX000001",
        "localisation": {
            "latitude": 35.6582,
            "longitude": 139.8752
        },
        "deployment_date": "2024-03-14",
        "owner": "tanguy.pemeja@gmail.com"
    }] * size
