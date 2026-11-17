# dev-pocket-tools documentation

Welcome. `dev-pocket-tools` is a zero-dependency, standard-library-only CLI toolkit with ten small tools for everyday developer tasks.

Start here:

- [Installation](INSTALL.md) — requirements and how to run the tools on Linux, macOS, and Windows.
- [Command reference](COMMANDS.md) — every tool's syntax, options, and example output.
- [Library usage](LIBRARY.md) — importing the logic modules from your own Python code.
- [Contributing](CONTRIBUTING.md) — development workflow and coding conventions.
- [Security](SECURITY.md) — the no-network/no-secrets policy and how to report issues.

## Quick references (cheatsheets)

| Tool | Cheatsheet |
| --- | --- |
| port-kill | [docs/cheatsheets/port-kill.md](cheatsheets/port-kill.md) |
| jwt-decode | [docs/cheatsheets/jwt-decode.md](cheatsheets/jwt-decode.md) |
| json-fmt | [docs/cheatsheets/json-fmt.md](cheatsheets/json-fmt.md) |
| env-diff | [docs/cheatsheets/env-diff.md](cheatsheets/env-diff.md) |
| git-clean-branches | [docs/cheatsheets/git-clean-branches.md](cheatsheets/git-clean-branches.md) |
| dir-size | [docs/cheatsheets/dir-size.md](cheatsheets/dir-size.md) |
| cron-explain | [docs/cheatsheets/cron-explain.md](cheatsheets/cron-explain.md) |
| pass-gen | [docs/cheatsheets/pass-gen.md](cheatsheets/pass-gen.md) |
| http-code | [docs/cheatsheets/http-code.md](cheatsheets/http-code.md) |
| epoch-convert | [docs/cheatsheets/epoch-convert.md](cheatsheets/epoch-convert.md) |

## The 30-second version

```console
$ python bin/dpt --help                     # list all tools
$ python bin/dpt http-code 404              # look up a status code
$ python bin/dpt cron-explain "0 9 * * 1-5" # explain a schedule
$ python -m unittest discover -s tests -v   # run the suite
```

## Design principles

1. **Standard library only.** No third-party runtime dependencies, ever.
2. **No network access.** No tool downloads, calls APIs, or sends telemetry.
3. **Thin entrypoints, testable logic.** CLI scripts live in `tools/`; importable modules live in `tools/dptlib/`.
4. **Safe by default.** Destructive operations default to dry-run or confirmation.
5. **Script-friendly.** Predictable stdout and meaningful exit codes.
