"""Small adapter-boundary utilities for External Agent Federation R1.

The SDK deliberately contains no planning loop, tool registry, memory system,
daemon or provider client.  It translates a public process/CLI boundary into
the vendor-neutral contracts in :mod:`agent_federation.contracts`.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Any, Iterable, Mapping, Sequence

from .contracts import (
    ArtifactRef,
    ExternalSessionRef,
    FederatedResultReceipt,
    FederationContractError,
    HandoffEligibility,
)


CAPABILITY_TAXONOMY = (
    "repo.read",
    "repo.write",
    "repo.test",
    "terminal.run",
    "browser.read",
    "browser.act",
    "web.read",
    "messaging.send",
    "long_task",
    "native_resume",
    "structured_progress",
    "subagents",
    "scheduler",
    "device.action",
)


class AdapterSDKError(FederationContractError):
    """Raised when an adapter boundary cannot be safely normalized."""


class CapabilityMismatch(AdapterSDKError):
    """A required routing token is not declared by an executor."""


class ProcessTimeout(AdapterSDKError):
    """A bounded adapter process exceeded its timeout."""


class MalformedOutput(AdapterSDKError):
    """An adapter process returned output outside the declared format."""


@dataclass(frozen=True)
class SafeProcessResult:
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    duration_ms: float
    timed_out: bool = False
    output_truncated: bool = False


def discover_executable(name: str) -> str | None:
    if not isinstance(name, str) or not name or "/" in name:
        raise AdapterSDKError("executable discovery accepts a bare executable name only")
    return shutil.which(name)


def match_version(version: str, pattern: str) -> bool:
    if not isinstance(version, str) or not isinstance(pattern, str) or not pattern:
        raise AdapterSDKError("version and pattern must be non-empty strings")
    try:
        return re.search(pattern, version) is not None
    except re.error as exc:
        raise AdapterSDKError(f"invalid version pattern: {exc}") from exc


def _bounded_text(raw: bytes, cap: int, field: str) -> tuple[str, bool]:
    if not isinstance(cap, int) or isinstance(cap, bool) or cap <= 0:
        raise AdapterSDKError("output cap must be a positive integer")
    truncated = len(raw) > cap
    return raw[:cap].decode("utf-8", errors="replace"), truncated


def run_safe_subprocess(
    argv: Sequence[str],
    *,
    cwd: Path | None = None,
    timeout_seconds: float = 30,
    output_cap_bytes: int = 64 * 1024,
    executable_allowlist: Iterable[str] = (),
    input_text: str | None = None,
) -> SafeProcessResult:
    """Run a public adapter CLI with shell disabled and bounded output."""

    if not isinstance(argv, (list, tuple)) or not argv or any(not isinstance(item, str) or not item for item in argv):
        raise AdapterSDKError("argv must be a non-empty sequence of non-empty strings")
    if any(item in {"|", ";", "&&", "||", ">", ">>"} for item in argv):
        raise AdapterSDKError("shell syntax is not an argv value")
    allowed = tuple(executable_allowlist)
    if allowed and argv[0] not in allowed and Path(argv[0]).name not in {Path(item).name for item in allowed}:
        raise AdapterSDKError("executable is not in the adapter allowlist")
    if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool) or timeout_seconds <= 0:
        raise AdapterSDKError("timeout_seconds must be positive")
    start = time.monotonic()
    process = subprocess.Popen(
        list(argv),
        cwd=str(cwd) if cwd is not None else None,
        stdin=subprocess.PIPE if input_text is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        env=None,
    )
    try:
        stdout, stderr = process.communicate(
            input=input_text.encode("utf-8") if input_text is not None else None,
            timeout=float(timeout_seconds),
        )
    except subprocess.TimeoutExpired as exc:
        process.kill()
        stdout, stderr = process.communicate()
        duration_ms = round((time.monotonic() - start) * 1000, 3)
        out, truncated_out = _bounded_text(stdout or exc.stdout or b"", output_cap_bytes, "stdout")
        err, truncated_err = _bounded_text(stderr or exc.stderr or b"", output_cap_bytes, "stderr")
        raise ProcessTimeout(f"adapter process exceeded {timeout_seconds}s; stdout={out!r}; stderr={err!r}") from exc
    duration_ms = round((time.monotonic() - start) * 1000, 3)
    out, truncated_out = _bounded_text(stdout, output_cap_bytes, "stdout")
    err, truncated_err = _bounded_text(stderr, output_cap_bytes, "stderr")
    if truncated_out or truncated_err:
        raise MalformedOutput(f"adapter process output exceeded {output_cap_bytes} bytes")
    return SafeProcessResult(tuple(argv), process.returncode, out, err, duration_ms, False, False)


def parse_json_object(text: str, *, field: str = "output") -> dict[str, Any]:
    if not isinstance(text, str) or not text.strip():
        raise MalformedOutput(f"{field} is empty")
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise MalformedOutput(f"{field} is not valid JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise MalformedOutput(f"{field} must be a JSON object")
    return value


def parse_jsonl_events(text: str, *, max_events: int = 1000, max_line_bytes: int = 64 * 1024) -> tuple[dict[str, Any], ...]:
    if not isinstance(text, str):
        raise MalformedOutput("JSONL input must be text")
    if not isinstance(max_events, int) or max_events <= 0 or not isinstance(max_line_bytes, int) or max_line_bytes <= 0:
        raise AdapterSDKError("JSONL parser limits must be positive integers")
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        if len(line.encode("utf-8")) > max_line_bytes:
            raise MalformedOutput(f"JSONL line {line_number} exceeds {max_line_bytes} bytes")
        if len(events) >= max_events:
            raise MalformedOutput(f"JSONL event count exceeds {max_events}")
        value = parse_json_object(line, field=f"JSONL line {line_number}")
        events.append(value)
    if not events:
        raise MalformedOutput("JSONL stream contains no events")
    return tuple(events)


_SECRET_PATTERNS = (
    re.compile(r"(?i)(authorization\s*:\s*bearer\s+)[^\s,]+"),
    re.compile(r"(?i)(api[_-]?key\s*[=:]\s*)[^\s,]+"),
    re.compile(r"(?i)(token\s*[=:]\s*)[^\s,]+"),
    re.compile(r"(?i)(cookie\s*[=:]\s*)[^\s,]+"),
)


def redact_text(text: str) -> str:
    if not isinstance(text, str):
        raise AdapterSDKError("redact_text expects a string")
    result = text
    for pattern in _SECRET_PATTERNS:
        result = pattern.sub(r"\1[REDACTED]", result)
    return result


def redact_public_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise AdapterSDKError("redact_public_mapping expects an object")
    result: dict[str, Any] = {}
    redacted_fields = 0
    for key, item in value.items():
        normalized = str(key).casefold()
        if any(marker in normalized for marker in ("prompt", "system_prompt", "chain_of_thought", "cot", "thoughts", "reasoning", "token", "secret", "cookie", "authorization", "api_key", "password")):
            redacted_fields += 1
        elif isinstance(item, str):
            result[str(key)] = redact_text(item)
        elif isinstance(item, Mapping):
            result[str(key)] = redact_public_mapping(item)
        elif isinstance(item, (list, tuple)):
            result[str(key)] = [redact_public_mapping(x) if isinstance(x, Mapping) else redact_text(x) if isinstance(x, str) else x for x in item]
        else:
            result[str(key)] = item
    if redacted_fields:
        result["redacted_fields"] = redacted_fields
    return result


def map_capabilities(raw_tokens: Iterable[str], mapping: Mapping[str, str] | None = None) -> tuple[str, ...]:
    mapping = dict(mapping or {})
    result: list[str] = []
    for raw in raw_tokens:
        if not isinstance(raw, str) or not raw:
            raise AdapterSDKError("raw capability tokens must be non-empty strings")
        token = mapping.get(raw, raw)
        if token not in CAPABILITY_TAXONOMY:
            raise AdapterSDKError(f"capability token is outside the federation taxonomy: {token}")
        if token not in result:
            result.append(token)
    return tuple(result)


def require_capabilities(required: Iterable[str], declared: Iterable[str]) -> None:
    required_tokens = set(map_capabilities(required))
    declared_tokens = set(map_capabilities(declared))
    missing = sorted(required_tokens - declared_tokens)
    if missing:
        raise CapabilityMismatch(f"unsupported capabilities: {missing}")


def cancel_process(process: subprocess.Popen[bytes], *, grace_seconds: float = 1.0) -> bool:
    if process.poll() is not None:
        return True
    process.terminate()
    try:
        process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=grace_seconds)
    return process.poll() is not None


def session_ref(executor_id: str, session_id: str, kind: str, created_at: str) -> ExternalSessionRef:
    return ExternalSessionRef(executor_id, session_id, kind, created_at, True)


def build_receipt(
    *,
    federation_task_id: str,
    executor_id: str,
    terminal_state: str,
    claimed_actions: Sequence[str],
    artifacts: Sequence[ArtifactRef],
    validation_refs: Sequence[str],
    external_session_ref: ExternalSessionRef | None,
    telemetry: Mapping[str, Any],
    unresolveds: Sequence[str],
    handoff_eligible: bool,
    handoff_reason: str,
) -> FederatedResultReceipt:
    """Construct the only supported public result receipt shape."""

    return FederatedResultReceipt.build(
        federation_task_id=federation_task_id,
        executor_id=executor_id,
        terminal_state=terminal_state,
        claimed_actions=claimed_actions,
        artifact_refs=artifacts,
        validation_refs=validation_refs,
        external_session_ref=external_session_ref,
        executor_telemetry=redact_public_mapping(telemetry),
        unresolveds=unresolveds,
        handoff_eligibility=HandoffEligibility(handoff_eligible, handoff_reason),
    )


def python_fixture_argv(code: str) -> tuple[str, ...]:
    """Return an explicit disposable fixture argv for conformance tests."""

    return (sys.executable, "-c", code)
