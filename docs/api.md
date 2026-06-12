# API reference

Public API grouped by module.

## `ledgercore.atomic`

Atomic UTF-8 text writes and race-safe file creation.

| Function                                                                                  | Description                                                         |
| ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------- | -------------------------------- |
| `atomic_write_text(path, contents, *, normalize=False, fsync=True, fast_io_env_var=None)` | Write text to a file atomically using a temp file and `os.replace`. |
| `atomic_create_text(path, contents, *, fsync=True, fast_io_env_var=None)`                 | Create a new file atomically using `O_CREAT                         | O_EXCL`. Fails if target exists. |

## `ledgercore.errors`

Shared exception hierarchy with stable error codes.

| Class                 | Code                    | Description                                           |
| --------------------- | ----------------------- | ----------------------------------------------------- |
| `LedgerCoreError`     | `LEDGERCORE_ERROR`      | Base exception for all ledgercore errors.             |
| `StorageError`        | `STORAGE_ERROR`         | Base exception for storage-related errors.            |
| `AtomicWriteError`    | `ATOMIC_WRITE_ERROR`    | Raised when an atomic write operation fails.          |
| `FrontMatterError`    | `FRONTMATTER_ERROR`     | Raised when front matter parsing or writing fails.    |
| `JsonStoreError`      | `JSON_STORE_ERROR`      | Raised when a JSON store operation fails.             |
| `YamlStoreError`      | `YAML_STORE_ERROR`      | Raised when a YAML store operation fails.             |
| `PathValidationError` | `PATH_VALIDATION_ERROR` | Raised when a path fails validation.                  |
| `IdFormatError`       | `ID_FORMAT_ERROR`       | Raised when an ID does not match the expected format. |

All exceptions accept an optional `code` keyword argument to override the default code.

## `ledgercore.frontmatter`

YAML front matter reader/writer and source file iteration.

| Symbol                                                                                    | Description                                                      |
| ----------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| `BodyMode`                                                                                | Literal type: `"preserve"` or `"ensure-single-final-newline"`.   |
| `read_front_matter_document(path)`                                                        | Read a YAML front matter document, returning `(metadata, body)`. |
| `write_front_matter_document(path, metadata, body, *, body_mode="preserve", atomic=True)` | Write a YAML front matter document.                              |
| `iter_source_files(directory, extensions, *, recursive=True)`                             | Iterate source files matching given extensions in sorted order.  |
| `iter_markdown_files(directory, *, recursive=False)`                                      | Iterate markdown files in sorted order.                          |
| `read_markdown_front_matter`                                                              | Compatibility alias for `read_front_matter_document`.            |
| `write_markdown_front_matter`                                                             | Compatibility alias for `write_front_matter_document`.           |

## `ledgercore.ids`

Prefixed numeric ID formatting, parsing, next-ID generation, and slug helpers.

| Symbol                                                                                           | Description                                                                                                                      |
| ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| `LedgerIdParts`                                                                                  | Frozen dataclass: `prefix`, `number`, `segment`.                                                                                 |
| `LedgerIdFormat(prefix, separator="-", width=4, segment_separator=None, segment_required=False)` | Configurable ID format with optional segment support. Methods: `format`, `parse`, `parse_parts`, `next`, `is_valid`, `filename`. |
| `NumericIdFormat(prefix, separator="-", width=4)`                                                | Simpler ID format for compatibility. Methods: `format`, `parse`, `next`.                                                         |
| `parse_prefixed_number(value, *, prefix, separator="-", width=4)`                                | Parse a prefixed numeric ID and return the number.                                                                               |
| `next_prefixed_id(prefix, existing_ids, *, separator="-", width=4)`                              | Return the next prefixed ID given existing IDs.                                                                                  |
| `slugify_ref(value, *, empty="item")`                                                            | Lowercase, trim, collapse non-alphanumeric runs to dashes.                                                                       |

## `ledgercore.io`

UTF-8 text helpers, newline normalization, content hash, text merging.

