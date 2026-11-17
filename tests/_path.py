"""Shared test bootstrap: path wiring and fixture loading.

Importing this module inserts ``<repo>/tools`` at the front of ``sys.path`` so
that the sibling ``dptlib`` package (``tools/dptlib``) is importable as
``from dptlib import ...``.  It also exposes helpers for reading the sample
data stored under ``tests/fixtures``.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(_HERE)
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
FIXTURES_DIR = os.path.join(_HERE, "fixtures")

if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)


def fixture_path(name):
    """Return the absolute path to a named fixture file."""
    return os.path.join(FIXTURES_DIR, name)


def fixture(name, strip=False):
    """Read and return the text of a named fixture file (UTF-8).

    When *strip* is true trailing whitespace/newlines are removed -- handy for
    fixtures whose content is a single token (JWT, cron line, ...).
    """
    with open(fixture_path(name), "r", encoding="utf-8") as handle:
        text = handle.read()
    return text.strip() if strip else text
