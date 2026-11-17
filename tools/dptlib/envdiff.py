"""Environment file parsing and diffing helpers.

These helpers work with the common ``KEY=VALUE`` dotenv format: blank lines and
``#`` comments are ignored, an optional ``export`` prefix is accepted and
surrounding quotes are stripped.  No third-party dotenv library is required.
"""

from __future__ import annotations

from typing import Any


def _unquote(value: str) -> str:
    """Strip one matching pair of surrounding single or double quotes."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def parse_env(text: str) -> dict[str, str]:
    """Parse dotenv-style *text* into a ``{KEY: VALUE}`` dictionary.

    * Blank lines and lines whose first non-space character is ``#`` are
      ignored.
    * A leading ``export `` (or ``export\\t``) is stripped.
    * The first ``=`` separates key from value; subsequent ``=`` characters
      are kept in the value.
    * Surrounding whitespace and one matching pair of quotes are removed from
      the value.  Empty values are preserved as ``""``.
    """
    result: dict[str, str] = {}
    if not text:
        return result

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export ") or stripped.startswith("export\t"):
            stripped = stripped[len("export") :].lstrip()
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if not key:
            continue
        result[key] = _unquote(value)
    return result


def diff_env(a: dict[str, str], b: dict[str, str]) -> dict[str, dict[str, Any]]:
    """Compare two environment dictionaries.

    Returns a dictionary with exactly four keys:

    ``added``
        ``{key: b[key]}`` for keys present only in *b*.
    ``removed``
        ``{key: a[key]}`` for keys present only in *a*.
    ``changed``
        ``{key: {"old": a[key], "new": b[key]}}`` for keys whose value differs.
    ``same``
        ``{key: a[key]}`` for keys present in both with equal values.

    Each result is itself a dict, so key membership tests and iteration over
    the changed/added keys work naturally.
    """
    a = a or {}
    b = b or {}
    added = {k: b[k] for k in b if k not in a}
    removed = {k: a[k] for k in a if k not in b}
    changed: dict[str, dict[str, Any]] = {}
    same: dict[str, str] = {}
    for k in a:
        if k in b:
            if a[k] == b[k]:
                same[k] = a[k]
            else:
                changed[k] = {"old": a[k], "new": b[k]}
    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "same": same,
    }


def mask_value(v: object) -> str:
    """Return a masked preview of a (possibly secret) value *v*.

    The first and last characters remain visible so a developer can confirm
    which entry is which; everything between them becomes ``*``.  Short values
    (zero, one or two characters) are masked entirely.
    """
    s = str(v)
    if len(s) == 0:
        return ""
    if len(s) <= 2:
        return "*" * len(s)
    return s[0] + ("*" * (len(s) - 2)) + s[-1]
