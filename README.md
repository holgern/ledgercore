# ledgercore

Generic ledger and storage primitives for Python projects.

## Overview

`ledgercore` is a standalone library providing reusable building blocks for
ledger-like applications: atomic file writes, YAML front matter handling,
deterministic JSON and YAML storage, prefixed ID formatting, POSIX path
validation, config discovery, and UTC timestamp generation.

It has no CLI and no dependencies on specific products.

## Installation

```bash
pip install ledgercore
```

## Requirements

- Python >= 3.10
- PyYAML

## API

### Atomic writes (`ledgercore.atomic`)

```python
from ledgercore.atomic import atomic_write_text, atomic_create_text

atomic_write_text(path, contents, *, normalize=False, fsync=True, fast_io_env_var=None)
atomic_create_text(path, contents, *, fsync=True, fast_io_env_var=None)
```

### Errors (`ledgercore.errors`)

```python
from ledgercore.errors import (
    LedgerCoreError, StorageError, AtomicWriteError,
    FrontMatterError, JsonStoreError, PathValidationError, IdFormatError,
)
```

### Front matter (`ledgercore.frontmatter`)

```python
from ledgercore.frontmatter import (
    read_front_matter_document, write_front_matter_document,
    iter_source_files, iter_markdown_files,
)

read_front_matter_document(path) -> tuple[dict[str, object], str]
write_front_matter_document(path, metadata, body, *, body_mode="preserve", atomic=True)
iter_source_files(directory, extensions, *, recursive=True) -> list[Path]
iter_markdown_files(directory, *, recursive=False) -> list[Path]
```

### ID formatting (`ledgercore.ids`)

```python
from ledgercore.ids import NumericIdFormat, next_prefixed_id, parse_prefixed_number, slugify_ref

NumericIdFormat(prefix, separator="-", width=4)
next_prefixed_id(prefix, existing_ids, *, separator="-", width=4)
parse_prefixed_number(value, *, prefix, separator="-", width=4)
slugify_ref(value, *, empty="item")
```

### Cross-ledger resource references (`ledgercore.refs`)

Use local IDs inside one ledger and global refs when linking records across ledgers.

```python
from ledgercore.refs import parse_resource_ref

ref = parse_resource_ref("tl:task-0001")
assert ref.local_id == "task-0001"
assert ref.global_ref == "tl:task-0001"
assert ref.file_ref == "tl-task-0001"
```

Canonical global refs use:

```text
<ledger>:<kind>-<number>
```

Examples:

```text
tl:task-0001
al:adr-0002
sw:spec-0003
```

File-safe aliases use `-` instead of `:`:

```text
tl-task-0001
al-adr-0002
```

Local IDs remain unchanged:

```text
task-0001
adr-0002
```

### Text I/O (`ledgercore.io`)

```python
from ledgercore.io import (
    normalize_newlines, ensure_dir, read_text, write_text,
    content_hash, summarize_text, merge_text,
)
```

### JSON storage (`ledgercore.jsonio`)

```python
from ledgercore.jsonio import load_json_object, load_json_array, write_json

load_json_object(path, *, label="JSON document")
load_json_array(path, *, label="JSON document")
write_json(path, payload, *, atomic=True)
```

### Path utilities (`ledgercore.paths`)

```python
from ledgercore.paths import (
    is_relative_to, validate_relative_posix_path,
    resolve_relative_child, find_config_upwards,
)

is_relative_to(path, parent) -> bool
validate_relative_posix_path(value, *, field_name="path")
resolve_relative_child(base_dir, relative_path, *, field_name="path")
find_config_upwards(start, filenames) -> Path | None
```

### Timestamps (`ledgercore.time`)

```python
from ledgercore.time import utc_now_iso

utc_now_iso() -> str  # Returns "YYYY-MM-DDTHH:MM:SSZ"
```

## Development

```bash
pip install -e ".[dev]"
python -m pytest -q
python -m ruff check .
python -m mypy ledgercore
```
