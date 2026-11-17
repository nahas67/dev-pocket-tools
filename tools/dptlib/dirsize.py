"""Directory/file size collection and table rendering helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable, Sequence

_UNITS = ("B", "KB", "MB", "GB", "TB", "PB", "EB")


def human_size(n: int | float) -> str:
    """Format a byte count *n* as a human-readable string (base 1024).

    Examples: ``0 -> "0 B"``, ``1024 -> "1.0 KB"``, ``1536 -> "1.5 KB"``.
    Negative values are handled by formatting their magnitude with a leading
    minus sign.
    """
    try:
        value = float(n)
    except (TypeError, ValueError):
        return str(n)
    sign = "-" if value < 0 else ""
    value = abs(value)
    for unit in _UNITS:
        if value < 1024 or unit == _UNITS[-1]:
            if unit == "B":
                return f"{sign}{int(value)} B"
            return f"{sign}{value:.1f} {unit}"
        value /= 1024.0
    return f"{sign}{value:.1f} {_UNITS[-1]}"  # pragma: no cover


def collect_sizes(paths: Iterable[str | os.PathLike[str]]) -> list[tuple[str, int, int]]:
    """Compute sizes for *paths*, recursing into directories.

    Returns a list of ``(path_string, size_in_bytes, file_count)`` tuples in
    the same order as the input.  A missing or unreadable path yields a zero
    size and zero count rather than raising, so a partially broken tree still
    produces a complete report.  Directory symlinks are not followed.
    """
    results: list[tuple[str, int, int]] = []
    for p in paths:
        path = Path(p)
        total = 0
        count = 0
        if path.is_file():
            try:
                total = path.stat().st_size
                count = 1
            except OSError:
                total, count = 0, 0
        elif path.is_dir():
            for root, _dirs, files in os.walk(path, followlinks=False, onerror=None):
                for name in files:
                    try:
                        total += os.path.getsize(os.path.join(root, name))
                        count += 1
                    except OSError:
                        continue
        results.append((str(path), total, count))
    return results


def format_table(rows: Sequence[Sequence[Any]]) -> str:
    """Render size rows as an aligned plain-text table.

    Each row may be ``(path, size)`` or ``(path, size, count)``.  An integer
    *size* is formatted with :func:`human_size`; a preformatted string is used
    verbatim.  A header and separator line are always included.
    """
    if not rows:
        return "No paths to report."

    normalised: list[tuple[str, str, str]] = []
    for row in rows:
        path = str(row[0])
        raw_size = row[1] if len(row) > 1 else 0
        size = human_size(raw_size) if isinstance(raw_size, (int, float)) else str(raw_size)
        count = str(row[2]) if len(row) > 2 else ""
        normalised.append((path, size, count))

    headers = ("PATH", "SIZE", "FILES")
    widths = [
        max(len(headers[i]), *(len(r[i]) for r in normalised))
        for i in range(3)
    ]
    lines = [
        f"{headers[0]:<{widths[0]}}  {headers[1]:>{widths[1]}}  {headers[2]:>{widths[2]}}",
        f"{'-' * widths[0]}  {'-' * widths[1]}  {'-' * widths[2]}",
    ]
    for path, size, count in normalised:
        lines.append(
            f"{path:<{widths[0]}}  {size:>{widths[1]}}  {count:>{widths[2]}}"
        )
    return "\n".join(lines)
