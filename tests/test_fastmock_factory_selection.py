from dataclasses import dataclass
from typing import TypedDict

import pytest
from polyfactory.factories import DataclassFactory, TypedDictFactory
from polyfactory.factories.pydantic_factory import ModelFactory

from fastmock.factories import DEFAULT_BASE_FACTORIES, get_mock_factory_class
from tests.device import Device


@dataclass
class DeviceDataclass:
    device_uuid: str


class DeviceTypedDict(TypedDict):
    device_uuid: str


@pytest.mark.parametrize("model, expected_factory", [
    (Device, ModelFactory),
    (DeviceDataclass, DataclassFactory),
    (DeviceTypedDict, TypedDictFactory),
])
def test_factory_selected_per_model_flavour(model, expected_factory):
    assert get_mock_factory_class(model) is expected_factory


@pytest.mark.parametrize("model", [str, int, float, bool])
def test_scalars_have_no_factory(model):
    """Scalars fall through to polyfactory's provider map instead of a factory."""
    assert get_mock_factory_class(model) is None


def test_selection_is_independent_of_import_side_effects():
    """
    Selection must come from the explicit registry, not from BaseFactory.__subclasses__(),
    which only reports direct subclasses and varies with which modules have been imported.
    """
    assert DEFAULT_BASE_FACTORIES == (ModelFactory, DataclassFactory, TypedDictFactory)


def test_custom_base_factories_are_honoured_in_order():
    class FirstWins(ModelFactory):
        __is_base_factory__ = True

    assert get_mock_factory_class(Device, [FirstWins, ModelFactory]) is FirstWins
    assert get_mock_factory_class(Device, [ModelFactory, FirstWins]) is ModelFactory


def test_custom_base_factories_can_exclude_support():
    assert get_mock_factory_class(Device, [DataclassFactory, TypedDictFactory]) is None
