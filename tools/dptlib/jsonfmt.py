"""JSON formatting, minifying, flattening and validation helpers.

All functions operate on JSON *text* (``str``) unless noted and use only the
standard library.  Formatting preserves data exactly; only whitespace and key
order change.
"""

from __future__ import annotations

import json
from typing import Any


def is_json(text: str) -> bool:
    """Return ``True`` if *text* is valid JSON.

    Any value accepted by :func:`json.loads` (object, array, string, number,
    boolean or null) counts as valid JSON.
    """
    if not isinstance(text, (str, bytes, bytearray)):
        return False
    try:
        json.loads(text)
    except (ValueError, TypeError):
        return False
    return True


def format_json(text: str, indent: int = 2, sort_keys: bool = False) -> str:
    """Pretty-print JSON *text* with the given *indent* and key ordering.

    Raises ``ValueError`` (with the parser message) when *text* is not valid
    JSON.  Output is always a ``str`` with a trailing newline omitted.
    """
    try:
        obj = json.loads(text)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"invalid JSON: {exc}") from exc
    return json.dumps(obj, indent=indent, sort_keys=sort_keys, ensure_ascii=False)


def minify(text: str) -> str:
    """Return *text* as compact JSON with no insignificant whitespace."""
    try:
        obj = json.loads(text)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"invalid JSON: {exc}") from exc
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


def flatten(obj: Any, prefix: str = "") -> dict[str, Any]:
    """Flatten a nested dict/list into a mapping of dotted paths to values.

    Dictionary keys are joined with ``.`` and list indices are appended as
    string indices, e.g.::

        {"a": {"b": [1, 2]}} -> {"a.b.0": 1, "a.b.1": 2}

    Empty dictionaries and lists are kept as leaf values at their path.  When
    *prefix* is non-empty it is prepended (with a dot separator) to every key.
    Scalar inputs produce ``{prefix: value}`` (or ``{"": value}``).
    """
    result: dict[str, Any] = {}

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            if not value:
                result[path] = value
                return
            for key, child in value.items():
                child_path = f"{path}.{key}" if path else str(key)
                walk(child, child_path)
        elif isinstance(value, list):
            if not value:
                result[path] = value
                return
            for index, child in enumerate(value):
                child_path = f"{path}.{index}" if path else str(index)
                walk(child, child_path)
        else:
            result[path] = value

    walk(obj, prefix)
    return result
