"""Tests for ledgercore.time."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

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

    def test_injected_now(self) -> None:
        injected = datetime(2025, 3, 15, 10, 30, 45, tzinfo=timezone.utc)
        result = utc_now_iso(now=injected)
        assert result == "2025-03-15T10:30:45Z"

    def test_injected_now_timezone_aware(self) -> None:
        utc_plus_2 = timezone(timedelta(hours=2))
        injected = datetime(2025, 6, 1, 14, 0, 0, tzinfo=utc_plus_2)
        result = utc_now_iso(now=injected)
        # strftime uses the datetime's tzinfo, so 14:00+02:00 -> 14:00 in strftime
        assert result == "2025-06-01T14:00:00Z"
