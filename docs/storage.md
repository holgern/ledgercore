# Storage helpers

`ledgercore` provides several storage primitives for safely reading and writing
structured files.

## Atomic writes

Use `atomic_write_text` when replacing a file is expected:

```python
from pathlib import Path
from ledgercore.atomic import atomic_write_text

atomic_write_text(Path("index.json"), "{}\n")
```

The write goes to a temporary file first, then `os.replace` atomically moves it
to the target. Parent directories are created automatically.

Use `atomic_create_text` when an existing file must not be overwritten:

```python
from pathlib import Path
from ledgercore.atomic import atomic_create_text

atomic_create_text(Path("records/task-0001.md"), "---\nid: task-0001\n---\n")
```

This uses `O_CREAT|O_EXCL` and raises `AtomicWriteError` if the target already
exists.

Both functions support an optional `fast_io_env_var` parameter. When the named
environment variable is set, `fsync` is skipped for faster I/O on temporary
filesystems.

## Front matter documents

Front matter documents are Markdown files with a YAML header:

```text
---
id: task-0001
status: open
---
# Task body here
```

### Reading

```python
from pathlib import Path
from ledgercore.frontmatter import read_front_matter_document

metadata, body = read_front_matter_document(Path("records/task-0001.md"))
```

The YAML block must be a mapping. `metadata` is always a `dict`. `body`
includes everything after the closing `---` delimiter.

### Writing

```python
from pathlib import Path
from ledgercore.frontmatter import write_front_matter_document

write_front_matter_document(
    Path("records/task-0001.md"),
    {"id": "task-0001", "status": "open"},
    "# Implement parser\n",
    body_mode="ensure-single-final-newline",
)
```

`body_mode="ensure-single-final-newline"` normalizes trailing whitespace in the
body. The default `"preserve"` writes the body as-is.

### Iterating files

```python
from pathlib import Path
from ledgercore.frontmatter import iter_markdown_files, iter_source_files

md_files = iter_markdown_files(Path("records/"))
all_files = iter_source_files(Path("records/"), (".md", ".yaml"))
```

Both return sorted `list[Path]`.

## JSON store

```python
from pathlib import Path
from ledgercore.jsonio import load_json_object, load_json_array, write_json

path = Path("state.json")
write_json(path, {"next": 4})
state = load_json_object(path, missing="empty")
```

- `load_json_object` validates that the root is a JSON object.
- `load_json_array` validates that the root is a JSON array.
- `write_json` produces deterministic output: indent 2, sorted keys, final newline.
- All operations raise `JsonStoreError` on failure.

Both loaders accept `missing="empty"` to return an empty container when the file
does not exist, and `empty="empty"` (the default) to return an empty container
when the file is blank.

## YAML store

```python
from pathlib import Path
from ledgercore.yamlio import load_yaml_object, write_yaml

path = Path("config.yaml")
write_yaml(path, {"records_dir": "records"}, sort_keys=True)
config = load_yaml_object(path, missing="empty")
```

- `load_yaml_object` validates that the root is a YAML mapping.
- `write_yaml` produces block-style output with a final newline. Keys can be
  sorted on request.
- All operations raise `YamlStoreError` on failure.

## Path safety

Path helpers enforce strict rules to prevent directory traversal:

```python
from ledgercore.paths import validate_relative_posix_path

validate_relative_posix_path("records/task-0001.md")  # ok
validate_relative_posix_path("../etc/passwd")          # raises PathValidationError
validate_relative_posix_path("/etc/passwd")            # raises PathValidationError
```

Rejected inputs include:

- Absolute paths (starting with `/`).
- Paths containing `..` or `.` segments.
- Paths containing backslashes.
- Paths that resolve outside the base directory.

### Config discovery

```python
from pathlib import Path
from ledgercore.paths import locate_config, resolve_config_relative_path

locator = locate_config(Path.cwd(), ("ledger.toml", ".ledger.toml"))
if locator is not None:
    records_dir = resolve_config_relative_path(
        locator.config_path,
        "records",
        field_name="records_dir",
    )
```

`locate_config` walks upward from the starting directory, returning a
`ConfigLocator` with `workspace_root`, `config_path`, and `source` fields.

`resolve_config_relative_path` resolves a path relative to the config file's
parent directory, applying the same safety checks.
