# epoch-convert cheatsheet

Convert Unix timestamps to ISO-8601 UTC dates, parse dates to seconds, humanize durations, or get the current time.

```
python tools/epoch-convert <value> [--unit UNIT]
python tools/epoch-convert --from-datetime <date>
python tools/epoch-convert --humanize <seconds>
python tools/epoch-convert --now-ms
```

A Unix timestamp is the number of non-leap seconds since **1970-01-01 00:00:00 UTC**. The mode flags are mutually exclusive.

## Units

| Unit | Divisor to seconds | Typical digit count (2020s) |
| --- | --- | --- |
| `s` (default) | 1 | 10 |
| `ms` | 1,000 | 13 |
| `us` | 1,000,000 | 16 |
| `ns` | 1,000,000,000 | 19 |

The unit is **explicit**: a 13-digit value is treated as seconds unless you pass `--unit ms`.

## Example session

```console
$ python tools/epoch-convert 1700000000
2023-11-14T22:13:20Z

$ python tools/epoch-convert 1700000000000 --unit ms
2023-11-14T22:13:20Z

$ python tools/epoch-convert 1700000000000000 --unit us
2023-11-14T22:13:20Z

$ python tools/epoch-convert --from-datetime "2023-11-14T22:13:20Z"
1700000000

$ python tools/epoch-convert --humanize 90061
1d 1h 1m 1s

$ python tools/epoch-convert --now-ms
1763374400123
```

Numeric input produces an ISO-8601 UTC string ending in `Z`; `--from-datetime` produces epoch seconds. `--now-ms` prints the current epoch milliseconds (value will vary).

## Conversion formulas

```
seconds = milliseconds / 1_000
seconds = microseconds / 1_000_000
seconds = nanoseconds  / 1_000_000_000
```

Python (timezone-aware):

```python
from datetime import datetime, timezone

dt = datetime.fromtimestamp(1700000000, tz=timezone.utc)
# datetime(2023, 11, 14, 22, 13, 20, tzinfo=timezone.utc)
int(dt.timestamp())                    # 1700000000
int(dt.timestamp() * 1000)             # 1700000000000
```

## Reference values

| Value | Meaning |
| --- | --- |
| `0` | 1970-01-01T00:00:00Z (the epoch) |
| `-1` | 1969-12-31T23:59:59Z |
| `1000000000` | 2001-09-09T01:46:40Z |
| `1700000000` | 2023-11-14T22:13:20Z |
| `2147483647` | 2038-01-19T03:14:07Z (32-bit signed limit) |

## Accepted date strings

`from_datetime` tries ISO-8601 first, then a few common formats. A trailing `Z` is treated as UTC; naive strings are also treated as UTC.

| Input | Result |
| --- | --- |
| `2023-11-14T22:13:20Z` | `1700000000` |
| `2023-11-14 22:13:20` | `1700000000` |
| `2023-11-14` | `1699920000` (midnight UTC) |
| `2023/11/14 22:13:20` | `1700000000` |

Offsets such as `2023-11-15T03:43:20+05:30` are honored by `fromisoformat`.

## Library equivalents

```python
from dptlib import epoch

epoch.to_datetime(0)                         # '1970-01-01T00:00:00Z'
epoch.to_datetime(1700000000000, unit="ms")  # '2023-11-14T22:13:20Z'
epoch.from_datetime("2023-11-14T22:13:20Z")  # 1700000000
epoch.humanize(90061)                        # '1d 1h 1m 1s'
epoch.humanize(3661)                         # '1h 1m 1s'
epoch.now_ms()                               # current epoch milliseconds
```

`humanize` renders durations as compact `d/h/m/s` units with optional `ms` for sub-second remainders; negative values keep a leading `-`.

## Gotchas

- There is **no auto-detection** and no `--tz` flag: pick the unit explicitly and remember output is always UTC.
- Unknown units, non-numeric input, or out-of-range timestamps raise `ValueError` (CLI exits `1`).
- Unix time ignores leap seconds, so it is not a strict count of elapsed SI seconds.
- Fractional seconds are shown in the ISO output only when non-zero.
