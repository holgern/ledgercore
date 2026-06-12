# ledgercore documentation

Welcome to the `ledgercore` documentation.

`ledgercore` is a small, typed Python library for projects that store structured
records as files. It provides reusable primitives for atomic writes, YAML front
matter, deterministic JSON/YAML storage, safe relative paths, config discovery,
numeric IDs, and cross-ledger references.

## Installation

```bash
pip install ledgercore
```

Requirements: Python 3.10+, PyYAML.

## Quick start

See the [README](../README.md) for a hands-on introduction.

## Documentation index

- [API reference](api.md): public API grouped by module.
- [Cross-ledger references](references.md): local IDs, global refs, file-safe refs.
- [Storage helpers](storage.md): atomic writes, front matter, JSON, YAML, path safety.
- [Release process](release.md): build, test, version, publish checklist.
