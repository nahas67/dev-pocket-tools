# cron-explain cheatsheet

Explain a five-field cron expression field by field.

```
python tools/cron-explain "<minute hour dom month dow>" [--json]
```

The tool **explains** expressions; it does not compute future run times. `--json` prints the expanded integer lists instead of prose.

## The five fields

```
 ┌───────────── minute        (0–59)
 │ ┌─────────── hour          (0–23)
 │ │ ┌───────── day of month  (1–31)
 │ │ │ ┌─────── month         (1–12 or JAN–DEC)
 │ │ │ │ ┌───── day of week   (0–7; 0 and 7 = Sunday, or SUN–SAT)
 │ │ │ │ │
 * * * * *
```

## Special characters

| Char | Meaning | Example | Interpretation |
| --- | --- | --- | --- |
| `*` | Every value | `* * * * *` | Every minute |
| `,` | List | `0,15,30,45 * * * *` | At those four minute values |
| `-` | Inclusive range | `0 9-17 * * *` | Hours 9 through 17 |
| `/` | Step | `*/15 * * * *` | Every 15 minutes |
| `a/n` | From a to max, step n | `5/10 * * * *` | Minutes 5, 15, 25, 35, 45, 55 |
| `a-b/n` | Range with step | `1-10/2 * * * *` | 1, 3, 5, 7, 9 |

## Example sessions

```console
$ python tools/cron-explain "*/15 9-17 * * 1-5"
Cron: */15 9-17 * * 1-5
  minute         at minutes 0, 15, 30, 45
  hour           at hours 9, 10, 11, 12, 13, 14, 15, 16, 17
  day_of_month   every day of the month
  month          every month
  day_of_week    at day of the weeks 1, 2, 3, 4, 5

$ python tools/cron-explain "0 9 * * 1-5"
Cron: 0 9 * * 1-5
  minute         at minute 0
  hour           at hour 9
  day_of_month   every day of the month
  month          every month
  day_of_week    at day of the weeks 1, 2, 3, 4, 5

$ python tools/cron-explain "0 9 * * 1-5" --json
{
  "day_of_month": [1, 2, 3, ..., 31],
  "day_of_week": [1, 2, 3, 4, 5],
  "expression": "0 9 * * 1-5",
  "hour": [9],
  "minute": [0],
  "month": [1, 2, 3, ..., 12]
}
```

The `...` above is an abbreviation; real output lists every integer explicitly.

Long expanded lists (e.g. all 31 days) are summarized as `every <field>`; a field with many but not all values lists the first ten followed by `, ...`.

## Common expressions

| Expression | Meaning |
| --- | --- |
| `* * * * *` | Every minute |
| `*/5 * * * *` | Every 5 minutes |
| `0 * * * *` | Top of every hour |
| `0 0 * * *` | Daily at midnight |
| `0 9 * * 1-5` | Weekdays at 09:00 |
| `30 2 * * 0` | Sundays at 02:30 |
| `0 0 1 * *` | First of each month at midnight |
| `0 0 1 1 *` | 1 January at midnight |
| `*/15 9-17 * * 1-5` | Every 15 minutes, business hours, weekdays |

## Cron shortcuts expanded

| Alias | Five-field form |
| --- | --- |
| `@yearly` / `@annually` | `0 0 1 1 *` |
| `@monthly` | `0 0 1 * *` |
| `@weekly` | `0 0 * * 0` |
| `@daily` / `@midnight` | `0 0 * * *` |
| `@hourly` | `0 * * * *` |

The tool takes the five-field form; `@reboot` has no schedule equivalent.

## Library equivalents

```python
from dptlib import cron

print(cron.explain("*/15 9-17 * * 1-5"))          # multi-line string
parsed = cron.describe("0 9 * * 1-5")
print(parsed["hour"])                             # [9]
print(parsed["day_of_week"])                      # [1, 2, 3, 4, 5]
cron.parse_field("1-10/2", 0, 59)                 # [1, 3, 5, 7, 9]
```

## Gotchas

- Exactly five fields are required; six-/seven-field Quartz/Spring expressions are rejected.
- In classic cron, if both day-of-month and day-of-week are restricted, the job fires when *either* matches — the explainer describes fields independently.
- Month and weekday names are case-insensitive three-letter abbreviations.
- Invalid fields, descending ranges, zero/negative steps, and out-of-range values exit `1` with a `ValueError` message.
