from datetime import date, datetime
from typing import Annotated, Any, Optional, Union

import pytest
from pydantic import EmailStr

from fastmock.factories import is_compatible, resolve_annotation
from fastmock.model import MockData
from fastmock.request_response import get_model_factory


class Unmockable:
    """A type polyfactory has neither a factory nor a provider for."""


@pytest.mark.parametrize("annotation, expected", [
    (str, str),
    (int, int),
    (date, date),
    (datetime, datetime),
    (Optional[str], str),
    (str | None, str),
    (Union[str, None], str),
])
def test_single_typed_annotations_resolve(annotation, expected):
    assert resolve_annotation(annotation) is expected


@pytest.mark.parametrize("annotation", [
    str | int,          # genuinely ambiguous
    Union[str, int],
    list[str],          # generic, not a plain type
    dict[str, int],
])
def test_ambiguous_annotations_do_not_resolve(annotation):
    assert resolve_annotation(annotation) is None


@pytest.mark.parametrize("annotation, expected", [
    (Annotated[str, "meta"], str),
    (Annotated[str | None, "meta"], str),
    (Annotated[Annotated[str, "inner"], "outer"], str),
])
def test_annotated_metadata_is_unwrapped(annotation, expected):
    """Field(...) and similar metadata wrap the real type and must be seen through."""
    assert resolve_annotation(annotation) is expected


def test_any_annotations_never_receive_a_provider():
    """
    `Any` is a class from Python 3.11 and a special form before it, so it resolves inconsistently
    across versions. What matters is that no provider is ever applied to such a field.
    """
    assert not is_compatible("x", Any)


def test_semantic_types_resolve_to_themselves_not_str():
    """
    EmailStr is a str subclass, but resolving it to str would let any string provider feed a
    validated field. Leaving it unresolved hands the field back to polyfactory, which already
    generates valid values for it.
    """
    assert resolve_annotation(EmailStr) is EmailStr
    assert not is_compatible("not-an-email", EmailStr)


@pytest.mark.parametrize("value, annotation, expected", [
    ("x", str, True),
    ("x", str | None, True),
    ("x", int, False),
    (1, int, True),
    (True, bool, True),
    (datetime.now(), datetime, True),
    (datetime.now(), date, False),   # datetime subclasses date; an exact match is required
    ("x", str | int, False),
])
def test_compatibility_requires_an_exact_type_match(value, annotation, expected):
    assert is_compatible(value, annotation) is expected


def test_unmockable_model_raises_a_clear_error():
    """
    Exercised directly rather than through a route: FastAPI rejects a type it cannot build a
    response field from before the middleware ever sees the request.
    """
    with pytest.raises(ValueError, match="Cannot mock Unmockable"):
        get_model_factory(Unmockable, MockData())
