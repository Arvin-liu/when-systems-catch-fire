"""Bounded public-process transport for the live executor bridge.

The transport is intentionally lower-level than an agent runtime: it starts
one allowlisted process, supplies one bounded input, captures public output,
and tears down the process group on timeout or output overflow.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import time
from typing import Any, Callable, Mapping, Sequence

from .contracts import FederationContractError


class LiveTransportError(FederationContractError):
    """Raised when a public process boundary is invalid before execution."""


@dataclass(frozen=True)
class LiveProcessResult:
    argv: tuple[str, ...]
    cwd: str
    returncode: int | None
    stdout: str
    stderr: str
    duration_ms: float
    timed_out: bool
    output_truncated: bool
    process_group_cleaned: bool
    started_at: str = ""
    ended_at: str = ""
    timeout_seconds: float = 0.0
    timeout_requested: bool = False
    termination_requested: bool = False
    signals_sent: tuple[str, ...] = ()
    process_group_status: str = "UNKNOWN"
    first_public_event_latency_ms: float | None = None
    monotonic_elapsed_ms: float | None = None
    stdout_bytes: int | None = None
    stderr_bytes: int | None = None
    stdout_digest: str | None = None
    stderr_digest: str | None = None
    wall_clock_order: str = "UNOBSERVED"


def interface_digest(public_help: str) -> str:
    if not isinstance(public_help, str):
        raise LiveTransportError("public interface text must be a string")
    return hashlib.sha256(public_help.encode("utf-8")).hexdigest()


def _validate_argv(argv: Sequence[str], executable_allowlist: Sequence[str]) -> tuple[str, ...]:
    if not isinstance(argv, (list, tuple)) or not argv or any(not isinstance(item, str) or not item for item in argv):
        raise LiveTransportError("live argv must be a non-empty sequence of non-empty strings")
    if any(item in {"|", ";", "&&", "||", ">", ">>", "<", "`"} for item in argv):
        raise LiveTransportError("shell syntax is not a literal argv value")
    if not isinstance(executable_allowlist, (list, tuple)) or not executable_allowlist:
        raise LiveTransportError("live process requires a non-empty executable allowlist")
    allowed = {str(item) for item in executable_allowlist}
    if argv[0] not in allowed and Path(argv[0]).name not in {Path(item).name for item in allowed}:
        raise LiveTransportError("executable is outside the live adapter allowlist")
    return tuple(argv)


def _sanitized_env(env_allowlist: Sequence[str], env_overrides: Mapping[str, str] | None) -> dict[str, str]:
    if not isinstance(env_allowlist, (list, tuple)) or any(not isinstance(key, str) or not key for key in env_allowlist):
        raise LiveTransportError("env_allowlist must contain non-empty names")
    allowed = set(env_allowlist)
    if any(any(marker in key.casefold() for marker in ("secret", "token", "api_key", "password", "cookie")) for key in allowed):
        raise LiveTransportError("secret-like environment names are not permitted in the live allowlist")
    result = {key: os.environ[key] for key in sorted(allowed) if key in os.environ}
    if env_overrides is not None:
        if not isinstance(env_overrides, Mapping):
            raise LiveTransportError("env_overrides must be an object")
        for key, value in env_overrides.items():
            if key not in allowed:
                raise LiveTransportError(f"environment override is outside the allowlist: {key}")
            if not isinstance(value, str):
                raise LiveTransportError(f"environment override must be text: {key}")
            result[key] = value
    return result


def _group_exists(pid: int) -> bool | None:
    """Return group existence, or None when the OS cannot prove it."""

    try:
        os.killpg(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return None
    return True


def _terminate_group(
    process: subprocess.Popen[bytes],
    *,
    grace_seconds: float = 0.5,
    descendant_streams_open: bool = False,
) -> tuple[str, tuple[str, ...]]:
    """Terminate the process group and report signals plus proof status.

    A returned ``CONFIRMED_GONE`` only describes the original process group.
    If the leader already exited while inherited pipes remain open, the
    transport cannot prove that a child did not escape that group and reports
    ``CHILD_LEFT_BEHIND`` instead.
    """

    signals_sent: list[str] = []
    initial = _group_exists(process.pid)
    if initial is False:
        if process.poll() is not None and descendant_streams_open:
            return "CHILD_LEFT_BEHIND", tuple(signals_sent)
        return "CONFIRMED_GONE", tuple(signals_sent)
    try:
        os.killpg(process.pid, signal.SIGTERM)
        signals_sent.append("SIGTERM")
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
            signals_sent.append("SIGKILL")
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=grace_seconds)
        except subprocess.TimeoutExpired:
            pass
    final = _group_exists(process.pid)
    if final is False:
        return "CONFIRMED_GONE", tuple(signals_sent)
    if final is None:
        return "UNKNOWN", tuple(signals_sent)
    return "UNKNOWN", tuple(signals_sent)


def _wall_clock_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _wall_clock_order(started_at: str, ended_at: str) -> str:
    try:
        start = datetime.fromisoformat(started_at)
        end = datetime.fromisoformat(ended_at)
    except ValueError:
        return "UNPARSEABLE"
    return "ORDERED" if end >= start else "DRIFTED"


class LiveProcessTransport:
    """Run exactly one bounded public process with an explicit cwd and env."""

    def __init__(
        self,
        *,
        executable_allowlist: Sequence[str],
        env_allowlist: Sequence[str] = ("PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "CODEX_HOME", "HERMES_HOME"),
        output_cap_bytes: int = 128 * 1024,
        input_cap_bytes: int = 32 * 1024,
        wall_clock: Callable[[], str] | None = None,
        monotonic_clock: Callable[[], float] | None = None,
    ) -> None:
        if not isinstance(output_cap_bytes, int) or isinstance(output_cap_bytes, bool) or output_cap_bytes <= 0:
            raise LiveTransportError("output_cap_bytes must be positive")
        if not isinstance(input_cap_bytes, int) or isinstance(input_cap_bytes, bool) or input_cap_bytes <= 0:
            raise LiveTransportError("input_cap_bytes must be positive")
        self.executable_allowlist = tuple(executable_allowlist)
        self.env_allowlist = tuple(env_allowlist)
        self.output_cap_bytes = output_cap_bytes
        self.input_cap_bytes = input_cap_bytes
        self._wall_clock = wall_clock or _wall_clock_iso
        self._monotonic = monotonic_clock or time.monotonic

    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: str | Path,
        timeout_seconds: float,
        input_text: str | None = None,
        env_overrides: Mapping[str, str] | None = None,
    ) -> LiveProcessResult:
        argv_tuple = _validate_argv(argv, self.executable_allowlist)
        root = Path(cwd)
        if not root.is_absolute() or not root.is_dir():
            raise LiveTransportError("live process cwd must be an existing absolute directory")
        if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool) or timeout_seconds <= 0:
            raise LiveTransportError("timeout_seconds must be positive")
        if input_text is not None:
            if not isinstance(input_text, str):
                raise LiveTransportError("input_text must be text or null")
            if len(input_text.encode("utf-8")) > self.input_cap_bytes:
                raise LiveTransportError("input_text exceeds the live input cap")
        environment = _sanitized_env(self.env_allowlist, env_overrides)
        started_at = self._wall_clock()
        start = self._monotonic()
        process = subprocess.Popen(
            list(argv_tuple),
            cwd=str(root),
            env=environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            start_new_session=True,
        )
        if process.stdin is not None:
            try:
                if input_text is not None:
                    process.stdin.write(input_text.encode("utf-8"))
                process.stdin.close()
            except (BrokenPipeError, OSError):
                pass

        selector = selectors.DefaultSelector()
        assert process.stdout is not None and process.stderr is not None
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")
        buffers: dict[str, bytearray] = {"stdout": bytearray(), "stderr": bytearray()}
        digests = {"stdout": hashlib.sha256(), "stderr": hashlib.sha256()}
        byte_counts = {"stdout": 0, "stderr": 0}
        first_public_event_latency_ms: float | None = None
        timed_out = False
        output_truncated = False
        cleaned = False
        signals_sent: tuple[str, ...] = ()
        process_group_status = "UNKNOWN"
        deadline = start + float(timeout_seconds)
        while selector.get_map():
            remaining = deadline - self._monotonic()
            if remaining <= 0:
                timed_out = True
                process_group_status, signals_sent = _terminate_group(
                    process, descendant_streams_open=bool(selector.get_map()) and process.poll() is not None,
                )
                cleaned = process_group_status == "CONFIRMED_GONE"
                break
            for key, _ in selector.select(timeout=min(remaining, 0.05)):
                stream = key.fileobj
                try:
                    chunk = os.read(stream.fileno(), 64 * 1024)
                except OSError:
                    chunk = b""
                if not chunk:
                    selector.unregister(stream)
                    stream.close()
                    continue
                if first_public_event_latency_ms is None:
                    first_public_event_latency_ms = round((self._monotonic() - start) * 1000, 3)
                target = buffers[key.data]
                digests[key.data].update(chunk)
                byte_counts[key.data] += len(chunk)
                target.extend(chunk)
                if len(target) > self.output_cap_bytes:
                    output_truncated = True
                    process_group_status, signals_sent = _terminate_group(
                        process, descendant_streams_open=bool(selector.get_map()) and process.poll() is not None,
                    )
                    cleaned = process_group_status == "CONFIRMED_GONE"
                    selector.unregister(stream)
                    stream.close()
                    break
            if output_truncated:
                break
            if process.poll() is not None and not selector.get_map():
                break
        selector.close()
        for stream in (process.stdout, process.stderr):
            if stream is not None and not stream.closed:
                stream.close()
        if timed_out or output_truncated:
            if process.poll() is None:
                process_group_status, signals_sent = _terminate_group(process)
                cleaned = process_group_status == "CONFIRMED_GONE"
        try:
            returncode = process.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            process_group_status, signals_sent = _terminate_group(process) 
            cleaned = process_group_status == "CONFIRMED_GONE"
            returncode = process.poll()
        ended_at = self._wall_clock()
        duration_ms = round((self._monotonic() - start) * 1000, 3)
        if not timed_out and not output_truncated:
            group_exists = _group_exists(process.pid)
            if group_exists is False:
                process_group_status = "CONFIRMED_GONE"
                cleaned = True
            elif group_exists is None:
                process_group_status = "UNKNOWN"
                cleaned = False
            elif process.poll() is not None:
                process_group_status = "CHILD_LEFT_BEHIND"
                cleaned = False
        if process_group_status == "UNKNOWN" and cleaned:
            cleaned = False
        stdout = bytes(buffers["stdout"][: self.output_cap_bytes]).decode("utf-8", errors="replace")
        stderr = bytes(buffers["stderr"][: self.output_cap_bytes]).decode("utf-8", errors="replace")
        return LiveProcessResult(
            argv_tuple, str(root), returncode, stdout, stderr, duration_ms, timed_out, output_truncated, cleaned,
            started_at=started_at, ended_at=ended_at, timeout_seconds=float(timeout_seconds),
            timeout_requested=timed_out, termination_requested=timed_out or output_truncated,
            signals_sent=signals_sent, process_group_status=process_group_status,
            first_public_event_latency_ms=first_public_event_latency_ms, monotonic_elapsed_ms=duration_ms,
            stdout_bytes=byte_counts["stdout"], stderr_bytes=byte_counts["stderr"],
            stdout_digest=digests["stdout"].hexdigest(), stderr_digest=digests["stderr"].hexdigest(),
            wall_clock_order=_wall_clock_order(started_at, ended_at),
        )


def parse_bounded_jsonl(text: str, *, max_events: int = 256, max_line_bytes: int = 64 * 1024) -> tuple[dict[str, Any], ...]:
    if not isinstance(text, str) or not text.strip():
        raise LiveTransportError("public JSONL output is empty")
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        if len(line.encode("utf-8")) > max_line_bytes:
            raise LiveTransportError(f"JSONL line {line_number} exceeds the public line cap")
        if len(events) >= max_events:
            raise LiveTransportError("JSONL event count exceeds the public cap")
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise LiveTransportError(f"JSONL line {line_number} is malformed") from exc
        if not isinstance(value, dict):
            raise LiveTransportError(f"JSONL line {line_number} is not an object")
        events.append(value)
    if not events:
        raise LiveTransportError("public JSONL output contains no events")
    return tuple(events)


__all__ = ["LiveProcessResult", "LiveProcessTransport", "LiveTransportError", "interface_digest", "parse_bounded_jsonl"]
