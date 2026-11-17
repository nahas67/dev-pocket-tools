# Command reference

Complete reference for the `dpt` launcher and all ten tools. Invoke a tool through `python bin/dpt <tool> [args]` or directly as `python tools/<tool> [args]` — both run the same script. Every command accepts `-h` / `--help`.

Exit codes: `0` success, `1` runtime error (bad input, unreadable file, unknown code), `2` argparse usage error.

---

## Launcher: `dpt`

```
dpt <tool> [args...]
dpt --help
dpt help
```

Running `dpt` with no arguments, with `--help`/`-h`, or with `help` prints the toolkit help (the command list below). Any other token is treated as a tool name; an unknown name exits `2`. There is no `list` subcommand and no `--version` flag — use `--help`.

---

## `port-kill`

Parse saved `netstat` / `lsof` output, summarize listeners, and build (or run) kill commands. Read-only by default — nothing is killed without `--execute`.

```
port-kill [--input FILE] [--format {auto,netstat,lsof}] [--port N] [--pid N]
          [--force] [--execute] [--yes]
```

| Option | Meaning |
| --- | --- |
| `--input`, `-i FILE` | Read listener text from a file; otherwise read stdin |
| `--format`, `-f` | `auto` (default), `netstat`, or `lsof` |
| `--port N` | Keep only entries for local port `N` |
| `--pid N` | Keep only entries for PID `N` |
| `--force` | Use `kill -9` (Unix) / `/F` (Windows) |
| `--execute` | Actually run the kill commands (default: print only) |
| `--yes` | Skip confirmation when using `--execute` |

`auto` detects `lsof` format when a line starts with `COMMAND` or contains ` (LISTEN)`; otherwise it assumes `netstat`.

```console
$ python tools/port-kill --input tests/fixtures/lsof_unix.txt --port 8000
1 listener(s) across 1 process(es) [1 TCP]
  TCP    *:8000                       LISTEN       pid=1234  python

Kill commands:
  kill 1234
```

Each listener record exposes `proto`, `protocol`, `address`, `local_address`, `port`, `state`, `pid`, and `process`. Duplicate PIDs are de-duplicated before building commands.

See the [port-kill cheatsheet](cheatsheets/port-kill.md).

---

## `jwt-decode`

Decode a JWT's header and payload for debugging. Never verifies the signature.

```
jwt-decode [token] [--redact] [--raw]
```

| Option | Meaning |
| --- | --- |
| `token` | JWT string; if omitted, read from stdin |
| `--redact` | Print only a non-reversible `first6...last6` preview |
| `--raw` | Print one JSON object with `header`, `payload`, `signature` (hex), `is_expired` |

Malformed segments degrade to `null` rather than failing the whole decode. A token with fewer than two dot-separated segments is an error (`1`). `is_expired` is `null` when there is no numeric `exp` claim.

```console
$ python tools/jwt-decode eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjk5OTk5OTk5OTl9.ZGV2LXNpZ25hdHVyZQ
HEADER:
{
  "alg": "HS256",
  "typ": "JWT"
}

PAYLOAD:
{
  "exp": 9999999999,
  "iat": 1516239022,
  "name": "John Doe",
  "sub": "1234567890"
}

SIGNATURE (hex): 6465762d7369676e6174757265
EXPIRY: valid

Note: signature was NOT verified.
```

See the [jwt-decode cheatsheet](cheatsheets/jwt-decode.md).

---

## `json-fmt`

Format, minify, validate, or flatten JSON text from a file or stdin.

```
json-fmt [FILE] [--indent N] [--sort-keys] [--minify] [--flatten] [--check]
```

| Option | Meaning |
| --- | --- |
| `FILE` | Path to a JSON file; omitted means stdin |
| `--indent N` | Indentation width (default `2`) |
| `--sort-keys` | Sort object keys |
| `--minify` | Compact output with no whitespace |
| `--flatten` | Emit `dotted.path<TAB>JSON-value` lines |
| `--check` | Only validate; print `Valid JSON` / `Invalid JSON` |

