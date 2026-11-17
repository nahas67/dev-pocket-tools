"""Unit tests for :mod:`dptlib.gitbranches`."""

import unittest

from _path import fixture

try:
    from dptlib import gitbranches
except Exception:  # pragma: no cover
    gitbranches = None


@unittest.skipIf(gitbranches is None, "dptlib.gitbranches is not available yet")
class TestParseBranchLines(unittest.TestCase):
    def test_parses_fixture(self):
        branches = gitbranches.parse_branch_lines(fixture("branches.txt"))
        self.assertEqual(len(branches), 5)
        self.assertEqual(
            [b["name"] for b in branches],
            ["main", "develop", "feature/auth", "feature/payments", "bugfix/issue-42"],
        )
        self.assertEqual([b["current"] for b in branches], [True, False, False, False, False])

    def test_exact_record_shape(self):
        branch = gitbranches.parse_branch_lines("* main\n")[0]
        self.assertEqual(
            branch,
            {"name": "main", "current": True, "hash": None, "protected": None, "raw": "* main"},
        )

    def test_optional_hash_column(self):
        branch = gitbranches.parse_branch_lines("* main a1b2c3d4\n")[0]
        self.assertEqual(branch["hash"], "a1b2c3d4")
        self.assertEqual(branch["name"], "main")

    def test_empty_and_junk_lines(self):
        self.assertEqual(gitbranches.parse_branch_lines(""), [])
        self.assertEqual(gitbranches.parse_branch_lines("\n  \n"), [])


@unittest.skipIf(gitbranches is None, "dptlib.gitbranches is not available yet")
class TestClassify(unittest.TestCase):
    def test_current_takes_precedence(self):
        self.assertEqual(gitbranches.classify("main", "main", None), "current")
        self.assertEqual(gitbranches.classify("main", "main", ["main"]), "current")

    def test_exact_and_default_protected(self):
        self.assertEqual(gitbranches.classify("main", "feature/x", None), "protected")
        self.assertEqual(gitbranches.classify("develop", "feature/x", None), "protected")

    def test_glob_protected(self):
        self.assertEqual(
            gitbranches.classify("release/1.2.0", "feature/x", ["release/*"]),
            "protected",
        )

    def test_deletable(self):
        self.assertEqual(gitbranches.classify("feature/x", "main", None), "deletable")

    def test_accepts_branch_dict(self):
        branch = {"name": "feature/y"}
        self.assertEqual(gitbranches.classify(branch, "main", None), "deletable")


@unittest.skipIf(gitbranches is None, "dptlib.gitbranches is not available yet")
class TestBuildDeleteCommands(unittest.TestCase):
    def test_dry_run_default(self):
        branches = gitbranches.parse_branch_lines(fixture("branches.txt"))
        commands = gitbranches.build_delete_commands(branches)
        self.assertEqual(
            commands,
            [
                "git branch -d feature/auth  # dry-run",
                "git branch -d feature/payments  # dry-run",
                "git branch -d bugfix/issue-42  # dry-run",
            ],
        )

    def test_non_dry_run_has_no_comment(self):
        commands = gitbranches.build_delete_commands(["feature/auth"], dry_run=False)
        self.assertEqual(commands, ["git branch -d feature/auth"])

    def test_current_and_protected_excluded(self):
        branches = ["main", "develop", "feature/x"]
        self.assertEqual(gitbranches.build_delete_commands(branches, dry_run=False),
                         ["git branch -d feature/x"])

    def test_empty_input(self):
        self.assertEqual(gitbranches.build_delete_commands([]), [])

    def test_empty_names_skipped(self):
        self.assertEqual(gitbranches.build_delete_commands(["", "  "], dry_run=False), [])
