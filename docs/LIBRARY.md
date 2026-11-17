# Library usage

Every tool's logic lives in an importable module under `tools/dptlib/`. The CLI scripts in `tools/` are thin wrappers that parse arguments and print output; the modules contain the behavior. You can reuse that logic directly from your own Python code.

## Importing

Run from the repository root and import the package name `dptlib` (the CLI scripts add `tools/` to `sys.path` for you; your code can do the same):

```python
import sys
sys.path.insert(0, "/path/to/dev-pocket-tools/tools")

from dptlib import ports, jwt, jsonfmt, envdiff, gitbranches
from dptlib import dirsize, cron, passgen, httpcode, epoch
```

`import dptlib` eagerly imports all ten modules; each also works standalone. Importing has no side effects: no file reads, no subprocesses, no network.

Package metadata: `dptlib.__version__` is `"1.0.0"`, and `dptlib.__all__` lists the ten module names.

---

## `dptlib.ports` — parse listener output, build kill commands

Pure parsers for the plain text produced by `netstat` (Windows) and `lsof` (Linux/macOS). No subprocess is launched here.

### `valid_port(value) -> bool`
Accepts ints 1–65535 and decimal strings; rejects booleans, floats, zero, out-of-range values, and junk.

### `parse_netstat(text) -> list[dict]`
Parses `netstat -ano` output. Each record has `proto`, `protocol`, `address`, `local_address`, `port`, `state`, `pid`, and `process`.

### `parse_lsof(text) -> list[dict]`
Parses `lsof -nP` output into the same record shape. Handles both the full `COMMAND PID USER ... NAME` layout and bare endpoint lines.

### `kill_command(pid, force=False) -> list[str]`
Returns an argv list for the platform: `["kill", "4242"]` (or `["kill", "-9", "4242"]` when forced) on Unix; `["taskkill", "/PID", "4242"]` (plus `"/F"`) on Windows. Raises `ValueError` for invalid PIDs.

### `summarize(entries) -> str`
Renders a compact human-readable summary of listener records.

```python
from dptlib import ports

entries = ports.parse_lsof("python 1234 user 3u IPv4 ... TCP *:8000 (LISTEN)\n")
print(ports.summarize(entries))
print(ports.kill_command(1234, force=True))   # ['kill', '-9', '1234'] on Unix
```

---

## `dptlib.jwt` — decode (never verify) JSON Web Tokens

### `b64url_decode(seg) -> bytes`
Base64URL-decodes a segment, restoring missing padding. Accepts `str` or `bytes`. Raises `ValueError` on invalid input.

### `decode(token) -> dict`
Splits a compact JWT and returns a dict with exactly four keys:

- `header` — parsed JOSE header dict, or `None` if unparsable
- `payload` — parsed claims dict, or `None` if unparsable
- `signature` — raw decoded signature bytes, or `b""`
- `is_expired` — result of `is_expired(payload)`, or `None`

Raises `ValueError` only for a non-string token or one with fewer than two dot-separated segments; malformed segments degrade to `None`/`b""`.

### `is_expired(payload, now=None) -> bool | None`
Checks the `exp` claim against `now` (an epoch number, a `datetime`, or the current time by default). Returns `None` when no numeric `exp` exists. `now >= exp` counts as expired.

### `redact(token) -> str`
Returns `first6...last6` for safe display; very short tokens become `"***"`.

```python
from dptlib import jwt

result = jwt.decode("header.payload.signature")
print(result["header"]["alg"])
print(jwt.is_expired(result["payload"], now=1_700_000_000))
```

> This module deliberately performs **no signature verification and no claim validation** beyond reading `exp`. Never use it for authorization decisions.

---

## `dptlib.jsonfmt` — JSON text helpers

All functions operate on JSON *text* and use the standard library.

### `is_json(text) -> bool`
True when `json.loads` accepts the text (objects, arrays, strings, numbers, booleans, null all count).

### `format_json(text, indent=2, sort_keys=False) -> str`
Pretty-print. Raises `ValueError` for invalid JSON. The returned string has no trailing newline.

### `minify(text) -> str`
Compact JSON with no insignificant whitespace.

### `flatten(obj, prefix="") -> dict`
Turns a nested dict/list into dotted paths: `{"a": {"b": [1, 2]}}` becomes `{"a.b.0": 1, "a.b.1": 2}`. Empty containers are kept as leaf values.

