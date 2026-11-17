"""Unit tests for :mod:`dptlib.ports`."""

import os
import unittest

from _path import fixture

try:
    from dptlib import ports
except Exception:  # pragma: no cover - only while the sibling code lands
    ports = None


@unittest.skipIf(ports is None, "dptlib.ports is not available yet")
class TestValidPort(unittest.TestCase):
    def test_valid_integer_ports(self):
        for value in (1, 80, 443, 8080, 65535):
            with self.subTest(value=value):
                self.assertIs(ports.valid_port(value), True)

    def test_valid_numeric_strings(self):
        self.assertIs(ports.valid_port("8080"), True)
        self.assertIs(ports.valid_port(" 443 "), True)

    def test_out_of_range_ports(self):
        for value in (0, -1, 65536, 99999):
            with self.subTest(value=value):
                self.assertIs(ports.valid_port(value), False)

    def test_junk_and_wrong_types(self):
        for value in ("abc", "", "80.5", None, True, 80.0):
            with self.subTest(value=value):
                self.assertIs(ports.valid_port(value), False)

    def test_string_boundaries(self):
        self.assertIs(ports.valid_port("0"), False)
        self.assertIs(ports.valid_port("65536"), False)


@unittest.skipIf(ports is None, "dptlib.ports is not available yet")
class TestParseNetstat(unittest.TestCase):
    def test_parses_fixture(self):
        entries = ports.parse_netstat(fixture("netstat_windows.txt"))
        self.assertEqual(len(entries), 4)
        self.assertEqual(
            [(e["proto"], e["port"], e["pid"]) for e in entries],
            [("TCP", 80, 1234), ("TCP", 443, 5678), ("TCP", 5432, 9012), ("UDP", 53, 700)],
        )
        self.assertEqual(entries[0]["address"], "0.0.0.0")
        self.assertEqual(entries[0]["state"], "LISTENING")
        self.assertEqual(entries[2]["state"], "ESTABLISHED")
        self.assertEqual(entries[3]["state"], "")

    def test_uniform_record_shape(self):
        entry = ports.parse_netstat(fixture("netstat_windows.txt"))[0]
        expected_keys = {
            "proto", "protocol", "address", "local_address",
            "port", "state", "pid", "process",
        }
        self.assertTrue(expected_keys.issubset(entry))
        self.assertEqual(entry["protocol"], entry["proto"])
        self.assertEqual(entry["local_address"], entry["address"])

    def test_empty_text(self):
        self.assertEqual(ports.parse_netstat(""), [])

    def test_header_and_junk_lines_ignored(self):
        text = "Active Connections\n\n  Proto  Local  Foreign  State  PID\nrandom noise here\n"
        self.assertEqual(ports.parse_netstat(text), [])

    def test_bracketed_ipv6_endpoint(self):
        text = "  TCP    [::]:443   [::]:0   LISTENING   4242\n"
        entries = ports.parse_netstat(text)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["address"], "::")
        self.assertEqual(entries[0]["port"], 443)
        self.assertEqual(entries[0]["pid"], 4242)


@unittest.skipIf(ports is None, "dptlib.ports is not available yet")
class TestParseLsof(unittest.TestCase):
    def test_parses_fixture(self):
        entries = ports.parse_lsof(fixture("lsof_unix.txt"))
        self.assertEqual(len(entries), 2)
        first, second = entries
        self.assertEqual(first["process"], "python")
        self.assertEqual(first["pid"], 1234)
        self.assertEqual(first["proto"], "TCP")
        self.assertEqual((first["address"], first["port"]), ("*", 8000))
        self.assertEqual(first["state"], "LISTEN")
        self.assertEqual(second["process"], "nginx")
        self.assertEqual(second["pid"], 5678)
        self.assertEqual((second["address"], second["port"]), ("::", 80))

    def test_empty_text(self):
        self.assertEqual(ports.parse_lsof(""), [])

    def test_header_only(self):
        header = "COMMAND  PID  USER  FD  TYPE  DEVICE  SIZE/OFF  NODE  NAME\n"
        self.assertEqual(ports.parse_lsof(header), [])


@unittest.skipIf(ports is None, "dptlib.ports is not available yet")
class TestKillCommand(unittest.TestCase):
    def test_command_shape_is_platform_correct(self):
        cmd = ports.kill_command(4242)
        if os.name == "nt":
            self.assertEqual(cmd, ["taskkill", "/PID", "4242"])
            self.assertEqual(
                ports.kill_command(4242, force=True),
                ["taskkill", "/PID", "4242", "/F"],
            )
        else:
            self.assertEqual(cmd, ["kill", "4242"])
            self.assertEqual(ports.kill_command(4242, force=True), ["kill", "-9", "4242"])

    def test_force_appends_flag(self):
        normal = ports.kill_command(99)
        forced = ports.kill_command(99, force=True)
        self.assertEqual(len(forced), len(normal) + 1)
        self.assertIn("99", forced)

    def test_numeric_string_pid(self):
        self.assertIn("1234", ports.kill_command("1234"))

    def test_invalid_pids_raise(self):
        for value in (0, -5, "abc", None, True):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    ports.kill_command(value)


@unittest.skipIf(ports is None, "dptlib.ports is not available yet")
class TestSummarize(unittest.TestCase):
    def test_empty_summary(self):
        self.assertEqual(ports.summarize([]), "No listeners found.")

    def test_summary_header_line(self):
        entries = [
            {"proto": "TCP", "address": "0.0.0.0", "port": 80, "state": "LISTENING", "pid": 1, "process": None},
            {"proto": "TCP", "address": "0.0.0.0", "port": 443, "state": "LISTENING", "pid": 2, "process": None},
        ]
        summary = ports.summarize(entries)
        self.assertEqual(
            summary.splitlines()[0],
            "2 listener(s) across 2 process(es) [2 TCP]",
        )
        self.assertIn("0.0.0.0:80", summary)
