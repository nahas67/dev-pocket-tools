"""Unit tests for :mod:`dptlib.epoch`."""

import time
import unittest

try:
    from dptlib import epoch
except Exception:  # pragma: no cover
    epoch = None


@unittest.skipIf(epoch is None, "dptlib.epoch is not available yet")
class TestToDatetime(unittest.TestCase):
    def test_epoch_zero(self):
        self.assertEqual(epoch.to_datetime(0), "1970-01-01T00:00:00Z")

    def test_milliseconds(self):
        self.assertEqual(
            epoch.to_datetime(1700000000000, unit="ms"),
            "2023-11-14T22:13:20Z",
        )

    def test_unit_aliases_and_numeric_string(self):
        self.assertEqual(epoch.to_datetime("0", unit="milliseconds"), "1970-01-01T00:00:00Z")
        self.assertEqual(epoch.to_datetime(1_000_000, unit="us"), "1970-01-01T00:00:01Z")

    def test_invalid_unit_and_value(self):
        with self.assertRaises(ValueError):
            epoch.to_datetime(0, unit="fortnights")
        with self.assertRaises(ValueError):
            epoch.to_datetime("not-a-number")
        with self.assertRaises(ValueError):
            epoch.to_datetime(True)


@unittest.skipIf(epoch is None, "dptlib.epoch is not available yet")
class TestFromDatetime(unittest.TestCase):
    def test_iso_with_z(self):
        self.assertEqual(epoch.from_datetime("1970-01-01T00:00:00Z"), 0)
        self.assertEqual(epoch.from_datetime("2023-11-14T22:13:20Z"), 1700000000)

    def test_common_formats_are_utc(self):
        self.assertEqual(epoch.from_datetime("1970-01-01 00:00:00"), 0)
        self.assertEqual(epoch.from_datetime("1970-01-01"), 0)

    def test_round_trip(self):
        for ts in (0, 1, 1516239022, 1700000000):
            with self.subTest(ts=ts):
                self.assertEqual(epoch.from_datetime(epoch.to_datetime(ts)), ts)

    def test_invalid_input(self):
        for text in ("", "not a date", None, 123):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    epoch.from_datetime(text)


@unittest.skipIf(epoch is None, "dptlib.epoch is not available yet")
class TestHumanize(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(epoch.humanize(0), "0s")

    def test_single_units(self):
        self.assertEqual(epoch.humanize(60), "1m")
        self.assertEqual(epoch.humanize(3600), "1h")
        self.assertEqual(epoch.humanize(86400), "1d")

    def test_compound_and_fractional(self):
        self.assertEqual(epoch.humanize(90), "1m 30s")
        self.assertEqual(epoch.humanize(90061), "1d 1h 1m 1s")
        self.assertEqual(epoch.humanize(1.5), "1s 500ms")
        self.assertEqual(epoch.humanize(0.25), "250ms")

    def test_negative(self):
        self.assertEqual(epoch.humanize(-90), "-1m 30s")

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            epoch.humanize(True)
        with self.assertRaises(ValueError):
            epoch.humanize("abc")


@unittest.skipIf(epoch is None, "dptlib.epoch is not available yet")
class TestNowMs(unittest.TestCase):
    def test_is_int_close_to_wall_clock(self):
        result = epoch.now_ms()
        self.assertIsInstance(result, int)
        self.assertLess(abs(result - int(time.time() * 1000)), 5000)
