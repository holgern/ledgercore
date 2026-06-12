"""Text I/O utilities for ledgercore."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


def normalize_newlines(text: str) -> str:
    """Convert CRLF and CR to LF."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def ensure_dir(path: Path) -> None:
    """Create parent directories as needed."""
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path, *, normalize: bool = True) -> str:
    """Read UTF-8 text from a file."""
    if normalize:
        text = path.read_text(encoding="utf-8")
        return normalize_newlines(text)
    return path.read_bytes().decode("utf-8")


def write_text(path: Path, text: str, *, normalize: bool = True) -> None:
    """Write UTF-8 text to a file, creating parent directories."""
    if normalize:
        text = normalize_newlines(text)
    ensure_dir(path.parent)
    path.write_bytes(text.encode("utf-8"))


def content_hash(text: str) -> str:
    """Return a stable SHA-256 hex digest of UTF-8 text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def summarize_text(text: str, max_chars: int = 80) -> str:
    """Collapse whitespace and truncate safely."""
    collapsed = re.sub(r"\s+", " ", text).strip()
    if len(collapsed) <= max_chars:
        return collapsed
    truncated = collapsed[:max_chars]
    if truncated.rfind(" ") > max_chars // 2:
        truncated = truncated[: truncated.rfind(" ")]
    return truncated.rstrip() + "..."


def merge_text(current: str, incoming: str, *, prepend: bool = False) -> str:
    """Combine text blocks without introducing excessive blank lines."""
    cur = current.strip()
    inc = incoming.strip()
    if not cur:
        return inc
    if not inc:
        return cur
    if prepend:
        parts = [inc, cur]
    else:
        parts = [cur, inc]
    return "\n\n".join(parts)
