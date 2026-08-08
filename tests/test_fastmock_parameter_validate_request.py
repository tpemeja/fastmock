from fastapi import Depends, FastAPI, status
from fastapi.testclient import TestClient

from fastmock.middleware import FastMockMiddleware
from fastmock.model import MockData
from tests.device import Device, DeviceNotFoundResponse

VALID_DEVICE = {
    "device_uuid": "DEVX000001",
    "localisation": {"latitude": 35.6582, "longitude": 139.8752},
    "deployment_date": "2024-03-14",
    "owner": "tanguy.pemeja@gmail.com"
}


def get_client(**kwargs) -> TestClient:
    # Recreate the app to reset the middleware and dependency call count for each test
    test_app = FastAPI()
    test_app.add_middleware(FastMockMiddleware, mock_data=MockData(**kwargs))
    test_app.state.dependency_calls = 0

    def track_dependency_call() -> dict:
        test_app.state.dependency_calls += 1
        return {"user": "fake"}

    @test_app.post("/validated",
                  status_code=status.HTTP_200_OK,
                  responses={
                      status.HTTP_200_OK: {"model": Device},
                      status.HTTP_404_NOT_FOUND: {"model": DeviceNotFoundResponse}
                  })
    async def create_device(device: Device, q: str, user: dict = Depends(track_dependency_call)):
        return {"msg": "Validated"}

    return TestClient(test_app)


def test_fastmock_validate_request_accepts_valid_request():
    client = get_client(type="example")
    response = client.post("/validated", params={"q": "hello"}, json=VALID_DEVICE)
    assert response.status_code == 200
    assert client.app.state.dependency_calls == 0


def test_fastmock_validate_request_rejects_invalid_body():
    client = get_client()
    response = client.post("/validated", params={"q": "hello"}, json={"device_uuid": 123})
    assert response.status_code == 422
    locations = [tuple(error["loc"]) for error in response.json()["detail"]]
    assert ("body", "device_uuid") in locations
    assert client.app.state.dependency_calls == 0


def test_fastmock_validate_request_rejects_malformed_json_body():
    client = get_client()
    response = client.post("/validated", params={"q": "hello"}, content=b"{not valid json")
    assert response.status_code == 422
    error_types = [error["type"] for error in response.json()["detail"]]
    assert "json_invalid" in error_types
    assert client.app.state.dependency_calls == 0


def test_fastmock_validate_request_rejects_missing_query_param():
    client = get_client()
    response = client.post("/validated", json=VALID_DEVICE)
    assert response.status_code == 422
    locations = [tuple(error["loc"]) for error in response.json()["detail"]]
    assert ("query", "q") in locations
    assert client.app.state.dependency_calls == 0


def test_fastmock_validate_request_disabled():
    client = get_client(validate_request=False)
    response = client.post("/validated", json={"device_uuid": 123})
    assert response.status_code == 200
    assert client.app.state.dependency_calls == 0
