#!/usr/bin/env bash
# git-week.sh - Summarize recent Git activity by author and day.
# Usage: git-week.sh [--days N] [--branch REF] [--path PATH]
set -euo pipefail

days=7
branch="HEAD"
path="."

usage() {
    printf 'Usage: %s [--days N] [--branch REF] [--path PATH]\n' "${0##*/}"
    printf '  --days N      look back N days (default: 7)\n'
    printf '  --branch REF  revision to inspect (default: HEAD)\n'
    printf '  --path PATH   restrict to a path (default: .)\n'
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --days)
            [ "$#" -ge 2 ] || { printf 'error: --days needs a value\n' >&2; exit 2; }
            days="$2"
            shift 2
            ;;
        --branch)
            [ "$#" -ge 2 ] || { printf 'error: --branch needs a value\n' >&2; exit 2; }
            branch="$2"
            shift 2
            ;;
        --path)
            [ "$#" -ge 2 ] || { printf 'error: --path needs a value\n' >&2; exit 2; }
            path="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            printf 'error: unknown argument: %s\n' "$1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

case "$days" in
    ''|*[!0-9]*) printf 'error: --days must be a non-negative integer\n' >&2; exit 2 ;;
esac

git rev-parse --git-dir >/dev/null 2>&1 || {
    printf 'error: not inside a Git repository\n' >&2
    exit 1
}

since="$(date -u -d "${days} days ago" +%Y-%m-%d 2>/dev/null || true)"
if [ -z "$since" ]; then
    # BSD/macOS date fallback.
    since="$(date -u -v-${days}d +%Y-%m-%d)"
fi

printf 'Commits since %s on %s (path: %s)\n\n' "$since" "$branch" "$path"
git shortlog -sne --since="$since" "$branch" -- "$path"
printf '\nCommits per day:\n'
git log --since="$since" "$branch" -- "$path" --date=short --pretty=format:'%ad' \
    | sort | uniq -c | sort -k2,2
printf '\n'
