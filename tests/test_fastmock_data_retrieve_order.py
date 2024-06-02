from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from fastmock.middleware import FastMockMiddleware
from tests.device import Device, DeviceNotFoundResponse
from fastmock.decorator import FastMockDecorator
from fastmock.tools import get_data_from_decorator_route, get_data_from_header


def get_client(retrieve_data_function_list: list | None) -> TestClient:
    # Recreate the app to reset the middleware for each test
    test_app = FastAPI()
    test_app.add_middleware(FastMockMiddleware,
                            retrieve_data_function_list=retrieve_data_function_list)

    mock = FastMockDecorator()

    @mock(activate=False, type="example")
    @test_app.get("/",
                  status_code=status.HTTP_200_OK,
                  responses={
                      status.HTTP_200_OK: {"model": list[Device]},
                      status.HTTP_404_NOT_FOUND: {"model": DeviceNotFoundResponse}
                  })
    async def get_device_list():
        return {"msg": "Device list"}

    return TestClient(test_app)


def test_fastmock_default_data_order():
    client = get_client(retrieve_data_function_list=None)
    response = client.get("/", headers={'X-FASTMOCK-ACTIVATE': 'True'})
    assert response.json() == [
        {
            'deployment_date': '2024-03-14',
            'device_uuid': 'DEVX000001',
            'localisation':
                {'latitude': 35.6582,
                 'longitude': 139.8752
                 },
            'owner': 'tanguy.pemeja@gmail.com'
        },
        {
            'deployment_date': '2024-03-14',
            'device_uuid': 'DEVX000001',
            'localisation':
                {'latitude': 35.6582,
                 'longitude': 139.8752
                 },
            'owner': 'tanguy.pemeja@gmail.com'
        }]


def test_fastmock_data_order():
    client = get_client(
        retrieve_data_function_list=[get_data_from_decorator_route, get_data_from_header])
    response = client.get("/", headers={'X-FASTMOCK-ACTIVATE': 'True'})
    assert response.json() == [
        {
            'deployment_date': '2024-03-14',
            'device_uuid': 'DEVX000001',
            'localisation':
                {'latitude': 35.6582,
                 'longitude': 139.8752
                 },
            'owner': 'tanguy.pemeja@gmail.com'
        },
        {
            'deployment_date': '2024-03-14',
            'device_uuid': 'DEVX000001',
            'localisation':
                {'latitude': 35.6582,
                 'longitude': 139.8752
                 },
            'owner': 'tanguy.pemeja@gmail.com'
        }]


def test_fastmock_data_reorder():
    client = get_client(
        retrieve_data_function_list=[get_data_from_header, get_data_from_decorator_route])
    response = client.get("/", headers={'X-FASTMOCK-ACTIVATE': 'True'})
    assert response.json() == {'msg': 'Device list'}
