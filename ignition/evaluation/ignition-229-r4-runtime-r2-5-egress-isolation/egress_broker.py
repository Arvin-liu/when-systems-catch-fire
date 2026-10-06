"""Deny-first, exact-host HTTPS CONNECT broker for the Task229 R4 runtime."""

from __future__ import annotations

import json
import os
import re
import select
import socket
import socketserver
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

MAX_CONNECT_LINE = 1024
MAX_HEADER_BYTES = 16 * 1024
CONNECT_TIMEOUT_SECONDS = 10
TUNNEL_IDLE_SECONDS = 1
HOST_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$")


def normalize_allowlist(values: Iterable[str]) -> frozenset[tuple[str, int]]:
    """Parse exact host:port values and reject wildcard or ambiguous authorities."""
    normalized: set[tuple[str, int]] = set()
    for value in values:
        host, separator, port_text = value.rpartition(":")
        if not separator or not HOST_RE.fullmatch(host) or host == "*":
            raise ValueError("allowlist entries must be exact DNS host:port authorities")
        if host.endswith(".") or ".." in host or ".-" in host or "-." in host:
            raise ValueError("allowlist hostname is not canonical")
        try:
            port = int(port_text, 10)
        except ValueError as error:
            raise ValueError("allowlist port must be numeric") from error
        if not 1 <= port <= 65535:
            raise ValueError("allowlist port is out of range")
        normalized.add((host.lower(), port))
    return frozenset(normalized)


class _BoundedThreadingHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = False
    daemon_threads = False
    block_on_close = True

    def __init__(self, address, handler, broker):
        self.broker = broker
        self._slots = threading.BoundedSemaphore(8)
        super().__init__(address, handler, bind_and_activate=True)

    def process_request(self, request, client_address):
        if not self._slots.acquire(blocking=False):
            try:
                request.sendall(b"HTTP/1.1 503 Busy\r\nConnection: close\r\n\r\n")
            finally:
                self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self._slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._slots.release()


class _ConnectHandler(socketserver.BaseRequestHandler):
    def handle(self):
        client: socket.socket = self.request
        client.settimeout(CONNECT_TIMEOUT_SECONDS)
        broker: EgressBroker = self.server.broker
        try:
            parsed = broker._read_connect_authority(client)
            if parsed is None:
                broker._record(None, None, "blocked", "non_connect_or_malformed")
                client.sendall(b"HTTP/1.1 403 Forbidden\r\nConnection: close\r\n\r\n")
                return
            host, port = parsed
            if (host, port) not in broker.allowlist:
                broker._record(host, port, "blocked", "not_allowlisted")
                client.sendall(b"HTTP/1.1 403 Forbidden\r\nConnection: close\r\n\r\n")
                return
            upstream, address = broker._open_upstream(host, port)
            broker._record(host, port, "forwarded", "exact_allowlist_match", address)
            with upstream:
                client.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                broker._tunnel(client, upstream)
        except (OSError, TimeoutError) as error:
            broker._record(None, None, "blocked", type(error).__name__)
            try:
                client.sendall(b"HTTP/1.1 502 Bad Gateway\r\nConnection: close\r\n\r\n")
            except OSError:
                pass


