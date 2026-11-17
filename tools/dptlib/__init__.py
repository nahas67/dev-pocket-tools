"""dptlib - a zero-dependency developer productivity toolkit.

This package contains the reusable library logic behind the ``dpt`` command
line tools.  Every module uses only the Python standard library and exposes a
small, well documented public API that is shared with the individual CLI
scripts living next to this package.

Modules
-------
ports       Parse netstat/lsof output and build process kill commands.
jwt         Inspect (never verify) JSON Web Tokens.
jsonfmt     Format, minify, flatten and validate JSON.
envdiff     Parse and diff ``KEY=VALUE`` environment files.
gitbranches Parse and classify local git branches.
dirsize     Compute directory sizes and render aligned tables.
cron        Parse and explain 5-field cron expressions.
passgen     Generate random passwords and estimate their entropy.
httpcode    Look up HTTP status codes.
epoch       Convert between epochs and human readable dates/durations.
"""

from __future__ import annotations

__version__ = "1.0.0"

__all__ = [
    "ports",
    "jwt",
    "jsonfmt",
    "envdiff",
    "gitbranches",
    "dirsize",
    "cron",
    "passgen",
    "httpcode",
    "epoch",
]

# Eagerly import the submodules so ``import dptlib; dptlib.ports`` works as
# well as ``from dptlib import ports``.  All modules are stdlib-only and cheap
# to import, so there is no startup penalty worth avoiding.
from . import (  # noqa: E402,F401
    ports,
    jwt,
    jsonfmt,
    envdiff,
    gitbranches,
    dirsize,
    cron,
    passgen,
    httpcode,
    epoch,
)
