"""UTC timestamp utilities for ledgercore."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

Timespec = Literal[
    "auto",
    "hours",
    "minutes",
    "seconds",
    "milliseconds",
    "microseconds",
]
TimezoneStyle = Literal["z", "offset"]


def utc_now_iso(
    *,
    now: datetime | None = None,
    timespec: Timespec = "seconds",
    timezone_style: TimezoneStyle = "z",
) -> str:
    """Return a normalized UTC timestamp in ISO-8601 format."""
    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    normalized = now.astimezone(timezone.utc)
    rendered = normalized.isoformat(timespec=timespec)
    if timezone_style == "z":
        return rendered.removesuffix("+00:00") + "Z"
    if timezone_style == "offset":
        return rendered
    raise ValueError(f"Unsupported timezone style: {timezone_style}")
