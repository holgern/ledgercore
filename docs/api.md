# API reference

Public API grouped by module.

## `ledgercore.atomic`

Atomic UTF-8 text writes and race-safe file creation.

| Function                                                                                  | Description                                                         |
| ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `atomic_write_text(path, contents, *, normalize=False, fsync=True, fast_io_env_var=None)` | Write text to a file atomically using a temp file and `os.replace`. |
| `atomic_create_text(path, contents, *, fsync=True, fast_io_env_var=None)`                 | Create a new file atomically using exclusive creation flags.        |

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
| `MissingFrontMatterMode`                                                                  | Literal type: `"error"` or `"empty"`.                            |
| `BodyMode`                                                                                | Body preservation and newline normalization policy.              |
| `ScalarStyle`                                                                             | Literal type: `"pyyaml"` or `"minimal"`.                         |
| `RemainingKeyOrder`                                                                       | Literal type: `"input"` or `"sorted"`.                           |
| `EmptyStringStyle`                                                                        | Literal type: `"single"` or `"double"`.                          |
| `TemplatePlaceholderMode`                                                                 | Boolean-compatible placeholder parsing mode.                     |
| `FrontMatterRenderOptions`                                                                | Frozen collection of all front matter rendering options.         |
| `split_front_matter_text(text, *, ...)`                                                   | Parse front matter from in-memory text.                          |
| `render_front_matter_text(metadata, body="", *, ...)`                                     | Render ordered metadata and body.                                |
| `update_front_matter_text(text, updates, *, ...)`                                         | Merge metadata updates into in-memory text.                      |
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

| Function                                                                           | Description                                                |
| ---------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| `load_json_object(path, *, label="JSON document", missing="error", empty="empty")` | Load and validate a JSON object.                           |
| `load_json_array(path, *, label="JSON document", missing="error", empty="empty")`  | Load and validate a JSON array.                            |
| `dumps_json(payload, *, ...)`                                                      | Render configurable deterministic JSON text.               |
| `write_json(path, payload, *, ...)`                                                | Write JSON with configurable indentation and compact mode. |
| `canonical_json(payload)`                                                          | Render compact sorted-key JSON for hashing.                |

## `ledgercore.jsonl`

Recoverable JSON Lines object loading and deterministic writing.

| Symbol                                     | Description                                                |
| ------------------------------------------ | ---------------------------------------------------------- |
| `JsonlLoadIssue`                           | Frozen line issue: `line`, `code`, and `message`.          |
| `JsonlLoadResult`                          | Valid `rows` plus recoverable `issues`.                    |
| `JsonlObjectRow`                           | Valid object plus its source line number.                  |
| `JsonlLoadRowsResult`                      | Line-aware valid rows plus recoverable issues.             |
| `JsonlObjectMapLoadResult`                 | Object rows keyed by a selected string field plus issues.  |
| `DuplicateKeyPolicy`                       | Literal type: `"last"`, `"first"`, or `"error"`.           |
| `load_jsonl_object_rows(path, *, ...)`     | Load object rows while preserving source line numbers.     |
| `load_jsonl_object_map(path, *, key, ...)` | Load object rows into a keyed map with recoverable issues. |
| `load_jsonl_objects(path, *, ...)`         | Load object rows while reporting malformed lines.          |
| `write_jsonl_objects(path, rows, *, ...)`  | Write compact object rows atomically by default.           |

## `ledgercore.paths`

Safe relative POSIX path validation, config discovery, config-relative resolution.

| Symbol                                                                                  | Description                                                         |
| --------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `is_relative_to(path, parent)`                                                          | Check whether path is relative to parent.                           |
| `validate_relative_posix_path(value, *, field_name="path", allow_trailing_slash=False)` | Validate that a path is a safe relative POSIX path.                 |
| `resolve_relative_child(base_dir, relative_path, *, field_name="path")`                 | Validate and resolve a relative path under a base directory.        |
| `ensure_inside_base(base_dir, path, *, field_name="path")`                              | Resolve a path and reject paths outside the base.                   |
| `relative_to_base(base_dir, path, *, field_name="path")`                                | Return a safe POSIX base-relative path string.                      |
| `resolve_under_base(base_dir, relative_path, *, ...)`                                   | Resolve a safe relative path with optional existence checking.      |
| `find_config_upwards(start, filenames)`                                                 | Walk from start upward, returning the first matching file, or None. |
| `ConfigLocator`                                                                         | Frozen dataclass: `workspace_root`, `config_path`, `source`.        |
| `locate_config(start, filenames, *, default_filename=None)`                             | Find a config file and return a `ConfigLocator`.                    |
| `resolve_config_relative_path(config_path, value, *, field_name)`                       | Resolve a relative path relative to the config file's directory.    |

## `ledgercore.path_text`

Human-authored path matching helpers. These functions do not authorize
filesystem access.

| Symbol                                  | Description                                                    |
| --------------------------------------- | -------------------------------------------------------------- |
| `PunctuationProfile`                    | Literal type: `"basic"`, `"wide"`, or `"none"`.                |
| `decode_unicode_escape_literals(value)` | Decode literal `\uXXXX` and `\UXXXXXXXX` sequences only.       |
| `normalize_path_text(value, *, ...)`    | Normalize Unicode, punctuation, slashes, whitespace, and case. |

## `ledgercore.hashing`

| Symbol                                   | Description                                              |
| ---------------------------------------- | -------------------------------------------------------- |
| `TextFingerprint`                        | Full, body, and canonical metadata SHA-256 values.       |
| `sha256_text(text)`                      | Hash UTF-8 text.                                         |
| `sha256_bytes(data)`                     | Hash bytes directly.                                     |
| `front_matter_fingerprint(text, *, ...)` | Fingerprint components with front matter parser options. |

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

UTC timestamp generation with configurable precision and suffix style.

| Symbol          | Description                                                  |
| --------------- | ------------------------------------------------------------ |
| `Timespec`      | Supported `datetime.isoformat()` precision values.           |
| `TimezoneStyle` | Literal type: `"z"` or `"offset"`.                           |
| `utc_now_iso()` | Normalize an aware datetime to UTC and render ISO-8601 text. |

## `ledgercore.yamlio`

Validated YAML mapping loading and deterministic YAML writing.

| Function                                                                           | Description                                                |
| ---------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| `load_yaml_object(path, *, label="YAML document", missing="error", empty="empty")` | Load and validate a YAML mapping.                          |
| `write_yaml(path, payload, *, atomic=True, sort_keys=False)`                       | Write a YAML mapping with block style and a final newline. |
