"""Prefixed numeric ID formatting and slug utilities for ledgercore."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class NumericIdFormat:
    """Configurable prefixed numeric ID format."""

    prefix: str
    separator: str = "-"
    width: int = 4

    def format(self, number: int) -> str:
        """Format a number as a prefixed, zero-padded ID string."""
        return f"{self.prefix}{self.separator}{number:0{self.width}d}"

    def parse(self, value: str) -> int:
        """Parse a prefixed ID string and return the numeric part."""
        expected_prefix = f"{self.prefix}{self.separator}"
        if not value.startswith(expected_prefix):
            raise ValueError(f"ID '{value}' does not match prefix '{expected_prefix}'")
        num_str = value[len(expected_prefix) :]
        if not num_str.isdigit():
            raise ValueError(f"Numeric part of ID '{value}' is not a valid number")
        return int(num_str)

    def next(self, existing_ids: Iterable[str]) -> str:
        """Return the next ID not present in existing_ids."""
        max_num = 0
        expected_prefix = f"{self.prefix}{self.separator}"
        for eid in existing_ids:
            if not eid.startswith(expected_prefix):
                continue
            num_str = eid[len(expected_prefix) :]
            if num_str.isdigit():
                num = int(num_str)
                if num > max_num:
                    max_num = num
        return self.format(max_num + 1)


def parse_prefixed_number(
    value: str,
    *,
    prefix: str,
    separator: str = "-",
    width: int = 4,
) -> int:
    """Parse a prefixed numeric ID string and return the number."""
    fmt = NumericIdFormat(prefix=prefix, separator=separator, width=width)
    return fmt.parse(value)


def next_prefixed_id(
    prefix: str,
    existing_ids: Iterable[str],
    *,
    separator: str = "-",
    width: int = 4,
) -> str:
    """Return the next prefixed ID given existing IDs."""
    fmt = NumericIdFormat(prefix=prefix, separator=separator, width=width)
    return fmt.next(existing_ids)


_slug_non_alpha = re.compile(r"[^a-z0-9]+")


def slugify_ref(value: str, *, empty: str = "item") -> str:
    """Lowercase, trim, collapse non-alphanumeric runs to dashes."""
    slug = _slug_non_alpha.sub("-", value.strip().lower()).strip("-")
    if not slug:
        return empty
    return slug
