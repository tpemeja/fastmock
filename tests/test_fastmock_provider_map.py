import re

import pytest
from faker import Faker

from fastmock.factories import DEFAULT_PROVIDER_MAP
from tests.clients import provider_map_client

FAKER = Faker()


def is_polyfactory_random_string(value: str) -> bool:
    """Polyfactory's unconstrained str values are 20 random alphanumeric characters."""
    return len(value) == 20 and value.isalnum()


def test_named_fields_use_matching_providers():
    """A field called `country` should hold a country, not a random string."""
    response = provider_map_client.get_client(type="generated").get("/profile")
    assert response.status_code == 200
    body = response.json()

    for field in ("first_name", "city", "country"):
        assert not is_polyfactory_random_string(body[field])

    # Faker's place and person values read as words: letters plus ordinary name punctuation
    for field in ("first_name", "city", "country"):
        assert re.fullmatch(r"[A-Za-z' .\-()]+", body[field]), body[field]


def test_unmapped_fields_are_left_to_polyfactory():
    """`bio` is not in the provider map, so it keeps polyfactory's generated value."""
    body = provider_map_client.get_client(type="generated").get("/profile").json()

    assert is_polyfactory_random_string(body["bio"])


def test_provider_is_skipped_when_the_type_does_not_match():
    """
    A field named `city` typed as an int must stay an int -- a provider is only applied when the
    value it produces exactly matches the field's declared type.
    """
    response = provider_map_client.get_client(type="generated").get("/odd-profile")
    assert response.status_code == 200
    body = response.json()

    assert isinstance(body["city"], int)
    assert isinstance(body["country"], float)
    assert isinstance(body["first_name"], bool)


def test_custom_providers_extend_the_default_map():
    body = provider_map_client.get_client(
        type="generated",
        provider_map={"bio": lambda faker: "a custom bio"},
    ).get("/profile").json()

    assert body["bio"] == "a custom bio"
    # defaults still apply alongside the custom entry
    assert body["first_name"].isalpha()


def test_custom_providers_override_the_default_map():
    body = provider_map_client.get_client(
        type="generated",
        provider_map={"country": lambda faker: "Wakanda"},
    ).get("/profile").json()

    assert body["country"] == "Wakanda"


def test_inference_can_be_disabled_with_an_empty_map():
    """An empty mapping is distinct from None: it disables name-based inference entirely."""
    body = provider_map_client.get_client(
        type="generated",
        provider_map={},
    ).get("/profile").json()

    assert is_polyfactory_random_string(body["country"])


@pytest.mark.parametrize("field_name", sorted(DEFAULT_PROVIDER_MAP))
def test_every_default_provider_is_callable_and_returns_a_value(field_name):
    value = DEFAULT_PROVIDER_MAP[field_name](FAKER)
    assert value is not None and value != ""


def test_bare_name_is_deliberately_absent():
    """
    `name` is too ambiguous to infer -- a `name` field is as likely to be a product or a company
    as a person. See the DEFAULT_PROVIDER_MAP docstring.
    """
    assert "name" not in DEFAULT_PROVIDER_MAP
