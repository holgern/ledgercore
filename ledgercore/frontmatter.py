"""YAML front matter read/write and file iteration for ledgercore."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Literal

import yaml

from ledgercore.errors import FrontMatterError

BodyMode = Literal["preserve", "ensure-single-final-newline"]

_FRONT_MATTER_DELIM = "---"


def read_front_matter_document(path: Path) -> tuple[dict[str, object], str]:
    """Read a YAML front matter document, returning (metadata, body)."""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise FrontMatterError(f"Cannot read {path}: {exc}") from exc

    raw = raw.replace("\r\n", "\n").replace("\r", "\n")

    if not raw.startswith(_FRONT_MATTER_DELIM + "\n"):
        raise FrontMatterError(
            f"Document must start with '---' followed by a newline: {path}"
        )

    rest = raw[len(_FRONT_MATTER_DELIM) + 1 :]

    # Look for closing --- followed by newline and body
    close_with_body = rest.find("\n" + _FRONT_MATTER_DELIM + "\n")
    # Look for closing --- at the very end of the document (no trailing body)
    close_at_end = rest.endswith("\n" + _FRONT_MATTER_DELIM)
    # Look for closing --- right at the start of rest (empty YAML block with body)
    close_immediate_with_body = -1
    if rest.startswith(_FRONT_MATTER_DELIM + "\n"):
        close_immediate_with_body = 0
    # Look for closing --- as the entirety of rest (empty YAML, no body)
    close_immediate_at_end = rest == _FRONT_MATTER_DELIM

    if close_with_body >= 0:
        yaml_block = rest[:close_with_body]
        body_start = close_with_body + len("\n" + _FRONT_MATTER_DELIM + "\n")
        body = rest[body_start:]
    elif close_immediate_with_body >= 0:
        yaml_block = ""
        body = rest[len(_FRONT_MATTER_DELIM) + 1 :]
    elif close_immediate_at_end:
        yaml_block = ""
        body = ""
    elif close_at_end:
        yaml_block = rest[: len(rest) - len("\n" + _FRONT_MATTER_DELIM)]
        body = ""
    else:
        raise FrontMatterError(f"No closing '---' delimiter found in {path}")

    if not yaml_block.strip():
        metadata: dict[str, object] = {}
    else:
        try:
            loaded = yaml.safe_load(yaml_block)
        except yaml.YAMLError as exc:
            raise FrontMatterError(f"Invalid YAML in {path}: {exc}") from exc
        if loaded is None:
            metadata = {}
        elif isinstance(loaded, dict):
            metadata = loaded
        else:
            raise FrontMatterError(
                f"YAML front matter must be a mapping,"
                f" got {type(loaded).__name__}: {path}"
            )

    return metadata, body


def write_front_matter_document(
    path: Path,
    metadata: Mapping[str, object],
    body: str,
    *,
    body_mode: BodyMode = "preserve",
    atomic: bool = True,
) -> None:
    """Write a YAML front matter document."""
    yaml_block = yaml.safe_dump(
        dict(metadata),
        allow_unicode=True,
        sort_keys=False,
    )
    if not yaml_block.endswith("\n"):
        yaml_block += "\n"

    if body_mode == "ensure-single-final-newline":
        if body and not body.endswith("\n"):
            body = body + "\n"
        elif body.endswith("\n\n"):
            body = body.rstrip("\n") + "\n"

    content = f"{_FRONT_MATTER_DELIM}\n{yaml_block}{_FRONT_MATTER_DELIM}\n{body}"

    if atomic:
        from ledgercore.atomic import atomic_write_text

        atomic_write_text(path, content)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def iter_source_files(
    directory: Path,
    extensions: tuple[str, ...],
    *,
    recursive: bool = True,
) -> list[Path]:
    """Iterate source files matching given extensions in sorted order."""
    if not directory.is_dir():
        return []
    ext_lower = {e.lower() for e in extensions}
    if recursive:
        paths = [
            p
            for p in directory.rglob("*")
            if p.is_file() and p.suffix.lower() in ext_lower
        ]
    else:
        paths = [
            p
            for p in directory.iterdir()
            if p.is_file() and p.suffix.lower() in ext_lower
        ]
    return sorted(paths)


def iter_markdown_files(
    directory: Path,
    *,
    recursive: bool = False,
) -> list[Path]:
    """Iterate markdown files in sorted order."""
    return iter_source_files(directory, (".md",), recursive=recursive)
