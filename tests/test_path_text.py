"""Tests for ledgercore.path_text."""

from ledgercore.path_text import (
    decode_unicode_escape_literals,
    normalize_path_text,
)


def test_decodes_only_unicode_escape_literals() -> None:
    assert decode_unicode_escape_literals(r"Owner\u2019s\note") == "Owner’s\\note"


def test_normalizes_punctuation_slashes_and_whitespace() -> None:
    assert normalize_path_text(" Raw\\Owner\u2019s\u2014Notes ") == (
        "Raw/Owner's-Notes"
    )


def test_casefold_is_optional() -> None:
    assert normalize_path_text("Raw/Sources", casefold=True) == "raw/sources"
