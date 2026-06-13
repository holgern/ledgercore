# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - Unreleased

### Added

- Deterministic minimal front matter rendering, typed render options, and
  update/write option passthrough.
- Whole-value and embedded template-placeholder parsing modes.
- Basic, wide, and custom path-text punctuation normalization profiles.
- Configurable JSON string/file formatting and compact output.
- Line-aware JSONL loading and recoverable keyed object-map loading.
- Configurable timestamp precision and UTC suffix style.
- Front matter parser option passthrough for document fingerprints.

### Changed

- Omitted front matter render options retain existing PyYAML output; explicit
  `scalar_style="minimal"` now performs deterministic minimal rendering.
- Aware injected timestamps are normalized to UTC; naive values are rejected.

## [0.1.0] - Unreleased

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
