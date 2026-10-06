"""Render and locally verify a Seatbelt profile limited to one loopback port."""

from __future__ import annotations

import json
import socket
import subprocess
import sys
import tempfile
import threading
from pathlib import Path


def render_profile(port: int) -> str:
    if not 1 <= port <= 65535:
        raise ValueError("loopback broker port is out of range")
    return "\n".join(
        [
            "(version 1)",
            "(allow default)",
            "(deny network-outbound)",
            f'(allow network-outbound (remote ip "localhost:{port}"))',
            "",
        ]
    )


def verify_profile(profile_path: Path, allowed_port: int, denied_port: int) -> dict:
    """Prove one local port succeeds and a different live loopback listener is denied."""
    if sys.platform != "darwin":
        raise RuntimeError("Seatbelt profile verification requires macOS")
    if allowed_port == denied_port:
        raise ValueError("probe ports must differ")

    allowed_listener = socket.socket()
    denied_listener = socket.socket()
    for listener in (allowed_listener, denied_listener):
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        listener.settimeout(2)

    allowed_port = allowed_listener.getsockname()[1]
    denied_port = denied_listener.getsockname()[1]
    profile_path.write_text(render_profile(allowed_port), encoding="utf-8")
    profile_path.chmod(0o600)

    accepted = {"allowed": False, "denied": False}

    def accept_allowed():
        try:
            connection, _ = allowed_listener.accept()
            with connection:
                accepted["allowed"] = connection.recv(64) == b"approved-loopback"
                connection.sendall(b"ok")
        except (TimeoutError, OSError):
            pass

    def accept_denied():
        try:
            connection, _ = denied_listener.accept()
            with connection:
                accepted["denied"] = True
        except (TimeoutError, OSError):
            pass

    allowed_thread = threading.Thread(target=accept_allowed)
    denied_thread = threading.Thread(target=accept_denied)
    allowed_thread.start()
    denied_thread.start()
    probe = r"""
import errno, json, socket, sys
allowed_port, denied_port = map(int, sys.argv[1:3])
with socket.create_connection(("localhost", allowed_port), timeout=1) as sock:
    sock.sendall(b"approved-loopback")
    allowed = sock.recv(2) == b"ok"
try:
    socket.create_connection(("localhost", denied_port), timeout=1)
    denied = False
except OSError as error:
    denied = error.errno in (errno.EPERM, errno.EACCES)
print(json.dumps({"allowed_loopback": allowed, "other_loopback_denied": denied}))
sys.exit(0 if allowed and denied else 3)
"""
    result = subprocess.run(
        [
            "/usr/bin/sandbox-exec",
            "-f",
            str(profile_path),
            sys.executable,
            "-c",
            probe,
            str(allowed_port),
            str(denied_port),
        ],
        capture_output=True,
        timeout=5,
        check=False,
    )
    allowed_thread.join(timeout=2)
    denied_thread.join(timeout=2)
    allowed_listener.close()
    denied_listener.close()
    output = json.loads(result.stdout.decode("utf-8")) if result.stdout else {}
    return {
        "returncode": result.returncode,
        "profile_text": profile_path.read_text(encoding="utf-8"),
        "profile_sha256": __import__("hashlib").sha256(
            profile_path.read_bytes()
        ).hexdigest(),
        "child_result": output,
        "allowed_listener_accepted": accepted["allowed"],
        "denied_listener_accepted": accepted["denied"],
        "stderr_bytes": len(result.stderr),
    }


def verify_profile_against_broker(profile_path: Path, broker_address: tuple[str, int]) -> dict:
    """Use the real broker port, then prove another live loopback port is denied."""
    if sys.platform != "darwin":
        raise RuntimeError("Seatbelt profile verification requires macOS")
    bind_host, allowed_port = broker_address
    if bind_host != "127.0.0.1":
        raise ValueError("broker address must be IPv4 loopback")

    denied_listener = socket.socket()
    denied_listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    denied_listener.bind(("127.0.0.1", 0))
    denied_listener.listen(1)
    denied_listener.settimeout(1)
    denied_port = denied_listener.getsockname()[1]
    profile_path.write_text(render_profile(allowed_port), encoding="utf-8")
    profile_path.chmod(0o600)
    accepted = {"denied": False}

    def accept_denied():
        try:
            connection, _ = denied_listener.accept()
            with connection:
                accepted["denied"] = True
        except (TimeoutError, OSError):
            pass

    denied_thread = threading.Thread(target=accept_denied)
    denied_thread.start()
    probe = r"""
import errno, json, socket, sys
proxy_port, denied_port = map(int, sys.argv[1:3])
with socket.create_connection(("localhost", proxy_port), timeout=1) as proxy:
    proxy.sendall(b"CONNECT stage02.local-probe.invalid:443 HTTP/1.1\r\nHost: stage02.local-probe.invalid:443\r\n\r\n")
    response = bytearray()
    while not response.endswith(b"\r\n\r\n"):
        response.extend(proxy.recv(1))
    broker_denied = response.startswith(b"HTTP/1.1 403")
try:
    socket.create_connection(("localhost", denied_port), timeout=1)
    denied = False
except OSError as error:
    denied = error.errno in (errno.EPERM, errno.EACCES)
try:
    socket.create_connection(("203.0.113.1", 443), timeout=1)
    external_denied = False
except OSError as error:
    external_denied = error.errno in (errno.EPERM, errno.EACCES)
print(json.dumps({"approved_loopback_reached_broker": True, "broker_denied_probe_host": broker_denied, "other_loopback_denied": denied, "direct_external_denied": external_denied}))
sys.exit(0 if broker_denied and denied and external_denied else 3)
"""
    result = subprocess.run(
        [
            "/usr/bin/sandbox-exec",
            "-f",
            str(profile_path),
            sys.executable,
            "-c",
            probe,
            str(allowed_port),
            str(denied_port),
        ],
        capture_output=True,
        timeout=5,
        check=False,
    )
    denied_thread.join(timeout=2)
    denied_listener.close()
    output = json.loads(result.stdout.decode("utf-8")) if result.stdout else {}
    return {
        "returncode": result.returncode,
        "profile_sha256": __import__("hashlib").sha256(
            profile_path.read_bytes()
        ).hexdigest(),
        "profile_text": profile_path.read_text(encoding="utf-8"),
        "child_result": output,
        "unapproved_loopback_listener_accepted": accepted["denied"],
        "stderr_bytes": len(result.stderr),
    }


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "sandbox-profile.sb"
        first = socket.socket()
        first.bind(("127.0.0.1", 0))
        allowed_port = first.getsockname()[1]
        first.close()
        second = socket.socket()
        second.bind(("127.0.0.1", 0))
        denied_port = second.getsockname()[1]
        second.close()
        print(json.dumps(verify_profile(temp_path, allowed_port, denied_port), sort_keys=True))
