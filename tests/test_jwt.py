"""Unit tests for :mod:`dptlib.jwt` (decode-only helpers)."""

import datetime
import unittest

from _path import fixture

try:
    from dptlib import jwt
except Exception:  # pragma: no cover
    jwt = None

TOKEN = fixture("sample_jwt.txt", strip=True)
HEADER_SEG = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
PAYLOAD_SEG = (
    "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjk5OTk5OTk5OTl9"
)


@unittest.skipIf(jwt is None, "dptlib.jwt is not available yet")
class TestB64UrlDecode(unittest.TestCase):
    def test_decodes_known_segment(self):
        self.assertEqual(jwt.b64url_decode("SGVsbG8"), b"Hello")

    def test_decodes_url_safe_alphabet(self):
        self.assertEqual(jwt.b64url_decode("-_8"), bytes([0xFB, 0xFF]))

    def test_accepts_padding_and_bytes(self):
        self.assertEqual(jwt.b64url_decode("SGVsbG8="), b"Hello")
        self.assertEqual(jwt.b64url_decode(b"SGVsbG8"), b"Hello")

    def test_invalid_input_raises(self):
        with self.assertRaises(ValueError):
            jwt.b64url_decode("***not base64***")

    def test_wrong_type_raises(self):
        with self.assertRaises(ValueError):
            jwt.b64url_decode(123)


@unittest.skipIf(jwt is None, "dptlib.jwt is not available yet")
class TestDecode(unittest.TestCase):
    def test_decodes_fixture_token(self):
        result = jwt.decode(TOKEN)
        self.assertEqual(
            result["header"], {"alg": "HS256", "typ": "JWT"}
        )
        self.assertEqual(
            result["payload"],
            {
                "sub": "1234567890",
                "name": "John Doe",
                "iat": 1516239022,
                "exp": 9999999999,
            },
        )
        self.assertEqual(result["signature"], b"dev-signature")
        self.assertIs(result["is_expired"], False)

    def test_result_has_required_keys(self):
        result = jwt.decode(TOKEN)
        self.assertEqual(
            set(result), {"header", "payload", "signature", "is_expired"}
        )

    def test_two_segment_token_has_empty_signature(self):
        result = jwt.decode(f"{HEADER_SEG}.{PAYLOAD_SEG}")
        self.assertEqual(result["signature"], b"")
        self.assertEqual(result["payload"]["sub"], "1234567890")

    def test_malformed_segments_degrade(self):
        result = jwt.decode("notbase64.notbase64.bad")
        self.assertIsNone(result["header"])
        self.assertIsNone(result["payload"])
        self.assertIsNone(result["is_expired"])

    def test_invalid_token_raises(self):
        for bad in ("abc", 123, None):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    jwt.decode(bad)


@unittest.skipIf(jwt is None, "dptlib.jwt is not available yet")
class TestIsExpired(unittest.TestCase):
    def test_past_expiry(self):
        self.assertIs(jwt.is_expired({"exp": 1000}, now=2000), True)

    def test_future_expiry(self):
        self.assertIs(jwt.is_expired({"exp": 1000}, now=500), False)

    def test_boundary_is_expired(self):
        self.assertIs(jwt.is_expired({"exp": 1000}, now=1000), True)

    def test_missing_or_invalid_claim_is_none(self):
        self.assertIsNone(jwt.is_expired({}, now=1000))
        self.assertIsNone(jwt.is_expired({"exp": "later"}, now=1000))
        self.assertIsNone(jwt.is_expired(None, now=1000))

    def test_datetime_now(self):
        when = datetime.datetime(1970, 1, 1, 0, 16, 40, tzinfo=datetime.timezone.utc)
        self.assertIs(jwt.is_expired({"exp": 1000}, now=when), True)


@unittest.skipIf(jwt is None, "dptlib.jwt is not available yet")
class TestRedact(unittest.TestCase):
    def test_redacts_fixture_token(self):
        expected = f"{TOKEN[:6]}...{TOKEN[-6:]}"
        self.assertEqual(jwt.redact(TOKEN), expected)

    def test_full_signature_not_leaked(self):
        redacted = jwt.redact(TOKEN)
        self.assertNotIn("ZGV2LXNpZ25hdHVyZQ", redacted)
        self.assertLess(len(redacted), len(TOKEN))

    def test_short_token_fully_masked(self):
        self.assertEqual(jwt.redact("short"), "***")
        self.assertEqual(jwt.redact("123456789012"), "***")

    def test_non_string_is_masked(self):
        self.assertEqual(jwt.redact(None), "***")
