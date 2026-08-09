"""
Factory selection for mock data generation.

Polyfactory ships one base factory per supported model flavour (Pydantic models, dataclasses,
``TypedDict``). This module keeps an explicit, ordered registry of those base factories rather
than discovering them dynamically, so that factory selection is deterministic and independent of
which polyfactory submodules happen to have been imported.
"""

from datetime import date, datetime, time, timedelta
from types import UnionType
from typing import Annotated, Any, Callable, Mapping, Optional, Sequence, Type, Union, get_args, \
    get_origin

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

#: Maps a field *name* to a Faker provider, so that a field called ``country`` yields a country
#: rather than a random string. Polyfactory itself only looks at a field's type, never its name.
#:
#: This map is deliberately conservative and matched exactly, never by substring or suffix. A
#: plausible-looking but wrong value is worse than obvious gibberish: gibberish tells you to reach
#: for a custom factory, a wrong value silently misleads. Notably absent is a bare ``name``, which
#: is far too ambiguous -- a ``name`` field is as likely to be a product or a bank as a person.
#:
#: Extend or replace it via the ``provider_map`` argument to FastMockMiddleware.
DEFAULT_PROVIDER_MAP: dict[str, Callable[[Any], Any]] = {
    # people
    "first_name": lambda faker: faker.first_name(),
    "last_name": lambda faker: faker.last_name(),
    "full_name": lambda faker: faker.name(),
    "username": lambda faker: faker.user_name(),
    "email": lambda faker: faker.email(),
    "phone": lambda faker: faker.phone_number(),
    "phone_number": lambda faker: faker.phone_number(),

    # places
    "address": lambda faker: faker.address(),
    "street_address": lambda faker: faker.street_address(),
    "city": lambda faker: faker.city(),
    "country": lambda faker: faker.country(),
    "country_code": lambda faker: faker.country_code(),
    "postcode": lambda faker: faker.postcode(),
    "timezone": lambda faker: faker.timezone(),

    # organisations
    "company": lambda faker: faker.company(),
    "job": lambda faker: faker.job(),

    # network
    "url": lambda faker: faker.url(),
    "hostname": lambda faker: faker.hostname(),
    "ipv4": lambda faker: faker.ipv4(),
    "ipv6": lambda faker: faker.ipv6(),
    "mac_address": lambda faker: faker.mac_address(),
    "user_agent": lambda faker: faker.user_agent(),

    # identifiers
    "uuid": lambda faker: str(faker.uuid4()),
    "slug": lambda faker: faker.slug(),
}


def resolve_annotation(annotation: Any) -> Optional[type]:
    """
    Reduces an annotation to the single concrete type it accepts, if there is exactly one.

    Unwraps ``Annotated[...]`` and single-typed unions such as ``str | None``. Returns None for
    anything ambiguous (bare unions of several types, generics, unresolvable annotations), which
    callers treat as "do not apply a name-based provider here".

    Args:
        annotation (Any): The annotation to reduce.

    Returns:
        Optional[type]: The concrete type, or None if the annotation is ambiguous.
    """
    while get_origin(annotation) is Annotated:
        annotation = get_args(annotation)[0]

    origin = get_origin(annotation)

    if origin in (Union, UnionType):
        concrete = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(concrete) != 1:
            return None
        return resolve_annotation(concrete[0])

    # Anything still carrying an origin is a parameterised generic such as list[str]. Checked
    # explicitly because isinstance(list[str], type) is True on Python 3.10 but False from 3.11.
    if origin is not None:
        return None

    return annotation if isinstance(annotation, type) else None


def is_compatible(value: Any, annotation: Any) -> bool:
    """
    Reports whether a provider's value can stand in for a field of the given annotation.

    Requires an exact type match rather than an isinstance check, so that a ``datetime`` is not
    silently accepted for a field annotated ``date`` (datetime being a subclass of date).

    Args:
        value (Any): The value produced by a provider.
        annotation (Any): The field's annotation.

    Returns:
        bool: True if the value's type is exactly the type the annotation accepts.
    """
    resolved = resolve_annotation(annotation)
    return resolved is not None and type(value) is resolved  # pylint: disable=unidiomatic-typecheck


