import re
from fastapi import Request
from fastmock.decorator import FastMockDecorator
from fastmock.request_response import get_matched_route


def get_data_from_decorator_route(request: Request) -> dict:
    """
    Retrieves mock data from a route's decorator if it exists.

    Args:
        request (Request): The incoming HTTP request.

    Returns:
        dict: The mock data retrieved from the route's decorator, or an empty dictionary if not found.
    """
    route = get_matched_route(request)
    if route is not None and hasattr(route.endpoint, FastMockDecorator.attribute_name):
        return getattr(route.endpoint, FastMockDecorator.attribute_name).dict()

    return {}


def get_data_from_header(request: Request, header_prefix: str = "X-FASTMOCK-") -> dict:
    """
    Retrieves mock data from request headers that match a specified prefix.

    Args:
        request (Request): The incoming HTTP request.
        header_prefix (str): The prefix to match headers against. Defaults to "X-FASTMOCK-".

    Returns:
        dict: The mock data retrieved from the headers.
    """
    header_data = {}
    # Create a regex pattern to match the prefix case-insensitively
    pattern = re.compile(re.escape(header_prefix), re.IGNORECASE)

    for header_name, header_value in request.headers.items():
        match = pattern.match(header_name)
        if match:
            # Extract the part after the prefix
            extracted_name = header_name[match.end():].lower().replace("-", "_")
            header_data[extracted_name] = header_value

    return header_data
