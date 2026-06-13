"""Tests for ledgercore.hashing."""

import hashlib

from ledgercore.hashing import (
    front_matter_fingerprint,
    sha256_bytes,
    sha256_text,
)


def test_text_and_bytes_hashes_match_reference() -> None:
    assert sha256_text("é") == hashlib.sha256("é".encode()).hexdigest()
    assert sha256_bytes(b"\x00\xff") == hashlib.sha256(b"\x00\xff").hexdigest()


def test_front_matter_fingerprint_is_component_stable() -> None:
    first = front_matter_fingerprint("---\na: 1\nb: 2\n---\nBody\n")
    reordered = front_matter_fingerprint("---\nb: 2\na: 1\n---\nBody\n")
    assert first.full_sha256 != reordered.full_sha256
    assert first.body_sha256 == reordered.body_sha256
    assert first.metadata_sha256 == reordered.metadata_sha256


def test_front_matter_fingerprint_allows_missing_header() -> None:
    result = front_matter_fingerprint("Body\n")
    assert result.body_sha256 == sha256_text("Body\n")
