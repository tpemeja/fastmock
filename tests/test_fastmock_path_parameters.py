from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from fastmock.middleware import FastMockMiddleware
from fastmock.model import MockData


def get_client(**kwargs) -> TestClient:
    # Recreate the app to reset the middleware for each test
    test_app = FastAPI()
    test_app.add_middleware(FastMockMiddleware, mock_data=MockData(**kwargs))

    @test_app.get("/items/{item_id}",
                  status_code=status.HTTP_200_OK,
                  responses={status.HTTP_200_OK: {"model": str}})
    async def get_item(item_id: int):
        return "item"

    @test_app.get("/files/{file_path:path}",
                  status_code=status.HTTP_200_OK,
                  responses={status.HTTP_200_OK: {"model": str}})
    async def get_file(file_path: str):
        return "file"

    @test_app.get("/items/{item_id}/parts/{part_id}",
                  status_code=status.HTTP_200_OK,
                  responses={status.HTTP_200_OK: {"model": str}})
    async def get_part(item_id: int, part_id: str):
        return "part"

    return TestClient(test_app)


def test_path_parameter_route_is_mocked():
    """
    Middleware runs before Starlette's router, so path parameters must be resolved explicitly.
    Without that, this route reported item_id as missing and returned 422.
    """
    response = get_client().get("/items/42")

    assert response.status_code == 200
    assert isinstance(response.json(), str)


def test_multiple_path_parameters_are_resolved():
    response = get_client().get("/items/42/parts/abc")

    assert response.status_code == 200


def test_path_converter_is_honoured():
    """The previous regex matcher could not express {file_path:path}, which spans slashes."""
    response = get_client().get("/files/some/nested/file.txt")

    assert response.status_code == 200


def test_invalid_path_parameter_is_still_rejected():
    """Resolving path params must not weaken validation: item_id is declared as an int."""
    response = get_client().get("/items/not-an-int")

    assert response.status_code == 422
    locations = [tuple(error["loc"]) for error in response.json()["detail"]]
    assert ("path", "item_id") in locations


def test_unmatched_path_is_not_mocked():
    response = get_client().get("/does-not-exist")

    assert response.status_code == 404


def test_method_mismatch_is_not_mocked():
    """A path that matches but a method that does not must fall through to the real app."""
    response = get_client().post("/items/42")

    assert response.status_code == 405
