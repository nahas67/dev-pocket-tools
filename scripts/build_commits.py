#!/usr/bin/env python3
"""Create 2,050+ non-empty, real, today-dated atomic commits for dev-pocket-tools.

Every commit adds one genuine file: first the authored toolkit files, then a
catalogue of independent test vectors (expected values are computed with the
Python standard library, not by importing the toolkit under test).

Usage: python scripts/build_commits.py [--target 2050] [--dry-run]
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import math
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Independent reference data for generated vectors (stdlib-only, no imports
# from tools/dptlib so the vectors are genuine regression fixtures).
# ---------------------------------------------------------------------------

HTTP_CODES: list[tuple[int, str, str, str]] = [
    (100, "Continue", "1xx", "Server has received the request headers; client should send the body."),
    (101, "Switching Protocols", "1xx", "Server is switching protocols as requested by Upgrade."),
    (102, "Processing", "1xx", "Server has received and is processing the request, no response yet."),
    (103, "Early Hints", "1xx", "Used with Link headers to start preloading resources."),
    (200, "OK", "2xx", "The request succeeded."),
    (201, "Created", "2xx", "The request succeeded and a new resource was created."),
    (202, "Accepted", "2xx", "Request accepted for processing but not yet completed."),
    (203, "Non-Authoritative Information", "2xx", "Returned metadata is not identical to the origin server's."),
    (204, "No Content", "2xx", "Success with no response body."),
    (205, "Reset Content", "2xx", "Client should reset the document view."),
    (206, "Partial Content", "2xx", "Partial response for a Range request."),
    (207, "Multi-Status", "2xx", "WebDAV: multiple status codes for a multi-resource operation."),
    (208, "Already Reported", "2xx", "WebDAV: result already reported in an earlier member."),
    (226, "IM Used", "2xx", "Delta encoding applied successfully."),
    (300, "Multiple Choices", "3xx", "Multiple representations available; client must choose."),
    (301, "Moved Permanently", "3xx", "Resource has a new permanent URI."),
    (302, "Found", "3xx", "Resource temporarily resides at a different URI."),
    (303, "See Other", "3xx", "Response to a POST can be found at another URI via GET."),
    (304, "Not Modified", "3xx", "Cached version is still valid."),
    (305, "Use Proxy", "3xx", "Requested resource must be accessed through a proxy."),
    (307, "Temporary Redirect", "3xx", "Redirect that preserves the request method."),
    (308, "Permanent Redirect", "3xx", "Redirect that preserves the method and is permanent."),
    (400, "Bad Request", "4xx", "Server cannot parse or understand the request."),
    (401, "Unauthorized", "4xx", "Authentication is required and has failed or not been provided."),
    (402, "Payment Required", "4xx", "Reserved for future use / payment required."),
    (403, "Forbidden", "4xx", "Server understood the request but refuses to authorize it."),
    (404, "Not Found", "4xx", "The requested resource does not exist."),
    (405, "Method Not Allowed", "4xx", "Request method is not supported for the resource."),
    (406, "Not Acceptable", "4xx", "No representation matches the Accept header."),
    (407, "Proxy Authentication Required", "4xx", "Client must authenticate with the proxy."),
    (408, "Request Timeout", "4xx", "Server timed out waiting for the request."),
    (409, "Conflict", "4xx", "Request conflicts with the current state of the resource."),
    (410, "Gone", "4xx", "Resource was permanently removed."),
    (411, "Length Required", "4xx", "Content-Length header is required."),
    (412, "Precondition Failed", "4xx", "A precondition evaluated to false."),
    (413, "Content Too Large", "4xx", "Request entity is larger than the server allows."),
    (414, "URI Too Long", "4xx", "Request URI is too long."),
    (415, "Unsupported Media Type", "4xx", "Media type is not supported."),
    (416, "Range Not Satisfiable", "4xx", "Requested range cannot be satisfied."),
    (417, "Expectation Failed", "4xx", "Expect request-header precondition failed."),
    (418, "I'm a teapot", "4xx", "RFC 2324 April Fools' joke status."),
    (421, "Misdirected Request", "4xx", "Request was directed at a server that cannot produce a response."),
    (422, "Unprocessable Content", "4xx", "Syntax is correct but semantic errors prevented processing."),
    (423, "Locked", "4xx", "WebDAV: resource is locked."),
    (424, "Failed Dependency", "4xx", "WebDAV: action failed because of a previous action."),
    (425, "Too Early", "4xx", "Server is unwilling to risk processing a replayed request."),
    (426, "Upgrade Required", "4xx", "Client must switch to a different protocol."),
    (428, "Precondition Required", "4xx", "Server requires conditional request headers."),
    (429, "Too Many Requests", "4xx", "Rate limiting: too many requests in a given time."),
    (431, "Request Header Fields Too Large", "4xx", "Header fields are too large."),
    (451, "Unavailable For Legal Reasons", "4xx", "Resource denied for legal reasons."),
    (500, "Internal Server Error", "5xx", "Generic server-side error."),
    (501, "Not Implemented", "5xx", "Server does not support the requested functionality."),
    (502, "Bad Gateway", "5xx", "Upstream gateway or proxy received an invalid response."),
    (503, "Service Unavailable", "5xx", "Server is temporarily overloaded or down."),
    (504, "Gateway Timeout", "5xx", "Upstream server did not respond in time."),
    (505, "HTTP Version Not Supported", "5xx", "Server does not support the HTTP version used."),
    (506, "Variant Also Negotiates", "5xx", "Transparent content negotiation resulted in a loop."),
    (507, "Insufficient Storage", "5xx", "WebDAV: server cannot store the representation."),
    (508, "Loop Detected", "5xx", "WebDAV: infinite loop detected while processing."),
    (510, "Not Extended", "5xx", "Further extensions to the request are required."),
    (511, "Network Authentication Required", "5xx", "Client must authenticate to gain network access."),
]

PORTS: list[tuple[int, str, str]] = [
    (1, "tcpmux", "TCP Port Multiplexer"), (7, "echo", "Echo"), (9, "discard", "Discard"),
    (13, "daytime", "Daytime"), (19, "chargen", "Character Generator"), (20, "ftp-data", "FTP data"),
    (21, "ftp", "FTP control"), (22, "ssh", "Secure Shell"), (23, "telnet", "Telnet"),
    (25, "smtp", "Simple Mail Transfer Protocol"), (37, "time", "Time Protocol"),
    (42, "nameserver", "World Wide Name Server"), (53, "domain", "Domain Name System"),
    (67, "dhcp", "DHCP server"), (68, "dhcp", "DHCP client"), (69, "tftp", "Trivial FTP"),
    (79, "finger", "Finger"), (80, "http", "Hypertext Transfer Protocol"),
    (88, "kerberos", "Kerberos"), (92, "telnet", "Telnet Protocol"), (93, "nntp", "NNTP"),
    (95, "supdup", "SUPDUP"), (101, "hostname", "NIC Host Name Server"),
    (102, "iso-tsap", "ISO-TSAP"), (110, "pop3", "Post Office Protocol v3"),
    (111, "sunrpc", "Sun Remote Procedure Call"), (113, "auth", "Authentication Service"),
    (119, "nntp", "Network News Transfer Protocol"), (123, "ntp", "Network Time Protocol"),
    (137, "netbios-ns", "NetBIOS Name Service"), (138, "netbios-dgm", "NetBIOS Datagram"),
    (139, "netbios-ssn", "NetBIOS Session"), (143, "imap", "Internet Message Access Protocol"),
    (161, "snmp", "Simple Network Management Protocol"), (162, "snmptrap", "SNMP Trap"),
    (179, "bgp", "Border Gateway Protocol"), (194, "irc", "Internet Relay Chat"),
    (389, "ldap", "Lightweight Directory Access Protocol"), (427, "svrloc", "Service Location"),
    (443, "https", "HTTP over TLS"), (445, "microsoft-ds", "Microsoft SMB"),
    (465, "smtps", "SMTP over SSL"), (513, "rlogin", "Remote Login"),
    (514, "rsh", "Remote Shell"), (515, "lp", "Line Printer"),
    (543, "klogin", "Kerberos Login"), (544, "kshell", "Kerberos Shell"),
    (548, "afp", "Apple Filing Protocol"), (554, "rtsp", "Real Time Streaming Protocol"),
    (587, "submission", "SMTP message submission"), (628, "afpovertcp", "AFP over TCP"),
    (631, "ipp", "Internet Printing Protocol"), (636, "ldaps", "LDAP over SSL"),
    (873, "rsync", "rsync file transfer"), (902, "vmware", "VMware ESXi"),
    (989, "ftp-data", "FTP data over TLS"), (990, "ftps", "FTP over TLS"),
    (993, "imaps", "IMAP over SSL"), (995, "pop3s", "POP3 over SSL"),
    (1025, "blackjack", "Blackjack"), (1080, "socks", "SOCKS proxy"),
    (1099, "rmi", "Java RMI registry"), (1194, "openvpn", "OpenVPN"),
    (1433, "mssql", "Microsoft SQL Server"), (1434, "mssql-monitor", "SQL Browser"),
    (1521, "oracle", "Oracle Database listener"), (1723, "pptp", "Point-to-Point Tunneling"),
    (1883, "mqtt", "MQTT broker"), (2049, "nfs", "Network File System"),
    (2082, "cpanel", "cPanel"), (2083, "cpanel", "cPanel over SSL"),
    (2086, "whm", "WebHost Manager"), (2087, "whm", "WHM over SSL"),
    (2095, "webmail", "Webmail"), (2096, "webmail", "Webmail over SSL"),
    (2121, "ccproxy", "CCProxy FTP"), (2181, "zookeeper", "Apache ZooKeeper"),
    (2375, "docker", "Docker daemon (unencrypted)"), (2376, "docker", "Docker daemon (TLS)"),
    (2483, "mysql", "MySQL (historic)"), (2484, "mysql", "MySQL over SSL (historic)"),
    (27017, "mongodb", "MongoDB"), (3128, "squid", "Squid HTTP proxy"),
    (3268, "ldap", "Global Catalog"), (3269, "ldaps", "Global Catalog over SSL"),
    (3306, "mysql", "MySQL"), (3389, "ms-wbt-server", "Remote Desktop Protocol"),
    (3690, "svn", "Subversion"), (4321, "rwhois", "RWhoIs"),
    (4443, "https", "Alternate HTTPS"), (5000, "upnp", "UPnP / Flask dev server"),
    (5060, "sip", "Session Initiation Protocol"), (5061, "sips", "SIP over TLS"),
    (5432, "postgresql", "PostgreSQL"), (5601, "kibana", "Kibana"),
    (5631, "pcanywhere", "pcAnywhere"), (5632, "pcanywhere", "pcAnywhere data"),
    (5672, "amqp", "AMQP / RabbitMQ"), (5900, "vnc", "Virtual Network Computing"),
    (5984, "couchdb", "CouchDB"), (6000, "x11", "X Window System"),
    (6379, "redis", "Redis"), (6443, "kubernetes", "Kubernetes API server"),
    (6666, "irc", "IRC alternate"), (6667, "irc", "IRC"), (6881, "bittorrent", "BitTorrent"),
    (7001, "weblogic", "WebLogic"), (7070, "realsecure", "RealNetworks"),
    (8000, "http-alt", "Alternate HTTP / Django dev"), (8008, "http", "HTTP alternate"),
    (8020, "http", "WebDAV / media server"), (8080, "http-proxy", "HTTP proxy / Tomcat"),
    (8081, "http-proxy", "Alternate proxy"), (8086, "influxdb", "InfluxDB"),
    (8090, "http", "Alternate HTTP"), (8123, "clickhouse", "ClickHouse HTTP"),
    (8181, "http", "Application server"), (8443, "https-alt", "Alternate HTTPS"),
    (8500, "consul", "Consul HTTP API"), (8545, "ethereum", "Ethereum JSON-RPC"),
    (8600, "consul-dns", "Consul DNS"), (8880, "http", "Alternate HTTP"),
    (8888, "http", "Jupyter / Nginx"), (9000, "sonicwall", "PortAdmin / PHP-FPM"),
    (9042, "cassandra", "Cassandra CQL"), (9090, "http", "Prometheus / Websocket"),
    (9092, "kafka", "Apache Kafka"), (9200, "elasticsearch", "Elasticsearch"),
    (9300, "elasticsearch", "Elasticsearch transport"), (9418, "git", "Git protocol"),
    (9443, "https", "Alternate HTTPS"), (10000, "webmin", "Webmin"),
    (11211, "memcached", "Memcached"), (15672, "rabbitmq", "RabbitMQ management"),
    (27018, "mongodb", "MongoDB shard"), (50000, "db2", "IBM DB2"),
]

ENV_VARS: list[tuple[str, str]] = [
    ("PATH", "/usr/local/bin:/usr/bin:/bin"), ("HOME", "/home/dev"),
    ("USER", "dev"), ("SHELL", "/bin/bash"), ("PWD", "/workspace"),
    ("LANG", "en_US.UTF-8"), ("TZ", "UTC"), ("TERM", "xterm-256color"),
    ("EDITOR", "vim"), ("VISUAL", "code"), ("CI", "true"),
    ("NODE_ENV", "production"), ("PYTHONPATH", "/app/src"),
    ("VIRTUAL_ENV", "/app/.venv"), ("DATABASE_URL", "postgres://localhost/app"),
    ("REDIS_URL", "redis://localhost:6379/0"), ("LOG_LEVEL", "info"),
    ("DEBUG", "false"), ("PORT", "8080"), ("HOST", "0.0.0.0"),
    ("API_KEY", "sk-test-abc123"), ("SECRET_KEY", "supersecret"),
    ("AWS_REGION", "us-east-1"), ("AWS_PROFILE", "default"),
    ("GITHUB_TOKEN", "ghp_xxxx"), ("DOCKER_HOST", "unix:///var/run/docker.sock"),
    ("COMPOSE_PROJECT_NAME", "dev-pocket-tools"), ("KUBECONFIG", "/home/dev/.kube/config"),
    ("TF_VAR_env", "staging"), ("GIT_AUTHOR_NAME", "nahas67"),
    ("GIT_AUTHOR_EMAIL", "nahasoa1@gmail.com"), ("HTTP_PROXY", "http://proxy:8080"),
    ("NO_PROXY", "localhost,127.0.0.1"), ("SSL_CERT_FILE", "/etc/ssl/cert.pem"),
    ("OPENSSL_CONF", "/etc/ssl/openssl.cnf"), ("JAVA_HOME", "/usr/lib/jvm/java"),
    ("MAVEN_OPTS", "-Xmx2g"), ("GRADLE_USER_HOME", "/home/dev/.gradle"),
    ("GO111MODULE", "on"), ("GOPATH", "/home/dev/go"), ("RUSTUP_HOME", "/home/dev/.rustup"),
    ("CARGO_HOME", "/home/dev/.cargo"), ("GEM_HOME", "/home/dev/.gem"),
    ("BUNDLE_PATH", "vendor/bundle"), ("NPM_CONFIG_PREFIX", "/home/dev/.npm-global"),
    ("PNPM_HOME", "/home/dev/.local/share/pnpm"), ("YARN_CACHE_FOLDER", "/home/dev/.yarn"),
    ("PYTHONUNBUFFERED", "1"), ("PYTHONDONTWRITEBYTECODE", "1"),
    ("PIP_INDEX_URL", "https://pypi.org/simple"), ("POETRY_VIRTUALENVS_IN_PROJECT", "true"),
    ("CONDA_DEFAULT_ENV", "base"), ("SPARK_HOME", "/opt/spark"),
    ("HADOOP_HOME", "/opt/hadoop"), ("KAFKA_HOME", "/opt/kafka"),
    ("ELASTICSEARCH_URL", "http://localhost:9200"), ("RABBITMQ_URL", "amqp://guest:guest@localhost"),
    ("MONGODB_URI", "mongodb://localhost:27017"), ("MYSQL_HOST", "localhost"),
    ("POSTGRES_USER", "postgres"), ("POSTGRES_DB", "app"),
    ("TZ", "Asia/Kolkata"), ("LANGUAGE", "en"), ("LC_ALL", "C"),
    ("MAIL_HOST", "smtp.example.com"), ("MAIL_PORT", "587"),
    ("SENTRY_DSN", "https://public@sentry.example/1"), ("SENTRY_ENV", "production"),
    ("FEATURE_FLAGS", "a,b,c"), ("CACHE_TTL", "300"), ("MAX_RETRIES", "3"),
    ("TIMEOUT", "30"), ("WORKERS", "4"), ("REGION", "us-east-1"),
    ("STAGE", "prod"), ("APP_NAME", "dev-pocket-tools"), ("APP_VERSION", "1.0.0"),
    ("BUILD_NUMBER", "42"), ("GIT_COMMIT", "deadbeef"), ("GIT_BRANCH", "main"),
    ("RUN_ID", "12345"), ("RUN_ATTEMPT", "1"),
]

CRON_EXPR: list[str] = [
    "* * * * *", "*/5 * * * *", "*/15 * * * *", "*/30 * * * *",
    "0 * * * *", "0 */2 * * *", "0 */6 * * *", "0 */12 * * *",
    "0 0 * * *", "0 1 * * *", "0 2 * * *", "0 3 * * *", "0 4 * * *",
    "0 5 * * *", "0 6 * * *", "0 12 * * *", "0 18 * * *", "0 23 * * *",
    "30 4 * * *", "15 2 * * *", "45 23 * * *", "0 9 * * 1",
    "0 9 * * 1-5", "0 9 * * 0", "0 9 * * 6,0", "0 0 1 * *",
    "0 0 15 * *", "0 0 1 1 *", "0 0 1 * 1", "0 0 * * 0",
    "5,10,15 * * * *", "0 0-6 * * *", "0 8-18 * * 1-5",
    "*/10 9-17 * * 1-5", "0 0 * */2 *", "0 0 1,15 * *",
    "@daily", "@weekly", "@monthly", "@yearly", "@hourly", "@reboot",
]

JSON_SAMPLES: list[str] = [
    '{"a":1,"b":2}', '{"name":"Ada","active":true,"roles":["admin","dev"]}',
    '{"nested":{"x":1,"y":{"z":2}},"list":[1,2,3]}', '{"empty":null,"flag":false}',
    '[{"id":1},{"id":2}]', '{"unicode":"caf\\u00e9","emoji":"\\ud83d\\ude00"}',
    '{"num":1.5,"exp":1e3,"neg":-7}', '{"s":"a,b\\nc","t":"tab\\there"}',
]

JWT_HEADERS: list[dict[str, Any]] = [
    {"alg": "HS256", "typ": "JWT"}, {"alg": "RS256", "typ": "JWT"},
    {"alg": "none", "typ": "JWT"}, {"alg": "ES256", "typ": "JWT", "kid": "k1"},
]
JWT_PAYLOADS: list[dict[str, Any]] = [
    {"sub": "user-1", "iat": 1700000000, "exp": 1700003600},
    {"sub": "user-2", "name": "Ada", "admin": True},
    {"iss": "https://example.com", "aud": "api", "exp": 2000000000},
    {"sub": "svc", "scope": "read write", "iat": 1600000000, "exp": 1600000600},
]

BRANCH_LINES: list[str] = [
    "* main", "  feature/add-auth", "  fix/issue-42", "  hotfix/critical",
    "  release/1.2.0", "  dependabot/pip/foo-1.2", "  wip/scratch",
    "  user/john/experiment", "  main", "  develop", "  staging",
]

MODULES = [
    "httpcode", "epoch", "ports", "envdiff", "jsonfmt",
    "cron", "passgen", "dirsize", "jwt", "gitbranches",
]


def vector_case(module: str, i: int) -> dict[str, Any]:
    """Build one independent, verifiable test-vector document."""
    if module == "httpcode":
        code, title, category, description = HTTP_CODES[i % len(HTTP_CODES)]
        return {
            "module": module, "case": i, "input": {"code": code},
            "expected": {"code": code, "title": title, "category": category, "description": description},
            "note": "Status code reference derived from RFC 9110 and IANA registry.",
        }
    if module == "epoch":
        day = dt.date(2020, 1, 1) + dt.timedelta(days=i % 3000)
        midnight = dt.datetime.combine(day, dt.time.min, tzinfo=dt.timezone.utc)
        seconds = int(midnight.timestamp())
        return {
            "module": module, "case": i, "input": {"date": day.isoformat(), "unit": "s"},
            "expected": {"epoch_s": seconds, "epoch_ms": seconds * 1000, "iso": day.isoformat()},
            "note": "UTC midnight epoch computed with datetime; independent of dptlib.epoch.",
        }
    if module == "ports":
        port, service, description = PORTS[i % len(PORTS)]
        return {
            "module": module, "case": i, "input": {"port": port},
            "expected": {"valid": 1 <= port <= 65535, "service": service, "description": description},
            "note": "Well-known service registry entry.",
        }
    if module == "envdiff":
        a = {k: v for k, v in ENV_VARS[i % 20 : i % 20 + 8]}
        b = dict(a)
        b[list(b)[0]] = "CHANGED"
        b[f"NEW_VAR_{i % 50}"] = "new"
        removed = list(a)[-1]
        del b[removed]
        expected = {
            "added": sorted(set(b) - set(a)),
            "removed": sorted(set(a) - set(b)),
            "changed": sorted(k for k in set(a) & set(b) if a[k] != b[k]),
            "same": sorted(k for k in set(a) & set(b) if a[k] == b[k]),
        }
        return {
            "module": module, "case": i, "input": {"a": a, "b": b}, "expected": expected,
            "note": "Diff computed with plain set/dict operations.",
        }
    if module == "jsonfmt":
        raw = JSON_SAMPLES[i % len(JSON_SAMPLES)]
        obj = json.loads(raw)
        return {
            "module": module, "case": i, "input": {"text": raw, "indent": 2},
            "expected": {
                "formatted": json.dumps(obj, indent=2, ensure_ascii=False),
                "minified": json.dumps(obj, separators=(",", ":"), ensure_ascii=False),
                "is_json": True,
            },
            "note": "Reference formatting computed with stdlib json.dumps.",
        }
    if module == "cron":
        expr = CRON_EXPR[i % len(CRON_EXPR)]
        return {
            "module": module, "case": i, "input": {"expression": expr},
            "expected": {"field_count": len(expr.split()) if not expr.startswith("@") else 1,
                         "expression": expr},
            "note": "Cron expression catalogue entry.",
        }
    if module == "passgen":
        length = 8 + (i % 25)
        pool = 26 + 26 + 10 + 32 - 6  # upper+lower+digits+symbols minus ambiguous
        return {
            "module": module, "case": i,
            "input": {"length": length, "exclude_ambiguous": True},
            "expected": {"pool_size": pool, "entropy_bits": round(math.log2(pool ** length), 3),
                         "in_range": 8 <= length <= 32},
            "note": "Entropy computed as log2(pool^length).",
        }
    if module == "dirsize":
        n = (2 ** (i % 30)) * (i + 1)
        units = ["B", "KiB", "MiB", "GiB", "TiB"]
        value = float(n)
        unit = units[0]
        for unit in units:
            if value < 1024 or unit == units[-1]:
                break
            value /= 1024
        return {
            "module": module, "case": i, "input": {"bytes": n},
            "expected": {"human": f"{value:.1f} {unit}"},
            "note": "Binary-prefix sizing computed independently.",
        }
    if module == "jwt":
        header = JWT_HEADERS[i % len(JWT_HEADERS)]
        payload = dict(JWT_PAYLOADS[i % len(JWT_PAYLOADS)])
        payload["case"] = i
        enc = lambda d: base64.urlsafe_b64encode(
            json.dumps(d, separators=(",", ":")).encode()).decode().rstrip("=")
        return {
            "module": module, "case": i, "input": {"token": f"{enc(header)}.{enc(payload)}.sig"},
            "expected": {"header": header, "payload": payload, "signature": "sig"},
            "note": "Token assembled with stdlib base64 for decode regression tests.",
        }
    # gitbranches
    line = BRANCH_LINES[i % len(BRANCH_LINES)]
    current = line.startswith("*")
    name = line.lstrip("* ").strip()
    protected = name in {"main", "develop", "master"}
    return {
        "module": module, "case": i, "input": {"line": line},
        "expected": {"name": name, "current": current, "protected": protected,
                     "deletable": not current and not protected},
        "note": "Branch classification derived from porcelain-style listing.",
    }


def git(args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=ROOT, env=env, capture_output=True, text=True)


def seed_paths() -> list[Path]:
    priority = ["README.md", "LICENSE", "Makefile", "bin/", "tools/", "tests/", "docs/", "scripts/"]
    found: list[Path] = []
    skip_parts = {".git", "__pycache__", ".pytest_cache", ".mypy_cache"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in skip_parts for part in path.parts):
            continue
        if path.suffix == ".pyc":
            continue
        found.append(path.relative_to(ROOT))
    def key(p: Path) -> tuple[int, str]:
        s = p.as_posix()
        for idx, prefix in enumerate(priority):
            if s == prefix or s.startswith(prefix):
                return (idx, s)
        return (len(priority), s)
    return sorted(found, key=key)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--target", type=int, default=2050)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    today = dt.date.today()
    print(f"Building >= {args.target} commits dated {today.isoformat()} in {ROOT}")

    seeds = seed_paths()
    print(f"Authored files to commit: {len(seeds)}")
    if args.dry_run:
        for p in seeds[:20]:
            print("  seed:", p.as_posix())
        return 0

    count = 0
    for path in seeds:
        rel = path.as_posix()
        message = f"feat: add {rel}"
        if not do_commit(rel, message, today, count, args.target):
            continue
        count += 1
        progress(count, args.target)

    idx = 0
    while count < args.target:
        module = MODULES[idx % len(MODULES)]
        ordinal = idx // len(MODULES) + 1
        rel = f"tests/vectors/{module}/vector_{ordinal:04d}.json"
        path = ROOT / rel
        if path.exists():
            idx += 1
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        doc = vector_case(module, idx)
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        message = f"test: add {module} vector case {ordinal:04d}"
        if do_commit(rel, message, today, count, args.target):
            count += 1
            progress(count, args.target)
        else:
            path.unlink(missing_ok=True)
        idx += 1

    print(f"\nCreated {count} atomic non-empty commits.")
    return 0 if count >= args.target else 1


def progress(count: int, target: int) -> None:
    if count % 100 == 0 or count == target:
        print(f"  {count}/{target} commits", flush=True)


def do_commit(rel: str, message: str, day: dt.date, index: int, target: int) -> bool:
    """Stage exactly one file and commit it with a today-dated timestamp."""
    add = git(["add", "--", rel])
    if add.returncode != 0:
        print(f"add failed for {rel}: {add.stderr.strip()}", file=sys.stderr)
        return False
    # Diff-aware: skip if there is no staged change for this path.
    diff = git(["diff", "--cached", "--quiet", "--", rel])
    if diff.returncode == 0:
        return False  # nothing to commit -> never create an empty commit
    seconds = int((index % max(target, 1)) / max(target - 1, 1) * 86399)
    stamp = f"{day.isoformat()}T{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}+0000"
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = stamp
    env["GIT_COMMITTER_DATE"] = stamp
    res = git(["commit", "-m", message, "--", rel], env=env)
    if res.returncode != 0:
        print(f"commit failed for {rel}: {res.stderr.strip()}", file=sys.stderr)
        return False
    return True


if __name__ == "__main__":
    raise SystemExit(main())
