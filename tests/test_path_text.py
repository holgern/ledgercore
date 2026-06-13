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


def test_default_basic_profile_preserves_existing_behavior() -> None:
    assert normalize_path_text("a\u2013b.md") == "a-b.md"


def test_wide_punctuation_profile() -> None:
    assert (
        normalize_path_text(
            "Bob\u201bs File\u2212v2.md", punctuation_profile="wide"
        )
        == "Bob's File-v2.md"
    )


def test_custom_translation_extends_profile() -> None:
    assert normalize_path_text(
        "a\u2022b.md", punctuation_translation={"\u2022": "-"}
    ) == "a-b.md"


def test_profile_none_still_uses_custom_translation() -> None:
    assert normalize_path_text(
        "a\u2013b\u2022c.md",
        punctuation_profile="none",
        punctuation_translation={"\u2022": "-"},
    ) == "a\u2013b-c.md"
