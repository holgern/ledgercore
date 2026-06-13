"""Deterministic JSON Lines object storage."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ledgercore.errors import JsonStoreError


@dataclass(frozen=True)
class JsonlLoadIssue:
    """A recoverable issue found on one JSONL line."""

    line: int
    code: str
    message: str


@dataclass(frozen=True)
class JsonlLoadResult:
    """Valid JSONL object rows and recoverable line issues."""

    rows: list[dict[str, object]]
    issues: list[JsonlLoadIssue]


@dataclass(frozen=True)
class JsonlObjectRow:
    """A valid JSONL object and its source line."""

    line: int
    value: dict[str, object]


@dataclass(frozen=True)
class JsonlLoadRowsResult:
    """Line-aware valid JSONL rows and recoverable issues."""

    rows: list[JsonlObjectRow]
    issues: list[JsonlLoadIssue]


DuplicateKeyPolicy = Literal["last", "first", "error"]


@dataclass(frozen=True)
class JsonlObjectMapLoadResult:
    """JSONL objects indexed by a field plus recoverable issues."""

    rows_by_key: dict[str, dict[str, object]]
    issues: list[JsonlLoadIssue]


def load_jsonl_object_rows(
    path: Path,
    *,
    label: str = "JSONL document",
    missing: Literal["error", "empty"] = "error",
    comments: bool = True,
    skip_blank: bool = True,
) -> JsonlLoadRowsResult:
    """Load JSON objects one per line while retaining source line numbers."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        if missing == "empty":
            return JsonlLoadRowsResult([], [])
        raise JsonStoreError(f"Cannot read {label}: {exc}") from exc
    except OSError as exc:
        raise JsonStoreError(f"Cannot read {label}: {exc}") from exc

    rows: list[JsonlObjectRow] = []
    issues: list[JsonlLoadIssue] = []
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if skip_blank and not stripped:
            continue
        if comments and stripped.startswith("#"):
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            issues.append(JsonlLoadIssue(number, "invalid_json", str(exc)))
            continue
        if not isinstance(value, dict):
            issues.append(
                JsonlLoadIssue(
                    number,
                    "non_object",
                    f"Expected JSON object, got {type(value).__name__}",
                )
            )
            continue
        rows.append(JsonlObjectRow(number, value))
    return JsonlLoadRowsResult(rows, issues)


def load_jsonl_objects(
    path: Path,
    *,
    label: str = "JSONL document",
    missing: Literal["error", "empty"] = "error",
    comments: bool = True,
    skip_blank: bool = True,
) -> JsonlLoadResult:
    """Load JSON objects one per line while retaining valid rows."""
    result = load_jsonl_object_rows(
        path,
        label=label,
        missing=missing,
        comments=comments,
        skip_blank=skip_blank,
    )
    return JsonlLoadResult(
        [row.value for row in result.rows],
        result.issues,
    )


def load_jsonl_object_map(
    path: Path,
    *,
    key: str,
    label: str = "JSONL document",
    missing: Literal["error", "empty"] = "error",
    comments: bool = True,
    skip_blank: bool = True,
    duplicate_keys: DuplicateKeyPolicy = "last",
    require_string_key: bool = True,
) -> JsonlObjectMapLoadResult:
    """Load JSONL objects indexed by a field while retaining content issues."""
    if duplicate_keys not in ("last", "first", "error"):
        raise ValueError(f"Unsupported duplicate key policy: {duplicate_keys}")
    result = load_jsonl_object_rows(
        path,
        label=label,
        missing=missing,
        comments=comments,
        skip_blank=skip_blank,
    )
    rows_by_key: dict[str, dict[str, object]] = {}
    issues = list(result.issues)
    for row in result.rows:
        if key not in row.value:
            issues.append(
                JsonlLoadIssue(
                    row.line,
                    "missing_key",
                    f"Object is missing key {key!r}",
                )
            )
            continue
        raw_key = row.value[key]
        if require_string_key and not isinstance(raw_key, str):
            issues.append(
                JsonlLoadIssue(
                    row.line,
                    "invalid_key",
                    f"Key {key!r} must be a string",
                )
            )
            continue
        map_key = raw_key if isinstance(raw_key, str) else str(raw_key)
        if map_key in rows_by_key:
            issues.append(
                JsonlLoadIssue(
                    row.line,
                    "duplicate_key",
                    f"Duplicate key {map_key!r}",
                )
            )
            if duplicate_keys != "last":
                continue
        rows_by_key[map_key] = row.value
    return JsonlObjectMapLoadResult(rows_by_key, issues)


def write_jsonl_objects(
    path: Path,
    rows: Iterable[Mapping[str, object]],
    *,
    atomic: bool = True,
    sort_keys: bool = True,
    ensure_ascii: bool = False,
) -> None:
    """Write compact deterministic JSON objects, one per line."""
    lines = [
        json.dumps(
            dict(row),
            sort_keys=sort_keys,
            ensure_ascii=ensure_ascii,
            separators=(",", ":"),
        )
        for row in rows
    ]
    text = "\n".join(lines) + ("\n" if lines else "")
    if atomic:
        from ledgercore.atomic import atomic_write_text

        atomic_write_text(path, text)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
