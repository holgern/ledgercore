---
schema_version: 3
id: content-0008
kind: content
type: section
section: cross_cutting_concepts
title: Cross-cutting Concepts
order: 80
status: accepted
date: "2026-06-13"
body_format: markdown
created_at: "2026-06-13T08:41:40.792531+00:00"
updated_at: "2026-06-13T08:56:00.859424+00:00"
source_refs:
  - path: ledgercore/paths.py
    reason: Cross-cutting path validation and confinement
---

# 8. Cross-cutting Concepts

## Errors

Package failures derive from `LedgerCoreError`. Storage failures derive from `StorageError`; specialized categories identify atomic, front matter, JSON, YAML, path, and ID failures. Downstream applications render them at their own boundary.

## Determinism

- JSON files use indent 2, sorted keys, and a final newline.
- Canonical JSON uses sorted keys and compact separators.
- JSONL output uses compact objects.
- YAML has explicit key sorting.
- File iteration is sorted.
- References normalize aliases and numeric width.
- Hashes use SHA-256 over UTF-8.

## Integrity and durability

Atomic output is default for structured writers. Temp files live beside targets. Optional fsync covers contents and the parent directory. This prevents partial ordinary replacement but provides no rollback, locking, or multi-file transaction.

## Path safety

Strict POSIX-relative validation rejects absolute paths, backslashes, empty segments, and traversal before resolution. Resolved paths are checked against a base. `normalize_path_text` is only a matching aid and must not authorize access.

## Serialization

YAML/object APIs and front matter accept mapping roots. JSON has separate object and array APIs. Missing and empty policies are explicit. Safe YAML loaders avoid arbitrary object construction. Timestamp strings and template placeholders have opt-in compatibility handling.

## Identity

Numbers are positive and normally padded to four digits. Generic IDs support separators and segments. Cross-ledger refs use `ledger:kind-number` canonically and accept selected aliases. Scan-based next-ID allocation is deterministic but not concurrency-safe.

## Time

`utc_now_iso` emits second-precision strings ending in `Z`. An injected datetime is formatted directly; callers needing actual UTC conversion must normalize it first.

## Evolution and testing

Compatibility uses permissive input and canonical output. Public additions should be exported, documented, typed, and tested. Pytest covers behavior; Ruff and strict mypy cover style and typing.
