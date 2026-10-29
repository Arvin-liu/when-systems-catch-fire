"""Fail-closed privacy boundary for live executor observations."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Any, Mapping, Sequence


class LivePrivacyError(ValueError):
    """Raised when an executor result cannot be made public and bounded."""


LIVE_PRIVACY_SCHEMA = "ignition-136-live-privacy-r1"
_HARD_PRIVATE_FIELDS = frozenset({
    "prompt", "raw_prompt", "full_prompt", "system_prompt", "chain_of_thought", "cot", "thoughts",
    "reasoning", "hidden_reasoning", "reasoning_tokens", "access_token", "api_key", "secret", "password",
    "cookie", "authorization", "bearer", "session_transcript", "full_transcript", "private_transcript",
})
_STRIP_FIELDS = frozenset({
    "provider", "provider_telemetry", "telemetry", "channel", "channel_id", "message", "browser", "browser_action",
    "repository", "repository_path", "repo_files", "user_data", "user_material", "private_state", "cwd", "home",
})
_SAFE_RESULT_KEYS = frozenset({
    "schema", "status", "nonce", "line_count", "field_value", "value", "path", "checksum_prefix", "result", "items",
    "task_id", "dispatch_id", "attempt_id", "executor_id", "exit_code", "timed_out", "output_truncated",
    "response_digest", "workspace_before_digest", "workspace_after_digest", "side_effect_observation",
    "validation_status", "reconciliation_status", "claim_ceiling", "parsed", "parse_error_code", "event_type",
})
_SECRET_VALUE_PATTERNS = (
    re.compile(r"(?i)authorization\s*:\s*bearer\s+[^\s,]+"),
    re.compile(r"(?i)(?:api[_-]?key|access[_-]?token|password|secret|cookie)\s*[=:]\s*[^\s,]+"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]{8,}"),
)
_PRIVATE_PATH = re.compile(r"(?<![A-Za-z0-9_])/(?:Users|home)/[^\s,;\"']+")
_TEMP_PATH = re.compile(r"(?<![A-Za-z0-9_])/(?:private/)?tmp/[^\s,;\"']+")
_DANGEROUS_TEXT = re.compile(r"(?i)(system\s+prompt|hidden\s+reasoning|chain[- ]of[- ]thought|full\s+(?:raw\s+)?transcript|print\s+the\s+prompt)")


@dataclass(frozen=True)
class SanitizedLiveResult:
    value: Mapping[str, Any]
    redacted_fields: tuple[str, ...]
    source_digest: str | None = None

    def to_public(self) -> dict[str, Any]:
        result = dict(self.value)
        if self.redacted_fields:
            result["redacted_fields"] = list(self.redacted_fields)
        if self.source_digest is not None:
            result["source_digest"] = self.source_digest
        return result


def _field_name(key: Any) -> str:
    if not isinstance(key, str) or not key.strip():
        raise LivePrivacyError("live result keys must be non-empty strings")
    return key.strip()


def _normalized_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", key.casefold()).strip("_")


def _safe_text(value: str, field: str) -> tuple[str, bool]:
    if _DANGEROUS_TEXT.search(value):
        raise LivePrivacyError(f"{field} contains hidden prompt or reasoning material")
    redacted = False
    result = value
    for pattern in _SECRET_VALUE_PATTERNS:
        result, count = pattern.subn("[REDACTED]", result)
        redacted = redacted or bool(count)
    result, count = _PRIVATE_PATH.subn("<HOME_PRIVATE_PATH>", result)
    redacted = redacted or bool(count)
    result, count = _TEMP_PATH.subn("<TEMP_PATH>", result)
    redacted = redacted or bool(count)
    return result, redacted


def _sanitize(value: Any, *, field: str, allowed_keys: frozenset[str], redactions: list[str], depth: int = 0) -> Any:
    if depth > 5:
        raise LivePrivacyError(f"{field} is too deeply nested")
    if isinstance(value, Mapping):
        output: dict[str, Any] = {}
        for raw_key, raw_value in value.items():
            key = _field_name(raw_key)
            normalized = _normalized_key(key)
            if normalized in _HARD_PRIVATE_FIELDS or any(marker in normalized for marker in ("prompt", "reasoning", "transcript", "token", "api_key", "password", "secret")):
                raise LivePrivacyError(f"{field}.{key} is private and cannot enter a live receipt")
            if normalized in _STRIP_FIELDS or any(marker in normalized for marker in ("channel", "browser", "telemetry", "repository", "user_material", "private_state")):
                redactions.append(f"{field}.{key}")
                continue
            if allowed_keys and normalized not in allowed_keys and depth == 0:
                redactions.append(f"{field}.{key}")
                continue
            output[key] = _sanitize(raw_value, field=f"{field}.{key}", allowed_keys=allowed_keys, redactions=redactions, depth=depth + 1)
        return output
    if isinstance(value, (list, tuple)):
        if len(value) > 100:
            raise LivePrivacyError(f"{field} contains too many items")
        return [_sanitize(item, field=f"{field}[]", allowed_keys=allowed_keys, redactions=redactions, depth=depth + 1) for item in value]
    if isinstance(value, str):
        result, changed = _safe_text(value, field)
        if changed:
            redactions.append(field)
        return result
    if value is None or isinstance(value, (bool, int, float)):
        return value
    raise LivePrivacyError(f"{field} contains an unsupported value type")


def sanitize_live_result(value: Mapping[str, Any], *, source_text: str | None = None, allowed_keys: Sequence[str] = ()) -> SanitizedLiveResult:
    """Return the only structured result shape permitted into canonical state."""

    if not isinstance(value, Mapping):
        raise LivePrivacyError("live result must be a mapping")
    keys = frozenset(_normalized_key(item) for item in (allowed_keys or _SAFE_RESULT_KEYS))
    redactions: list[str] = []
    sanitized = _sanitize(value, field="structured_result", allowed_keys=keys, redactions=redactions)
    if not isinstance(sanitized, dict):
        raise LivePrivacyError("sanitized live result must remain an object")
    source_digest = hashlib.sha256(source_text.encode("utf-8")).hexdigest() if source_text is not None else None
    return SanitizedLiveResult(sanitized, tuple(sorted(set(redactions))), source_digest)


def sanitize_public_summary(value: str, *, max_chars: int = 512) -> str:
    if not isinstance(value, str):
        raise LivePrivacyError("live public summary must be text")
    normalized, _ = _safe_text(" ".join(value.split()), "summary")
    if not normalized:
        return "public executor returned no safe summary"
    return normalized[:max_chars]


__all__ = ["LIVE_PRIVACY_SCHEMA", "LivePrivacyError", "SanitizedLiveResult", "sanitize_live_result", "sanitize_public_summary"]
