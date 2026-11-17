"""Port and listener inspection helpers.

This module parses the plain-text output of ``netstat`` (Windows) and ``lsof``
(macOS / Linux) into a single, uniform record shape so callers never have to
care which platform produced the data.  It also builds the correct per-platform
command used to terminate a process.

Uniform record shape
--------------------
Every parser returns a list of dictionaries with these keys::

    proto          protocol name, e.g. "TCP" or "UDP"
    protocol       alias of ``proto``
    address        local bind address, e.g. "0.0.0.0" or "[::]"
    local_address  alias of ``address``
    port           integer local port
    state          connection state string (may be empty for UDP)
    pid            integer process id (or ``None`` when unavailable)
    process        process/command name (or ``None`` when unavailable)

No third-party libraries are used and no subprocesses are launched here; all
functions are pure apart from ``kill_command`` which only *builds* a command.
"""

from __future__ import annotations

import os
import re
from typing import Any

# Common key aliases documented above.
_RECORD_KEYS = (
    "proto",
    "protocol",
    "address",
    "local_address",
    "port",
    "state",
    "pid",
    "process",
)

# Tokens that identify a network line in netstat output.
_NETSTAT_PROTOS = {"TCP", "TCPv6", "UDP", "UDPv6"}
_LSOF_PROTOS = ("TCP", "UDP", "TCPv6", "UDPv6", "TCPv4", "UDPv4")


def _record(
    proto: str,
    address: str,
    port: int | None,
    state: str,
    pid: int | None,
    process: str | None,
) -> dict[str, Any]:
    """Build a uniform listener record from parser primitives."""
    return {
        "proto": proto,
        "protocol": proto,
        "address": address,
        "local_address": address,
        "port": port,
        "state": state,
        "pid": pid,
        "process": process,
    }


def valid_port(value: object) -> bool:
    """Return ``True`` if *value* is a valid TCP/UDP port (1-65535).

    Integers and strings of decimal digits are accepted.  Anything else -
    including booleans, floats, negative numbers, ``0``, ``65536`` and junk
    text - returns ``False``.

    >>> valid_port(80)
    True
    >>> valid_port("8080")
    True
    >>> valid_port(65536)
    False
    """
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return 1 <= value <= 65535
    if isinstance(value, str):
        s = value.strip()
        if not s.isdigit():
            return False
        try:
            return 1 <= int(s) <= 65535
        except ValueError:  # pragma: no cover - isdigit guards this
            return False
    return False


def _split_endpoint(token: str) -> tuple[str, int | None]:
    """Split an ``address:port`` token into ``(address, port)``.

    Handles IPv4 (``0.0.0.0:80``), bracketed IPv6 (``[::]:443``) and wildcard
    forms (``*:3000``).  Returns ``(token, None)`` when no port can be found.
    """
    token = token.strip()
    if not token:
        return "", None

    # Bracketed IPv6: [::]:443 or [::1]:5432
    if token.startswith("["):
        end = token.find("]")
        if end != -1:
            address = token[1:end]
            rest = token[end + 1 :]
            if rest.startswith(":"):
                port_text = rest[1:]
                return address, int(port_text) if port_text.isdigit() else None
            return address, None

    # Unbracketed IPv6 has many colons; take the text after the last one as
    # the port only when it is a pure decimal number.
    if token.count(":") == 1:
        address, port_text = token.rsplit(":", 1)
        return address, int(port_text) if port_text.isdigit() else None
    if token.count(":") > 1:
        address, _, port_text = token.rpartition(":")
        if port_text.isdigit():
            return address, int(port_text)
        return token, None

    return token, None


def parse_netstat(text: str) -> list[dict[str, Any]]:
    """Parse Windows-style ``netstat -ano`` text into listener records.

    Recognises the standard columns ``Proto Local Foreign State PID``.  Header
    lines, blank lines and unrelated text are ignored.  Malformed rows are
    skipped rather than raising, so truncated or localised output degrades
    gracefully.
    """
    entries: list[dict[str, Any]] = []
    if not text:
        return entries

    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        proto = parts[0].upper()
        if proto not in _NETSTAT_PROTOS:
            continue

        local = parts[1]
        address, port = _split_endpoint(local)

        # PID is the last whitespace-separated token and must be numeric.
        pid: int | None = None
        if parts[-1].isdigit():
            pid = int(parts[-1])

        # State: for TCP it is the token right after the foreign address;
        # UDP rows often have no state (and the PID follows the foreign addr).
        state = ""
        if proto.startswith("TCP") and len(parts) >= 5:
            candidate = parts[3]
            if not candidate.isdigit():
                state = candidate

        entries.append(_record(proto, address, port, state, pid, None))
    return entries


