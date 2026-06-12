"""JSON I/O utilities for ledgercore."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from ledgercore.errors import JsonStoreError


def load_json_object(
    path: Path,
    *,
    label: str = "JSON document",
    missing: Literal["error", "empty"] = "error",
    empty: Literal["error", "empty"] = "empty",
) -> dict[str, object]:
    """Load a JSON file and validate that the root is an object.

    Args:
        path: Path to the JSON file.
        label: Human-readable label for error messages.
        missing: Policy for missing files. "error" raises, "empty" returns {}.
        empty: Policy for empty files. "error" raises, "empty" returns {}.

    Returns:
        The parsed JSON object.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        if missing == "empty":
            return {}
        raise JsonStoreError(f"Cannot read {label}: {exc}") from exc

    if not text.strip():
        if empty == "empty":
            return {}
        raise JsonStoreError(f"{label} is empty: {path}")

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
    missing: Literal["error", "empty"] = "error",
    empty: Literal["error", "empty"] = "empty",
) -> list[object]:
    """Load a JSON file and validate that the root is an array.

    Args:
        path: Path to the JSON file.
        label: Human-readable label for error messages.
        missing: Policy for missing files. "error" raises, "empty" returns [].
        empty: Policy for empty files. "error" raises, "empty" returns [].

    Returns:
        The parsed JSON array.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        if missing == "empty":
            return []
        raise JsonStoreError(f"Cannot read {label}: {exc}") from exc

    if not text.strip():
        if empty == "empty":
            return []
        raise JsonStoreError(f"{label} is empty: {path}")

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
