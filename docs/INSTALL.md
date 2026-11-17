# Installation

There is nothing to install. `dev-pocket-tools` has **no third-party dependencies** and no build step. You need only Python 3.8 or newer.

## Requirements

- Python **3.8+** (check with `python --version` or `python3 --version`)
- A terminal
- Git, only to clone the repository

No `pip install`, no virtual environment, no compiler, and no network access at runtime.

## Get the code

```console
$ git clone https://github.com/nahas67/dev-pocket-tools.git
$ cd dev-pocket-tools
```

Alternatively, download a release archive and unpack it. The tools are fully portable — no install hook needs to run.

## Verify the checkout

Run the test suite and a smoke check:

```console
$ python -m unittest discover -s tests -v
$ python bin/dpt --help
$ python bin/dpt http-code 200
```

If all three work, you are ready.

## Running the tools

Every command can be run through the unified launcher from the repository root:

```console
$ python bin/dpt <tool> [args]
```

For example:

```console
$ python bin/dpt epoch-convert 1700000000
Epoch (s):   1700000000
UTC:         2023-11-14 22:13:20 UTC
```

You can also invoke an individual tool script directly:

```console
$ python tools/epoch-convert 1700000000
```

Both forms are equivalent. The launcher simply dispatches to the tool script.

## Optional: put `dpt` on your PATH

On Linux or macOS you can make the launcher directly executable and symlink it:

```console
$ chmod +x bin/dpt
$ ln -s "$PWD/bin/dpt" /usr/local/bin/dpt
$ dpt --help
```

If you prefer not to write to `/usr/local/bin`, add the repository's `bin/` directory to your shell profile instead:

```bash
# ~/.bashrc or ~/.zshrc
export PATH="/path/to/dev-pocket-tools/bin:$PATH"
```

Then ensure `bin/dpt` is executable (`chmod +x bin/dpt`) and run `dpt --help`.

> **Windows:** PATH setup works too, but the simplest invocation is always `python bin/dpt <tool>`. You can create a `dpt.cmd` shim in a directory on your PATH containing `@python "%~dp0..\bin\dpt" %*` if you want a `dpt` command.

## Platform notes

- **port-kill** shells out to `lsof`/`fuser` on Linux and macOS and `netstat`/`taskkill` on Windows. Those OS utilities ship with the platform; `dev-pocket-tools` itself still needs no third-party Python packages. Some systems require elevated privileges to inspect or kill another user's process.
- **git-clean-branches** requires `git` on your PATH and must be run inside a git work tree.
- All other tools are pure Python and behave identically everywhere (aside from timezone names accepted by `epoch-convert`, which come from the OS).

## Updating

Because there is no install step, updating is just pulling the repository:

```console
$ git pull
$ python -m unittest discover -s tests -v
```

## Uninstalling

Delete the cloned directory (and any PATH entry or symlink you created). No global state, caches, or configuration files are written outside the repository — Python may create local `__pycache__` directories, which `make clean` removes.
