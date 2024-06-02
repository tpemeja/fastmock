from enum import Enum
from pydantic import BaseModel


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
    """
    activate: bool = True
    element_size: int = 2
    type: GenerationTypeEnum = GenerationTypeEnum.default
    response_status_code: int | None = None
