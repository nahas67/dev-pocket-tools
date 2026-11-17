# jwt-decode cheatsheet

Decode a JSON Web Token's header and payload for debugging.

```
python tools/jwt-decode [token] [--redact] [--raw]
```

> **Decoding is not verification.** The tool never checks the signature, `iss`, `aud`, or any claim except reading `exp` for the EXPIRY line. Never use its output for authorization.

## Structure of a JWT

```
<header>.<payload>.<signature>
```

Each segment is Base64URL encoded (URL-safe `-` and `_`, padding often omitted). The tool decodes the first two and hex-encodes the signature for display.

## Example session

Using the bundled sample token:

```console
$ python tools/jwt-decode $(cat tests/fixtures/sample_jwt.txt)
HEADER:
{
  "alg": "HS256",
  "typ": "JWT"
}

PAYLOAD:
{
  "exp": 9999999999,
  "iat": 1516239022,
  "name": "John Doe",
  "sub": "1234567890"
}

SIGNATURE (hex): 6465762d7369676e6174757265
EXPIRY: valid

Note: signature was NOT verified.
```

The signature hex `6465762d...` decodes to the literal bytes `dev-signature` — a placeholder in the fixture, not a real signature.

## Options

| Option | Meaning |
| --- | --- |
| `token` | JWT string; if omitted, read from stdin |
| `--redact` | Print only `first6...last6` (or `***` for short tokens) |
| `--raw` | Print one JSON object: `header`, `payload`, `signature` (hex), `is_expired` |

```console
$ python tools/jwt-decode $(cat tests/fixtures/sample_jwt.txt) --redact
eyJhbG...dHVyZQ
```

## Header claims

| Claim | Meaning | Example |
| --- | --- | --- |
| `alg` | Signing algorithm | `HS256`, `RS256`, `ES256`, `none` |
| `typ` | Token type | `JWT` |
| `kid` | Which key signed it | `"key-2026-01"` |

## Registered payload claims

| Claim | Name | Meaning |
| --- | --- | --- |
| `iss` | Issuer | Who issued the token |
| `sub` | Subject | Usually a user ID |
| `aud` | Audience | Intended recipient(s) |
| `exp` | Expiration | Unix timestamp after which the token is invalid |
| `nbf` | Not before | Unix timestamp before which it is invalid |
| `iat` | Issued at | Unix timestamp of issuance |
| `jti` | JWT ID | Unique token identifier |

Numeric date claims are seconds since the Unix epoch — convert them with `python tools/epoch-convert <value>`.

## EXPIRY values

| Output | Meaning |
| --- | --- |
| `valid` | `now < exp` |
| `EXPIRED` | `now >= exp` |
| `unknown (no exp claim)` | No numeric `exp` claim, or it was not a number |

## Library equivalents

```python
from dptlib import jwt

result = jwt.decode(token)          # header / payload / signature / is_expired
jwt.is_expired(result["payload"], now=1_700_000_000)
safe = jwt.redact(token)
base64_bytes = jwt.b64url_decode("SGVsbG8")   # b"Hello"
```

## Safety notes

- A JWT is a **bearer credential**. Pasting a production token into a terminal, issue, or chat can expose it; use `--redact` when sharing.
- Malformed segments degrade to `null` in `--raw` output rather than failing; a token with fewer than two segments exits `1`.
- The `exp` check is informational and has no tolerance — a forged token can claim any expiry.
