"""JSON I/O utilities for ledgercore."""

from __future__ import annotations

import json
from pathlib import Path

from ledgercore.errors import JsonStoreError


def load_json_object(
    path: Path,
    *,
    label: str = "JSON document",
) -> dict[str, object]:
    """Load a JSON file and validate that the root is an object."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise JsonStoreError(f"Cannot read {label}: {exc}") from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise JsonStoreError(f"Invalid JSON in {label}: {exc}") from exc
    if not isinstance(data, dict):
        raise JsonStoreError(
            f"{label} must contain a JSON object, got {type(data).__name__}"
        )
    return data


def load_json_array(
    path: Path,
    *,
    label: str = "JSON document",
) -> list[object]:
    """Load a JSON file and validate that the root is an array."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise JsonStoreError(f"Cannot read {label}: {exc}") from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise JsonStoreError(f"Invalid JSON in {label}: {exc}") from exc
    if not isinstance(data, list):
        raise JsonStoreError(
            f"{label} must contain a JSON array, got {type(data).__name__}"
        )
    return data


def write_json(
    path: Path,
    payload: object,
    *,
    atomic: bool = True,
) -> None:
    """Write JSON with deterministic pretty output: indent=2, sort_keys, newline."""
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if atomic:
        from ledgercore.atomic import atomic_write_text

        atomic_write_text(path, text)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
