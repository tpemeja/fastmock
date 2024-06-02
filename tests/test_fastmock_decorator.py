from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from fastmock.middleware import FastMockMiddleware
from tests.device import Device, DeviceNotFoundResponse
from fastmock.decorator import FastMockDecorator
from fastmock.model import MockData

def get_client() -> TestClient:
    # Recreate the app to reset the middleware for each test
    test_app = FastAPI()
    test_app.add_middleware(FastMockMiddleware, mock_data=MockData(activate=False))

    mock = FastMockDecorator()

    @mock
    @test_app.get("/",
                  status_code=status.HTTP_200_OK,
                  responses={
                      status.HTTP_200_OK: {"model": list[Device]},
                      status.HTTP_404_NOT_FOUND: {"model": DeviceNotFoundResponse}
                  })
    async def get_device_list():
        return {"msg": "Device list"}

    return TestClient(test_app)


def test_fastmock_decorator_work_without_parenthesis():
    client = get_client()
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() != {"msg": "Device list"}