class EgressBroker:
    """Loopback-only broker; HTTPS is tunneled without TLS interception."""

    def __init__(
        self,
        *,
        allowlist: Iterable[str] = (),
        event_log: Path,
        bind_host: str = "127.0.0.1",
        port: int = 0,
        connector: Callable[[str, int], tuple[socket.socket, str]] | None = None,
    ):
        if bind_host != "127.0.0.1":
            raise ValueError("broker must bind to IPv4 loopback only")
        self.allowlist = normalize_allowlist(allowlist)
        self.event_log = Path(event_log)
        self.connector = connector or self._connect_exact_host
        self._lock = threading.Lock()
        self._sequence = 0
        self._stopping = threading.Event()
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(self.event_log, flags, 0o600)
        os.close(fd)
        self._server = _BoundedThreadingHTTPServer(
            (bind_host, port), _ConnectHandler, broker=self
        )
        self._thread: threading.Thread | None = None

    @property
    def address(self) -> tuple[str, int]:
        host, port = self._server.server_address[:2]
        return str(host), int(port)

    def start(self) -> "EgressBroker":
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            kwargs={"poll_interval": 0.05},
            name="task229-egress-broker",
            daemon=False,
        )
        self._thread.start()
        return self

    def stop(self) -> None:
        self._stopping.set()
        self._server.shutdown()
        self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2)
            if self._thread.is_alive():
                raise RuntimeError("egress broker thread did not stop")

    def _record(self, host, port, decision, reason, upstream_address=None) -> None:
        with self._lock:
            self._sequence += 1
            event = {
                "sequence": self._sequence,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "host": host,
                "port": port,
                "decision": decision,
                "reason": reason,
            }
            if upstream_address is not None:
                event["upstream_ip"] = upstream_address
            payload = (json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n").encode()
            flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            fd = os.open(self.event_log, flags, 0o600)
            try:
                os.write(fd, payload)
                os.fsync(fd)
            finally:
                os.close(fd)

    @staticmethod
    def _read_connect_authority(client: socket.socket) -> tuple[str, int] | None:
        """Read only the CONNECT authority; discard headers without retaining values."""
        first_line = bytearray()
        total = 0
        while len(first_line) <= MAX_CONNECT_LINE:
            byte = client.recv(1)
            if not byte:
                return None
            total += 1
            if byte == b"\n":
                break
            if byte != b"\r":
                first_line.extend(byte)
        else:
            return None
        try:
            parts = first_line.decode("ascii", "strict").split()
        except UnicodeDecodeError:
            return None
        if len(parts) != 3 or parts[0] != "CONNECT" or parts[2] not in ("HTTP/1.0", "HTTP/1.1"):
            return None
        authority = parts[1]
        host, separator, port_text = authority.rpartition(":")
        if (
            not separator
            or not HOST_RE.fullmatch(host)
            or host.endswith(".")
            or ".." in host
            or ".-" in host
            or "-." in host
        ):
            return None
        try:
            port = int(port_text, 10)
        except ValueError:
            return None
        if not 1 <= port <= 65535:
            return None
        host = host.lower()

        # Discard, but never parse or log, proxy headers such as Proxy-Authorization.
        line_nonempty = False
        while total <= MAX_HEADER_BYTES:
            byte = client.recv(1)
            if not byte:
                return None
            total += 1
            if byte == b"\n":
                if not line_nonempty:
                    return host, port
                line_nonempty = False
            elif byte != b"\r":
                line_nonempty = True
        return None

    @staticmethod
    def _connect_exact_host(host: str, port: int) -> tuple[socket.socket, str]:
        addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        last_error: OSError | None = None
        for family, socktype, proto, _canonname, sockaddr in addresses:
            upstream = socket.socket(family, socktype, proto)
            upstream.settimeout(CONNECT_TIMEOUT_SECONDS)
            try:
                upstream.connect(sockaddr)
                upstream.settimeout(None)
                return upstream, str(sockaddr[0])
            except OSError as error:
                last_error = error
                upstream.close()
        if last_error is not None:
            raise last_error
        raise OSError("allowlisted host had no address records")

    def _open_upstream(self, host: str, port: int) -> tuple[socket.socket, str]:
        # This method is reachable only after an exact (host, port) allowlist match.
        return self.connector(host, port)

    def _tunnel(self, client: socket.socket, upstream: socket.socket) -> None:
        client.settimeout(None)
        sockets = (client, upstream)
        while not self._stopping.is_set():
            readable, _, exceptional = select.select(
                sockets, (), sockets, TUNNEL_IDLE_SECONDS
            )
            if exceptional:
                return
            if not readable:
                # A short idle check keeps shutdown bounded while preserving the tunnel.
                continue
            for source in readable:
                destination = upstream if source is client else client
                try:
                    data = source.recv(16 * 1024)
                except OSError:
                    return
                if not data:
                    return
                try:
                    destination.sendall(data)
                except OSError:
                    return


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--event-log", required=True, type=Path)
    parser.add_argument("--allow-host", action="append", default=[])
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    broker = EgressBroker(
        allowlist=args.allow_host,
        event_log=args.event_log,
        port=args.port,
    ).start()
    host, port = broker.address
    print(json.dumps({"bind_host": host, "port": port, "allowlist": sorted(broker.allowlist)}), flush=True)
    try:
        while True:
            time.sleep(0.25)
    except KeyboardInterrupt:
        broker.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
