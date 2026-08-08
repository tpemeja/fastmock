"""
Derives a deterministic seed from a request, so that mock responses are reproducible.

The contract is that a response is a pure function of the request: the same method, path, query
string and body always produce the same mock data, across refreshes, restarts and machines. That
is what makes generated data usable for demos, integration tests and bug reports.

Note that fault injection is deliberately *not* covered by this. polyfactory's ``seed_random``
seeds its own ``__random__`` and Faker instance and never touches the stdlib ``random`` module,
so ``fail_rate`` stays genuinely random while payloads stay stable.
"""

import hashlib
import json

from fastapi import Request
from polyfactory import BaseFactory

#: Only the first slice of a request body feeds the seed. Beyond this, extra fidelity buys
#: nothing and hashing large uploads on every request would be wasteful.
MAX_SEEDED_BODY_BYTES = 64 * 1024

#: Content types whose bodies are excluded from the seed. File uploads and form submissions carry
#: boundary markers and binary payloads that would make the seed needlessly unstable.
UNSEEDED_CONTENT_TYPES = ("multipart/form-data", "application/x-www-form-urlencoded")


def get_canonical_body(body: bytes) -> bytes:
    """
    Reduces a request body to a stable form for hashing.

    JSON is re-serialised with sorted keys and no incidental whitespace, so that two clients
    sending the same logical payload with different key ordering or formatting receive the same
    response. Anything that is not JSON is hashed as raw bytes.

    Args:
        body (bytes): The raw request body.

    Returns:
        bytes: A canonical representation suitable for hashing.
    """
    try:
        parsed = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return body

    return json.dumps(parsed, sort_keys=True, separators=(",", ":")).encode()


async def get_seeded_body(request: Request) -> bytes:
    """
    Retrieves the portion of the request body that contributes to the seed.

    Args:
        request (Request): The incoming HTTP request.

    Returns:
        bytes: The canonical body, or empty bytes if the body is excluded from the seed.
    """
    content_type = request.headers.get("content-type", "")
    if any(content_type.startswith(excluded) for excluded in UNSEEDED_CONTENT_TYPES):
        return b""

    body = await request.body()

    return get_canonical_body(body[:MAX_SEEDED_BODY_BYTES])


async def get_request_seed(request: Request, seed: int) -> int:
    """
    Derives a seed from the request, mixed with the configured base seed.

    Args:
        request (Request): The incoming HTTP request.
        seed (int): The configured base seed, which shifts the whole data set when changed.

    Returns:
        int: A seed derived from the base seed, method, path, query string and body.
    """
    query = "&".join(f"{key}={value}" for key, value in sorted(request.query_params.multi_items()))

    digest = hashlib.blake2b(digest_size=8)
    for part in (str(seed), request.method, request["path"], query):
        digest.update(part.encode())
        digest.update(b"\x00")
    digest.update(await get_seeded_body(request))

    return int.from_bytes(digest.digest(), "big")


def seed_factories(seed: int) -> None:
    """
    Seeds polyfactory's shared random and Faker instances.

    Seeding BaseFactory propagates to every subclass that does not shadow ``__random__``, which
    includes the factories fastmock builds. This must be called immediately before generation,
    with no await in between, since the state it sets is shared process-wide.

    Args:
        seed (int): The seed to apply.
    """
    BaseFactory.seed_random(seed)
