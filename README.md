# ledgercore

Generic, typed storage and reference primitives for ledger-like Python applications.

`ledgercore` is a small Python library for projects that store structured records
as files. It provides reusable primitives for atomic writes, YAML front matter,
deterministic JSON/YAML storage, safe relative paths, config discovery, numeric
IDs, and cross-ledger references.

It has no CLI and no dependency on any downstream ledger application.

## Why ledgercore exists

Ledger-like tools (task trackers, architecture logs, spec registries) share the
same low-level problems: safely writing files, formatting IDs, validating paths,
and linking records across namespaces. `ledgercore` extracts those shared
primitives into one typed, zero-surprise package so downstream projects do not
reinvent them.

## What is included

- Atomic UTF-8 text writes and create-only writes.
- YAML front matter read/write helpers.
- Deterministic JSON and YAML file I/O.
- Safe relative POSIX path validation.
- Upward config discovery.
- Prefixed numeric ID formatting.
- Cross-ledger references such as `tl:task-0001`.
- A typed public API and shared exception hierarchy.

## What is not included

- No command-line interface.
- No database layer.
- No sync protocol.
- No task, architecture, or project-specific schema.
- No dependency on `taskledger`, `archledger`, or another product package.

## Installation

```bash
pip install ledgercore
```

Requirements:

- Python 3.10+
- PyYAML

## Quick start

```python
from pathlib import Path

from ledgercore.frontmatter import write_front_matter_document
from ledgercore.ids import LedgerIdFormat
from ledgercore.refs import parse_resource_ref

task_ids = LedgerIdFormat(prefix="task")
task_id = task_ids.next(["task-0001", "task-0002"])

write_front_matter_document(
    Path(f"records/{task_id}.md"),
    {"id": task_id, "status": "open"},
    "# New task\n",
)

ref = parse_resource_ref("tl:task-0003")
assert ref.local_id == "task-0003"
assert ref.global_ref == "tl:task-0003"
```

## Cross-ledger references

Inside a single ledger, keep local IDs short:

```text
task-0001
adr-0002
```

When linking records across ledgers, use canonical global refs:

```text
<ledger>:<kind>-<number>
```

Examples:

```text
tl:task-0001
al:adr-0002
sw:spec-0003
```

A cross-ledger link can then store both endpoints unambiguously:

```yaml
source: tl:task-0001
target: al:adr-0002
relation: implements
```

For filenames or systems that cannot use `:`, use the file-safe alias:

```text
tl-task-0001
al-adr-0002
```

```python
from ledgercore.refs import parse_resource_ref

ref = parse_resource_ref("tl:task-0001")

assert ref.ledger == "tl"
assert ref.kind == "task"
assert ref.number == 1
assert ref.local_id == "task-0001"
assert ref.global_ref == "tl:task-0001"
assert ref.file_ref == "tl-task-0001"
```

## ID formatting

Use `LedgerIdFormat` as the primary ID formatter:

```python
from ledgercore.ids import LedgerIdFormat

ids = LedgerIdFormat(prefix="task")

assert ids.format(1) == "task-0001"
assert ids.parse("task-0007") == 7
assert ids.next(["task-0001", "task-0002"]) == "task-0003"
```

For segmented, legacy-compatible IDs:

```python
from ledgercore.ids import LedgerIdFormat

adr_ids = LedgerIdFormat(prefix="adr", separator="-", segment_separator="-")

assert adr_ids.format(13, segment="content") == "adr-content-0013"
```

`NumericIdFormat` remains available as a simpler compatibility wrapper.

## Front matter documents

```python
from pathlib import Path
from ledgercore.frontmatter import read_front_matter_document, write_front_matter_document

path = Path("records/task-0001.md")

write_front_matter_document(
    path,
    {"id": "task-0001", "status": "open"},
    "# Implement parser\n",
    body_mode="ensure-single-final-newline",
)

metadata, body = read_front_matter_document(path)
```

Front matter documents must start with `---` followed by a newline and contain a
YAML mapping. The body follows the closing `---` delimiter.

## JSON and YAML stores

```python
from pathlib import Path
from ledgercore.jsonio import load_json_object, write_json
from ledgercore.yamlio import load_yaml_object, write_yaml

state_path = Path("state.json")
write_json(state_path, {"next": 4})
state = load_json_object(state_path, missing="empty")
```

JSON output uses indent 2, sorted keys, and a final newline. YAML uses block
style and can sort keys when requested.

## Safe paths and config discovery

```python
from pathlib import Path
from ledgercore.paths import (
    ConfigLocator, locate_config, resolve_config_relative_path,
)

locator = locate_config(Path.cwd(), ("ledger.toml", ".ledger.toml"))
if locator is not None:
    records_dir = resolve_config_relative_path(
        locator.config_path,
        "records",
        field_name="records_dir",
    )
```

`locate_config` returns a `ConfigLocator` with `workspace_root`, `config_path`,
and `source` fields. Path helpers reject absolute paths, `..`, `.` segments,
backslashes, and paths escaping the base directory.

## Atomic writes

```python
from pathlib import Path
from ledgercore.atomic import atomic_create_text, atomic_write_text

atomic_create_text(Path("records/task-0001.md"), "---\nid: task-0001\n---\n")
atomic_write_text(Path("index.json"), "{}\n")
```

- `atomic_create_text`: create only; fails if target exists.
- `atomic_write_text`: replace target atomically via temp file and `os.replace`.

## Error model

All package-specific errors inherit from `LedgerCoreError`.

```python
from ledgercore.errors import (
    LedgerCoreError, StorageError, AtomicWriteError,
    FrontMatterError, JsonStoreError, YamlStoreError,
    PathValidationError, IdFormatError,
)

try:
    ...
except LedgerCoreError as exc:
    print(exc.code, str(exc))
```

Each exception carries a stable `code` attribute for programmatic handling.

## Type checking

`ledgercore` ships a `py.typed` marker. It is fully typed and passes strict
mypy with `strict = true`.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check .
python -m mypy ledgercore
```

## Release checklist

1. Update version in `pyproject.toml`.
2. Run `python -m pytest -q`.
3. Run `python -m ruff check .`.
4. Run `python -m mypy ledgercore`.
5. Run `python -m build`.
6. Run `python -m twine check dist/*`.
7. Smoke-test the built wheel in a clean virtualenv.

## Stability

`ledgercore` is pre-1.0. Public APIs are intended to be stable within the
0.1.x series, but breaking changes may still happen before 1.0.0 when needed
to keep the core API small and consistent.

- No CLI is included.
- No global configuration format is imposed.
- No ledger schema is imposed.
- No product-specific IDs are baked in.
- All paths and refs are strings/paths chosen by downstream packages.

## License

Apache-2.0.
