import pytest

from tests.clients import (decorator_client, decorator_initialization_client,
                           middleware_client, header_client)


@pytest.mark.parametrize("get_client", [
    middleware_client.get_client,
    decorator_client.get_client,
    decorator_initialization_client.get_client,
    header_client.get_client
])
def test_fastmock_openapi_working(get_client):
    response = get_client().get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    assert set(schema["paths"].keys()) == {"/list", "/dict", "/device", "/str", "/int"}

    for path_item in schema["paths"].values():
        responses = path_item["get"]["responses"]
        assert "200" in responses
        assert "404" in responses

    component_schemas = schema["components"]["schemas"]
    for name in ("Device", "Coordinate", "DeviceNotFoundResponse"):
        assert name in component_schemas
