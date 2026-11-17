# port-kill cheatsheet

Parse `netstat` / `lsof` listener output, summarize it, and build — or run — process kill commands.

```
python tools/port-kill [--input FILE] [--format {auto,netstat,lsof}]
                       [--port N] [--pid N] [--force] [--execute] [--yes]
```

> **Read-only by default.** The tool prints the commands it *would* run. Add `--execute` to actually kill processes.

## Example session

Using the bundled `lsof` fixture:

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

## Options

| Option | Meaning |
| --- | --- |
| `--input`, `-i FILE` | Read listener text from a file (otherwise stdin) |
| `--format`, `-f` | `auto` (default), `netstat`, or `lsof` |
| `--port N` | Keep only entries on local port `N` |
| `--pid N` | Keep only entries for PID `N` |
| `--force` | Force kill: `kill -9` / `taskkill /F` |
| `--execute` | Run the commands (with confirmation) |
| `--yes` | Skip confirmation with `--execute` |

`auto` treats input as `lsof` when a line starts with `COMMAND` or contains ` (LISTEN)`, otherwise as `netstat`.

## Producing the input

The tool is a parser — generate its input with the OS utility:

```bash
# Linux / macOS: lsof
lsof -nP -iTCP -sTCP:LISTEN | python tools/port-kill --format lsof
lsof -nP | python tools/port-kill --port 8080

# Linux alternative: fuser / ss (format as lsof-like text or use netstat-style rows)
ss -ltnp

# Windows: netstat
netstat -ano | python tools/port-kill --format netstat --port 8080
```

On Windows PowerShell you can also use `Get-NetTCPConnection`, but `netstat -ano` output is what the parser expects.

## Record shape

Each parsed entry has:

| Key | Meaning |
| --- | --- |
| `proto` / `protocol` | `TCP`, `UDP`, etc. |
| `address` / `local_address` | Bind address, e.g. `0.0.0.0`, `::` |
| `port` | Integer local port |
| `state` | `LISTENING`, `LISTEN`, `ESTABLISHED`, or empty |
| `pid` | Process ID, or `None` |
| `process` | Command name (`lsof` only), or `None` |

## Safe workflow

1. **Capture** listener output with the OS command above.
2. **Preview** with `port-kill` (no `--execute`) and read the summary and commands.
3. **Narrow** with `--port` / `--pid` so only intended processes are targeted.
4. **Execute** with `--execute` (confirm), adding `--force` only if graceful termination fails.

## Gotchas

- If stdin is a terminal and no `--input` is given, the tool reports `No input supplied` and exits `1`.
- Entries with no PID are skipped when building commands (`No PIDs available to kill.`).
- Duplicate PIDs are killed once. Killing another user's process usually needs root/admin rights.
- The kill command itself is platform-correct: `kill`/`kill -9` on Unix, `taskkill /PID ... /F` on Windows.
