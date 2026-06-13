# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- Shared `.ledger.toml` config discovery and namespaced mapping selection via
  `ledgercore.config`.

## [0.2.0] - 2026-06-13

### Added

- Deterministic minimal front matter rendering, typed render options, and
  update/write option passthrough.
- Whole-value and embedded template-placeholder parsing modes.
- Basic, wide, and custom path-text punctuation normalization profiles.
- Configurable JSON string/file formatting and compact output.
- Line-aware JSONL loading and recoverable keyed object-map loading.
- Configurable timestamp precision and UTC suffix style.
- Front matter parser option passthrough for document fingerprints.
- `ledgercore.__version__` exposed at runtime via a build-generated, gitignored
  `ledgercore/_version.py` (hatch-vcs build hook).

### Changed

- Omitted front matter render options retain existing PyYAML output; explicit
  `scalar_style="minimal"` now performs deterministic minimal rendering.
- Aware injected timestamps are normalized to UTC; naive values are rejected.

### Fixed

- Error subclasses now expose their documented stable `code` attributes
  (`STORAGE_ERROR`, `ATOMIC_WRITE_ERROR`, `FRONTMATTER_ERROR`,
  `JSON_STORE_ERROR`, `YAML_STORE_ERROR`, `PATH_VALIDATION_ERROR`,
  `ID_FORMAT_ERROR`) instead of inheriting the base code.
- Minimal front matter rendering now quotes YAML plain-scalar hazards so values
  such as `- item`, `*alias`, `~`, or `2026-06-13` round-trip instead of
  emitting invalid YAML or changing type.
- JSON and YAML loaders with `missing="empty"` no longer mask non-missing
  I/O errors such as reading a directory; only absent files return empty.
- `LedgerIdFormat` and `NumericIdFormat` consistently reject zero, negative,
  and boolean IDs across format, parse, and validity checks.
- `atomic_create_text()` now loops `os.write()` to complete writes even when
  the OS performs a partial write.

## [0.1.0] - 2026-06-12

### Added

- Atomic UTF-8 text writes and race-safe file creation (`ledgercore.atomic`).
- Shared exception hierarchy with stable error codes (`ledgercore.errors`).
- YAML front matter reader/writer and source file iteration (`ledgercore.frontmatter`).
- Prefixed numeric ID formatting, parsing, next-ID generation, slug helpers (`ledgercore.ids`).
- UTF-8 text helpers, newline normalization, content hash, text merging (`ledgercore.io`).
- Validated JSON object/array loading and deterministic JSON writing (`ledgercore.jsonio`).
- Safe relative POSIX path validation, config discovery, config-relative resolution (`ledgercore.paths`).
- Canonical cross-ledger resource references (`ledgercore.refs`).
- UTC timestamp generation with second precision (`ledgercore.time`).
- Validated YAML mapping loading and deterministic YAML writing (`ledgercore.yamlio`).
- `py.typed` marker for PEP 561 type checking support.
- Full pytest suite covering atomic writes, storage formats, paths, IDs, refs,
  hashing, and timestamps.
