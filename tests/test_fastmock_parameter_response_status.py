import pytest
from tests.clients import (decorator_client, decorator_initialization_client,
                           middleware_client, header_client)


@pytest.mark.parametrize("get_client", [
    middleware_client.get_client,
    decorator_client.get_client,
    decorator_initialization_client.get_client,
    header_client.get_client
])
@pytest.mark.parametrize("response_status_code", [200, 404, 409])
def test_fastmock_status_code(get_client, response_status_code: int):
    try:
        client = get_client(response_status_code=response_status_code, type='example')
        response = client.get("/device")
        assert response.status_code == 200

    except Exception as e:
        if response_status_code == 404:
            assert str(e) == "Mock using model example but no example found for the API"
        elif response_status_code == 409:
            assert str(e) == "Mock status code not defined in API declaration"
        else:
            assert False
