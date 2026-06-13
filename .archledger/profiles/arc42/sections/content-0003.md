---
schema_version: 3
id: content-0003
kind: content
type: section
section: context_and_scope
title: Context and Scope
order: 30
status: accepted
date: "2026-06-13"
body_format: markdown
created_at: "2026-06-13T08:41:40.792531+00:00"
updated_at: "2026-06-13T08:55:58.317204+00:00"
source_refs:
  - path: ledgercore/__init__.py
    reason: Public integration boundary
---

# 3. Context and Scope

```text
Developer / operator
        |
        v
Downstream Python application
        |
        | imports functions and dataclasses
        v
ledgercore ----> PyYAML
    |
    v
Local filesystem
```

`ledgercore` is not directly operated by an end user. A downstream application invokes it to validate identifiers and paths, parse or render records, and read or update local files. The application supplies domain semantics, chooses locations, and translates `LedgerCoreError` failures into its own interface.

## External interfaces

| Interface            | Contract                                                                                      |
| -------------------- | --------------------------------------------------------------------------------------------- |
| Python API           | Functions, frozen dataclasses, literal policy arguments, and package exceptions               |
| Local filesystem     | UTF-8 text; JSON, JSONL, YAML, and front-matter documents; atomic replacement where requested |
| PyYAML               | Safe YAML loading and dumping                                                                 |
| Environment variable | An optional caller-selected variable can disable fsync                                        |
| Clock                | Current time is rendered at second precision with a `Z` suffix                                |

## Inside the boundary

- Atomic create and replace of one text file
- Generic text read/write/merge/hash helpers
- JSON, JSONL, YAML, and front matter serialization
- Path normalization, strict path validation, confinement, and config discovery
- Numeric ID and cross-ledger reference parsing/formatting
- SHA-256 fingerprints and UTC timestamp formatting
- Package-specific exception taxonomy

## Outside the boundary

- Record schemas, ownership, and workflows
- Multi-file consistency, recovery journals, and inter-process locking
- Filesystem permissions and trust policy
- UI, observability, configuration parsing, and network access
- Choice of ledger codes, kinds, and relation semantics

The downstream application owns all persisted data. `ledgercore` keeps no catalog or process-global state.