#: Absolute window that seeded temporal values are drawn from.
#:
#: Polyfactory's temporal providers are all relative to the current clock -- datetime spans
#: "-30y" to "now", date is bounded by today, and time and timedelta are measured from now. A
#: seed therefore fixes the *offset* rather than the value, so timestamps drift between runs even
#: though every other field is stable. Anchoring the window to fixed dates makes them reproducible
#: like everything else.
SEEDED_PERIOD_START = datetime(2000, 1, 1)
SEEDED_PERIOD_END = datetime(2035, 1, 1)


class StableTemporalFactoryMixin:  # pylint: disable=too-few-public-methods
    """
    Draws temporal values from a fixed window instead of one anchored to the current clock.

    Without this, two identical requests a minute apart return timestamps a minute apart, which
    contradicts the guarantee that a response is a pure function of the request.
    """

    @classmethod
    def get_provider_map(cls) -> dict:
        """
        Replaces polyfactory's clock-relative temporal providers with absolute-window ones.

        Returns:
            dict: The provider map, with datetime, date, time and timedelta overridden.
        """
        provider_map = super().get_provider_map()

        provider_map[datetime] = lambda: cls.__faker__.date_time_between(
            start_date=SEEDED_PERIOD_START, end_date=SEEDED_PERIOD_END)
        provider_map[date] = lambda: cls.__faker__.date_between_dates(
            date_start=SEEDED_PERIOD_START.date(), date_end=SEEDED_PERIOD_END.date())
        provider_map[time] = lambda: cls.__faker__.date_time_between(
            start_date=SEEDED_PERIOD_START, end_date=SEEDED_PERIOD_END).time()
        provider_map[timedelta] = lambda: timedelta(
            seconds=cls.__faker__.pyint(min_value=0, max_value=365 * 24 * 3600))

        return provider_map


class NameAwareFactoryMixin:  # pylint: disable=too-few-public-methods
    """
    Resolves field values from a name-based provider map before falling back to polyfactory.

    Mixed into each base factory by build_base_factories. A provider is only used when the value
    it produces exactly matches the field's declared type, so a field named ``city`` that happens
    to be an ``int`` still generates an int.
    """

    #: Field name to Faker provider. Overridden per subclass by build_base_factories.
    __provider_map__: Mapping[str, Callable[[Any], Any]] = {}

    @classmethod
    def get_field_value(cls, field_meta, field_build_parameters=None, build_context=None):
        """
        Resolves a field from the name-based provider map, falling back to polyfactory.

        Args:
            field_meta: Polyfactory's metadata for the field being built.
            field_build_parameters: Build parameters passed down for this field.
            build_context: Polyfactory's build context.

        Returns:
            Any: The generated value.
        """
        provider = cls.__provider_map__.get(field_meta.name)

        if provider is not None:
            value = provider(cls.__faker__)
            if is_compatible(value, field_meta.annotation):
                return value

        return super().get_field_value(field_meta, field_build_parameters, build_context)


def build_base_factories(
        provider_map: Optional[Mapping[str, Callable[[Any], Any]]] = None
) -> tuple[Type[BaseFactory], ...]:
    """
    Builds name-aware variants of the default base factories.

    Args:
        provider_map (Mapping[str, Callable] | None): Field name to Faker provider, merged over
            DEFAULT_PROVIDER_MAP. None keeps the defaults untouched. An *empty* mapping is the
            explicit opt-out and disables name-based inference entirely -- merging an empty
            mapping over the defaults would otherwise be a no-op, so the call would be pointless.

    Returns:
        tuple[Type[BaseFactory], ...]: Base factories, in the same priority order as
            DEFAULT_BASE_FACTORIES.
    """
    if provider_map is None:
        merged = dict(DEFAULT_PROVIDER_MAP)
    elif not provider_map:
        merged = {}
    else:
        merged = {**DEFAULT_PROVIDER_MAP, **provider_map}

    return tuple(
        type(
            f"FastMock{base.__name__}",
            (NameAwareFactoryMixin, StableTemporalFactoryMixin, base),
            {"__is_base_factory__": True, "__provider_map__": merged},
        )
        for base in DEFAULT_BASE_FACTORIES
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
