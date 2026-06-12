# Release process

This document describes how to build, validate, and publish a `ledgercore`
release.

## Prerequisites

Install build and validation tools:

```bash
python -m pip install -e ".[dev]"
python -m pip install build twine
```

## Pre-release checklist

1. Ensure all tests pass:

```bash
python -m pytest -q
```

2. Ensure lint is clean:

```bash
python -m ruff check .
```

3. Ensure type checking passes:

```bash
python -m mypy ledgercore
```

4. Ensure the README examples are correct (manually or via doctest).

## Building

```bash
python -m build
```

This produces `dist/ledgercore-<version>.tar.gz` and
`dist/ledgercore-<version>-py3-none-any.whl`.

## Validating the distribution

```bash
python -m twine check dist/*
```

## Smoke testing

Install the built wheel into a clean virtualenv and run a small import test:

```bash
python -m venv /tmp/ledgercore-smoke
/tmp/ledgercore-smoke/bin/python -m pip install dist/*.whl
/tmp/ledgercore-smoke/bin/python - <<'PY'
from ledgercore.ids import LedgerIdFormat
from ledgercore.refs import parse_resource_ref

assert LedgerIdFormat(prefix="task").format(1) == "task-0001"
assert parse_resource_ref("tl:task-0001").global_ref == "tl:task-0001"
print("ledgercore smoke test passed")
PY
```

## Publishing

```bash
python -m twine upload dist/*
```

## Version policy

`ledgercore` is pre-1.0. Public APIs are intended to be stable within the
0.1.x series, but breaking changes may still happen before 1.0.0 when needed
to keep the core API small and consistent.

Update the version in `pyproject.toml` before building a new release.
