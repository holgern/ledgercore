"""Generic SHA-256 content fingerprint helpers."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Literal

from ledgercore.frontmatter import split_front_matter_text
from ledgercore.jsonio import canonical_json


@dataclass(frozen=True)
class TextFingerprint:
    """SHA-256 values for a document and its front matter components."""

    full_sha256: str
    body_sha256: str
    metadata_sha256: str


def sha256_text(text: str) -> str:
    """Return the SHA-256 digest of UTF-8 text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Return the SHA-256 digest of bytes."""
    return hashlib.sha256(data).hexdigest()


def front_matter_fingerprint(
    text: str, *, missing: Literal["error", "empty"] = "empty"
) -> TextFingerprint:
    """Fingerprint a full document, parsed body, and canonical metadata."""
    metadata, body = split_front_matter_text(text, missing=missing)
    return TextFingerprint(
        full_sha256=sha256_text(text),
        body_sha256=sha256_text(body),
        metadata_sha256=sha256_text(canonical_json(metadata)),
    )
