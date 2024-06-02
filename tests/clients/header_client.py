from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from typing import Any

from fastmock.middleware import FastMockMiddleware
from tests.device import Device, DeviceNotFoundResponse


class CustomTestClient(TestClient):
    def __init__(self, app: FastAPI, headers: dict[str, Any] = None):
        super().__init__(app)
        self._custom_headers = headers or {}

    def request(self, method: str, url: str, **kwargs):
        headers = kwargs.get('headers', {})
        if headers is None:
            headers = {}
        # Convert all header values to strings
        headers.update({key: str(value) for key, value in self._custom_headers.items()})
        kwargs['headers'] = headers
        return super().request(method, url, **kwargs)


def get_client(**kwargs) -> TestClient:
    # Recreate the app to reset the middleware for each test
    test_app = FastAPI()
    test_app.add_middleware(FastMockMiddleware)

    @test_app.get("/list",
                  status_code=status.HTTP_200_OK,
                  responses={
                      status.HTTP_200_OK: {"model": list[Device]},
                      status.HTTP_404_NOT_FOUND: {"model": DeviceNotFoundResponse}
                  })
    async def get_device_list():
        return {"msg": "Device list"}

    @test_app.get("/dict",
                  status_code=status.HTTP_200_OK,
                  responses={
                      status.HTTP_200_OK: {"model": dict[str, Device]},
                      status.HTTP_404_NOT_FOUND: {"model": DeviceNotFoundResponse}
                  })
    async def get_device():
        return {"msg": "Device dict"}

    @test_app.get("/device",
                  status_code=status.HTTP_200_OK,
                  responses={
                      status.HTTP_200_OK: {"model": Device},
                      status.HTTP_404_NOT_FOUND: {"model": DeviceNotFoundResponse}
                  })
    async def get_device():
        return {"msg": "Device"}

    @test_app.get("/str",
                  status_code=status.HTTP_200_OK,
                  responses={
                      status.HTTP_200_OK: {"model": str},
                      status.HTTP_404_NOT_FOUND: {"model": DeviceNotFoundResponse}
                  })
    async def get_str():
        return {"msg": "Str"}

    @test_app.get("/int",
                  status_code=status.HTTP_200_OK,
                  responses={
                      status.HTTP_200_OK: {"model": int},
                      status.HTTP_404_NOT_FOUND: {"model": DeviceNotFoundResponse}
                  })
    async def get_int():
        return {"msg": "Int"}

    custom_headers = {f"X-FASTMOCK-{key.upper().replace('-', '_')}": value for key, value in kwargs.items()}

    return CustomTestClient(test_app, headers=custom_headers)
