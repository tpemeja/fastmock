"""
Temporal values must be reproducible like every other field.

Polyfactory's temporal providers are anchored to the current clock, so a seed fixes the offset
rather than the value. Before this was corrected, two identical requests a minute apart returned
timestamps a minute apart while every other field stayed identical.
"""

import time as time_module
from datetime import date, datetime, time, timedelta

import pytest
from pydantic import BaseModel

from fastmock.factories import (SEEDED_PERIOD_END, SEEDED_PERIOD_START, build_base_factories,
                                get_mock_factory_class)
from fastmock.seeding import seed_factories

# Long enough that a clock-anchored provider would visibly move.
CLOCK_DRIFT = 1.1


class Temporal(BaseModel):
    at: datetime
    on: date
    during: time
    lasting: timedelta
    label: str


def build_temporal(seed: int = 7) -> Temporal:
    base_factories = build_base_factories()
    factory_class = get_mock_factory_class(Temporal, base_factories)
    seed_factories(seed)

    return factory_class.create_factory(model=Temporal, __use_defaults__=False).build()


def test_temporal_values_survive_the_passage_of_time():
    """The regression: identical seeds separated by real time must agree."""
    first = build_temporal()
    time_module.sleep(CLOCK_DRIFT)
    second = build_temporal()

    assert first.at == second.at
    assert first.on == second.on
    assert first.during == second.during
    assert first.lasting == second.lasting
    assert first.label == second.label


@pytest.mark.parametrize("seed", [1, 42, 99])
def test_datetimes_fall_inside_the_fixed_window(seed):
    built = build_temporal(seed)

    assert SEEDED_PERIOD_START <= built.at <= SEEDED_PERIOD_END
    assert SEEDED_PERIOD_START.date() <= built.on <= SEEDED_PERIOD_END.date()


def test_different_seeds_still_give_different_times():
    """Stability must not collapse into a single constant."""
    moments = {build_temporal(seed).at for seed in range(12)}

    assert len(moments) > 1


def test_timedelta_is_bounded_and_non_negative():
    built = build_temporal()

    assert timedelta(0) <= built.lasting <= timedelta(days=366)


def test_temporal_fields_are_addressable_through_the_middleware():
    """End to end: the same request returns the same timestamp after real time has passed."""
    from fastapi import FastAPI, status
    from fastapi.testclient import TestClient

    from fastmock.middleware import FastMockMiddleware

    app = FastAPI()
    app.add_middleware(FastMockMiddleware)

    @app.get("/event",
             status_code=status.HTTP_200_OK,
             responses={status.HTTP_200_OK: {"model": Temporal}})
    async def get_event():
        return {}

    client = TestClient(app)
    first = client.get("/event").json()
    time_module.sleep(CLOCK_DRIFT)

    assert client.get("/event").json() == first
