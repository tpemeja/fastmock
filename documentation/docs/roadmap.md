# Roadmap

This page describes where fastmock is going, and — just as importantly — where it isn't.

## What fastmock is for

fastmock targets the **realistic fake backend**: a mock server you can point a real client at for
QA, staging, demos, and integration tests.

It is deliberately *not* optimised for the "I haven't written this endpoint yet" placeholder case.
If that's all you need, [fastapi-mock](https://github.com/dantetemplar/fastapi-mock) is a lower-friction
fit — you just `raise NotImplementedError()`. fastmock asks for a little more setup in exchange for
control over data shape, status codes, failure modes, and reproducibility.

## Scope boundaries

Three things fastmock will not do. Each has a supported answer instead.

### Hand-written payloads

fastmock is **schema-driven**. Mock data is derived from your response models, and "you never
hand-write the payload" is the point. There are no inline fixtures — tools like WireMock and Prism
already do that well.

### Cross-field coherence

fastmock generates data that is **plausible field by field**. It does not, and will not, infer
relationships *between* fields. Given:

```python
class Order(BaseModel):
    line_items: list[LineItem]
    total: float
    status: Literal["pending", "shipped"]
    tracking_number: str | None
```

fastmock will produce a believable `total` and a believable `status`, but it will not make
`total` equal the sum of `line_items`, nor guarantee that `tracking_number` is non-null exactly
when `status == "shipped"`. Those invariants live in your domain, not in the schema, and any
attempt to guess them would be wrong for someone.

**Instead:** supply your own [polyfactory](https://polyfactory.litestar.dev/) factory for the
routes where invariants matter, and let generation handle the rest.

```python
@mock(factory=OrderFactory)
@app.get("/orders", responses={200: {"model": list[Order]}})
def list_orders(): ...
```

### Statefulness

fastmock does not keep a store. A `POST` followed by a `GET` will not return what you posted.
Responses **vary with** the request, but never **echo** it.

## Shipped in 0.2.0

The theme was: fastmock's output becomes stable and plausible.

### Deterministic responses

Before 0.2.0, two identical requests returned different data — which made demos jump around on
refresh and made integration tests impossible to write against a literal payload.

The contract is now:

> **A response is a pure function of the request.**

The seed is derived from the request method, path, query string, and body, mixed with a
configurable base. `GET /items/1` returns the same item every time — across refreshes, across
restarts, and across machines — while `GET /items/2` returns a different but equally stable one.

```python
seed: int | None = 1   # set to None for non-deterministic output
```

!!! warning "Behaviour change"
    Determinism is **on by default** as of 0.2.0. If you rely on responses varying between
    identical requests (load testing with varied payloads, for example), set `seed=None` to
    restore the previous behaviour.

Fault injection stays genuinely random: `fail_rate` is unaffected by seeding, so a flaky endpoint
stays flaky. If you want an endpoint to fail *deterministically*, that is already expressible with
`fail_rate=1.0` or `response_status_code`.

### Plausible values from field names

A field named `country` used to get a random string. It now gets a country.

fastmock ships a conservative, exact-match map from common field names to Faker providers —
`email`, `first_name`, `last_name`, `phone`, `city`, `country`, `url` and similar. The map is
deliberately small: a plausible-looking *wrong* value (a country name where your client expects
an ISO code) is worse than obvious gibberish, because gibberish tells you to reach for the escape
hatch and a wrong value doesn't.

The map is extensible, in keeping with how the rest of fastmock works — see
[Field Name Providers](middleware.md#field-name-providers):

```python
app.add_middleware(
    FastMockMiddleware,
    provider_map={"sku": lambda faker: faker.bothify("???-####")},
)
```

Note that two things already work today and need no changes: pydantic field constraints
(`Field(ge=0, le=1000)` keeps generated values in range) and semantic types like `EmailStr`.
If a generated value looks wildly implausible, adding a constraint to the model is often the fix.

### Custom factories

The `factory=` escape hatch described under [cross-field coherence](#cross-field-coherence) is now
a supported parameter — see [Custom Factories](mock-data.md#custom-factories).

## Where configuration lives

As fastmock grows, one rule governs where each new option goes:

- **`MockData`** holds per-route and per-request knobs — `element_size`, `delay`, `seed`.
- **The middleware constructor** holds global policy — `retrieve_data_function_list`, `provider_map`.

A useful consequence: every scalar on `MockData` can be overridden per-request through an
`X-FASTMOCK-*` header. Non-scalar options (callables, maps) can't travel by header, which is
precisely why they belong on the constructor.
