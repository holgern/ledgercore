"""UTC timestamp utilities for ledgercore."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now_iso(*, now: datetime | None = None) -> str:
    """Return UTC timestamp in ISO-8601 format with second precision."""
    if now is None:
        now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")
