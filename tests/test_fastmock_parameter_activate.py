import pytest
from tests.clients import (decorator_client, decorator_initialization_client,
                           middleware_client, header_client)


@pytest.mark.parametrize("get_client", [
    middleware_client.get_client,
    decorator_client.get_client,
    decorator_initialization_client.get_client,
    header_client.get_client
])
@pytest.mark.parametrize("activate", [True, False])
def test_fastmock_activation(get_client, activate: bool):
    client = get_client(activate=activate, type="example")
    response = client.get("/device")
    assert response.status_code == 200

    if activate:
        assert response.json() == {
            "device_uuid": "DEVX000001",
            "localisation": {
                "latitude": 35.6582,
                "longitude": 139.8752
            },
            "deployment_date": "2024-03-14",
            "owner": "tanguy.pemeja@gmail.com"
        }
    else:
        assert response.json() == {'msg': 'Device'}


@pytest.mark.parametrize("get_client", [
    middleware_client.get_client,
    decorator_client.get_client,
    decorator_initialization_client.get_client,
    header_client.get_client
])
@pytest.mark.parametrize("value_type", ["dict", "list", "device", "str", "int"])
def test_fastmock_activation_value(get_client, value_type: str):
    client = get_client(activate=False)
    response = client.get(f"/{value_type}")
    assert response.status_code == 200
    assert response.json().get("msg", False)
