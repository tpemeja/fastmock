import re
from types import GenericAlias
from typing import Any, Mapping, Optional, Sequence, get_args, get_origin, Type

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from polyfactory import BaseFactory

from fastmock.model import MockData


def get_matched_route(request: Request) -> APIRoute | None:
    """
    Matches the request to a defined APIRoute in the FastAPI application.

    Args:
        request (Request): The incoming HTTP request.

    Returns:
        APIRoute | None: The matched route or None if no match is found.
    """
    for route in request["app"].routes:
        if isinstance(route, APIRoute):
            # Convert route path to regex pattern
            route_pattern = re.sub(r"{\w+}", r"[^/]+", route.path)
            route_pattern = f"^{route_pattern}$"

            # Check if requested path matches the regex pattern of the route
            if re.match(route_pattern, request["path"]) and request["method"] in route.methods:
                return route

    return None


def get_model_response(model, mock_data: MockData):
    """
    Generates a response based on the provided model and mock data.

    Args:
        model: The model class to generate the response for.
        mock_data (MockData): The mock data configuration.

    Returns:
        Any: The generated model response.
    """
    if isinstance(model, GenericAlias) and issubclass(get_origin(model), Sequence):
        return [get_model_factory(get_args(model)[0], mock_data)
                for _ in range(mock_data.element_size)]

    if isinstance(model, GenericAlias) and issubclass(get_origin(model), Mapping):
        key_type, value_type = get_args(model)
        keys = BaseFactory.__faker__.pylist(
            nb_elements=mock_data.element_size,
            variable_nb_elements=False,
            value_types=[key_type]
        )

        model_response = {}
        for key in keys:
            model_response[key] = get_model_factory(value_type, mock_data)

        return model_response

    return get_model_factory(model, mock_data)


def get_model_factory(model, mock_data: MockData):
    """
    Creates a factory for the provided model and generates mock data.

    Args:
        model: The model class to generate the factory for.
        mock_data (MockData): The mock data configuration.

    Returns:
        Any: The generated model instance.
    """
    if mock_data.type == mock_data.type.example:
        model_example = (getattr(model, "model_config", {})
                         .get("json_schema_extra", {}).get("example", None))

        if model_example:
            return model_example

        raise Exception("Mock using model example but no example found for the API")

    factory_class = get_mock_factory_class(model)

    if factory_class:
        factory = factory_class.create_factory(
            model=model,
            __use_defaults__=mock_data.type == mock_data.type.default
        )
        return factory.build()

    provider = BaseFactory.get_provider_map().get(model, None)

    if provider:
        return provider()

    raise ValueError(f'Cannot mock {model.response_model.__name__}')


def get_mock_factory_class(response_model: Any) -> Optional[Type[BaseFactory]]:
    """
    Retrieves the appropriate factory class for the provided response model.

    Args:
        response_model (Any): The response model class.

    Returns:
        Optional[Type[BaseFactory]]: The factory class if found, else None.
    """
    for factory in BaseFactory.__subclasses__():
        if factory.is_supported_type(response_model):
            return factory

    return None


def get_response(request: Request, mock_data: MockData):
    """
    Generates a JSON response based on the matched route and mock data.

    Args:
        request (Request): The incoming HTTP request.
        mock_data (MockData): The mock data configuration.

    Returns:
        JSONResponse: The generated JSON response.
    """
    api_route = get_matched_route(request)

    if mock_data.response_status_code is None:
        status_code = api_route.status_code
    else:
        status_code = mock_data.response_status_code

    if status_code not in api_route.responses:
        raise Exception("Mock status code not defined in API declaration")
    api_response = api_route.responses[status_code]

    response_model = get_model_response(api_response.get("model"), mock_data)

    return JSONResponse(status_code=status_code,
                        content=jsonable_encoder(response_model))
