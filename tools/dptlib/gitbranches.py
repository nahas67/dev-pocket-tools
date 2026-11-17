"""Local git branch parsing and safe-cleanup helpers.

These helpers never run git themselves; they parse ``git branch`` output and
produce classification labels plus the exact commands a caller may choose to
execute.  Deletion commands use the safe ``git branch -d`` form by default.
"""

from __future__ import annotations

from fnmatch import fnmatch
from typing import Any, Iterable

# Branches that should never be auto-deleted unless explicitly overridden.
DEFAULT_PROTECTED: tuple[str, ...] = (
    "main",
    "master",
    "develop",
    "development",
)


def parse_branch_lines(text: str) -> list[dict[str, Any]]:
    """Parse plain ``git branch`` output into branch records.

    Recognises the current-branch marker (``* ``), optional short commit hash
    columns and plain names.  Header-like or empty lines are ignored.

    Each record contains:

    ``name``        branch name without the ``*`` marker.
    ``current``     ``True`` for the checked-out branch.
    ``hash``        short commit hash when one was present, else ``None``.
    ``protected``   ``None`` (callers may set their own protected list).
    ``raw``         the original stripped line.
    """
    branches: list[dict[str, Any]] = []
    if not text:
        return branches

    for line in text.splitlines():
        raw = line.rstrip()
        if not raw.strip():
            continue
        stripped = raw.lstrip()
        current = stripped.startswith("* ")
        if current:
            stripped = stripped[2:].lstrip()

        parts = stripped.split()
        if not parts:
            continue

        # Recognise a short/full commit hash by shape (hex, 4-40 chars) so we
        # accept both "name hash" and "hash name" column orders.
        def is_hash(token: str) -> bool:
            return 4 <= len(token) <= 40 and all(c in "0123456789abcdefABCDEF" for c in token)

        hash_tokens = [tok for tok in parts if is_hash(tok)]
        commit: str | None = None
        name_tokens = parts
        if hash_tokens and len(parts) > 1:
            commit = hash_tokens[0]
            name_tokens = [tok for tok in parts if tok != commit]

        name = name_tokens[0] if name_tokens else parts[0]

        branches.append(
            {
                "name": name,
                "current": current,
                "hash": commit,
                "protected": None,
                "raw": raw.strip(),
            }
        )
    return branches


def _branch_name(branch: Any) -> str:
    """Extract a branch name from a string or a ``parse_branch_lines`` dict."""
    if isinstance(branch, dict):
        return str(branch.get("name", "")).strip()
    return str(branch).strip()


def classify(branch: Any, current: str, protected: Iterable[str] | None) -> str:
    """Classify *branch* as ``"current"``, ``"protected"`` or ``"deletable"``.

    ``current`` is the name of the checked-out branch and takes precedence.
    ``protected`` is an iterable of exact names or ``fnmatch``-style glob
    patterns (e.g. ``"release/*"``).  ``None`` falls back to
    :data:`DEFAULT_PROTECTED`.
    """
    name = _branch_name(branch)
    if name and name == current:
        return "current"

    patterns = list(protected) if protected is not None else list(DEFAULT_PROTECTED)
    for pattern in patterns:
        pattern = str(pattern)
        if name == pattern or fnmatch(name, pattern):
            return "protected"
    return "deletable"


def build_delete_commands(
    branches: Iterable[Any], dry_run: bool = True
) -> list[str]:
    """Build ``git branch -d`` commands for all deletable branches.

    *branches* is an iterable of branch names or of records returned by
    :func:`parse_branch_lines`.  For records, the ``current`` and ``protected``
    fields are honoured (falling back to :data:`DEFAULT_PROTECTED`); the
    checked-out branch and protected branches are never queued for deletion.

    When *dry_run* is ``True`` (the default) each command carries a trailing
    ``# dry-run`` comment so it can be reviewed but is harmless to paste.
    """
    commands: list[str] = []
    for branch in branches:
        name = _branch_name(branch)
        if not name:
            continue

        current_name = ""
        protected: Iterable[str] | None = None
        if isinstance(branch, dict):
            if branch.get("current"):
                current_name = name
            if branch.get("protected") is not None:
                protected = branch["protected"]

        if classify(name, current_name, protected) != "deletable":
            continue

        command = f"git branch -d {name}"
        if dry_run:
            command += "  # dry-run"
        commands.append(command)
    return commands
