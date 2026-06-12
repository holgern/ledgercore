"""Tests for ledgercore.time."""

from __future__ import annotations

import re

from ledgercore.time import utc_now_iso


class TestUtcNowIso:
    def test_format(self) -> None:
        result = utc_now_iso()
        assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", result)

    def test_ends_with_z(self) -> None:
        assert utc_now_iso().endswith("Z")

    def test_no_microseconds(self) -> None:
        result = utc_now_iso()
        assert "." not in result
