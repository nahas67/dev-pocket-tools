#!/usr/bin/env python3
"""Push the local `main` history to `origin main` in bounded batches.

GitHub can time out a single push carrying thousands of commits. This script
pushes an explicit refspec per batch (oldest commit first), so each push
advances the remote branch by at most BATCH commits. A short deliberate pacing
delay between batches keeps the push rate gentle on GitHub's side.

Usage:
    python scripts/push_batches.py --url https://github.com/<user>/dev-pocket-tools.git
    python scripts/push_batches.py --batch 400 --delay 3 --dry-run
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def configure_origin(url: str) -> bool:
    existing = git(["remote", "get-url", "origin"])
    if existing.returncode == 0:
        current = existing.stdout.strip()
        if current == url:
            print(f"origin already points to {url}")
            return True
        print(f"Replacing existing origin {current} -> {url}")
        seturl = git(["remote", "set-url", "origin", url])
    else:
        print(f"Adding origin {url}")
        seturl = git(["remote", "add", "origin", url])
    if seturl.returncode != 0:
        print(f"Failed to configure origin: {seturl.stderr.strip()}", file=sys.stderr)
        return False
    return True


def commit_shas() -> list[str]:
    res = git(["rev-list", "--reverse", "HEAD"])
    if res.returncode != 0:
        print(f"Cannot enumerate commits: {res.stderr.strip()}", file=sys.stderr)
        return []
    return res.stdout.split()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", help="GitHub repository URL for origin (prompted if omitted)")
    ap.add_argument("--batch", type=int, default=400)
    ap.add_argument("--delay", type=float, default=3.0,
                    help="pacing delay in seconds between batches (rate-limit courtesy)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    shas = commit_shas()
    if not shas:
        return 1
    print(f"Local commits: {len(shas)}")

    if args.dry_run:
        for i in range(0, len(shas), args.batch):
            part = shas[i : i + args.batch]
            print(f"batch {i // args.batch + 1}: {len(part)} commits -> {part[-1][:12]}")
        return 0

    url = args.url
    if not url:
        existing = git(["remote", "get-url", "origin"])
        if existing.returncode == 0 and existing.stdout.strip():
            url = existing.stdout.strip()
            print(f"Using existing origin: {url}")
        else:
            try:
                url = input("New GitHub repository URL for origin: ").strip()
            except EOFError:
                url = ""
            if not url:
                print("A repository URL is required.", file=sys.stderr)
                return 1

    if not configure_origin(url):
        return 1

    batches = [shas[i : i + args.batch] for i in range(0, len(shas), args.batch)]
    print(f"Pushing {len(batches)} batch(es) of up to {args.batch} commits (delay {args.delay}s).")

    for n, part in enumerate(batches, 1):
        target = part[-1]
        print(f"[{n}/{len(batches)}] pushing {len(part)} commits -> {target[:12]}", flush=True)
        res = git(["push", "origin", f"{target}:refs/heads/main"])
        if res.returncode != 0:
            print(f"Push failed: {res.stderr.strip()}", file=sys.stderr)
            return 1
        if n < len(batches) and args.delay > 0:
            # Deliberate rate-limit pacing between batches (not a wait-for-work sleep).
            time.sleep(args.delay)

    print("All batches pushed. Verifying remote HEAD...")
    local = git(["rev-parse", "HEAD"]).stdout.strip()
    lsremote = subprocess.run(
        ["git", "ls-remote", "origin", "refs/heads/main"],
        cwd=ROOT, capture_output=True, text=True,
    )
    remote = lsremote.stdout.split()[0] if lsremote.stdout.strip() else ""
    print(f"local HEAD : {local}")
    print(f"remote main: {remote}")
    return 0 if remote == local else 1


if __name__ == "__main__":
    raise SystemExit(main())