def parse_lsof(text: str) -> list[dict[str, Any]]:
    """Parse ``lsof -nP`` text into listener records.

    Both the classic column layout (``COMMAND PID USER FD TYPE DEVICE SIZE/OFF
    NODE NAME``) and bare ``NAME``-only lines are handled.  The network name
    column looks like ``TCP *:8080 (LISTEN)`` or ``UDP 127.0.0.1:53``.
    """
    entries: list[dict[str, Any]] = []
    if not text:
        return entries

    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue

        # Locate the network-type token; everything relevant follows it.
        proto_idx = -1
        for idx, token in enumerate(parts):
            if token.upper() in _LSOF_PROTOS:
                proto_idx = idx
                break
        if proto_idx == -1:
            continue

        proto = parts[proto_idx].upper()
        # The endpoint is the token following the protocol token.
        endpoint = parts[proto_idx + 1] if proto_idx + 1 < len(parts) else ""
        address, port = _split_endpoint(endpoint)

        # State is typically the trailing "(LISTEN)" token.
        state = ""
        for token in parts[proto_idx + 2 :]:
            m = re.match(r"\(([^)]+)\)", token)
            if m:
                state = m.group(1)
                break

        # PID is the second column in the standard lsof layout.
        pid: int | None = None
        process: str | None = None
        if parts[0].upper() != "COMMAND" and parts[1].isdigit():
            pid = int(parts[1])
            process = parts[0]

        entries.append(_record(proto, address, port, state, pid, process))
    return entries


def kill_command(pid: object, force: bool = False) -> list[str]:
    """Return the platform-correct command (as an argv list) to kill *pid*.

    On Windows this yields ``taskkill`` with ``/PID`` (and ``/F`` when
    *force* is true).  Elsewhere it yields ``kill`` with ``-9`` when forced.

    Raises ``ValueError`` for a non-positive or non-integer pid.
    """
    if isinstance(pid, bool):
        raise ValueError("pid must be a positive integer")
    try:
        pid_int = int(pid)
    except (TypeError, ValueError) as exc:
        raise ValueError("pid must be a positive integer") from exc
    if pid_int <= 0:
        raise ValueError("pid must be a positive integer")

    if os.name == "nt":
        cmd = ["taskkill", "/PID", str(pid_int)]
        if force:
            cmd.append("/F")
        return cmd

    cmd = ["kill"]
    if force:
        cmd.append("-9")
    cmd.append(str(pid_int))
    return cmd


def summarize(entries: list[dict[str, Any]]) -> str:
    """Return a compact human-readable summary of listener *entries*.

    The first line reports totals; subsequent lines list each listener.  An
    empty input produces a single friendly message.
    """
    if not entries:
        return "No listeners found."

    proto_counts: dict[str, int] = {}
    pids: set[int] = set()
    for entry in entries:
        proto = str(entry.get("proto") or entry.get("protocol") or "?").upper()
        proto_counts[proto] = proto_counts.get(proto, 0) + 1
        pid = entry.get("pid")
        if isinstance(pid, int) and pid > 0:
            pids.add(pid)

    breakdown = ", ".join(f"{count} {proto}" for proto, count in sorted(proto_counts.items()))
    lines = [
        f"{len(entries)} listener(s) across {len(pids)} process(es) [{breakdown}]"
    ]

    for entry in entries:
        proto = str(entry.get("proto") or entry.get("protocol") or "?")
        address = entry.get("address") or entry.get("local_address") or "*"
        port = entry.get("port")
        state = entry.get("state") or "-"
        pid = entry.get("pid")
        process = entry.get("process")
        endpoint = f"{address}:{port}" if port is not None else str(address)
        pid_text = f"pid={pid}" if pid is not None else "pid=?"
        proc_text = f"  {process}" if process else ""
        lines.append(f"  {proto:<6} {endpoint:<28} {state:<12} {pid_text}{proc_text}")

    return "\n".join(lines)
