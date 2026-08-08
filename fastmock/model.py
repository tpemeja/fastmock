from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class GenerationTypeEnum(str, Enum):
    """
    Enumeration for the type of generation for mock data.

    Attributes:
        default (str): Represents default data.
        example (str): Represents example data.
        generated (str): Represents data generated dynamically.
    """
    default = 'default'
    example = 'example'
    generated = 'generated'


class MockData(BaseModel):
    """
    Model for defining mock data configurations.

    Attributes:
        activate (bool): Flag to activate or deactivate mock responses. Defaults to True.
        element_size (int): Number of elements to be included in the mock response. Defaults to 2.
        type (GenerationTypeEnum): The type of data generation. Defaults to GenerationTypeEnum.default.
        response_status_code (int | None): HTTP status code for the mock response. If None, a default status code is used.
        delay (float): Number of seconds to wait before returning the mock response. Defaults to 0.
        fail_rate (float): Probability (0-1) of returning `fail_status_code` instead of the normal
            mock response. Defaults to 0.
        fail_status_code (int | None): HTTP status code to return when a request fails per
            `fail_rate`. Required if `fail_rate` is greater than 0.
        validate_request (bool): Whether to validate the request's path, query, header, cookie,
            and body parameters against the endpoint's declared types before mocking a response,
            returning a 422 on mismatch just like a real FastAPI implementation would. Defaults
            to True.
        seed (int | None): Base seed making responses reproducible. With a seed set, a response
            is a pure function of the request: the same method, path, query and body always
            produce the same data, across restarts and machines. Change it to shift the whole
            data set. Set to None for a freshly generated response every time. Defaults to 1.
            Fault injection is unaffected and stays genuinely random.
        factory (Any): A polyfactory factory used to build the response instead of deriving one
            from the response model. This is the escape hatch for invariants fastmock cannot
            infer from a schema, such as a total matching the sum of its line items. Takes
            precedence over `type`. Being a callable it cannot be set through a request header.
            Defaults to None.
    """
    activate: bool = True
    element_size: int = 2
    type: GenerationTypeEnum = GenerationTypeEnum.default
    response_status_code: int | None = None
    delay: float = 0
    fail_rate: float = Field(default=0, ge=0, le=1)
    fail_status_code: int | None = None
    validate_request: bool = True
    seed: int | None = 1
    factory: Any = None
