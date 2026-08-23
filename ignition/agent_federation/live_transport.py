"""Bounded public-process transport for the live executor bridge.

The transport is intentionally lower-level than an agent runtime: it starts
one allowlisted process, supplies one bounded input, captures public output,
and tears down the process group on timeout or output overflow.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import time
from typing import Any, Mapping, Sequence

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


def _terminate_group(process: subprocess.Popen[bytes], *, grace_seconds: float = 0.5) -> bool:
    if process.poll() is not None:
        return True
    cleaned = False
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return True
    try:
        process.wait(timeout=grace_seconds)
        cleaned = True
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=grace_seconds)
            cleaned = True
        except subprocess.TimeoutExpired:
            cleaned = False
    return cleaned


class LiveProcessTransport:
    """Run exactly one bounded public process with an explicit cwd and env."""

    def __init__(
        self,
        *,
        executable_allowlist: Sequence[str],
        env_allowlist: Sequence[str] = ("PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "CODEX_HOME", "HERMES_HOME"),
        output_cap_bytes: int = 128 * 1024,
        input_cap_bytes: int = 32 * 1024,
    ) -> None:
        if not isinstance(output_cap_bytes, int) or isinstance(output_cap_bytes, bool) or output_cap_bytes <= 0:
            raise LiveTransportError("output_cap_bytes must be positive")
        if not isinstance(input_cap_bytes, int) or isinstance(input_cap_bytes, bool) or input_cap_bytes <= 0:
            raise LiveTransportError("input_cap_bytes must be positive")
        self.executable_allowlist = tuple(executable_allowlist)
        self.env_allowlist = tuple(env_allowlist)
        self.output_cap_bytes = output_cap_bytes
        self.input_cap_bytes = input_cap_bytes

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
        start = time.monotonic()
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
        timed_out = False
        output_truncated = False
        cleaned = False
        deadline = start + float(timeout_seconds)
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = True
                cleaned = _terminate_group(process)
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
                target = buffers[key.data]
                target.extend(chunk)
                if len(target) > self.output_cap_bytes:
                    output_truncated = True
                    cleaned = _terminate_group(process)
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
                cleaned = _terminate_group(process) or cleaned
        try:
            returncode = process.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            cleaned = _terminate_group(process) or cleaned
            returncode = process.poll()
        duration_ms = round((time.monotonic() - start) * 1000, 3)
        stdout = bytes(buffers["stdout"][: self.output_cap_bytes]).decode("utf-8", errors="replace")
        stderr = bytes(buffers["stderr"][: self.output_cap_bytes]).decode("utf-8", errors="replace")
        return LiveProcessResult(argv_tuple, str(root), returncode, stdout, stderr, duration_ms, timed_out, output_truncated, cleaned)


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
