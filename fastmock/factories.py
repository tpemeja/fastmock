"""
Factory selection for mock data generation.

Polyfactory ships one base factory per supported model flavour (Pydantic models, dataclasses,
``TypedDict``). This module keeps an explicit, ordered registry of those base factories rather
than discovering them dynamically, so that factory selection is deterministic and independent of
which polyfactory submodules happen to have been imported.
"""

from typing import Any, Optional, Sequence, Type

from polyfactory import BaseFactory
from polyfactory.factories import DataclassFactory, TypedDictFactory
from polyfactory.factories.pydantic_factory import ModelFactory

#: Base factories consulted, in order, when looking for one that supports a response model.
#:
#: The order matters: the first factory reporting support for a model wins. Pydantic comes first
#: because it is the common case for FastAPI response models.
DEFAULT_BASE_FACTORIES: tuple[Type[BaseFactory], ...] = (
    ModelFactory,
    DataclassFactory,
    TypedDictFactory,
)


def get_mock_factory_class(
        response_model: Any,
        base_factories: Optional[Sequence[Type[BaseFactory]]] = None
) -> Optional[Type[BaseFactory]]:
    """
    Retrieves the appropriate factory class for the provided response model.

    Args:
        response_model (Any): The response model class.
        base_factories (Sequence[Type[BaseFactory]] | None): The base factories to consider,
            in priority order. Defaults to DEFAULT_BASE_FACTORIES.

    Returns:
        Optional[Type[BaseFactory]]: The factory class if found, else None.
    """
    for factory in base_factories or DEFAULT_BASE_FACTORIES:
        if factory.is_supported_type(response_model):
            return factory

    return None
