from tests.clients import seeding_client


def test_identical_requests_return_identical_data():
    client = seeding_client.get_client()

    assert client.get("/device").json() == client.get("/device").json()


def test_stable_across_application_instances():
    """
    A fresh app stands in for a server restart: the seed derives from the request alone, so the
    same request must produce the same data in a brand new process.
    """
    first = seeding_client.get_client().get("/device").json()
    second = seeding_client.get_client().get("/device").json()

    assert first == second


def test_different_paths_return_different_data():
    client = seeding_client.get_client()

    assert client.get("/device").json() != client.get("/other-device").json()


def test_different_path_parameters_return_different_data():
    """Each resource is addressable: /device/1 and /device/2 are stable but distinct."""
    client = seeding_client.get_client()

    first = client.get("/device/1").json()
    second = client.get("/device/2").json()

    assert first != second
    assert first == client.get("/device/1").json()


def test_different_query_strings_return_different_data():
    """Without this, every page of a paginated demo would show the same rows."""
    client = seeding_client.get_client()

    page_one = client.get("/list?page=1").json()
    page_two = client.get("/list?page=2").json()

    assert page_one != page_two
    assert page_one == client.get("/list?page=1").json()


def test_query_parameter_order_does_not_matter():
    client = seeding_client.get_client()

    assert client.get("/list?a=1&b=2").json() == client.get("/list?b=2&a=1").json()


def test_different_bodies_return_different_data():
    client = seeding_client.get_client()

    first = client.post("/device", json={"label": "alpha", "rank": 1}).json()
    second = client.post("/device", json={"label": "beta", "rank": 2}).json()

    assert first != second
    assert first == client.post("/device", json={"label": "alpha", "rank": 1}).json()


def test_body_key_order_and_whitespace_do_not_matter():
    """
    The same logical payload must yield the same response, whatever the client's key ordering or
    formatting -- otherwise a reformatted fixture silently changes the data.
    """
    client = seeding_client.get_client()
    headers = {"content-type": "application/json"}

    compact = client.post("/device", content=b'{"label":"alpha","rank":1}', headers=headers).json()
    reordered = client.post("/device", content=b'{ "rank" : 1 , "label" : "alpha" }',
                            headers=headers).json()

    assert compact == reordered


def test_changing_the_seed_shifts_the_whole_data_set():
    assert (seeding_client.get_client(seed=1).get("/device").json()
            != seeding_client.get_client(seed=2).get("/device").json())


def test_seed_none_generates_fresh_data_every_time():
    client = seeding_client.get_client(seed=None)

    assert client.get("/device").json() != client.get("/device").json()


def test_list_elements_are_not_identical():
    """
    Seeding happens once per response, not once per element. Seeding per element would make every
    row of a list the same.
    """
    body = seeding_client.get_client(element_size=5).get("/list").json()

    assert len(body) == 5
    assert len({device["device_uuid"] for device in body}) == 5


def test_fault_injection_stays_random_under_seeding():
    """
    polyfactory's seeding never touches the stdlib random module, so fail_rate remains genuinely
    random even though payloads are deterministic.
    """
    client = seeding_client.get_client(fail_rate=0.5, fail_status_code=404)

    statuses = {client.get("/device").status_code for _ in range(60)}

    assert statuses == {200, 404}


def test_seed_is_overridable_per_request_via_header():
    """seed is a scalar, so it rides the X-FASTMOCK- header channel like every other knob."""
    client = seeding_client.get_client()

    default = client.get("/device").json()
    overridden = client.get("/device", headers={"X-FASTMOCK-SEED": "99"}).json()

    assert default != overridden
    assert overridden == client.get("/device", headers={"X-FASTMOCK-SEED": "99"}).json()
