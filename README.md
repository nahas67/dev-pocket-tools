# dev-pocket-tools

A genuinely useful, zero-dependency command-line toolkit for developers. Ten small, focused tools for the tasks you reach for every day — inspecting a JWT, finding what is holding a port, explaining a cron expression, diffing two `.env` files — bundled behind one launcher and written in pure Python standard library. No `pip install`, no virtualenv, no config files, no telemetry. Just Python 3.8+ and a terminal.

> **Zero dependencies.** Every tool runs on the Python standard library alone. Nothing is downloaded, nothing phones home.

---

## Features

- **One launcher, ten tools.** Run everything through `bin/dpt`, or call a tool script directly.
- **No installation step.** Clone the repo and run. No packages, no build, no network access required.
- **Stdlib only.** `argparse`, `json`, `base64`, `secrets`, `datetime`, `subprocess`, `pathlib` — batteries included.
- **Script-friendly.** Clean stdout, meaningful exit codes, and `--json` output where it helps.
- **Safe by default.** Port kills and branch deletions are read-only unless `--execute` is passed.
- **Library-ready.** Each tool's logic lives in an importable module under `tools/dptlib/`.

| Tool | What it does |
| --- | --- |
| [`port-kill`](#port-kill) | Parse `netstat`/`lsof` output and build (or run) process kill commands |
| [`jwt-decode`](#jwt-decode) | Decode a JWT header and payload without verifying the signature |
| [`json-fmt`](#json-fmt) | Pretty-print, minify, validate, and flatten JSON (jq-free) |
| [`env-diff`](#env-diff) | Compare two `.env` files: added, removed, changed, same |
| [`git-clean-branches`](#git-clean-branches) | Classify local branches and build safe delete commands |
| [`dir-size`](#dir-size) | Compute file/directory sizes and print an aligned table |
| [`cron-explain`](#cron-explain) | Explain a five-field cron expression field by field |
| [`pass-gen`](#pass-gen) | Generate secure random passwords with entropy estimates |
| [`http-code`](#http-code) | Look up HTTP status codes |
| [`epoch-convert`](#epoch-convert) | Convert between Unix timestamps and ISO-8601 dates |

---

## Quickstart

Requires **Python 3.8 or newer** — nothing else.

```console
$ git clone https://github.com/nahas67/dev-pocket-tools.git
$ cd dev-pocket-tools

# List everything available
$ python bin/dpt --help
dpt - developer productivity toolkit

Usage:
  python bin/dpt <command> [args...]
  python bin/dpt <command> --help     show help for a command

Commands:
  port-kill            Parse netstat/lsof output and build process kill commands
  jwt-decode           Decode a JWT header/payload (never verifies signature)
  json-fmt             Pretty-print, minify, validate or flatten JSON
  env-diff             Diff two dotenv-style environment files
  git-clean-branches   Classify local git branches and build safe delete commands
  dir-size             Report recursive file/directory sizes
  cron-explain         Explain a five-field cron expression in plain English
  pass-gen             Generate cryptographically secure random passwords
  http-code            Look up HTTP status codes, or list them all
  epoch-convert        Convert epoch timestamps, datetimes and durations

Run `python bin/dpt --help` or `python bin/dpt help` to see this message.
```

Each tool has its own `--help`:

```console
$ python tools/jwt-decode --help
usage: jwt-decode [-h] [--redact] [--raw] [token]

Decode a JSON Web Token for debugging (no signature verification).
...
```

> **Windows note:** every entry point is a Python script. Invoke them as `python bin/dpt <tool>` or `python tools/<tool>`. On Linux/macOS you may `chmod +x bin/dpt` and run `./dpt` if you prefer.

---

## Command reference

Examples below use the individual tool scripts, which is what the launcher dispatches to. Every command accepts `-h` / `--help`. Exit codes: `0` success, `1` runtime error (bad input, unreadable file), `2` argparse usage error.

### port-kill

Parse `netstat`/`lsof` listener output, summarize it, and print the exact commands that would kill the matching processes. **It does not kill anything unless `--execute` is passed.**

```
port-kill [--input FILE] [--format {auto,netstat,lsof}] [--port N] [--pid N]
          [--force] [--execute] [--yes]
```

Feed it saved output with `--input` or pipe it on stdin; `--format auto` detects `lsof` vs `netstat`.

```console
$ python tools/port-kill --input tests/fixtures/lsof_unix.txt --port 8000
1 listener(s) across 1 process(es) [1 TCP]
  TCP    *:8000                       LISTEN       pid=1234  python

Kill commands:
  kill 1234

$ python tools/port-kill --input tests/fixtures/netstat_windows.txt --force
4 listener(s) across 4 process(es) [3 TCP, 1 UDP]
  TCP    0.0.0.0:80                   LISTENING    pid=1234
  TCP    0.0.0.0:443                  LISTENING    pid=5678
  TCP    127.0.0.1:5432               ESTABLISHED  pid=9012
  UDP    0.0.0.0:53                   -            pid=700

Kill commands:
  taskkill /PID 1234 /F
  taskkill /PID 5678 /F
  taskkill /PID 9012 /F
  taskkill /PID 700 /F
```

`--execute` runs the printed commands, prompting for confirmation unless `--yes` is given. `--force` uses `kill -9` on Unix or `/F` on Windows. See the [port-kill cheatsheet](docs/cheatsheets/port-kill.md) for the OS commands that produce the input.

### jwt-decode

Decode the header and payload of a JSON Web Token. **Decoding is not verification** — the signature is never checked.

```
jwt-decode [token] [--redact] [--raw]
```

The token may be an argument or piped on stdin. Output includes the signature in hex and a simple `exp` check.

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

$ python tools/jwt-decode <token> --redact
eyJhbG...dHVyZQ
```

`--raw` prints a single JSON object with `header`, `payload`, `signature` (hex), and `is_expired` keys. See the [jwt-decode cheatsheet](docs/cheatsheets/jwt-decode.md).

### json-fmt

Format, minify, validate, or flatten JSON. Reads a file argument or stdin.

```
json-fmt [FILE] [--indent N] [--sort-keys] [--minify] [--flatten] [--check]
```

```console
$ echo '{"b":2,"a":1}' | python tools/json-fmt
{
  "b": 2,
  "a": 1
}

$ echo '{"b":2,"a":1}' | python tools/json-fmt --sort-keys
{
  "a": 1,
  "b": 2
}

$ echo '{"b":2,"a":1}' | python tools/json-fmt --minify
{"b":2,"a":1}

$ echo '{"a":{"b":[1,2]}}' | python tools/json-fmt --flatten
a.b.0	1
a.b.1	2

$ echo '{"ok":true}' | python tools/json-fmt --check
Valid JSON
```

`--flatten` emits `TAB`-separated dotted-path/value lines. `--check` prints `Valid JSON` or `Invalid JSON` and exits `1` for invalid input. See the [json-fmt cheatsheet](docs/cheatsheets/json-fmt.md).

### env-diff

Compare two dotenv files by key. Pass `-` for stdin. Use `--mask` to hide values and `--show-same` to list unchanged keys.

```
env-diff <A> <B> [--mask] [--show-same]
```

```console
$ python tools/env-diff tests/fixtures/sample.env tests/fixtures/sample2.env
ADDED (1):
  NEW_FLAG='enabled'
REMOVED (1):
  EMPTY_VALUE=''
CHANGED (1):
  DEBUG: 'true' -> 'false'
SAME (3): (hidden; use --show-same)

$ python tools/env-diff tests/fixtures/sample.env tests/fixtures/sample2.env --mask
ADDED (1):
  NEW_FLAG='e*****d'
REMOVED (1):
  EMPTY_VALUE=''
CHANGED (1):
  DEBUG: 't**e' -> 'f***e'
SAME (3): (hidden; use --show-same)
```

Values are **shown by default** — add `--mask` when working with real secrets. Parsing handles `#` comments, optional `export ` prefixes, quotes, and `=` inside values. See the [env-diff cheatsheet](docs/cheatsheets/env-diff.md).

### git-clean-branches

Parse `git branch` output, classify each branch, and print safe `git branch -d` commands. Deletion never happens unless `--execute` is passed.

```
git-clean-branches [--input FILE] [--protected A,B,GLOB] [--execute] [--yes]
```

With no `--input` and an interactive terminal, it runs `git branch --no-color` itself; you can also pipe output in.

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

`--protected` overrides the default `main,master,develop,development` and accepts globs like `release/*`. With `--execute` the commands actually run (confirmation required unless `--yes`). See the [git-clean-branches cheatsheet](docs/cheatsheets/git-clean-branches.md).

### dir-size

Compute recursive sizes of files/directories and print an aligned table.

```
dir-size [PATH ...] [--json]
```

```console
$ python tools/dir-size tests/fixtures
PATH              SIZE  FILES
--------------  ------  -----
tests\fixtures  1.3 KB      8

$ python tools/dir-size tests/fixtures --json
[
  {
    "path": "tests\\fixtures",
    "bytes": 1366,
    "files": 8
  }
]
```

`--json` emits one object per path with `path`, `bytes`, and `files`. Unreadable paths report zero rather than failing. See the [dir-size cheatsheet](docs/cheatsheets/dir-size.md).

### cron-explain

Explain a five-field cron expression field by field.

```
cron-explain "<minute hour dom month dow>" [--json]
```

```console
$ python tools/cron-explain "*/15 9-17 * * 1-5"
Cron: */15 9-17 * * 1-5
  minute         at minutes 0, 15, 30, 45
  hour           at hours 9, 10, 11, 12, 13, 14, 15, 16, 17
  day_of_month   every day of the month
  month          every month
  day_of_week    at day of the weeks 1, 2, 3, 4, 5
```

Supports `*`, comma lists, ranges, steps, and month/weekday names. `--json` prints the expanded field values instead. Invalid expressions exit `1`. See the [cron-explain cheatsheet](docs/cheatsheets/cron-explain.md).

### pass-gen

Generate cryptographically secure random passwords using `secrets`. Entropy and pool size are reported on stderr; passwords go to stdout.

```
pass-gen [--length N] [--count N] [--no-symbols] [--no-digits] [--no-upper]
         [--no-lower] [--allow-ambiguous]
```

```console
$ python tools/pass-gen --length 16
# pool=71  entropy=98.4 bits
@MVoeAc8esFJZqK=

$ python tools/pass-gen --length 12 --count 2 --no-symbols
# pool=57  entropy=70.0 bits
uTVRmwZZDp69
MJm6jRdRzAHu
```

Ambiguous characters (`0`, `O`, `1`, `l`, ...) are excluded by default, which makes the default pool 71 characters; `--allow-ambiguous` raises it to 94. Entropy is `length × log2(pool_size)`. See the [pass-gen cheatsheet](docs/cheatsheets/pass-gen.md).

### http-code

Look up one or more HTTP status codes, or list every known code.

```
http-code <code> [code ...]
http-code --list
```

```console
$ python tools/http-code 404 429
404 Not Found [Client Error]
  The requested resource could not be found.
429 Too Many Requests [Client Error]
  The client has sent too many requests in a given amount of time.

$ python tools/http-code --list      # also the default when no code is given
100  Continue                         Informational
101  Switching Protocols              Informational
102  Processing                       Informational
...
```

Unknown codes are reported on stderr and exit `1`. See the [http-code cheatsheet](docs/cheatsheets/http-code.md).

### epoch-convert

Convert Unix timestamps to ISO-8601 UTC dates, parse dates back to seconds, or humanize a duration.

```
epoch-convert <value> [--unit s|ms|us|ns]
epoch-convert --from-datetime <date>
epoch-convert --humanize <seconds>
epoch-convert --now-ms
```

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

Numeric input is converted to a date; use `--from-datetime` for date-string input. See the [epoch-convert cheatsheet](docs/cheatsheets/epoch-convert.md).

---

## Library usage

The `dptlib` package (under `tools/`) exposes the logic behind every tool. It has no side effects and uses only standard-library types.

```python
import sys
sys.path.insert(0, "tools")

from dptlib import jwt, httpcode, epoch, passgen

result = jwt.decode("header.payload.signature")
print(result["header"]["alg"])              # "HS256"
print(result["is_expired"])                 # None when no exp claim

print(httpcode.lookup(404)["title"])        # "Not Found"

print(epoch.to_datetime(1700000000))        # 2023-11-14T22:13:20Z
print(epoch.from_datetime("2023-11-14T22:13:20Z"))  # 1700000000

password = passgen.generate(20)
print(password, f"{passgen.estimate_entropy(20, 94):.1f} bits")
```

The full module-by-module reference is in [docs/LIBRARY.md](docs/LIBRARY.md).

---

## Running tests

The suite uses only `unittest` from the standard library:

```console
$ python -m unittest discover -s tests -v
```

Or via the Makefile:

```console
$ make test      # run tests
$ make lint      # byte-compile tools, bin and tests
$ make clean     # remove __pycache__ and .pyc files
$ make help      # list targets
```

---

## Project layout

```
dev-pocket-tools/
├── bin/
│   └── dpt                  # unified launcher: dpt <tool> [args]
├── tools/
│   ├── port-kill            # executable entry points (thin argparse wrappers)
│   ├── jwt-decode
│   ├── json-fmt
│   ├── env-diff
│   ├── git-clean-branches
│   ├── dir-size
│   ├── cron-explain
│   ├── pass-gen
│   ├── http-code
│   ├── epoch-convert
│   └── dptlib/              # reusable logic modules (importable)
│       ├── ports.py
│       ├── jwt.py
│       ├── jsonfmt.py
│       ├── envdiff.py
│       ├── gitbranches.py
│       ├── dirsize.py
│       ├── cron.py
│       ├── passgen.py
│       ├── httpcode.py
│       └── epoch.py
├── tests/                   # unittest suite + fixtures
├── docs/                    # this documentation set
│   ├── index.md
│   ├── INSTALL.md
│   ├── COMMANDS.md
│   ├── LIBRARY.md
│   ├── CONTRIBUTING.md
│   ├── SECURITY.md
│   └── cheatsheets/         # one quick-reference per tool
├── Makefile
├── LICENSE
└── README.md
```

The split is intentional: entry-point scripts parse arguments and format output; `dptlib` modules contain the logic and are safe to import from your own code.

---

## Contributing

Contributions are welcome. Keep the two hard rules intact: **standard library only** and **no network calls**. Add a test for every behavior change, keep entrypoints thin, and update the matching docs. See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).

## License

Released under the MIT License. See [LICENSE](LICENSE).

Copyright (c) 2026 nahas67.
