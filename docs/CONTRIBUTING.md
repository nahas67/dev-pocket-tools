# Contributing

Thanks for helping improve `dev-pocket-tools`. The project is deliberately small and focused, so contributions are easiest when they follow a few clear rules.

## Ground rules

Two rules are non-negotiable:

1. **Standard library only.** No third-party runtime dependencies. If a feature seems to need one, look for a stdlib equivalent first (`json`, `argparse`, `secrets`, `datetime`, `pathlib`, `subprocess`, `base64` cover most needs).
2. **No network access.** Tools must not download data, call APIs, or send telemetry. All work is local.

Beyond that:

- Keep entrypoint scripts in `tools/` thin — argument parsing and output formatting only.
- Put real logic in the matching `tools/dptlib/<name>.py` module so it can be imported and tested.
- Keep behavior safe by default: destructive operations default to dry-run or explicit confirmation.
- Write for a terminal: predictable stdout, errors to stderr, meaningful exit codes (`0` success, `1` runtime error, `2` usage error).

## Development setup

There is no install step. Clone the repo and run the tests:

```console
$ git clone https://github.com/nahas67/dev-pocket-tools.git
$ cd dev-pocket-tools
$ python -m unittest discover -s tests -v
```

## Workflow

1. **Create a branch** from `main`, e.g. `git checkout -b feature/shorter-help`.
2. **Write a failing test first.** Add or update a test under `tests/` that captures the behavior you want.
3. **Implement the change** in the appropriate `dptlib` module and update the thin CLI wrapper if the interface changes.
4. **Run the checks** until everything is green:
   ```console
   $ python -m unittest discover -s tests -v
   $ make lint
   ```
5. **Update the docs.** If you change a command's interface, update `README.md`, `docs/COMMANDS.md`, and the matching cheatsheet in `docs/cheatsheets/`. If you change a library function, update `docs/LIBRARY.md`.
6. **Open a pull request** describing the change and how you tested it.

## Adding a new tool

A new tool touches several places. Use this checklist:

- [ ] `tools/<name>` — executable entrypoint using `argparse`
- [ ] `tools/dptlib/<name>.py` — importable logic with no I/O side effects
- [ ] `tests/test_<name>.py` — unit tests for the logic and, where useful, the CLI
- [ ] `bin/dpt` — register the tool so `dpt <name>` dispatches correctly
- [ ] `README.md` — add it to the features table, quickstart `list` output, project layout, and command reference
- [ ] `docs/COMMANDS.md` — full syntax, options table, and example output
- [ ] `docs/cheatsheets/<name>.md` — quick reference with real examples
- [ ] `docs/LIBRARY.md` — document its importable functions
- [ ] `docs/index.md` — add it to the cheatsheet table

Pick a name that is short, lowercase, and hyphenated (e.g. `json-fmt`). The matching module uses a compact underscore-free name (e.g. `jsonfmt.py`, `httpcode.py`).

## Code style

- Target **Python 3.8+**. Avoid syntax that requires a newer interpreter.
- Follow PEP 8: four-space indents, descriptive names, lines under ~88 characters where practical.
- Add type hints to library functions and docstrings to public functions.
- Use `pathlib.Path` for filesystem paths and `argparse` for CLIs.
- Never use `random` for secrets; use `secrets` (this applies to `pass-gen` and anything similar).
- Do not add a `__pycache__` or `.pyc` file to a commit — `make clean` removes them.

## Testing conventions

- Use `unittest` (already the project standard). No pytest plugin is required.
- One test module per tool plus one for the launcher is the normal layout.
- Test logic through `dptlib` functions; keep CLI tests focused on argument parsing and output shape.
- Avoid tests that depend on the host's network, timezone database details beyond UTC, or a specific machine's process table. Where a test must touch the OS (e.g. `port-kill`), mock the platform calls.
- Run the full suite before opening a PR:
  ```console
  $ python -m unittest discover -s tests -v
  ```

## Commit and PR guidance

- Keep commits focused; one logical change per commit.
- Write imperative commit messages ("Add `--mask` to env-diff", not "added stuff").
- In the PR, list the commands you ran and their results. A green test run is the clearest evidence.
- Be responsive to review feedback — small tools benefit from careful, quick iterations.

## Reporting bugs

Open an issue with: the tool and exact command, your OS and Python version, what you expected, and what actually happened (paste the full output). Include a minimal reproduction if possible.

## License

By contributing, you agree that your work is licensed under the project's MIT License. See [LICENSE](../LICENSE).
