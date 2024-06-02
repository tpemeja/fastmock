import pytest
from tests.clients import (decorator_client, decorator_initialization_client,
                           middleware_client, header_client)


@pytest.mark.parametrize("get_client", [
    middleware_client.get_client,
    decorator_client.get_client,
    decorator_initialization_client.get_client,
    header_client.get_client
])
@pytest.mark.parametrize("value_type", ["dict", "list", "device", "str"])
def test_fastmock_response_type(get_client, value_type: str):
    try:
        client = get_client(type='example')
        response = client.get(f"/{value_type}")
        assert response.status_code == 200

        match value_type:
            case "dict":
                assert isinstance(response.json(), dict)
                for value in response.json().values():
                    assert value == {
                        "device_uuid": "DEVX000001",
                        "localisation": {
                            "latitude": 35.6582,
                            "longitude": 139.8752
                        },
                        "deployment_date": "2024-03-14",
                        "owner": "tanguy.pemeja@gmail.com"
                    }
            case "list":
                assert isinstance(response.json(), list)
                for value in response.json():
                    assert value == {
                        "device_uuid": "DEVX000001",
                        "localisation": {
                            "latitude": 35.6582,
                            "longitude": 139.8752
                        },
                        "deployment_date": "2024-03-14",
                        "owner": "tanguy.pemeja@gmail.com"
                    }
            case "device":
                assert response.json() == {
                    "device_uuid": "DEVX000001",
                    "localisation": {
                        "latitude": 35.6582,
                        "longitude": 139.8752
                    },
                    "deployment_date": "2024-03-14",
                    "owner": "tanguy.pemeja@gmail.com"
                }
            case _:
                assert False

    except Exception as e:
        match value_type:
            case "str":
                assert str(e) == "Mock using model example but no example found for the API"
            case _:
                assert False
