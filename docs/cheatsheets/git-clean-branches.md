# git-clean-branches cheatsheet

Classify local branches and print safe `git branch -d` delete commands. Nothing is deleted unless `--execute` is passed.

```
python tools/git-clean-branches [--input FILE] [--protected A,B,GLOB] [--execute] [--yes]
```

## Example session

Using the bundled fixture:

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

## Options

| Option | Meaning |
| --- | --- |
| `--input`, `-i FILE` | File containing `git branch` output (default: run `git branch --no-color`) |
| `--protected LIST` | Comma-separated protected names/globs |
| `--execute` | Actually delete branches (default: print commands only) |
| `--yes` | Skip confirmation with `--execute` |

Default protected names: `main`, `master`, `develop`, `development` (`gitbranches.DEFAULT_PROTECTED`). Globs work too: `--protected 'main,release/*,staging'`.

## Classification

| Label | Meaning |
| --- | --- |
| `current` | The checked-out branch (takes precedence over everything) |
| `protected` | Matches a protected name or glob |
| `deletable` | Everything else — candidate for deletion |

Only `deletable` branches appear in the DELETE COMMANDS list. The dry-run commands carry a trailing `# dry-run` comment, so they are harmless to paste into a shell.

## Safe cleanup workflow

```bash
# 1. Update refs first
git checkout main && git pull && git fetch --prune

# 2. Preview (tool runs `git branch` itself in a terminal)
python tools/git-clean-branches

# 3. Protect long-lived branches with globs
python tools/git-clean-branches --protected 'main,develop,release/*'

# 4. Delete interactively (confirmation prompt)
python tools/git-clean-branches --execute

# 5. Non-interactive / CI (no prompt)
python tools/git-clean-branches --execute --yes
```

You can also feed it saved output for review without touching the current repo:

```bash
git branch --no-color > /tmp/branches.txt
python tools/git-clean-branches --input /tmp/branches.txt --protected 'main,release/*'
```

## Equivalent manual commands

```bash
git branch --merged main          # list branches merged into main
git branch -d feature/auth        # safe delete (refuses unmerged work)
git branch -D feature/auth        # FORCE delete (destroys unmerged commits)
git push origin --delete name     # delete a remote branch
```

## Gotchas

- The tool classifies by name and protection rules; it does **not** check whether a branch is merged. Git's own `git branch -d` performs that safety check at execution time — hence the safe `-d` rather than `-D`.
- Squash-merged and rebased branches may not show up as merged to git; verify before deleting.
- Empty branch output exits `1` with `No branch output to process.`
- The tool only handles **local** branches; remote pruning is a separate manual step.
- Running with `--input` or piped stdin avoids invoking git entirely, which is useful in tests and scripts.
