"""Unit tests for :mod:`dptlib.passgen`."""

import math
import string
import unittest

try:
    from dptlib import passgen
except Exception:  # pragma: no cover
    passgen = None


@unittest.skipIf(passgen is None, "dptlib.passgen is not available yet")
class TestGenerate(unittest.TestCase):
    def test_default_length(self):
        self.assertEqual(len(passgen.generate()), 16)

    def test_requested_length(self):
        for length in (1, 8, 32, 64):
            with self.subTest(length=length):
                self.assertEqual(len(passgen.generate(length)), length)

    def test_digits_only(self):
        value = passgen.generate(
            32, use_upper=False, use_lower=False, use_digits=True,
            use_symbols=False, exclude_ambiguous=False,
        )
        self.assertTrue(set(value).issubset(set(string.digits)))
        self.assertEqual(len(value), 32)

    def test_single_class_guarantee(self):
        value = passgen.generate(
            20, use_upper=True, use_lower=False, use_digits=False, use_symbols=False
        )
        self.assertTrue(set(value).issubset(set(string.ascii_uppercase)))

    def test_ambiguous_excluded_when_requested(self):
        ambiguous = set(passgen.AMBIGUOUS)
        for _ in range(20):
            value = passgen.generate(
                48, use_upper=False, use_lower=False, use_digits=True,
                use_symbols=False, exclude_ambiguous=True,
            )
            self.assertFalse(set(value) & ambiguous)
            self.assertNotIn("0", value)
            self.assertNotIn("1", value)

    def test_invalid_length_and_no_classes_raise(self):
        for length in (0, -1):
            with self.subTest(length=length):
                with self.assertRaises(ValueError):
                    passgen.generate(length)
        with self.assertRaises(ValueError):
            passgen.generate(
                16, use_upper=False, use_lower=False, use_digits=False, use_symbols=False
            )

    def test_output_is_random(self):
        self.assertNotEqual(passgen.generate(32), passgen.generate(32))


@unittest.skipIf(passgen is None, "dptlib.passgen is not available yet")
class TestEstimateEntropy(unittest.TestCase):
    def test_known_formula(self):
        self.assertAlmostEqual(passgen.estimate_entropy(16, 94), 16 * math.log2(94))

    def test_binary_pool(self):
        self.assertEqual(passgen.estimate_entropy(10, 2), 10.0)

    def test_degenerate_pools(self):
        self.assertEqual(passgen.estimate_entropy(10, 1), 0.0)
        self.assertEqual(passgen.estimate_entropy(0, 94), 0.0)
        self.assertEqual(passgen.estimate_entropy(-5, 94), 0.0)

    def test_bool_inputs_are_zero(self):
        self.assertEqual(passgen.estimate_entropy(True, 94), 0.0)
        self.assertEqual(passgen.estimate_entropy(10, True), 0.0)

    def test_result_is_float(self):
        self.assertIsInstance(passgen.estimate_entropy(8, 64), float)
