import pytest
from tests.clients import (decorator_client, decorator_initialization_client,
                           middleware_client, header_client)


@pytest.mark.parametrize("get_client", [
    middleware_client.get_client,
    decorator_client.get_client,
    decorator_initialization_client.get_client,
    header_client.get_client
])
@pytest.mark.parametrize("response_type", ["example", "default", "generated"])
def test_fastmock_model_response_value(get_client, response_type: str):
    client = get_client(type=response_type)
    response = client.get("/device")
    assert response.status_code == 200

    match response_type:
        case "example":
            assert response.json() == {
                "device_uuid": "DEVX000001",
                "localisation": {
                    "latitude": 35.6582,
                    "longitude": 139.8752
                },
                "deployment_date": "2024-03-14",
                "owner": "tanguy.pemeja@gmail.com"
            }
        case "default":
            assert response.json() != {
                "device_uuid": "DEVX000001",
                "localisation": {
                    "latitude": 35.6582,
                    "longitude": 139.8752
                },
                "deployment_date": "2024-03-14",
                "owner": "tanguy.pemeja@gmail.com"
            }
            assert list(response.json().keys()) == ['device_uuid', 'localisation', 'deployment_date', 'owner']
            assert response.json()["localisation"] is None and response.json()["deployment_date"] is None

        case "generated":
            assert response.json() != {
                "device_uuid": "DEVX000001",
                "localisation": {
                    "latitude": 35.6582,
                    "longitude": 139.8752
                },
                "deployment_date": "2024-03-14",
                "owner": "tanguy.pemeja@gmail.com"
            }
            assert list(response.json().keys()) == ['device_uuid', 'localisation', 'deployment_date', 'owner']
            assert (response.json()["localisation"] is not None
                    and response.json()["deployment_date"] is not None)
        case _:
            assert False


@pytest.mark.parametrize("get_client", [
    middleware_client.get_client,
    decorator_client.get_client,
    decorator_initialization_client.get_client,
    header_client.get_client
])
@pytest.mark.parametrize("response_type", ["example", "default", "generated"])
def test_fastmock_str_response_value(get_client, response_type: str):
    try:
        client = get_client(type=response_type)
        response = client.get("/str")
        assert response.status_code == 200

        match response_type:
            case "default":
                assert type(response.json()) == str
            case "generated":
                assert type(response.json()) == str
            case _:
                assert False

    except Exception as e:
        match response_type:
            case "example":
                assert str(e) == "Mock using model example but no example found for the API"
            case _:
                assert False
