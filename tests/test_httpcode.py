"""Unit tests for :mod:`dptlib.httpcode`."""

import unittest

try:
    from dptlib import httpcode
except Exception:  # pragma: no cover
    httpcode = None


@unittest.skipIf(httpcode is None, "dptlib.httpcode is not available yet")
class TestLookup(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(
            httpcode.lookup(200),
            {
                "code": 200,
                "title": "OK",
                "category": "Success",
                "description": "The request succeeded.",
            },
        )

    def test_client_and_server_errors(self):
        self.assertEqual(httpcode.lookup(404)["title"], "Not Found")
        self.assertEqual(httpcode.lookup(404)["category"], "Client Error")
        self.assertEqual(httpcode.lookup(500)["title"], "Internal Server Error")
        self.assertEqual(httpcode.lookup(500)["category"], "Server Error")

    def test_informational_and_redirect(self):
        self.assertEqual(httpcode.lookup(100)["category"], "Informational")
        self.assertEqual(httpcode.lookup(301)["category"], "Redirection")

    def test_numeric_string_accepted(self):
        self.assertEqual(httpcode.lookup("404"), httpcode.lookup(404))

    def test_unknown_and_invalid_return_none(self):
        for code in (99, 999, 99999, "abc", None, True):
            with self.subTest(code=code):
                self.assertIsNone(httpcode.lookup(code))


@unittest.skipIf(httpcode is None, "dptlib.httpcode is not available yet")
class TestCategories(unittest.TestCase):
    def test_exact_categories(self):
        self.assertEqual(
            httpcode.CATEGORIES,
            {
                1: "Informational",
                2: "Success",
                3: "Redirection",
                4: "Client Error",
                5: "Server Error",
            },
        )


@unittest.skipIf(httpcode is None, "dptlib.httpcode is not available yet")
class TestAllCodes(unittest.TestCase):
    def test_is_sorted_list_of_known_codes(self):
        codes = httpcode.all_codes()
        self.assertIsInstance(codes, list)
        self.assertEqual(codes, sorted(codes))
        for code in (100, 200, 301, 404, 500):
            with self.subTest(code=code):
                self.assertIn(code, codes)

    def test_all_codes_have_entries(self):
        for code in httpcode.all_codes():
            with self.subTest(code=code):
                self.assertIsNotNone(httpcode.lookup(code))
