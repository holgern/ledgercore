"""Prefixed numeric ID formatting and slug utilities for ledgercore."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class LedgerIdParts:
    """Parsed components of a ledger ID."""

    prefix: str
    number: int
    segment: str | None


@dataclass(frozen=True)
class LedgerIdFormat:
    """Configurable prefixed numeric ID format with optional segment support.

    Supports ID patterns like:
      task-0001         (prefix="task")
      plan-0001         (prefix="plan")
      al_0013           (prefix="al", separator="_")
      al_content_0013   (prefix="al", separator="_", segment_separator="_")
    """

    prefix: str
    separator: str = "-"
    width: int = 4
    segment_separator: str | None = None
    segment_required: bool = False

    def format(self, number: int, *, segment: str | None = None) -> str:
        """Format a number (and optional segment) as an ID string."""
        _validate_number(number)
        padded = f"{number:0{self.width}d}"
        if segment is not None:
            seg_sep = (
                self.segment_separator if self.segment_separator else self.separator
            )
            return f"{self.prefix}{seg_sep}{segment}{self.separator}{padded}"
        return f"{self.prefix}{self.separator}{padded}"

    def parse(self, value: str) -> int:
        """Parse an ID string and return the numeric part."""
        return self.parse_parts(value).number

    def parse_parts(self, value: str) -> LedgerIdParts:
        """Parse an ID string and return all components."""
        # Try simple pattern first (prefix + sep + number)
        simple = self._build_simple_pattern()
        m = simple.fullmatch(value)
        if m:
            return LedgerIdParts(
                prefix=self.prefix,
                number=int(m.group("number")),
                segment=None,
            )
        # If segment support is enabled, try segmented pattern
        if self.segment_separator is not None:
            seg = self._build_segmented_pattern()
            m = seg.fullmatch(value)
            if m:
                return LedgerIdParts(
                    prefix=self.prefix,
                    number=int(m.group("number")),
                    segment=m.group("segment"),
                )
        raise ValueError(
            f"ID '{value}' does not match format "
            f"prefix='{self.prefix}' separator='{self.separator}'"
        )

    def next(
        self,
        existing_ids: Iterable[str],
        *,
        segment: str | None = None,
    ) -> str:
        """Return the next ID not present in existing_ids."""
        max_num = 0
        for eid in existing_ids:
            try:
                parts = self.parse_parts(eid)
            except ValueError:
                continue
            if segment is not None and parts.segment != segment:
                continue
            if segment is None and parts.segment is not None:
                continue
            if parts.number > max_num:
                max_num = parts.number
        return self.format(max_num + 1, segment=segment)

    def is_valid(self, value: object) -> bool:
        """Check whether a value is a valid ID for this format."""
        if not isinstance(value, str):
            return False
        try:
            parts = self.parse_parts(value)
            if parts.segment is not None and self.segment_required is False:
                return True
            if parts.segment is None and self.segment_required:
                return False
            return True
        except ValueError:
            return False

    def filename(self, value: str, *, extension: str) -> str:
        """Convert an ID to a filename with the given extension."""
        return f"{value}{extension}"

    def _build_simple_pattern(self) -> re.Pattern[str]:
        sep = re.escape(self.separator)
        return re.compile(rf"^{re.escape(self.prefix)}{sep}(?P<number>\d+)$")

    def _build_segmented_pattern(self) -> re.Pattern[str]:
        assert self.segment_separator is not None
        seg_sep = re.escape(self.segment_separator)
        sep = re.escape(self.separator)
        return re.compile(
            rf"^{re.escape(self.prefix)}"
            rf"{seg_sep}(?P<segment>[a-zA-Z0-9_-]+)"
            rf"{sep}(?P<number>\d+)$"
        )


@dataclass(frozen=True)
class NumericIdFormat:
    """Configurable prefixed numeric ID format (legacy compatibility)."""

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


def _validate_number(number: int) -> None:
    """Validate that number is a positive integer and not a boolean."""
    if isinstance(number, bool):
        raise ValueError("Number must not be a boolean")
    if number <= 0:
        raise ValueError(f"Number must be positive, got {number}")


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
