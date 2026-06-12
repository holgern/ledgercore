"""Tests for ledgercore.ids."""

from __future__ import annotations

import pytest

from ledgercore.ids import (
    NumericIdFormat,
    next_prefixed_id,
    parse_prefixed_number,
    slugify_ref,
)


class TestNumericIdFormat:
    def test_format_default(self) -> None:
        fmt = NumericIdFormat(prefix="task")
        assert fmt.format(1) == "task-0001"

    def test_format_custom_separator(self) -> None:
        fmt = NumericIdFormat(prefix="al", separator="_")
        assert fmt.format(5) == "al_0005"

    def test_format_custom_width(self) -> None:
        fmt = NumericIdFormat(prefix="run", width=2)
        assert fmt.format(3) == "run-03"

    def test_parse(self) -> None:
        fmt = NumericIdFormat(prefix="task")
        assert fmt.parse("task-0001") == 1

    def test_parse_custom(self) -> None:
        fmt = NumericIdFormat(prefix="al", separator="_")
        assert fmt.parse("al_0042") == 42

    def test_parse_wrong_prefix(self) -> None:
        fmt = NumericIdFormat(prefix="task")
        with pytest.raises(ValueError, match="prefix"):
            fmt.parse("run-0001")

    def test_parse_non_numeric(self) -> None:
        fmt = NumericIdFormat(prefix="task")
        with pytest.raises(ValueError, match="not a valid number"):
            fmt.parse("task-abc")

    def test_next_from_empty(self) -> None:
        fmt = NumericIdFormat(prefix="task")
        assert fmt.next([]) == "task-0001"

    def test_next_from_existing(self) -> None:
        fmt = NumericIdFormat(prefix="task")
        assert fmt.next(["task-0001", "task-0002"]) == "task-0003"

    def test_next_ignores_non_matching(self) -> None:
        fmt = NumericIdFormat(prefix="task")
        assert fmt.next(["run-0001", "task-0001"]) == "task-0002"

    def test_next_no_zero(self) -> None:
        fmt = NumericIdFormat(prefix="task")
        ids = ["task-0001", "task-0003"]
        assert fmt.next(ids) == "task-0004"


class TestParsePrefixedNumber:
    def test_default(self) -> None:
        assert parse_prefixed_number("task-0001", prefix="task") == 1

    def test_custom(self) -> None:
        assert parse_prefixed_number("al_0042", prefix="al", separator="_") == 42


class TestNextPrefixedId:
    def test_default(self) -> None:
        assert next_prefixed_id("task", []) == "task-0001"

    def test_with_existing(self) -> None:
        assert next_prefixed_id("task", ["task-0001"]) == "task-0002"


class TestSlugifyRef:
    def test_lowercases(self) -> None:
        assert slugify_ref("Hello World") == "hello-world"

    def test_collapses_non_alnum(self) -> None:
        assert slugify_ref("a   b!!!c") == "a-b-c"

    def test_trims(self) -> None:
        assert slugify_ref("  hello  ") == "hello"

    def test_empty_returns_default(self) -> None:
        assert slugify_ref("") == "item"

    def test_custom_empty(self) -> None:
        assert slugify_ref("!!!", empty="none") == "none"

    def test_only_dashes(self) -> None:
        assert slugify_ref("---") == "item"
