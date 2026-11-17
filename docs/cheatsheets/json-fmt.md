# json-fmt cheatsheet

Format, minify, validate, or flatten JSON — no `jq` required.

```
python tools/json-fmt [FILE] [--indent N] [--sort-keys] [--minify] [--flatten] [--check]
```

Reads from `FILE` if given, otherwise from stdin. Invalid JSON exits `1`.

## Options

| Option | Meaning |
| --- | --- |
| `FILE` | Path to a JSON file (default: stdin) |
| `--indent N` | Indentation width (default `2`) |
| `--sort-keys` | Sort object keys alphabetically |
| `--minify` | Compact output, no whitespace |
| `--flatten` | Emit `dotted.path<TAB>JSON-value` lines |
| `--check` | Only validate; print `Valid JSON` / `Invalid JSON` |

## Recipes

### Pretty-print (default)

```console
$ echo '{"b":2,"a":1}' | python tools/json-fmt
{
  "b": 2,
  "a": 1
}
```

Key order is preserved unless `--sort-keys` is given.

### Sort keys

```console
$ echo '{"b":2,"a":1}' | python tools/json-fmt --sort-keys
{
  "a": 1,
  "b": 2
}
```

### Minify

```console
$ echo '{"b": 2, "a": 1}' | python tools/json-fmt --minify
{"b":2,"a":1}
```

### Custom indentation

```console
$ echo '{"a":1}' | python tools/json-fmt --indent 4
{
    "a": 1
}
```

### Flatten to dotted paths

Nested objects and arrays become `dotted.path` keys; list indices are numeric segments. Empty containers are kept as leaf values. Output is `path`, a literal tab, then the value serialized as JSON.

```console
$ echo '{"a":{"b":[1,2]},"empty":{}}' | python tools/json-fmt --flatten
a.b.0	1
a.b.1	2
empty	{}
```

### Validate only

```console
$ echo '{"ok":true}' | python tools/json-fmt --check
Valid JSON

$ echo '{bad' | python tools/json-fmt --check
Invalid JSON
```

## jq equivalence table

| Goal | jq | json-fmt |
| --- | --- | --- |
| Pretty-print | `jq .` | `json-fmt` |
| Minify | `jq -c .` | `json-fmt --minify` |
| Sort keys | `jq -S .` | `json-fmt --sort-keys` |
| Indent 4 | `jq --indent 4 .` | `json-fmt --indent 4` |
| Flatten paths | `jq 'paths(scalars)'` | `json-fmt --flatten` |
| Validate | `jq empty` | `json-fmt --check` |

`json-fmt` focuses on formatting and flattening; it does not implement jq's filter/select/map language.

## Everyday pipelines

```bash
# Format a file in place (via a temp file)
python tools/json-fmt config.json --sort-keys > config.pretty.json

# Flatten to a shell-friendly key/value list
python tools/json-fmt settings.json --flatten | head -20

# Gate a build on valid JSON
python tools/json-fmt manifest.json --check >/dev/null || exit 1
```

## Gotchas

- Empty input exits `1` with `No JSON supplied.`
- Only one JSON document per invocation; JSON Lines / NDJSON needs one call per line.
- Scalars are valid JSON (`123`, `true`, `null`, `"text"`) and will be formatted, not rejected.
- Non-ASCII characters are preserved (`ensure_ascii=False`).
- Duplicate keys in input: the last value wins, as with Python's `json` module.
