from __future__ import annotations

import json
import socket
import tempfile
import threading
import unittest
from pathlib import Path

from egress_broker import EgressBroker, normalize_allowlist

TEMP_ROOT = Path(__file__).resolve().parents[1]


def read_header(sock: socket.socket) -> bytes:
    data = bytearray()
    while not data.endswith(b"\r\n\r\n"):
        chunk = sock.recv(1)
        if not chunk:
            break
        data.extend(chunk)
        if len(data) > 2048:
            raise AssertionError("response header exceeded fixture limit")
    return bytes(data)


class EgressBrokerTests(unittest.TestCase):
    def test_allowlist_is_exact_and_rejects_wildcards(self):
        self.assertEqual(
            normalize_allowlist(["API.OpenAI.com:443"]),
            frozenset({("api.openai.com", 443)}),
        )
        for value in ("*:443", "api.openai.com:*", "api.openai.com:0", "api..openai.com:443"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_allowlist([value])

    def test_deny_first_records_attempt_without_forwarding(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temp_dir:
            event_log = Path(temp_dir) / "events.jsonl"
            connector_calls: list[tuple[str, int]] = []

            def forbidden_connector(host, port):
                connector_calls.append((host, port))
                raise AssertionError("deny-first broker attempted upstream forwarding")

            broker = EgressBroker(
                event_log=event_log,
                connector=forbidden_connector,
            ).start()
            try:
                with socket.create_connection(broker.address, timeout=2) as client:
                    client.sendall(
                        b"CONNECT api.openai.com:443 HTTP/1.1\r\n"
                        b"Proxy-Authorization: Basic synthetic-secret-marker\r\n"
                        b"Host: api.openai.com:443\r\n\r\n"
                    )
                    response = read_header(client)
                self.assertTrue(response.startswith(b"HTTP/1.1 403"))
            finally:
                broker.stop()

            self.assertEqual(connector_calls, [])
            events = [json.loads(line) for line in event_log.read_text().splitlines()]
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["host"], "api.openai.com")
            self.assertEqual(events[0]["port"], 443)
            self.assertEqual(events[0]["decision"], "blocked")
            self.assertEqual(events[0]["reason"], "not_allowlisted")
            self.assertNotIn("synthetic-secret-marker", event_log.read_text())
            self.assertNotIn("Proxy-Authorization", event_log.read_text())

    def test_allowlisted_tls_tunnel_is_byte_transparent(self):
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        echo_port = listener.getsockname()[1]
        received: list[bytes] = []

        def echo_server():
            connection, _ = listener.accept()
            with connection:
                payload = connection.recv(4096)
                received.append(payload)
                connection.sendall(payload)

        server_thread = threading.Thread(target=echo_server)
        server_thread.start()

        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temp_dir:
            event_log = Path(temp_dir) / "events.jsonl"
            broker = EgressBroker(
                allowlist=["api.openai.com:443"],
                event_log=event_log,
                connector=lambda host, port: (
                    socket.create_connection(("127.0.0.1", echo_port), timeout=2),
                    "127.0.0.1",
                ),
            ).start()
            try:
                with socket.create_connection(broker.address, timeout=2) as client:
                    client.sendall(
                        b"CONNECT api.openai.com:443 HTTP/1.1\r\n"
                        b"Host: api.openai.com:443\r\n\r\n"
                    )
                    response = read_header(client)
                    self.assertTrue(response.startswith(b"HTTP/1.1 200"))
                    tls_fixture = b"\x16\x03\x01\x00\x05HELLO"
                    client.sendall(tls_fixture)
                    self.assertEqual(client.recv(len(tls_fixture)), tls_fixture)
            finally:
                broker.stop()
                listener.close()
                server_thread.join(timeout=2)

            self.assertFalse(server_thread.is_alive())
            self.assertEqual(received, [tls_fixture])
            event = json.loads(event_log.read_text().splitlines()[0])
            self.assertEqual((event["host"], event["port"]), ("api.openai.com", 443))
            self.assertEqual(event["decision"], "forwarded")
            self.assertEqual(event["reason"], "exact_allowlist_match")
            self.assertNotIn("HELLO", event_log.read_text())

    def test_lookalike_host_and_wrong_port_never_call_connector(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temp_dir:
            event_log = Path(temp_dir) / "events.jsonl"
            connector_calls: list[tuple[str, int]] = []
            broker = EgressBroker(
                allowlist=["api.openai.com:443"],
                event_log=event_log,
                connector=lambda host, port: connector_calls.append((host, port)),
            ).start()
            try:
                for target in ("api.openai.com.evil:443", "api.openai.com:80"):
                    with socket.create_connection(broker.address, timeout=2) as client:
                        client.sendall(
                            f"CONNECT {target} HTTP/1.1\r\nHost: {target}\r\n\r\n".encode()
                        )
                        self.assertTrue(read_header(client).startswith(b"HTTP/1.1 403"))
            finally:
                broker.stop()
            self.assertEqual(connector_calls, [])
            events = [json.loads(line) for line in event_log.read_text().splitlines()]
            self.assertEqual([(item["host"], item["port"]) for item in events], [
                ("api.openai.com.evil", 443),
                ("api.openai.com", 80),
            ])
            self.assertTrue(all(item["decision"] == "blocked" for item in events))

    def test_non_loopback_bind_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temp_dir:
            with self.assertRaises(ValueError):
                EgressBroker(event_log=Path(temp_dir) / "events.jsonl", bind_host="0.0.0.0")


if __name__ == "__main__":
    unittest.main()
