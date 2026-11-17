# dir-size cheatsheet

Compute recursive sizes of files/directories and print an aligned table or JSON.

```
python tools/dir-size [PATH ...] [--json]
```

Read-only: it only walks the filesystem and sums file sizes.

## Example session

```console
$ python tools/dir-size tests/fixtures
PATH              SIZE  FILES
--------------  ------  -----
tests\fixtures  1.3 KB      8

$ python tools/dir-size . src tests --json
[
  {
    "path": ".",
    "bytes": 4096,
    "files": 12
  },
  {
    "path": "src",
    "bytes": 8192,
    "files": 5
  }
]
```

## Options

| Option | Meaning |
| --- | --- |
| `PATH ...` | One or more paths to measure (default: `.`) |
| `--json` | Emit JSON objects with `path`, `bytes`, `files` instead of a table |

With no paths, `.` is measured. Each directory is walked recursively; its reported size is the sum of all file sizes beneath it, and `FILES` is the count of files found.

## Size units

Human-readable sizes use base-1024 units with one decimal place:

| Label | Bytes |
| --- | --- |
| `B` | 1 (shown as an integer) |
| `KB` | 1,024 |
| `MB` | 1,048,576 |
| `GB` | 1,073,741,824 |
| `TB` | 1,099,511,627,776 |

Need exact numbers? Use `--json` and read the `bytes` field.

## Typical workflows

```bash
# Inspect several project areas at once
python tools/dir-size .git node_modules dist docs

# Machine-readable report for a script
python tools/dir-size /var/log --json > sizes.json

# Find the largest subtree by piping through the OS sort
python tools/dir-size * | sort -k2 -h
```

To find the largest children of a directory, pass them explicitly (the tool does not enumerate children for you):

```bash
python tools/dir-size ./* 2>/dev/null | sort -k2 -h | tail -10
```

## Equivalent manual commands

```bash
du -sh -- * | sort -rh | head -20        # GNU Linux
du -sh * | sort -rh | head -20           # macOS / BSD
du -sb path/to/dir                       # exact bytes
```

## Gotchas

- Missing or unreadable paths produce a zero-size, zero-file row rather than an error.
- Directory symlinks are not followed, preventing symlink loops.
- Hidden directories (`.git`, `.cache`) are included only if you pass them or `.` (`.` recurses into everything).
- Reported sizes are logical file sizes (like `du --apparent-size`); sparse files may occupy less physical disk.
- On Windows the table shows backslash paths (`tests\fixtures`), as produced by `pathlib`.
- Empty path list cannot occur via the CLI (default `.`), but the library's `collect_sizes([])` returns `[]` and `format_table([])` returns `No paths to report.`
