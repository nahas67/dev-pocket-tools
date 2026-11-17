# pass-gen cheatsheet

Generate cryptographically secure random passwords with Python's `secrets` module.

```
python tools/pass-gen [--length N] [--count N] [--no-symbols] [--no-digits]
                      [--no-upper] [--no-lower] [--allow-ambiguous]
```

Passwords are printed to stdout. A pool/entropy line is always printed to **stderr** — there is no `--entropy` flag to turn on.

## Example session

```console
$ python tools/pass-gen --length 16
# pool=71  entropy=98.4 bits
@MVoeAc8esFJZqK=

$ python tools/pass-gen --length 12 --count 2 --no-symbols
# pool=57  entropy=70.0 bits
uTVRmwZZDp69
MJm6jRdRzAHu

$ python tools/pass-gen --length 20 --allow-ambiguous
# pool=94  entropy=131.1 bits
aB3!xY7@qLmN2#pR9sTu
```

Generated values differ every run — that is the point.

## Options

| Option | Default | Effect |
| --- | --- | --- |
| `--length`, `-n N` | `16` | Characters per password |
| `--count`, `-c N` | `1` | Number of passwords (must be ≥ 1) |
| `--no-symbols` | symbols on | Remove `string.punctuation` |
| `--no-digits` | digits on | Remove `0-9` |
| `--no-upper` | upper on | Remove `A-Z` |
| `--no-lower` | lower on | Remove `a-z` |
| `--allow-ambiguous` | ambiguous excluded | Keep `0`, `O`, `1`, `l`, `I`, etc. |

At least one class must remain. The `# pool=N entropy=X.X bits` line reflects the exact pool after exclusions.

## Character pools

Ambiguous characters are **excluded by default** for readability, shrinking the pools:

| Classes | Ambiguous excluded (default) | With `--allow-ambiguous` |
| --- | --- | --- |
| lower + upper + digits + symbols | 71 | 94 |
| lower + upper + digits | 57 | 62 |
| lower + upper | 47 | 52 |

## Entropy guidance

Entropy is `length × log2(pool_size)` bits; every extra bit doubles the brute-force search space.

| Configuration | Entropy | Assessment |
| --- | --- | --- |
| 8 × letters | ~37 bits | Weak |
| 16 × digits | 53.2 bits | Weak against offline attacks |
| 12 × alphanumeric (pool 57) | 70.0 bits | Acceptable for online-only use |
| 16 × default pool (71) | 98.4 bits | Strong — the CLI default |
| 16 × full pool (94, `--allow-ambiguous`) | 104.9 bits | Strong |
| 20 × full pool (94) | 131.1 bits | Very strong |

Aim for **at least 80 bits** for anything that may be attacked offline (password managers, disk encryption, hashed credential stores). Prefer longer passwords over exotic character sets.

## How generation works

- One character from each enabled class is included when the requested length allows it.
- Remaining characters are drawn uniformly from the combined pool with `secrets.choice`.
- Characters are shuffled with `secrets.SystemRandom().shuffle` so guaranteed-class positions are unpredictable.
- `random` is never used.

## Library equivalents

```python
from dptlib import passgen

password = passgen.generate(20)                       # 20 chars, ambiguous excluded
simple = passgen.generate(12, use_symbols=False)      # alphanumeric
full = passgen.generate(20, exclude_ambiguous=False)  # keep 0/O/1/l
bits = passgen.estimate_entropy(16, 71)               # 98.37...
```

Constants for custom pools: `passgen.UPPER`, `LOWER`, `DIGITS`, `SYMBOLS`, `AMBIGUOUS`.

## Gotchas

- Output lands in terminal scrollback and shell history; clear it after generating real credentials.
- `--count` values below 1 exit `1`. Non-positive lengths or disabling every class raise `ValueError` (exit `1`).
- Because the entropy line goes to stderr, redirecting stdout (`pass-gen > pw.txt`) leaves entropy on the console and the password in the file.
- Some legacy systems reject punctuation; use `--no-symbols` and compensate with a longer length.
- Do not reuse passwords across systems; store the output in a password manager.
