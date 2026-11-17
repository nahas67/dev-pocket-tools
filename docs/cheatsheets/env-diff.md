# env-diff cheatsheet

Compare two dotenv (`.env`) files by key.

```
python tools/env-diff <A> <B> [--mask] [--show-same]
```

Values are **shown by default**. Use `--mask` before sharing output from files that contain real secrets.

## Example session

Bundled fixtures:

```console
$ python tools/env-diff tests/fixtures/sample.env tests/fixtures/sample2.env
ADDED (1):
  NEW_FLAG='enabled'
REMOVED (1):
  EMPTY_VALUE=''
CHANGED (1):
  DEBUG: 'true' -> 'false'
SAME (3): (hidden; use --show-same)

$ python tools/env-diff tests/fixtures/sample.env tests/fixtures/sample2.env --show-same
ADDED (1):
  NEW_FLAG='enabled'
REMOVED (1):
  EMPTY_VALUE=''
CHANGED (1):
  DEBUG: 'true' -> 'false'
SAME (3):
  API_KEY='supersecretkey123'
  APP_NAME='nios'
  PORT='8080'
```

## Options

| Option | Meaning |
| --- | --- |
| `--mask` | Mask values: keep first/last character, replace the middle with `*` |
| `--show-same` | List unchanged keys (otherwise only the count is shown) |

`A` and `B` are file paths; use `-` for stdin. With `--mask`, a value like `supersecretkey123` becomes `s***************3`; values of length ≤ 2 are fully masked.

## What the parser accepts

```dotenv
# comments and blank lines are ignored
APP_NAME=nios
export PORT=8080        # "export " prefix is stripped
QUOTED="hello"          # one matching pair of quotes is removed
URL=a=b=c               # only the first "=" splits key/value
EMPTY=                  # empty values are preserved
```

Duplicate keys keep the last occurrence. Keys are case-sensitive.

## Typical workflows

### Template vs. local config

```console
$ python tools/env-diff .env.example .env.local --mask
```

Investigate every ADDED/REMOVED line: it is configuration drift between the documented template and a real deployment.

### Verify all expected keys are present

```console
$ python tools/env-diff .env.example .env.production --show-same --mask
```

A well-formed production config should show no REMOVED entries relative to the template.

### Diff from a pipe

```bash
git show HEAD:.env.example | python tools/env-diff - .env.local --mask
```

### Confirm a rotation touched only one key

```console
$ python tools/env-diff .env.before .env.after --mask
```

## Report legend

| Section | Meaning |
| --- | --- |
| `ADDED (n)` | Keys present only in file B |
| `REMOVED (n)` | Keys present only in file A |
| `CHANGED (n)` | Keys in both files whose values differ (`old -> new`) |
| `SAME (n)` | Keys in both files with equal values (hidden unless `--show-same`) |

## Gotchas

- Values print as Python repr with single quotes (`'value'`).
- Inline `#` comments after a value are part of the value; put comments on their own lines.
- The comparison is textual: `true` and `1` count as changed.
- `--mask` is display-only; it does not alter the parsed values used for comparison.
