"""JSON Web Token inspection helpers (decode only - never verify).

The functions here are intended for developers who need to peek at a JWT's
header and payload during debugging.  ``decode`` intentionally performs **no
signature verification and no claim validation**: it simply base64url-decodes
and JSON-parses the segments.  Never use this module to make authorization
decisions.
"""

from __future__ import annotations

import base64
import binascii
import json
import time
from datetime import datetime, timezone
from typing import Any


def b64url_decode(seg: str | bytes) -> bytes:
    """Base64url-decode *seg*, adding missing padding as needed.

    Both ``str`` and ``bytes`` inputs are accepted.  The URL-safe alphabet
    (``-`` and ``_``) is handled.  Invalid input raises ``ValueError``.
    """
    if isinstance(seg, str):
        raw = seg.encode("ascii", "strict")
    elif isinstance(seg, bytes):
        raw = seg
    else:
        raise ValueError("segment must be str or bytes")

    # Strip any stray whitespace and normalise padding.
    raw = raw.strip()
    padding = b"=" * (-len(raw) % 4)
    try:
        return base64.urlsafe_b64decode(raw + padding)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("invalid base64url segment") from exc


def is_expired(payload: dict[str, Any], now: object | None = None) -> bool | None:
    """Return whether the ``exp`` claim in *payload* has passed.

    * ``None`` is returned when there is no ``exp`` claim or it is not a
      number (a token without an expiry cannot be judged).
    * ``now`` may be an ``int``/``float`` epoch timestamp or a ``datetime``
      (naive datetimes are treated as UTC).  It defaults to the current time.

    A small tolerance of zero is used: a token is expired when ``now >= exp``.
    """
    if not isinstance(payload, dict):
        return None
    exp = payload.get("exp")
    if isinstance(exp, bool) or not isinstance(exp, (int, float)):
        return None

    if now is None:
        now_ts: float = time.time()
    elif isinstance(now, datetime):
        if now.tzinfo is None:
            now_ts = now.replace(tzinfo=timezone.utc).timestamp()
        else:
            now_ts = now.timestamp()
    elif isinstance(now, (int, float)) and not isinstance(now, bool):
        now_ts = float(now)
    else:
        now_ts = time.time()

    return now_ts >= float(exp)


def decode(token: str) -> dict[str, Any]:
    """Decode a JWT into a dictionary with diagnostic information.

    The returned dictionary always contains these keys:

    ``header``
        Parsed JOSE header (``dict``), or ``None`` when unparsable.
    ``payload``
        Parsed claims (``dict``), or ``None`` when unparsable.
    ``signature``
        Raw decoded signature bytes, or ``b""`` when absent/invalid.
    ``is_expired``
        Result of :func:`is_expired` on the payload (``bool`` or ``None``).

    A ``ValueError`` is raised only when the token is not a string or does not
    have at least two dot-separated segments.  Individual malformed segments
    degrade to ``None``/``b""`` rather than aborting the whole decode.
    """
    if not isinstance(token, str):
        raise ValueError("token must be a string")
    parts = token.strip().split(".")
    if len(parts) < 2:
        raise ValueError("token must have at least two segments (header.payload)")

    header: dict[str, Any] | None = None
    payload: dict[str, Any] | None = None
    signature = b""

    try:
        header_obj = json.loads(b64url_decode(parts[0]).decode("utf-8"))
        if isinstance(header_obj, dict):
            header = header_obj
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        header = None

    try:
        payload_obj = json.loads(b64url_decode(parts[1]).decode("utf-8"))
        if isinstance(payload_obj, dict):
            payload = payload_obj
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        payload = None

    if len(parts) >= 3:
        try:
            signature = b64url_decode(parts[2])
        except ValueError:
            signature = b""

    expired = is_expired(payload) if payload is not None else None
    return {
        "header": header,
        "payload": payload,
        "signature": signature,
        "is_expired": expired,
    }


def redact(token: str) -> str:
    """Return a shortened, non-reversible preview of *token*.

    Only the first and last six characters are kept.  Very short tokens are
    replaced entirely with ``"***"`` so no meaningful material leaks.
    """
    if not isinstance(token, str):
        return "***"
    stripped = token.strip()
    if len(stripped) <= 12:
        return "***"
    return f"{stripped[:6]}...{stripped[-6:]}"
