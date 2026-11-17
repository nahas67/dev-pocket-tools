"""Unit tests for :mod:`dptlib.envdiff`."""

import unittest

from _path import fixture

try:
    from dptlib import envdiff
except Exception:  # pragma: no cover
    envdiff = None


@unittest.skipIf(envdiff is None, "dptlib.envdiff is not available yet")
class TestParseEnv(unittest.TestCase):
    def test_parses_fixture(self):
        parsed = envdiff.parse_env(fixture("sample.env"))
        self.assertEqual(
            parsed,
            {
                "APP_NAME": "nios",
                "DEBUG": "true",
                "PORT": "8080",
                "EMPTY_VALUE": "",
                "API_KEY": "supersecretkey123",
            },
        )

    def test_comments_and_blanks_ignored(self):
        text = "# a comment\n\n   # indented comment\nKEY=value\n"
        self.assertEqual(envdiff.parse_env(text), {"KEY": "value"})

    def test_export_prefix_and_quotes(self):
        text = 'export A="hello"\nexport B=\'world\'\n'
        self.assertEqual(envdiff.parse_env(text), {"A": "hello", "B": "world"})

    def test_equals_in_value_preserved(self):
        self.assertEqual(envdiff.parse_env("URL=a=b=c"), {"URL": "a=b=c"})

    def test_empty_input(self):
        self.assertEqual(envdiff.parse_env(""), {})


@unittest.skipIf(envdiff is None, "dptlib.envdiff is not available yet")
class TestDiffEnv(unittest.TestCase):
    def test_exact_diff_structure(self):
        a = {"A": "1", "B": "2", "C": "3"}
        b = {"B": "2", "C": "changed", "D": "4"}
        self.assertEqual(
            envdiff.diff_env(a, b),
            {
                "added": {"D": "4"},
                "removed": {"A": "1"},
                "changed": {"C": {"old": "3", "new": "changed"}},
                "same": {"B": "2"},
            },
        )

    def test_fixture_diff(self):
        a = envdiff.parse_env(fixture("sample.env"))
        b = envdiff.parse_env(fixture("sample2.env"))
        result = envdiff.diff_env(a, b)
        self.assertEqual(result["added"], {"NEW_FLAG": "enabled"})
        self.assertEqual(result["removed"], {"EMPTY_VALUE": ""})
        self.assertEqual(result["changed"], {"DEBUG": {"old": "true", "new": "false"}})
        self.assertEqual(
            result["same"],
            {"APP_NAME": "nios", "PORT": "8080", "API_KEY": "supersecretkey123"},
        )

    def test_identical_dicts(self):
        a = {"X": "1"}
        self.assertEqual(
            envdiff.diff_env(a, a),
            {"added": {}, "removed": {}, "changed": {}, "same": {"X": "1"}},
        )

    def test_empty_inputs(self):
        self.assertEqual(
            envdiff.diff_env({}, {}),
            {"added": {}, "removed": {}, "changed": {}, "same": {}},
        )

    def test_none_inputs(self):
        self.assertEqual(
            envdiff.diff_env(None, None),
            {"added": {}, "removed": {}, "changed": {}, "same": {}},
        )


@unittest.skipIf(envdiff is None, "dptlib.envdiff is not available yet")
class TestMaskValue(unittest.TestCase):
    def test_masks_long_value(self):
        value = "supersecretkey123"
        self.assertEqual(
            envdiff.mask_value(value),
            value[0] + "*" * (len(value) - 2) + value[-1],
        )

    def test_short_values(self):
        self.assertEqual(envdiff.mask_value(""), "")
        self.assertEqual(envdiff.mask_value("a"), "*")
        self.assertEqual(envdiff.mask_value("ab"), "**")

    def test_non_string_value(self):
        self.assertEqual(envdiff.mask_value(12345), "1***5")
