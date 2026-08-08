from typing import Any, Callable, Mapping

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from fastmock.factories import build_base_factories
from fastmock.request_response import get_matched_route, get_response
from fastmock.model import MockData

from fastmock.tools import get_data_from_decorator_route, get_data_from_header


class FastMockMiddleware(BaseHTTPMiddleware):
    """
    Middleware for FastAPI to mock responses based on predefined data.

    This middleware intercepts requests and provides mock responses based on
    specified rules and data. It allows for flexible retrieval and merging of
    mock data from various sources.

    Attributes:
        retrieve_data_function_list (list[Callable[[Request], dict]]): List of functions
            to retrieve additional data from the request, ordered from least to most
            important.
        mock_data (MockData): The base mock data configuration.
        base_factories (tuple): Name-aware base factories used to generate mock values.
    """

    def __init__(
            self,
            app,
            mock_data: MockData = MockData(),
            retrieve_data_function_list: list[Callable[[Request], dict]] = None,
            provider_map: Mapping[str, Callable[[Any], Any]] = None
    ):
        """
        Initializes the FastMockMiddleware.

        Args:
            app: The FastAPI application instance.
            mock_data (MockData): The base mock data configuration. Defaults to an empty MockData instance.
            retrieve_data_function_list (list[Callable[[Request], dict]]): List of functions
                to retrieve additional data from the request, ordered from least to most
                important function. Defaults to [get_data_from_decorator_route, get_data_from_header].
            provider_map (Mapping[str, Callable[[Any], Any]]): Field name to Faker provider,
                merged over fastmock.factories.DEFAULT_PROVIDER_MAP. Pass an empty mapping to
                disable name-based inference. This is global policy rather than per-request
                state, which is why it lives here instead of on MockData.
        """
        super().__init__(app)

        if retrieve_data_function_list is None:
            retrieve_data_function_list = [get_data_from_decorator_route, get_data_from_header]

        self.retrieve_data_function_list = retrieve_data_function_list
        self.mock_data = mock_data
        self.base_factories = build_base_factories(provider_map)

    def get_mock_data(self, request: Request) -> MockData:
        """
        Merges base mock data with additional data retrieved from the request.

        Args:
            request (Request): The incoming HTTP request.

        Returns:
            MockData: The merged mock data.
        """
        merged_data = self.mock_data.model_dump()
        for retrieve_data_function in self.retrieve_data_function_list:
            merged_data.update(retrieve_data_function(request))

        return MockData(**merged_data)

    async def dispatch(self, request, call_next):
        """
        Intercepts the request and returns a mock response if applicable.

        Args:
            request (Request): The incoming HTTP request.
            call_next (Callable): The next callable in the middleware chain.

        Returns:
            Response: The HTTP response.
        """
        mock_data = self.get_mock_data(request)

        # Check if the route matches and if mocking is activated
        if get_matched_route(request) is None or not mock_data.activate:
            response = await call_next(request)
            return response

        # Get the mock response based on the request and mock data
        route_response = await get_response(request, mock_data, self.base_factories)

        return route_response