```python
from dptlib import jsonfmt

print(jsonfmt.format_json('{"b":2,"a":1}', sort_keys=True))
print(jsonfmt.minify('{\n "a": 1\n}'))          # {"a":1}
print(jsonfmt.flatten({"a": {"b": [1, 2]}}))    # {'a.b.0': 1, 'a.b.1': 2}
```

---

## `dptlib.envdiff` — dotenv parsing and comparison

### `parse_env(text) -> dict[str, str]`
Parses `KEY=VALUE` lines. Blank lines and `#` comments are ignored, an optional `export ` prefix is stripped, the first `=` splits key from value, and one matching pair of surrounding quotes is removed. Empty values are preserved. Duplicate keys keep the last value.

### `diff_env(a, b) -> dict`
Returns exactly four dicts:

- `added` — `{key: b[key]}` for keys only in `b`
- `removed` — `{key: a[key]}` for keys only in `a`
- `changed` — `{key: {"old": a[key], "new": b[key]}}` for differing values
- `same` — `{key: a[key]}` for equal keys

### `mask_value(v) -> str`
Masks a value for display: keeps first and last characters, replaces the middle with `*`; values of length ≤ 2 are fully masked.

```python
from dptlib import envdiff

a = envdiff.parse_env("PORT=8080\nDEBUG=true\n")
b = envdiff.parse_env("PORT=9090\nDEBUG=true\nNEW=1\n")
diff = envdiff.diff_env(a, b)
print(diff["added"])                  # {'NEW': '1'}
print(diff["changed"]["PORT"])        # {'old': '8080', 'new': '9090'}
print(envdiff.mask_value("secret"))   # 's****t'
```

---

## `dptlib.gitbranches` — branch parsing and safe cleanup

These helpers never run git; they parse `git branch` output and build commands for the caller.

### `parse_branch_lines(text) -> list[dict]`
Recognises the `*` current-branch marker and an optional short hash column. Each record has `name`, `current`, `hash`, `protected`, and `raw`.

### `classify(branch, current, protected) -> str`
Returns `"current"`, `"protected"`, or `"deletable"`. `protected` accepts exact names or `fnmatch` globs such as `"release/*"`; `None` uses `DEFAULT_PROTECTED`.

### `DEFAULT_PROTECTED`
Tuple: `("main", "master", "develop", "development")`.

### `build_delete_commands(branches, dry_run=True) -> list[str]`
Builds `git branch -d <name>` commands. `dry_run=True` appends a `  # dry-run` comment so the output is safe to paste. The current branch and protected branches are always excluded.

```python
from dptlib import gitbranches

branches = gitbranches.parse_branch_lines("* main\n  feature/login\n  release/1.2\n")
for b in branches:
    b["protected"] = ["main", "release/*"]
print(gitbranches.build_delete_commands(branches, dry_run=True))
# ['git branch -d feature/login  # dry-run']
```

---

## `dptlib.dirsize` — size collection and table rendering

### `human_size(n) -> str`
Formats bytes with base-1024 units: `0 -> "0 B"`, `1024 -> "1.0 KB"`, `1536 -> "1.5 KB"`, `1024**2 -> "1.0 MB"`.

### `collect_sizes(paths) -> list[tuple[str, int, int]]`
For each path returns `(path_string, size_in_bytes, file_count)` in input order. Directories are walked recursively; an unreadable or missing path yields `(path, 0, 0)` rather than raising. Directory symlinks are not followed.

### `format_table(rows) -> str`
Renders rows as an aligned table with `PATH`, `SIZE`, `FILES` columns and a separator line. Integer sizes are humanized; preformatted strings are used verbatim. Empty input returns `"No paths to report."`.

```python
from dptlib import dirsize

rows = dirsize.collect_sizes(["src", "tests", "README.md"])
print(dirsize.format_table(rows))
print(dirsize.human_size(2048))   # "2.0 KB"
```

---

## `dptlib.cron` — five-field cron parsing and explanation

### `parse_field(field, lo, hi) -> list[int]`
Expands one field into sorted integers. Supports `*`, single numbers, comma lists, ranges (`a-b`), and steps (`*/n`, `a-b/n`, `a/n`). Raises `ValueError` for empty fields, bad tokens, descending ranges, zero/negative steps, or out-of-range values.

