"""Five-field cron expression parsing and human-readable explanation.

Supported field syntax: ``*``, single numbers, comma lists, inclusive ranges
(``a-b``), step values (``*/n``, ``a-b/n``, ``a/n``).  Month names (``JAN``)
and weekday names (``MON``) are accepted in the corresponding fields.  No
external cron library is used.
"""

from __future__ import annotations

import re
from typing import Any

_MONTHS = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}
_DAYS = {
    "SUN": 0, "MON": 1, "TUE": 2, "WED": 3, "THU": 4, "FRI": 5, "SAT": 6,
}
_FIELD_SPECS: tuple[tuple[str, int, int, dict[str, int] | None], ...] = (
    ("minute", 0, 59, None),
    ("hour", 0, 23, None),
    ("day_of_month", 1, 31, None),
    ("month", 1, 12, _MONTHS),
    ("day_of_week", 0, 7, _DAYS),
)


def _replace_names(field: str, names: dict[str, int] | None) -> str:
    """Replace month/weekday abbreviations with their numbers."""
    if not names:
        return field

    def sub(match: re.Match[str]) -> str:
        token = match.group(0).upper()
        if token in names:
            value = names[token]
            # Sunday may be written as 7 in cron; keep the canonical 0 here.
            return str(value)
        return token

    return re.sub(r"[A-Za-z]{3}", sub, field)


def parse_field(field: str, lo: int, hi: int) -> list[int]:
    """Expand one cron *field* into a sorted list of integers in ``[lo, hi]``.

    Raises ``ValueError`` for empty fields, non-numeric tokens, zero/negative
    steps or out-of-range values.  ``a/n`` means "from a to hi, every n".
    """
    if field is None or not str(field).strip():
        raise ValueError("empty cron field")
    field = str(field).strip()
    values: set[int] = set()

    for part in field.split(","):
        part = part.strip()
        if not part:
            raise ValueError(f"empty value in cron field: {field!r}")

        step = 1
        if "/" in part:
            base, step_text = part.split("/", 1)
            if not step_text.isdigit() or int(step_text) <= 0:
                raise ValueError(f"invalid step in cron field: {part!r}")
            step = int(step_text)
        else:
            base = part

        base = base.strip()
        if base == "*":
            start, end = lo, hi
        elif "-" in base:
            left, right = base.split("-", 1)
            if not left.isdigit() or not right.isdigit():
                raise ValueError(f"invalid range in cron field: {part!r}")
            start, end = int(left), int(right)
            if start > end:
                raise ValueError(f"descending range in cron field: {part!r}")
        elif base.isdigit():
            start = int(base)
            end = hi if "/" in part else start
        else:
            raise ValueError(f"invalid value in cron field: {part!r}")

        if start < lo or end > hi:
            raise ValueError(
                f"value out of range in cron field {part!r} (allowed {lo}-{hi})"
            )
        values.update(range(start, end + 1, step))

    return sorted(values)


def describe(expr: str) -> dict[str, Any]:
    """Parse a 5-field cron *expr* into a dictionary of expanded fields.

    Returns a dict with keys ``expression``, ``minute``, ``hour``,
    ``day_of_month``, ``month`` and ``day_of_week``.  The four field values
    are sorted integer lists.  Raises ``ValueError`` when the expression does
    not have exactly five fields or a field is invalid.
    """
    if not isinstance(expr, str):
        raise ValueError("cron expression must be a string")
    parts = expr.split()
    if len(parts) != 5:
        raise ValueError("cron expression must have exactly 5 fields")

    result: dict[str, Any] = {"expression": expr}
    for (name, lo, hi, names), field in zip(_FIELD_SPECS, parts):
        result[name] = parse_field(_replace_names(field, names), lo, hi)
    return result


def _field_phrase(values: list[int], lo: int, hi: int, singular: str) -> str:
    """Build a short English phrase for one expanded cron field."""
    full = list(range(lo, hi + 1))
    if values == full:
        return f"every {singular}"
    if len(values) == 1:
        return f"at {singular} {values[0]}"
    shown = ", ".join(str(v) for v in values[:10])
    if len(values) > 10:
        shown += ", ..."
    return f"at {singular}s {shown}"


def explain(expr: str) -> str:
    """Return a multi-line human-readable explanation of a cron *expr*.

    The first line echoes the expression; each following line names a field
    and summarises when it fires.  Raises ``ValueError`` for invalid input.
    """
    parsed = describe(expr)
    labels = (
        ("minute", 0, 59, "minute"),
        ("hour", 0, 23, "hour"),
        ("day_of_month", 1, 31, "day of the month"),
        ("month", 1, 12, "month"),
        ("day_of_week", 0, 7, "day of the week"),
    )
    lines = [f"Cron: {parsed['expression']}"]
    for key, lo, hi, label in labels:
        lines.append(f"  {key:<14} {_field_phrase(parsed[key], lo, hi, label)}")
    return "\n".join(lines)
