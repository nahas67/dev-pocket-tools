"""HTTP status code lookup with descriptions.

Pure data + lookup helpers: no network access and no third-party packages.
"""

from __future__ import annotations

from typing import Any

CATEGORIES: dict[int, str] = {
    1: "Informational",
    2: "Success",
    3: "Redirection",
    4: "Client Error",
    5: "Server Error",
}

# code -> (title, description)
_CODES: dict[int, tuple[str, str]] = {
    100: ("Continue", "The server has received the request headers and the client should proceed to send the request body."),
    101: ("Switching Protocols", "The requester has asked the server to switch protocols and the server has agreed."),
    102: ("Processing", "The server has received and is processing the request, but no response is available yet."),
    103: ("Early Hints", "Used to return some response headers before the final HTTP message."),
    200: ("OK", "The request succeeded."),
    201: ("Created", "The request succeeded and a new resource was created."),
    202: ("Accepted", "The request was accepted for processing but has not been completed."),
    203: ("Non-Authoritative Information", "The returned metadata is not exactly the same as that available from the origin server."),
    204: ("No Content", "The request succeeded but there is no content to send in the response."),
    205: ("Reset Content", "The server wants the client to reset the document view."),
    206: ("Partial Content", "The server is delivering only part of the resource due to a Range header."),
    207: ("Multi-Status", "The message body contains multiple status codes for a multi-resource operation."),
    208: ("Already Reported", "The members of a DAV binding have already been enumerated."),
    226: ("IM Used", "The server has fulfilled a GET request and the response is a representation of a modified instance."),
    300: ("Multiple Choices", "There are multiple possible responses; the client must choose one."),
    301: ("Moved Permanently", "The requested resource has been assigned a new permanent URI."),
    302: ("Found", "The requested resource resides temporarily under a different URI."),
    303: ("See Other", "The response to the request can be found under a different URI."),
    304: ("Not Modified", "The resource has not been modified since the version specified by the client."),
    305: ("Use Proxy", "The requested resource is available only through a proxy."),
    307: ("Temporary Redirect", "The request should be repeated with another URI without changing the method."),
    308: ("Permanent Redirect", "The request should be repeated with another URI and future requests should use the new URI."),
    400: ("Bad Request", "The server cannot process the request due to a client error."),
    401: ("Unauthorized", "The request requires user authentication."),
    402: ("Payment Required", "Reserved for future use, often for digital payment schemes."),
    403: ("Forbidden", "The server understood the request but refuses to authorize it."),
    404: ("Not Found", "The requested resource could not be found."),
    405: ("Method Not Allowed", "The request method is not supported for the requested resource."),
    406: ("Not Acceptable", "The server cannot produce a response matching the client's Accept headers."),
    407: ("Proxy Authentication Required", "The client must authenticate with a proxy first."),
    408: ("Request Timeout", "The server timed out waiting for the request."),
    409: ("Conflict", "The request conflicts with the current state of the resource."),
    410: ("Gone", "The requested resource is no longer available and will not be available again."),
    411: ("Length Required", "The request did not specify the length of its content."),
    412: ("Precondition Failed", "One of the request's preconditions evaluated to false."),
    413: ("Payload Too Large", "The request is larger than the server is willing to process."),
    414: ("URI Too Long", "The URI provided was too long for the server to process."),
    415: ("Unsupported Media Type", "The request entity has an unsupported media type."),
    416: ("Range Not Satisfiable", "The client asked for a range that the server cannot supply."),
    417: ("Expectation Failed", "The server cannot meet the requirements of the Expect header."),
    418: ("I'm a Teapot", "Apr 1 joke RFC: the server refuses to brew coffee because it is a teapot."),
    421: ("Misdirected Request", "The request was directed at a server that cannot produce a response."),
    422: ("Unprocessable Entity", "The request was well-formed but could not be followed due to semantic errors."),
    423: ("Locked", "The resource that is being accessed is locked."),
    424: ("Failed Dependency", "The request failed because of a failure of a previous request."),
    425: ("Too Early", "The server is unwilling to process a request that might be replayed."),
    426: ("Upgrade Required", "The client should switch to a different protocol."),
    428: ("Precondition Required", "The server requires the request to be conditional."),
    429: ("Too Many Requests", "The client has sent too many requests in a given amount of time."),
    431: ("Request Header Fields Too Large", "The server is unwilling to process the request because its headers are too large."),
    451: ("Unavailable For Legal Reasons", "The resource is unavailable due to a legal demand."),
    500: ("Internal Server Error", "The server encountered an unexpected condition and could not fulfill the request."),
    501: ("Not Implemented", "The server does not support the functionality required to fulfill the request."),
    502: ("Bad Gateway", "The server received an invalid response from an upstream server."),
    503: ("Service Unavailable", "The server is currently unavailable, usually due to overload or maintenance."),
    504: ("Gateway Timeout", "The server did not receive a timely response from an upstream server."),
    505: ("HTTP Version Not Supported", "The server does not support the HTTP version used in the request."),
    506: ("Variant Also Negotiates", "The server has an internal configuration error."),
    507: ("Insufficient Storage", "The server is unable to store the representation needed to complete the request."),
    508: ("Loop Detected", "The server detected an infinite loop while processing the request."),
    510: ("Not Extended", "Further extensions to the request are required for the server to fulfill it."),
    511: ("Network Authentication Required", "The client needs to authenticate to gain network access."),
}


def lookup(code: object) -> dict[str, Any] | None:
    """Look up an HTTP status *code*.

    Accepts an ``int`` or a decimal string.  Returns a dictionary with keys
    ``code`` (int), ``title``, ``category`` (e.g. ``"Client Error"``) and
    ``description``, or ``None`` when the code is unknown.
    """
    if isinstance(code, bool):
        return None
    try:
        code_int = int(code)
    except (TypeError, ValueError):
        return None
    entry = _CODES.get(code_int)
    if entry is None:
        return None
    title, description = entry
    category = CATEGORIES.get(code_int // 100, "Unknown")
    return {
        "code": code_int,
        "title": title,
        "category": category,
        "description": description,
    }


def all_codes() -> list[int]:
    """Return a sorted list of every status code known to this module."""
    return sorted(_CODES)
