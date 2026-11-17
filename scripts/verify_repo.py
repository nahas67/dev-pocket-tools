#!/usr/bin/env python3
"""Verify commit count, author dates, non-empty commits, and test health."""

from __future__ import annotations

import datetime as dt
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True)


def empty_commits() -> list[str]:
    """A commit is empty when its tree equals its first parent's tree.

    Parses `git log --numstat` once instead of spawning thousands of commands.
    """
    res = run(["git", "log", "--reverse", "--format=@@COMMIT@@%H", "--numstat"])
    empties: list[str] = []
    current: str | None = None
    has_changes = False
    for line in res.stdout.splitlines():
        if line.startswith("@@COMMIT@@"):
            if current is not None and not has_changes:
                empties.append(current)
            current = line[len("@@COMMIT@@") :]
            has_changes = False
        elif line.strip() and "\t" in line:
            has_changes = True
    if current is not None and not has_changes:
        empties.append(current)
    return empties


def main() -> int:
    ok = True
    total = run(["git", "rev-list", "--count", "HEAD"]).stdout.strip()
    print(f"Total commits: {total}")
    if not total.isdigit() or int(total) < 2050:
        ok = False
        print("FAIL: expected at least 2050 commits")

    dates = run(["git", "log", "--format=%aI"]).stdout.split()
    today = dt.date.today().isoformat()
    bad = [d for d in dates if not d.startswith(today)]
    print(f"Commits dated {today}: {len(dates) - len(bad)}/{len(dates)}")
    if bad:
        ok = False
        print(f"FAIL: {len(bad)} commits have a different date (e.g. {bad[:3]})")

    empties = empty_commits()
    print(f"Empty commits: {len(empties)}")
    if empties:
        ok = False
        print(f"FAIL: first empty commit: {empties[0]}")

    tests = run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
    print(f"Tests: returncode={tests.returncode}")
    tail = "\n".join(tests.stderr.strip().splitlines()[-12:])
    if tail:
        print(tail)
    if tests.returncode != 0:
        ok = False

    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
