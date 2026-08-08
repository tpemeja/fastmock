import time

import pytest
from tests.clients import (decorator_client, decorator_initialization_client,
                           middleware_client, header_client)


@pytest.mark.parametrize("get_client", [
    middleware_client.get_client,
    decorator_client.get_client,
    decorator_initialization_client.get_client,
    header_client.get_client
])
def test_fastmock_delay(get_client):
    delay = 0.05
    client = get_client(delay=delay)

    start = time.monotonic()
    response = client.get("/device")
    elapsed = time.monotonic() - start

    assert response.status_code == 200
    assert elapsed >= delay


@pytest.mark.parametrize("get_client", [
    middleware_client.get_client,
    decorator_client.get_client,
    decorator_initialization_client.get_client,
    header_client.get_client
])
def test_fastmock_no_fail_by_default(get_client):
    client = get_client()
    response = client.get("/device")
    assert response.status_code == 200


@pytest.mark.parametrize("get_client", [
    middleware_client.get_client,
    decorator_client.get_client,
    decorator_initialization_client.get_client,
    header_client.get_client
])
def test_fastmock_fail_rate_returns_fail_status_code(get_client):
    client = get_client(fail_rate=1, fail_status_code=404)
    response = client.get("/device")
    assert response.status_code == 404
    assert response.json() == {"message": "Device not found"}


@pytest.mark.parametrize("get_client", [
    middleware_client.get_client,
    decorator_client.get_client,
    decorator_initialization_client.get_client,
    header_client.get_client
])
def test_fastmock_fail_rate_without_fail_status_code(get_client):
    try:
        client = get_client(fail_rate=1)
        client.get("/device")
        assert False
    except Exception as e:
        assert str(e) == "Mock fail_rate is set but no fail_status_code was defined"


@pytest.mark.parametrize("get_client", [
    middleware_client.get_client,
    decorator_client.get_client,
    decorator_initialization_client.get_client,
    header_client.get_client
])
def test_fastmock_fail_status_code_not_declared(get_client):
    try:
        client = get_client(fail_rate=1, fail_status_code=409)
        client.get("/device")
        assert False
    except Exception as e:
        assert str(e) == "Mock status code not defined in API declaration"
