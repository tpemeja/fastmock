from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from pydantic import BaseModel

from fastmock.middleware import FastMockMiddleware
from fastmock.model import MockData


class Profile(BaseModel):
    """Plainly-typed fields, so name-based inference is free to apply."""
    first_name: str
    city: str
    country: str
    bio: str


class OddlyTypedProfile(BaseModel):
    """Field names that match the provider map but whose types do not."""
    city: int
    country: float
    first_name: bool


def get_client(provider_map=None, **kwargs) -> TestClient:
    # Recreate the app to reset the middleware for each test
    test_app = FastAPI()
    test_app.add_middleware(
        FastMockMiddleware,
        mock_data=MockData(**kwargs),
        provider_map=provider_map,
    )

    @test_app.get("/profile",
                  status_code=status.HTTP_200_OK,
                  responses={status.HTTP_200_OK: {"model": Profile}})
    async def get_profile():
        return {}

    @test_app.get("/odd-profile",
                  status_code=status.HTTP_200_OK,
                  responses={status.HTTP_200_OK: {"model": OddlyTypedProfile}})
    async def get_odd_profile():
        return {}

    return TestClient(test_app)
