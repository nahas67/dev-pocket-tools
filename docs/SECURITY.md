# Security policy

`dev-pocket-tools` is designed to be safe to run on developer machines and in CI. This document explains the security model, the handling of sensitive data, and how to report a concern.

## Security model

The toolkit is built on three hard constraints:

1. **No network access.** No tool opens sockets to remote hosts, downloads data, or sends telemetry. `port-kill` only parses listener text you give it; it never contacts the processes it describes.
2. **Standard library only.** No third-party runtime dependencies means no transitive supply chain from pip packages.
3. **Local, explicit action.** Tools operate on files and text you supply. Destructive actions require an explicit `--execute` flag (plus a confirmation prompt unless `--yes` is given); the default prints what *would* happen.

These properties are enforced by design and should be preserved by every contribution. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Sensitive data

Several tools touch values that may be secrets. Treat their output carefully.

### `env-diff`

- Values are **shown by default** — the report prints `KEY='value'` for added/removed keys and `'old' -> 'new'` for changed ones. Assume any `env-diff` output may contain secrets.
- Pass `--mask` to hide values (first and last character remain visible so you can identify entries). Use it whenever output may be seen by others.
- Avoid piping unmasked output into logs, chat, or CI artifacts. `--show-same` also reveals unchanged values, so use it with the same care.

### `jwt-decode`

- Decoding a JWT is **not verification**. The tool displays the header and payload exactly as encoded and never verifies the signature, issuer (`iss`), or audience (`aud`). It reads `exp` only for an informational `EXPIRY` line, with no cryptographic trust.
- A JWT is a bearer credential. Pasting one into a terminal, shell history, or an issue tracker can expose it. Prefer test tokens when documenting or sharing output; `--redact` prints a non-reversible preview.
- Never make an authorization decision based solely on `jwt-decode` output. Use a proper verification library in the consuming application.

### `pass-gen`

- Passwords are generated with the `secrets` module (CSPRNG), not `random`. Ambiguous characters are excluded by default; `--allow-ambiguous` restores them.
- Generated passwords are printed to stdout and are not stored, logged, or transmitted by the toolkit.
- Be mindful of terminal scrollback and shell history when generating real credentials. Use the entropy estimate to choose a length appropriate for your threat model (see the [pass-gen cheatsheet](cheatsheets/pass-gen.md)).

## Process and filesystem safety

### `port-kill`

- Killing a process is destructive. The tool is read-only by default: it prints the exact kill commands. Nothing runs until you pass `--execute`, which prompts for confirmation unless `--yes` is given. Review the PID and command before confirming — port numbers can be reused.
- `--force` escalates to `kill -9` / `taskkill /F`; use it only when graceful termination fails.
- On multi-user systems, terminating another user's process typically requires elevated privileges. The tool does not attempt privilege escalation on its own.

### `git-clean-branches`

- Deletions are dry-run by default. You must pass `--execute` (and typically confirm) for branches to be removed.
- The current branch and `main`, `master`, `develop`, `development` are always protected; `--protected` lets you add names or globs such as `release/*`.
- The tool emits safe `git branch -d` commands, which git refuses to apply to unmerged branches. Because branch deletion discards references to commits, verify the work landed before executing.

### `dir-size`

- Read-only. It walks directories and sums file sizes; it does not modify or delete anything.
- Unreadable or missing paths are reported with zero size and zero files rather than aborting the run.

## Reporting a vulnerability

If you find a security issue — for example, a tool that unexpectedly accesses the network, leaks secret values, or performs an unsafe action — please report it privately rather than opening a public issue.

Email: **security@dev-pocket-tools.invalid** (replace with the maintainer's preferred private contact when one is published).

Include:

- The tool and exact command that triggers the issue
- Your OS and Python version
- A description of the impact and a minimal reproduction
- Any suggested fix, if you have one

You should receive an acknowledgement within a reasonable timeframe. Please give the maintainer a chance to address the issue before disclosing it publicly.

## Supported versions

Security fixes are applied to the latest release only. Because the toolkit has no runtime dependencies and no network surface, the most common security concerns are accidental secret exposure in tool output and unsafe use of destructive flags — both covered above.

See [LICENSE](../LICENSE) for the project license.