```console
$ echo '{"b":2,"a":1}' | python tools/json-fmt --sort-keys
{
  "a": 1,
  "b": 2
}

$ echo '{"a":{"b":[1,2]}}' | python tools/json-fmt --flatten
a.b.0	1
a.b.1	2

$ echo '{bad' | python tools/json-fmt --check
Invalid JSON
```

Empty input exits `1` with `No JSON supplied.`. Invalid JSON exits `1` with the parser message. See the [json-fmt cheatsheet](cheatsheets/json-fmt.md).

---

## `env-diff`

Compare two dotenv (`KEY=VALUE`) files. Use `-` as a filename to read from stdin.

```
env-diff <A> <B> [--mask] [--show-same]
```

| Option | Meaning |
| --- | --- |
| `--mask` | Mask changed/added/removed values before printing |
| `--show-same` | List unchanged keys too (hidden by default) |

Parsing ignores blank lines and `#` comments, strips an optional `export ` prefix, splits on the first `=`, and removes one matching pair of surrounding quotes. Duplicate keys keep the last value.

```console
$ python tools/env-diff tests/fixtures/sample.env tests/fixtures/sample2.env
ADDED (1):
  NEW_FLAG='enabled'
REMOVED (1):
  EMPTY_VALUE=''
CHANGED (1):
  DEBUG: 'true' -> 'false'
SAME (3): (hidden; use --show-same)
```

Values are shown by default; use `--mask` for secrets. See the [env-diff cheatsheet](cheatsheets/env-diff.md).

---

## `git-clean-branches`

Classify local branches from `git branch` output and print safe `git branch -d` commands. Dry-run by default.

```
git-clean-branches [--input FILE] [--protected A,B,GLOB] [--execute] [--yes]
```

| Option | Meaning |
| --- | --- |
| `--input`, `-i FILE` | File containing `git branch` output (default: run `git branch --no-color`) |
| `--protected LIST` | Comma-separated protected names/globs (default `main,master,develop,development`) |
| `--execute` | Actually delete branches (default: print commands only) |
| `--yes` | Skip the confirmation prompt with `--execute` |

With no `--input` and a non-interactive stdin, piped text is used. The current branch, protected names, and glob matches are never deleted.

```console
$ python tools/git-clean-branches --input tests/fixtures/branches.txt
BRANCH CLASSIFICATION:
  current    main
  protected  develop
  deletable  feature/auth
  deletable  feature/payments
  deletable  bugfix/issue-42

DELETE COMMANDS:
  git branch -d feature/auth  # dry-run
  git branch -d feature/payments  # dry-run
  git branch -d bugfix/issue-42  # dry-run
```

See the [git-clean-branches cheatsheet](cheatsheets/git-clean-branches.md).

---

## `dir-size`

Compute recursive sizes of files/directories and print an aligned table or JSON.

```
dir-size [PATH ...] [--json]
```

| Option | Meaning |
| --- | --- |
| `PATH ...` | Paths to measure (default: `.`) |
| `--json` | Emit `[{"path", "bytes", "files"}, ...]` instead of a table |

The table has `PATH`, `SIZE`, `FILES` columns; sizes use base-1024 units (`B`, `KB`, `MB`, ...). Missing or unreadable paths report zero rather than failing.

```console
$ python tools/dir-size tests/fixtures
PATH              SIZE  FILES
--------------  ------  -----
tests\fixtures  1.3 KB      8
```

See the [dir-size cheatsheet](cheatsheets/dir-size.md).

---

## `cron-explain`

Explain a five-field cron expression field by field.

```
cron-explain "<minute hour dom month dow>" [--json]
```

With `--json`, prints the expanded integer lists from `dptlib.cron.describe` instead of the prose explanation.

Supports `*`, single numbers, comma lists, ranges (`a-b`), steps (`*/n`, `a-b/n`, `a/n`), and month/weekday names (`JAN`–`DEC`, `SUN`–`SAT`). Day-of-week accepts `0`–`7` (both `0` and `7` mean Sunday). Invalid expressions exit `1`.

