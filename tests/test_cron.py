"""Unit tests for :mod:`dptlib.cron`."""

import unittest

from _path import fixture

try:
    from dptlib import cron
except Exception:  # pragma: no cover
    cron = None


@unittest.skipIf(cron is None, "dptlib.cron is not available yet")
class TestParseField(unittest.TestCase):
    def test_wildcard(self):
        self.assertEqual(cron.parse_field("*", 0, 59), list(range(60)))
        self.assertEqual(cron.parse_field("*", 1, 12), list(range(1, 13)))

    def test_single_value(self):
        self.assertEqual(cron.parse_field("5", 0, 59), [5])

    def test_inclusive_range(self):
        self.assertEqual(cron.parse_field("1-5", 0, 59), [1, 2, 3, 4, 5])

    def test_step_values(self):
        self.assertEqual(cron.parse_field("*/15", 0, 59), [0, 15, 30, 45])
        self.assertEqual(cron.parse_field("1-6/2", 0, 59), [1, 3, 5])

    def test_comma_list_and_from_step(self):
        self.assertEqual(cron.parse_field("0,10,20", 0, 59), [0, 10, 20])
        self.assertEqual(cron.parse_field("5/10", 0, 59), [5, 15, 25, 35, 45, 55])

    def test_invalid_fields_raise(self):
        for field in ("", "abc", "60", "5-3", "*/0", "1,,2", "-1"):
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    cron.parse_field(field, 0, 59)


@unittest.skipIf(cron is None, "dptlib.cron is not available yet")
class TestDescribe(unittest.TestCase):
    def test_every_five_minutes(self):
        result = cron.describe("*/5 * * * *")
        self.assertEqual(result["expression"], "*/5 * * * *")
        self.assertEqual(result["minute"], list(range(0, 60, 5)))
        self.assertEqual(result["hour"], list(range(24)))
        self.assertEqual(result["day_of_month"], list(range(1, 32)))
        self.assertEqual(result["month"], list(range(1, 13)))
        self.assertEqual(result["day_of_week"], list(range(8)))

    def test_weekday_expression(self):
        result = cron.describe("0 9 * * 1-5")
        self.assertEqual(result["minute"], [0])
        self.assertEqual(result["hour"], [9])
        self.assertEqual(result["day_of_week"], [1, 2, 3, 4, 5])

    def test_month_and_weekday_names(self):
        result = cron.describe("0 0 * JAN MON")
        self.assertEqual(result["month"], [1])
        self.assertEqual(result["day_of_week"], [1])

    def test_wrong_field_count_raises(self):
        with self.assertRaises(ValueError):
            cron.describe("* * * *")
        with self.assertRaises(ValueError):
            cron.describe("* * * * * *")

    def test_non_string_raises(self):
        with self.assertRaises(ValueError):
            cron.describe(None)


@unittest.skipIf(cron is None, "dptlib.cron is not available yet")
class TestExplain(unittest.TestCase):
    def test_first_line_echoes_expression(self):
        explanation = cron.explain("*/5 * * * *")
        self.assertEqual(explanation.splitlines()[0], "Cron: */5 * * * *")

    def test_contains_field_labels(self):
        explanation = cron.explain("0 9 * * 1-5")
        for label in ("minute", "hour", "day_of_month", "month", "day_of_week"):
            with self.subTest(label=label):
                self.assertIn(label, explanation)

    def test_fixture_expressions_all_explainable(self):
        for line in fixture("cron_expressions.txt").splitlines():
            with self.subTest(expression=line):
                self.assertIsInstance(cron.explain(line), str)

    def test_invalid_expression_raises(self):
        with self.assertRaises(ValueError):
            cron.explain("not a cron expression")