| Function                                          | Description                                              |
| ------------------------------------------------- | -------------------------------------------------------- |
| `normalize_newlines(text)`                        | Convert CRLF and CR to LF.                               |
| `ensure_dir(path)`                                | Create parent directories as needed.                     |
| `read_text(path, *, normalize=True)`              | Read UTF-8 text from a file.                             |
| `write_text(path, text, *, normalize=True)`       | Write UTF-8 text to a file, creating parent directories. |
| `content_hash(text)`                              | Return a stable SHA-256 hex digest of UTF-8 text.        |
| `summarize_text(text, max_chars=80)`              | Collapse whitespace and truncate safely.                 |
| `merge_text(current, incoming, *, prepend=False)` | Combine text blocks without excessive blank lines.       |

## `ledgercore.jsonio`

Validated JSON object/array loading and deterministic JSON writing.

| Function                                                                           | Description                                                 |
| ---------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| `load_json_object(path, *, label="JSON document", missing="error", empty="empty")` | Load and validate a JSON object.                            |
| `load_json_array(path, *, label="JSON document", missing="error", empty="empty")`  | Load and validate a JSON array.                             |
| `write_json(path, payload, *, atomic=True)`                                        | Write JSON with indent 2, sorted keys, and a final newline. |

## `ledgercore.paths`

Safe relative POSIX path validation, config discovery, config-relative resolution.

| Symbol                                                                                  | Description                                                         |
| --------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `is_relative_to(path, parent)`                                                          | Check whether path is relative to parent.                           |
| `validate_relative_posix_path(value, *, field_name="path", allow_trailing_slash=False)` | Validate that a path is a safe relative POSIX path.                 |
| `resolve_relative_child(base_dir, relative_path, *, field_name="path")`                 | Validate and resolve a relative path under a base directory.        |
| `find_config_upwards(start, filenames)`                                                 | Walk from start upward, returning the first matching file, or None. |
| `ConfigLocator`                                                                         | Frozen dataclass: `workspace_root`, `config_path`, `source`.        |
| `locate_config(start, filenames, *, default_filename=None)`                             | Find a config file and return a `ConfigLocator`.                    |
| `resolve_config_relative_path(config_path, value, *, field_name)`                       | Resolve a relative path relative to the config file's directory.    |

## `ledgercore.refs`

Canonical cross-ledger resource references.

| Symbol                                 | Description                                                                                                            |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `RefStyle`                             | Literal type: `"canonical"`, `"file"`, `"local"`.                                                                      |
| `LedgerResourceRef`                    | Frozen dataclass with properties: `local_id`, `is_global`, `global_ref`, `file_ref`. Methods: `format`, `with_ledger`. |
| `parse_resource_ref(value, *, ...)`    | Parse a canonical, file-safe, legacy, or local resource reference.                                                     |
| `parse_global_ref(value, **kwargs)`    | Parse and require a ledger namespace.                                                                                  |
| `parse_local_ref(value, *, width=4)`   | Parse a local kind-number ID without assigning a ledger.                                                               |
| `is_resource_ref(value, **kwargs)`     | Return True if value is a valid resource ref.                                                                          |
| `normalize_ref_token(value, *, label)` | Lowercase and validate a short token.                                                                                  |
| `normalize_kind(value)`                | Lowercase, replace underscores with hyphens, and validate a resource kind.                                             |

## `ledgercore.time`

UTC timestamp generation with second precision.

| Function        | Description                       |
| --------------- | --------------------------------- |
| `utc_now_iso()` | Returns `"YYYY-MM-DDTHH:MM:SSZ"`. |

## `ledgercore.yamlio`

Validated YAML mapping loading and deterministic YAML writing.

| Function                                                                           | Description                                                |
| ---------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| `load_yaml_object(path, *, label="YAML document", missing="error", empty="empty")` | Load and validate a YAML mapping.                          |
| `write_yaml(path, payload, *, atomic=True, sort_keys=False)`                       | Write a YAML mapping with block style and a final newline. |
