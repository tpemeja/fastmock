from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from fastmock.middleware import FastMockMiddleware
from tests.device import Device, DeviceNotFoundResponse
from fastmock.decorator import FastMockDecorator


def get_client(**kwargs) -> TestClient:
    # Recreate the app to reset the middleware for each test
    test_app = FastAPI()
    test_app.add_middleware(FastMockMiddleware)

    mock = FastMockDecorator(**kwargs)

    @mock
    @test_app.get("/list",
                  status_code=status.HTTP_200_OK,
                  responses={
                      status.HTTP_200_OK: {"model": list[Device]},
                      status.HTTP_404_NOT_FOUND: {"model": DeviceNotFoundResponse}
                  })
    async def get_device_list():
        return {"msg": "Device list"}

    @mock
    @test_app.get("/dict",
                  status_code=status.HTTP_200_OK,
                  responses={
                      status.HTTP_200_OK: {"model": dict[str, Device]},
                      status.HTTP_404_NOT_FOUND: {"model": DeviceNotFoundResponse}
                  })
    async def get_device():
        return {"msg": "Device dict"}

    @mock
    @test_app.get("/device",
                  status_code=status.HTTP_200_OK,
                  responses={
                      status.HTTP_200_OK: {"model": Device},
                      status.HTTP_404_NOT_FOUND: {"model": DeviceNotFoundResponse}
                  })
    async def get_device():
        return {"msg": "Device"}

    @mock
    @test_app.get("/str",
                  status_code=status.HTTP_200_OK,
                  responses={
                      status.HTTP_200_OK: {"model": str},
                      status.HTTP_404_NOT_FOUND: {"model": DeviceNotFoundResponse}
                  })
    async def get_str():
        return {"msg": "Str"}

    @mock
    @test_app.get("/int",
                  status_code=status.HTTP_200_OK,
                  responses={
                      status.HTTP_200_OK: {"model": int},
                      status.HTTP_404_NOT_FOUND: {"model": DeviceNotFoundResponse}
                  })
    async def get_int():
        return {"msg": "Int"}

    return TestClient(test_app)
