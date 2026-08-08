# Contributing

## Development setup

This project uses [uv](https://docs.astral.sh/uv/) to manage the Python environment and dependencies, declared in `pyproject.toml`.

```console
$ git clone https://github.com/tpemeja/fastmock.git
$ cd fastmock
$ uv sync --group dev
```

This creates a `.venv` and installs the package together with the `test`, `lint`, and `docs` dependency groups (bundled as `dev`).

## Running the tests

```console
$ uv run pytest tests
```

To also collect coverage:

```console
$ uv run coverage run --source=fastmock -m pytest tests
$ uv run coverage report
```

## Linting

```console
$ uv run pylint fastmock/
```

## Building the docs locally

```console
$ uv run mkdocs serve --config-file documentation/mkdocs.yml
```

## Continuous integration

Every push to `main` runs the [`Test` workflow](https://github.com/tpemeja/fastmock/actions/workflows/test.yml): pylint, the test suite across Python 3.10-3.13, and a coverage upload to Coveralls.

## Releasing

Releases are cut with the [`Release` workflow](https://github.com/tpemeja/fastmock/actions/workflows/release.yml):

1. Go to **Actions → Release → Run workflow**.
2. Pick the version bump: `patch`, `minor`, or `major`.
3. The workflow runs the test suite, bumps the version in `pyproject.toml`/`uv.lock`, commits and tags it, publishes the package to PyPI, deploys the documentation, and creates the GitHub release — no local steps required.

If you need to release manually instead: bump `version` in `pyproject.toml`, commit, tag the commit with the same version (e.g. `git tag 0.1.2`), and push both. Pushing the tag deploys the docs, and creating a GitHub Release from that tag publishes the package to PyPI.