```console
$ python tools/cron-explain "*/15 9-17 * * 1-5"
Cron: */15 9-17 * * 1-5
  minute         at minutes 0, 15, 30, 45
  hour           at hours 9, 10, 11, 12, 13, 14, 15, 16, 17
  day_of_month   every day of the month
  month          every month
  day_of_week    at day of the weeks 1, 2, 3, 4, 5
```

The tool explains expressions; computing future run times is out of scope. See the [cron-explain cheatsheet](cheatsheets/cron-explain.md).

---

## `pass-gen`

Generate secure random passwords with `secrets`. Passwords go to stdout; a pool/entropy line goes to stderr.

```
pass-gen [--length N] [--count N] [--no-symbols] [--no-digits] [--no-upper]
         [--no-lower] [--allow-ambiguous]
```

| Option | Meaning |
| --- | --- |
| `--length`, `-n N` | Password length (default `16`) |
| `--count`, `-c N` | How many passwords to generate (default `1`; must be ≥ 1) |
| `--no-symbols` / `--no-digits` | Exclude punctuation / digits |
| `--no-upper` / `--no-lower` | Exclude uppercase / lowercase letters |
| `--allow-ambiguous` | Keep easily-confused characters (`0`, `O`, `1`, `l`, ...); default pool is 71 chars, 94 with this flag |

At least one character class must remain. One character from each enabled class is guaranteed when length allows, then the rest are drawn from the full pool and shuffled. Entropy is always printed to stderr as `# pool=N  entropy=X.X bits`.

```console
$ python tools/pass-gen --length 16
# pool=71  entropy=98.4 bits
@MVoeAc8esFJZqK=

$ python tools/pass-gen --length 12 --count 2 --no-symbols
# pool=57  entropy=70.0 bits
uTVRmwZZDp69
MJm6jRdRzAHu
```

See the [pass-gen cheatsheet](cheatsheets/pass-gen.md).

---

## `http-code`

Look up one or more HTTP status codes, or list the full table.

```
http-code <code> [code ...]
http-code --list
```

| Form | Meaning |
| --- | --- |
| `<code> [code ...]` | Print each code's title, category, and description |
| `--list` | Print `code  title  category` for every known code |
| *(no arguments)* | Same as `--list` |

Categories are `Informational`, `Success`, `Redirection`, `Client Error`, `Server Error`. Unknown codes are reported on stderr and exit `1`.

```console
$ python tools/http-code 404 429
404 Not Found [Client Error]
  The requested resource could not be found.
429 Too Many Requests [Client Error]
  The client has sent too many requests in a given amount of time.
```

See the [http-code cheatsheet](cheatsheets/http-code.md).

---

## `epoch-convert`

Convert Unix timestamps to ISO-8601 UTC dates, parse dates to seconds, humanize durations, or read the current time.

```
epoch-convert <value> [--unit s|ms|us|ns]
epoch-convert --from-datetime <date>
epoch-convert --humanize <seconds>
epoch-convert --now-ms
```

| Option | Meaning |
| --- | --- |
| `<value>` | Numeric timestamp (default mode), or a date string with `--from-datetime` |
| `--unit UNIT` | Unit for numeric input: `s` (default), `ms`, `us`, `ns` (long forms accepted by the library) |
| `--from-datetime` | Parse `<value>` as a date string and print epoch seconds |
| `--humanize` | Treat `<value>` as seconds and print `1d 2h 3m 4s` style output |
| `--now-ms` | Print the current epoch time in milliseconds (no value needed) |

The mode flags are mutually exclusive. Numeric input renders as `YYYY-MM-DDTHH:MM:SSZ`; date strings are treated as UTC when naive.

```console
$ python tools/epoch-convert 1700000000
2023-11-14T22:13:20Z

$ python tools/epoch-convert 1700000000000 --unit ms
2023-11-14T22:13:20Z

$ python tools/epoch-convert --from-datetime "2023-11-14T22:13:20Z"
1700000000

$ python tools/epoch-convert --humanize 90061
1d 1h 1m 1s
```

See the [epoch-convert cheatsheet](cheatsheets/epoch-convert.md).
