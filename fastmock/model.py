from enum import Enum
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
    """
    activate: bool = True
    element_size: int = 2
    type: GenerationTypeEnum = GenerationTypeEnum.default
    response_status_code: int | None = None
    delay: float = 0
    fail_rate: float = Field(default=0, ge=0, le=1)
    fail_status_code: int | None = None
