"""Unit tests for :mod:`dptlib.jsonfmt`."""

import unittest

from _path import fixture

try:
    from dptlib import jsonfmt
except Exception:  # pragma: no cover
    jsonfmt = None


@unittest.skipIf(jsonfmt is None, "dptlib.jsonfmt is not available yet")
class TestFormatJson(unittest.TestCase):
    def test_default_indent(self):
        self.assertEqual(
            jsonfmt.format_json('{"a":1}'),
            '{\n  "a": 1\n}',
        )

    def test_sort_keys(self):
        self.assertEqual(
            jsonfmt.format_json('{"b":1,"a":2}', sort_keys=True),
            '{\n  "a": 2,\n  "b": 1\n}',
        )

    def test_custom_indent(self):
        self.assertEqual(
            jsonfmt.format_json('{"a":1}', indent=4),
            '{\n    "a": 1\n}',
        )

    def test_fixture_round_trips_through_stdlib(self):
        import json
        formatted = jsonfmt.format_json(fixture("sample.json"))
        self.assertEqual(json.loads(formatted), json.loads(fixture("sample.json")))

    def test_invalid_json_raises(self):
        with self.assertRaises(ValueError):
            jsonfmt.format_json("{not json}")


@unittest.skipIf(jsonfmt is None, "dptlib.jsonfmt is not available yet")
class TestMinify(unittest.TestCase):
    def test_minifies_whitespace(self):
        self.assertEqual(jsonfmt.minify('{\n  "a": 1\n}'), '{"a":1}')

    def test_minifies_nested(self):
        source = '{\n  "a": {\n    "b": [1, 2]\n  }\n}'
        self.assertEqual(jsonfmt.minify(source), '{"a":{"b":[1,2]}}')

    def test_invalid_json_raises(self):
        with self.assertRaises(ValueError):
            jsonfmt.minify("oops")


@unittest.skipIf(jsonfmt is None, "dptlib.jsonfmt is not available yet")
class TestFlatten(unittest.TestCase):
    def test_flattens_nested_dict_and_list(self):
        self.assertEqual(
            jsonfmt.flatten({"a": {"b": [1, 2]}}),
            {"a.b.0": 1, "a.b.1": 2},
        )

    def test_prefix(self):
        result = jsonfmt.flatten({"x": 1, "y": {"z": 2}}, prefix="root")
        self.assertEqual(result, {"root.x": 1, "root.y.z": 2})

    def test_empty_containers_are_leaves(self):
        self.assertEqual(
            jsonfmt.flatten({"empty": {}, "list": []}),
            {"empty": {}, "list": []},
        )

    def test_scalar_input(self):
        self.assertEqual(jsonfmt.flatten(5), {"": 5})
        self.assertEqual(jsonfmt.flatten("hi", prefix="p"), {"p": "hi"})

    def test_already_flat(self):
        self.assertEqual(jsonfmt.flatten({"a": 1, "b": 2}), {"a": 1, "b": 2})


@unittest.skipIf(jsonfmt is None, "dptlib.jsonfmt is not available yet")
class TestIsJson(unittest.TestCase):
    def test_valid_values(self):
        for text in ('{"a":1}', '[1,2,3]', '"hello"', '123', 'true', 'null'):
            with self.subTest(text=text):
                self.assertIs(jsonfmt.is_json(text), True)

    def test_invalid_values(self):
        for text in ("{bad", "", "not json", "{'a':1}"):
            with self.subTest(text=text):
                self.assertIs(jsonfmt.is_json(text), False)

    def test_non_string_is_false(self):
        self.assertIs(jsonfmt.is_json(123), False)
        self.assertIs(jsonfmt.is_json(None), False)