### `describe(expr) -> dict`
Parses a five-field expression and returns `expression` plus sorted integer lists under `minute`, `hour`, `day_of_month`, `month`, and `day_of_week`. Month and weekday names (`JAN`, `MON`) are accepted.

### `explain(expr) -> str`
Returns a multi-line explanation beginning `Cron: <expr>`, with one line per field. Invalid expressions raise `ValueError`.

```python
from dptlib import cron

print(cron.explain("*/15 9-17 * * 1-5"))
print(cron.describe("0 9 * * 1-5")["hour"])   # [9]
```

The module explains expressions; it does not compute future run times.

---

## `dptlib.passgen` — secure password generation and entropy

### `generate(length=16, use_upper=True, use_lower=True, use_digits=True, use_symbols=True, exclude_ambiguous=True) -> str`
Generates a password of exactly `length` characters using `secrets.choice`. When the length allows, at least one character from every enabled class is included; the result is shuffled. Raises `ValueError` for non-positive lengths or when no class is enabled.

Constants: `UPPER`, `LOWER`, `DIGITS`, `SYMBOLS` (from `string.punctuation`), `AMBIGUOUS` (characters like `0`, `O`, `1`, `l` that are easy to confuse). Ambiguous characters are excluded by default.

### `estimate_entropy(length, pool_size) -> float`
Returns `length * log2(pool_size)` bits; non-positive lengths or pool sizes ≤ 1 yield `0.0`.

```python
from dptlib import passgen

password = passgen.generate(20)
bits = passgen.estimate_entropy(20, 94)
print(password, f"{bits:.1f} bits")
```

---

## `dptlib.httpcode` — HTTP status lookup

### `lookup(code) -> dict | None`
Accepts an int or decimal string. Returns `{"code": int, "title": str, "category": str, "description": str}` or `None` for unknown codes. `category` is one of `Informational`, `Success`, `Redirection`, `Client Error`, `Server Error` (from `CATEGORIES`).

### `all_codes() -> list[int]`
Sorted list of every status code known to the module (the `CATEGORIES` map and internal code table cover standard HTTP codes).

```python
from dptlib import httpcode

print(httpcode.lookup(404))
# {'code': 404, 'title': 'Not Found', 'category': 'Client Error',
#  'description': 'The requested resource could not be found.'}
print(len(httpcode.all_codes()))
```

---

## `dptlib.epoch` — epoch and duration helpers

Timestamps are interpreted as UTC and rendered as ISO-8601 strings ending in `Z`.

### `to_datetime(ts, unit="s") -> str`
Converts an epoch value (int, float, or numeric string) to an ISO-8601 UTC string. `unit` accepts `s`/`sec`/`seconds`, `ms`/`milliseconds`, `us`/`microseconds`, `ns`/`nanoseconds`. Raises `ValueError` for unknown units, non-numeric input, or out-of-range timestamps.

```python
epoch.to_datetime(0)                          # '1970-01-01T00:00:00Z'
epoch.to_datetime(1700000000000, unit="ms")   # '2023-11-14T22:13:20Z'
```

### `from_datetime(text) -> int`
Parses an ISO-8601 or common datetime string into epoch seconds. Trailing `Z` is accepted; naive timestamps are treated as UTC. Several `%Y-%m-%d ...` formats are tried as fallbacks. Raises `ValueError` when parsing fails.

### `humanize(seconds) -> str`
Renders a duration as compact units: `90061 -> "1d 1h 1m 1s"`, `0 -> "0s"`, negative values prefixed with `-`, sub-second remainders shown in `ms`.

### `now_ms() -> int`
Current epoch time in milliseconds as an integer.

```python
from dptlib import epoch

print(epoch.to_datetime(1700000000))              # 2023-11-14T22:13:20Z
print(epoch.from_datetime("2023-11-14T22:13:20Z")) # 1700000000
print(epoch.humanize(3661))                        # 1h 1m 1s
```

---

## Design notes

- **No side effects on import** and **no network access** anywhere in the package.
- **Exceptions, not exits.** Errors are raised; callers decide how to handle them.
- **Built-in types only.** Return values are `dict`, `list`, `tuple`, `str`, `int`, `float`, or `bytes` — no third-party types to install.
- **Return-shape stability.** These shapes are covered by the unittest suite in `tests/`, so library consumers can rely on them.
