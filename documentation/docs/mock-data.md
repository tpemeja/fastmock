# Mock Data Configuration

## Overview

This documentation describes the configuration options available for defining mock data in your application.
The configuration is defined using the `MockData` model, which allows you to specify various parameters for generating mock responses.

## Enumeration: GenerationTypeEnum

The `GenerationTypeEnum` is an enumeration that specifies the type of generation for mock data. It includes the following options:

- **default**: Represents default data.
- **example**: Represents example data.
- **generated**: Represents data generated dynamically.

```python
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
```

## Model: MockData
The MockData model is used to define the configuration for mock data generation. It includes the following attributes:

* **activate (bool)**: Flag to activate or deactivate mock responses. Defaults to `True`.
* **element_size (int)**: Number of elements to be included in the mock response. Defaults to `2`.
* **type (GenerationTypeEnum)**: The type of data generation. Defaults to `GenerationTypeEnum.default`.
* **response_status_code (int | None)**: HTTP status code for the mock response. If None, a default status code is used.

```python
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
```

### Usage Example
Here is an example of how you can use the MockData model to configure mock data generation:
```python
mock_data_config = MockData(
    activate=True,
    element_size=5,
    type=GenerationTypeEnum.generated,
    response_status_code=200
)

print(mock_data_config)
```

In this example, the mock data generation is activated, five elements will be included in the mock response,
the data type is set to generated, and the HTTP response status code is set to 200.

