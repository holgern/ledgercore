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


def load_jsonl_objects(
    path: Path,
    *,
    label: str = "JSONL document",
    missing: Literal["error", "empty"] = "error",
    comments: bool = True,
    skip_blank: bool = True,
) -> JsonlLoadResult:
    """Load JSON objects one per line while retaining valid rows."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        if missing == "empty":
            return JsonlLoadResult([], [])
        raise JsonStoreError(f"Cannot read {label}: {exc}") from exc
    except OSError as exc:
        raise JsonStoreError(f"Cannot read {label}: {exc}") from exc

    rows: list[dict[str, object]] = []
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
        rows.append(value)
    return JsonlLoadResult(rows, issues)


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
