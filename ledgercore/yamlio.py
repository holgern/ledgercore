"""YAML mapping storage for ledgercore."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Literal

import yaml

from ledgercore.errors import YamlStoreError


def load_yaml_object(
    path: Path,
    *,
    label: str = "YAML document",
    missing: Literal["error", "empty"] = "error",
    empty: Literal["error", "empty"] = "empty",
) -> dict[str, object]:
    """Load a YAML file and validate that the root is a mapping.

    Args:
        path: Path to the YAML file.
        label: Human-readable label for error messages.
        missing: Policy for missing files. "error" raises, "empty" returns {}.
        empty: Policy for empty files. "error" raises, "empty" returns {}.

    Returns:
        The parsed mapping.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        if missing == "empty":
            return {}
        raise YamlStoreError(f"Cannot read {label}: {exc}") from exc

    if not text.strip():
        if empty == "empty":
            return {}
        raise YamlStoreError(f"{label} is empty: {path}")

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise YamlStoreError(f"Invalid YAML in {label}: {exc}") from exc

    if data is None:
        return {}

    if not isinstance(data, dict):
        raise YamlStoreError(
            f"{label} must contain a YAML mapping, got {type(data).__name__}"
        )

    return data


def write_yaml(
    path: Path,
    payload: Mapping[str, object],
    *,
    atomic: bool = True,
    sort_keys: bool = False,
) -> None:
    """Write a YAML mapping to a file with deterministic output.

    Output is UTF-8, block style, with a final newline.
    """
    text = yaml.safe_dump(
        dict(payload),
        allow_unicode=True,
        sort_keys=sort_keys,
    )
    if not text.endswith("\n"):
        text += "\n"

    if atomic:
        from ledgercore.atomic import atomic_write_text

        atomic_write_text(path, text)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
