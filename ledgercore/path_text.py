"""Normalization helpers for human-authored path text."""

from __future__ import annotations

import re
import unicodedata
from typing import Literal

_UNICODE_ESCAPE = re.compile(r"\\u([0-9a-fA-F]{4})|\\U([0-9a-fA-F]{8})")
_PUNCTUATION_TRANSLATION = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
    }
)


def decode_unicode_escape_literals(value: str) -> str:
    """Decode only literal Unicode escape sequences."""
    def replace(match: re.Match[str]) -> str:
        digits = match.group(1) or match.group(2)
        return chr(int(digits, 16))

    return _UNICODE_ESCAPE.sub(replace, value)


def normalize_path_text(
    value: str,
    *,
    unicode_form: Literal["NFC", "NFD", "NFKC", "NFKD"] = "NFKC",
    normalize_punctuation: bool = True,
    slashify_backslashes: bool = True,
    collapse_whitespace: bool = True,
    casefold: bool = False,
) -> str:
    """Normalize path-like text for matching, not filesystem authorization."""
    normalized = decode_unicode_escape_literals(value)
    normalized = unicodedata.normalize(unicode_form, normalized)
    if normalize_punctuation:
        normalized = normalized.translate(_PUNCTUATION_TRANSLATION)
    if slashify_backslashes:
        normalized = normalized.replace("\\", "/")
    if collapse_whitespace:
        normalized = " ".join(normalized.split())
    if casefold:
        normalized = normalized.casefold()
    return normalized
