"""Smoke tests that run each CLI tool with ``--help`` via subprocess.

Every tool must exit with status 0 and print a non-empty help/usage message.
These tests exercise the scripts as a user would, independently of importing
the library modules directly.
"""

import os
import subprocess
import sys
import unittest

from _path import REPO_ROOT, TOOLS_DIR

COMMANDS = (
    "port-kill",
    "jwt-decode",
    "json-fmt",
    "env-diff",
    "git-clean-branches",
    "dir-size",
    "cron-explain",
    "pass-gen",
    "http-code",
    "epoch-convert",
)


class TestCliHelp(unittest.TestCase):
    def _run_help(self, command):
        script = os.path.join(TOOLS_DIR, command)
        return subprocess.run(
            [sys.executable, script, "--help"],
            cwd=REPO_ROOT,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )

    def test_all_commands_ship_help(self):
        for command in COMMANDS:
            with self.subTest(command=command):
                result = self._run_help(command)
                self.assertEqual(
                    result.returncode, 0,
                    f"{command} --help failed: {result.stderr.strip()}",
                )
                self.assertTrue(
                    result.stdout.strip(),
                    f"{command} --help printed nothing to stdout",
                )
                self.assertIn("usage", (result.stdout + result.stderr).lower())

    def test_every_command_script_exists(self):
        for command in COMMANDS:
            with self.subTest(command=command):
                self.assertTrue(
                    os.path.isfile(os.path.join(TOOLS_DIR, command)),
                    f"missing CLI script: tools/{command}",
                )


if __name__ == "__main__":
    unittest.main()
