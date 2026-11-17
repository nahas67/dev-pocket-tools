"""Epoch timestamp conversion and duration humanising helpers.

Timestamps are interpreted as UTC and rendered as ISO-8601 strings ending in
``Z``.  Everything uses the standard library only.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

_UNIT_DIVISOR = {
    "s": 1.0,
    "sec": 1.0,
    "secs": 1.0,
    "second": 1.0,
    "seconds": 1.0,
    "ms": 1000.0,
    "msec": 1000.0,
    "millisecond": 1000.0,
    "milliseconds": 1000.0,
    "us": 1_000_000.0,
    "microsecond": 1_000_000.0,
    "microseconds": 1_000_000.0,
    "ns": 1_000_000_000.0,
    "nanosecond": 1_000_000_000.0,
    "nanoseconds": 1_000_000_000.0,
}


def to_datetime(ts: object, unit: str = "s") -> str:
    """Convert an epoch timestamp *ts* to an ISO-8601 UTC string.

    *unit* selects how *ts* is scaled to seconds: ``"s"`` (default), ``"ms"``,
    ``"us"`` or ``"ns"`` (long forms such as ``"milliseconds"`` are accepted).
    *ts* may be an int, float or numeric string.

    >>> to_datetime(0)
    '1970-01-01T00:00:00Z'
    >>> to_datetime(1700000000000, unit="ms")
    '2023-11-14T22:13:20Z'
    """
    divisor = _UNIT_DIVISOR.get(str(unit).lower().strip())
    if divisor is None:
        raise ValueError(f"unknown time unit: {unit!r}")
    if isinstance(ts, bool):
        raise ValueError("timestamp must be numeric")
    try:
        value = float(ts)
    except (TypeError, ValueError) as exc:
        raise ValueError("timestamp must be numeric") from exc
    seconds = value / divisor
    try:
        dt = datetime.fromtimestamp(seconds, tz=timezone.utc)
    except (OverflowError, OSError, ValueError) as exc:
        raise ValueError("timestamp out of range") from exc
    return dt.isoformat(timespec="microseconds").replace("+00:00", "Z").replace(".000000Z", "Z")


def from_datetime(text: str) -> int:
    """Parse an ISO-8601 (or common) datetime *text* into epoch seconds.

    A trailing ``Z`` is accepted, and naive timestamps are interpreted as UTC.
    Raises ``ValueError`` when the string cannot be parsed.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("datetime text must be a non-empty string")
    value = text.strip()
    iso = value[:-1] + "+00:00" if value.endswith(("Z", "z")) else value
    dt: datetime | None = None
    try:
        dt = datetime.fromisoformat(iso)
    except ValueError:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"):
            try:
                dt = datetime.strptime(value, fmt)
                break
            except ValueError:
                continue
    if dt is None:
        raise ValueError(f"could not parse datetime: {text!r}")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def humanize(seconds: object) -> str:
    """Render a duration in *seconds* as a compact ``"1d 2h 3m 4s"`` string.

    Zero-valued units are omitted; a duration of zero yields ``"0s"``.
    Negative durations are prefixed with ``-``.  Sub-second values are shown
    as milliseconds (``ms``).
    """
    if isinstance(seconds, bool):
        raise ValueError("seconds must be numeric")
    try:
        total = float(seconds)
    except (TypeError, ValueError) as exc:
        raise ValueError("seconds must be numeric") from exc

    sign = "-" if total < 0 else ""
    remaining = abs(total)
    parts: list[str] = []

    days = int(remaining // 86400)
    remaining -= days * 86400
    hours = int(remaining // 3600)
    remaining -= hours * 3600
    minutes = int(remaining // 60)
    remaining -= minutes * 60
    secs = int(remaining)
    millis = int(round((remaining - secs) * 1000))
    if millis == 1000:
        secs += 1
        millis = 0

    for amount, label in ((days, "d"), (hours, "h"), (minutes, "m"), (secs, "s")):
        if amount:
            parts.append(f"{amount}{label}")
    if millis:
        parts.append(f"{millis}ms")
    if not parts:
        return "0s"
    return sign + " ".join(parts)


def now_ms() -> int:
    """Return the current epoch time in milliseconds as an ``int``."""
    return int(time.time() * 1000)
