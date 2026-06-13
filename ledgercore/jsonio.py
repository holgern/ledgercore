"""JSON I/O utilities for ledgercore."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Literal

from ledgercore.errors import JsonStoreError


def canonical_json(payload: Mapping[str, object]) -> str:
    """Return compact, deterministic JSON suitable for hashing."""
    return dumps_json(payload, compact=True, final_newline=False)


def dumps_json(
    payload: object,
    *,
    indent: int | None = 2,
    sort_keys: bool = True,
    ensure_ascii: bool = False,
    final_newline: bool = True,
    compact: bool = False,
) -> str:
    """Serialize JSON with deterministic, configurable formatting."""
    text = json.dumps(
        payload,
        indent=None if compact else indent,
        sort_keys=sort_keys,
        ensure_ascii=ensure_ascii,
        separators=(",", ":") if compact else None,
    )
    return text + ("\n" if final_newline else "")


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
    except FileNotFoundError as exc:
        if missing == "empty":
            return {}
        raise JsonStoreError(f"Cannot read {label}: {exc}") from exc
    except OSError as exc:
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
    except FileNotFoundError as exc:
        if missing == "empty":
            return []
        raise JsonStoreError(f"Cannot read {label}: {exc}") from exc
    except OSError as exc:
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
    indent: int | None = 2,
    sort_keys: bool = True,
    ensure_ascii: bool = False,
    final_newline: bool = True,
    compact: bool = False,
) -> None:
    """Write JSON with deterministic, configurable formatting."""
    text = dumps_json(
        payload,
        indent=indent,
        sort_keys=sort_keys,
        ensure_ascii=ensure_ascii,
        final_newline=final_newline,
        compact=compact,
    )
    if atomic:
        from ledgercore.atomic import atomic_write_text

        atomic_write_text(path, text)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
