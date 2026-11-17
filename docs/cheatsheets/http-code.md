# http-code cheatsheet

Look up HTTP status codes — no network access, just a built-in table.

```
python tools/http-code <code> [code ...]
python tools/http-code --list
```

With no arguments, `--list` behavior is used automatically.

## Status code classes

The module groups codes by their first digit (`dptlib.httpcode.CATEGORIES`):

| Range | Category |
| --- | --- |
| `1xx` | Informational |
| `2xx` | Success |
| `3xx` | Redirection |
| `4xx` | Client Error |
| `5xx` | Server Error |

## Example session

```console
$ python tools/http-code 404
404 Not Found [Client Error]
  The requested resource could not be found.

$ python tools/http-code 429
429 Too Many Requests [Client Error]
  The client has sent too many requests in a given amount of time.

$ python tools/http-code 200
200 OK [Success]
  The request succeeded.

$ python tools/http-code 200 404       # several codes at once
200 OK [Success]
  The request succeeded.
404 Not Found [Client Error]
  The requested resource could not be found.

$ python tools/http-code --list        # code  title  category, one per line
100  Continue                         Informational
101  Switching Protocols              Informational
102  Processing                       Informational
...
```

## Common status codes

| Code | Title | Notes |
| --- | --- | --- |
| `100` | Continue | Send the request body |
| `101` | Switching Protocols | Protocol upgrade |
| `200` | OK | Standard success |
| `201` | Created | New resource; see `Location` |
| `202` | Accepted | Accepted for async processing |
| `204` | No Content | Success, empty body |
| `206` | Partial Content | Range request response |
| `301` | Moved Permanently | New permanent URI |
| `302` | Found | Temporary redirect |
| `304` | Not Modified | Cached copy is valid |
| `307` | Temporary Redirect | Redirect preserving method |
| `308` | Permanent Redirect | Redirect preserving method |
| `400` | Bad Request | Malformed request |
| `401` | Unauthorized | Authentication required |
| `403` | Forbidden | Not permitted |
| `404` | Not Found | Resource does not exist |
| `405` | Method Not Allowed | Verb unsupported |
| `408` | Request Timeout | Client took too long |
| `409` | Conflict | State conflict |
| `410` | Gone | Permanently removed |
| `413` | Payload Too Large | Body too big |
| `415` | Unsupported Media Type | Bad `Content-Type` |
| `418` | I'm a Teapot | April Fools' RFC 2324 |
| `422` | Unprocessable Entity | Semantic validation failed |
| `429` | Too Many Requests | Rate limited; see `Retry-After` |
| `500` | Internal Server Error | Unexpected server failure |
| `501` | Not Implemented | Functionality unsupported |
| `502` | Bad Gateway | Invalid upstream response |
| `503` | Service Unavailable | Overload / maintenance |
| `504` | Gateway Timeout | Upstream timed out |

The table also includes less common codes such as `102`, `103`, `207`, `208`, `226`, `402`, `406`, `407`, `411`, `412`, `414`, `416`, `417`, `421`, `423`–`426`, `428`, `431`, `451`, and `505`–`511`.

## Library equivalents

```python
from dptlib import httpcode

status = httpcode.lookup(404)
# {'code': 404, 'title': 'Not Found', 'category': 'Client Error',
#  'description': 'The requested resource could not be found.'}

print(httpcode.lookup("200")["title"])   # decimal strings work too
print(httpcode.lookup(999))              # None
codes = httpcode.all_codes()             # sorted list of known codes
```

`lookup` returns `None` for unknown or invalid values; the CLI exits `1` in that case.

## Gotchas

- Codes are looked up as integers (decimal strings are accepted); names like `"not found"` are not supported.
- The table covers standard registry codes, not vendor-specific extensions (e.g. Cloudflare's `520`–`527`).
- Descriptions are short summaries, not full RFC text.
