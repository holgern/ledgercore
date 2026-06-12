# Contributing to ledgercore

Thank you for your interest in contributing to `ledgercore`.

## Setup

Clone the repository and install with dev dependencies:

```bash
git clone https://github.com/holgern/ledgercore.git
cd ledgercore
python -m pip install -e ".[dev]"
```

## Running tests

```bash
python -m pytest -q
```

All tests must pass before submitting a change.

## Linting

```bash
python -m ruff check .
```

Ruff is configured in `.ruff.toml`. Fix any reported issues before submitting.

## Type checking

```bash
python -m mypy ledgercore
```

The project uses strict mypy. There should be no errors.

## Making changes

- Keep the package dependency-free except for PyYAML.
- Do not add a CLI.
- Do not couple to `taskledger`, `archledger`, or any product-specific package.
- Maintain the typed public API.
- Add tests for new functionality.
- Update `CHANGELOG.md` under an appropriate section.
- Run all checks before opening a pull request.

## Building

```bash
python -m build
python -m twine check dist/*
```

## Pull request checklist

- [ ] Tests pass (`python -m pytest -q`).
- [ ] Lint passes (`python -m ruff check .`).
- [ ] Type checking passes (`python -m mypy ledgercore`).
- [ ] Build succeeds (`python -m build`).
- [ ] Twine check passes (`python -m twine check dist/*`).
- [ ] CHANGELOG.md updated if applicable.

## License

By contributing, you agree that your contributions will be licensed under the
Apache-2.0 license.
