import asyncio
import json
import random
import re
from types import GenericAlias
from typing import Mapping, Optional, Sequence, get_args, get_origin, Type

from fastapi import Request, params
from fastapi.dependencies.utils import request_body_to_args, request_params_to_args
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from polyfactory import BaseFactory

from fastmock.factories import get_mock_factory_class
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


def get_model_response(
        model,
        mock_data: MockData,
        base_factories: Optional[Sequence[Type[BaseFactory]]] = None
):
    """
    Generates a response based on the provided model and mock data.

    Args:
        model: The model class to generate the response for.
        mock_data (MockData): The mock data configuration.
        base_factories (Sequence[Type[BaseFactory]] | None): The base factories to select from.

    Returns:
        Any: The generated model response.
    """
    if isinstance(model, GenericAlias) and issubclass(get_origin(model), Sequence):
        return [get_model_factory(get_args(model)[0], mock_data, base_factories)
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
            model_response[key] = get_model_factory(value_type, mock_data, base_factories)

        return model_response

    return get_model_factory(model, mock_data, base_factories)


def get_model_factory(
        model,
        mock_data: MockData,
        base_factories: Optional[Sequence[Type[BaseFactory]]] = None
):
    """
    Creates a factory for the provided model and generates mock data.

    Args:
        model: The model class to generate the factory for.
        mock_data (MockData): The mock data configuration.
        base_factories (Sequence[Type[BaseFactory]] | None): The base factories to select from.

    Returns:
        Any: The generated model instance.
    """
    if mock_data.type == mock_data.type.example:
        model_example = (getattr(model, "model_config", {})
                         .get("json_schema_extra", {}).get("example", None))

        if model_example:
            return model_example

        raise Exception("Mock using model example but no example found for the API")

    factory_class = get_mock_factory_class(model, base_factories)

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


async def get_request_validation_errors(request: Request, api_route: APIRoute) -> list:
    """
    Validates the request's path, query, header, cookie, and body parameters against the
    route's declared types, the same way FastAPI itself would when actually handling the
    request. Dependencies declared with `Depends(...)` are intentionally never resolved or
    called, so mocking a route never triggers real auth, database, or other side-effecting
    dependencies.

    Args:
        request (Request): The incoming HTTP request.
        api_route (APIRoute): The matched route.

    Returns:
        list: A list of FastAPI-style validation error dicts, empty if the request is valid.
    """
    dependant = api_route.dependant
    errors = []

    for fields, received in (
        (dependant.path_params, request.path_params),
        (dependant.query_params, request.query_params),
        (dependant.header_params, request.headers),
        (dependant.cookie_params, request.cookies),
    ):
        _, param_errors = request_params_to_args(fields, received)
        errors += param_errors

    is_body_form = api_route.body_field and isinstance(api_route.body_field.field_info, params.Form)
    if dependant.body_params and not is_body_form:
        body = None
        try:
            body_bytes = await request.body()
            if body_bytes:
                body = await request.json()
        except json.JSONDecodeError as error:
            errors.append({
                "type": "json_invalid",
                "loc": ("body", error.pos),
                "msg": "JSON decode error",
                "input": {},
                "ctx": {"error": error.msg},
            })
        else:
            _, body_errors = await request_body_to_args(
                body_fields=dependant.body_params,
                received_body=body,
                embed_body_fields=getattr(api_route, "_embed_body_fields", False),
            )
            errors += body_errors

    return errors


async def get_response(
        request: Request,
        mock_data: MockData,
        base_factories: Optional[Sequence[Type[BaseFactory]]] = None
):
    """
    Generates a JSON response based on the matched route and mock data.

    Args:
        request (Request): The incoming HTTP request.
        mock_data (MockData): The mock data configuration.
        base_factories (Sequence[Type[BaseFactory]] | None): The base factories to select from.

    Returns:
        JSONResponse: The generated JSON response.
    """
    if mock_data.delay:
        await asyncio.sleep(mock_data.delay)

    api_route = get_matched_route(request)

    if mock_data.validate_request:
        validation_errors = await get_request_validation_errors(request, api_route)
        if validation_errors:
            return JSONResponse(status_code=422,
                                content={"detail": jsonable_encoder(validation_errors)})

    if mock_data.fail_rate and random.random() < mock_data.fail_rate:
        if mock_data.fail_status_code is None:
            raise Exception("Mock fail_rate is set but no fail_status_code was defined")
        status_code = mock_data.fail_status_code
    elif mock_data.response_status_code is None:
        status_code = api_route.status_code
    else:
        status_code = mock_data.response_status_code

    if status_code not in api_route.responses:
        raise Exception("Mock status code not defined in API declaration")
    api_response = api_route.responses[status_code]

    response_model = get_model_response(api_response.get("model"), mock_data, base_factories)

    return JSONResponse(status_code=status_code,
                        content=jsonable_encoder(response_model))
