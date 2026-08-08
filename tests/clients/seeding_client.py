from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from pydantic import BaseModel

from fastmock.middleware import FastMockMiddleware
from fastmock.model import MockData
from tests.device import Device, DeviceNotFoundResponse


class DeviceCreate(BaseModel):
    label: str
    rank: int


def get_client(**kwargs) -> TestClient:
    # Recreate the app to reset the middleware for each test
    test_app = FastAPI()
    test_app.add_middleware(FastMockMiddleware, mock_data=MockData(**kwargs))

    @test_app.get("/device",
                  status_code=status.HTTP_200_OK,
                  responses={
                      status.HTTP_200_OK: {"model": Device},
                      status.HTTP_404_NOT_FOUND: {"model": DeviceNotFoundResponse}
                  })
    async def get_device():
        return {}

    @test_app.get("/other-device",
                  status_code=status.HTTP_200_OK,
                  responses={status.HTTP_200_OK: {"model": Device}})
    async def get_other_device():
        return {}

    @test_app.get("/device/{device_id}",
                  status_code=status.HTTP_200_OK,
                  responses={status.HTTP_200_OK: {"model": Device}})
    async def get_device_by_id(device_id: str):
        return {}

    @test_app.get("/list",
                  status_code=status.HTTP_200_OK,
                  responses={status.HTTP_200_OK: {"model": list[Device]}})
    async def get_device_list():
        return []

    @test_app.post("/device",
                   status_code=status.HTTP_201_CREATED,
                   responses={status.HTTP_201_CREATED: {"model": Device}})
    async def create_device(device: DeviceCreate):
        return {}

    return TestClient(test_app)
