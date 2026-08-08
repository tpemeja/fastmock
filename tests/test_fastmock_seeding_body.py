import pytest
from starlette.requests import Request

from fastmock.seeding import (MAX_SEEDED_BODY_BYTES, get_canonical_body, get_request_seed,
                              get_seeded_body)


def build_request(body: bytes, content_type: str = "application/json") -> Request:
    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/device",
        "query_string": b"",
        "headers": [(b"content-type", content_type.encode())],
    }
    return Request(scope, receive)


def test_json_bodies_are_canonicalised():
    """Key order and incidental whitespace must not change the response."""
    assert (get_canonical_body(b'{"b":2,"a":1}')
            == get_canonical_body(b'{ "a" : 1 , "b" : 2 }'))


def test_nested_json_is_canonicalised():
    assert (get_canonical_body(b'{"outer":{"b":2,"a":1}}')
            == get_canonical_body(b'{"outer":{"a":1,"b":2}}'))


def test_json_arrays_keep_their_order():
    """Order is meaningful in an array, unlike in an object."""
    assert get_canonical_body(b'[1,2]') != get_canonical_body(b'[2,1]')


@pytest.mark.parametrize("body", [b"not json at all", b"\xff\xfe binary", b"{unclosed"])
def test_non_json_bodies_are_hashed_as_raw_bytes(body):
    assert get_canonical_body(body) == body


@pytest.mark.asyncio
@pytest.mark.parametrize("content_type", [
    "multipart/form-data; boundary=abc",
    "application/x-www-form-urlencoded",
])
async def test_form_bodies_are_excluded_from_the_seed(content_type):
    """
    File uploads and form submissions carry boundary markers and binary payloads that would make
    the seed needlessly unstable.
    """
    assert await get_seeded_body(build_request(b"anything", content_type)) == b""


@pytest.mark.asyncio
async def test_json_bodies_are_included_in_the_seed():
    assert await get_seeded_body(build_request(b'{"a":1}')) == b'{"a":1}'


@pytest.mark.asyncio
async def test_only_the_first_slice_of_a_large_body_is_hashed():
    oversized = b"x" * (MAX_SEEDED_BODY_BYTES + 100)

    assert len(await get_seeded_body(build_request(oversized, "text/plain"))) \
        == MAX_SEEDED_BODY_BYTES


@pytest.mark.asyncio
async def test_form_requests_still_seed_from_method_path_and_query():
    """Excluding the body must not collapse every form request onto one seed."""
    first = await get_request_seed(build_request(b"a=1", "application/x-www-form-urlencoded"), 1)
    second = await get_request_seed(build_request(b"a=2", "application/x-www-form-urlencoded"), 1)
    third = await get_request_seed(build_request(b"a=1", "application/x-www-form-urlencoded"), 2)

    assert first == second   # body ignored
    assert first != third    # base seed still applies


@pytest.mark.asyncio
async def test_seed_changes_with_the_body_for_json_requests():
    first = await get_request_seed(build_request(b'{"a":1}'), 1)
    second = await get_request_seed(build_request(b'{"a":2}'), 1)

    assert first != second
