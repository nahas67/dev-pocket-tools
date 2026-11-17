"""Unit tests for :mod:`dptlib.dirsize`."""

import os
import unittest

from _path import FIXTURES_DIR, fixture_path

try:
    from dptlib import dirsize
except Exception:  # pragma: no cover
    dirsize = None


@unittest.skipIf(dirsize is None, "dptlib.dirsize is not available yet")
class TestHumanSize(unittest.TestCase):
    def test_bytes(self):
        self.assertEqual(dirsize.human_size(0), "0 B")
        self.assertEqual(dirsize.human_size(512), "512 B")

    def test_kilobytes_and_fractional(self):
        self.assertEqual(dirsize.human_size(1024), "1.0 KB")
        self.assertEqual(dirsize.human_size(1536), "1.5 KB")

    def test_larger_units(self):
        self.assertEqual(dirsize.human_size(1024 ** 2), "1.0 MB")
        self.assertEqual(dirsize.human_size(1024 ** 3), "1.0 GB")

    def test_negative(self):
        self.assertEqual(dirsize.human_size(-1024), "-1.0 KB")

    def test_non_numeric_passthrough(self):
        self.assertEqual(dirsize.human_size("unknown"), "unknown")


@unittest.skipIf(dirsize is None, "dptlib.dirsize is not available yet")
class TestCollectSizes(unittest.TestCase):
    def test_single_file(self):
        path = fixture_path("sample.json")
        result = dirsize.collect_sizes([path])
        self.assertEqual(len(result), 1)
        path_out, size, count = result[0]
        self.assertEqual(path_out, path)
        self.assertEqual(size, os.path.getsize(path))
        self.assertEqual(count, 1)

    def test_missing_path_is_zero(self):
        missing = os.path.join(FIXTURES_DIR, "__definitely_missing__")
        self.assertEqual(dirsize.collect_sizes([missing]), [(missing, 0, 0)])

    def test_directory_counts_files(self):
        result = dirsize.collect_sizes([FIXTURES_DIR])
        self.assertEqual(len(result), 1)
        _path, size, count = result[0]
        self.assertGreaterEqual(count, 8)
        self.assertGreater(size, 0)

    def test_empty_input(self):
        self.assertEqual(dirsize.collect_sizes([]), [])

    def test_order_preserved(self):
        paths = [fixture_path("sample.json"), fixture_path("sample.env")]
        self.assertEqual([r[0] for r in dirsize.collect_sizes(paths)], paths)


@unittest.skipIf(dirsize is None, "dptlib.dirsize is not available yet")
class TestFormatTable(unittest.TestCase):
    def test_empty_rows(self):
        self.assertEqual(dirsize.format_table([]), "No paths to report.")

    def test_header_and_separator(self):
        table = dirsize.format_table([("a.txt", 2048, 1)])
        lines = table.splitlines()
        self.assertIn("PATH", lines[0])
        self.assertIn("SIZE", lines[0])
        self.assertIn("FILES", lines[0])
        self.assertIn("---", lines[1])

    def test_humanizes_integer_size(self):
        table = dirsize.format_table([("big", 1024, 1)])
        self.assertIn("1.0 KB", table)

    def test_preformatted_string_size_kept(self):
        table = dirsize.format_table([("x", "1.5 GB")])
        self.assertIn("1.5 GB", table)
