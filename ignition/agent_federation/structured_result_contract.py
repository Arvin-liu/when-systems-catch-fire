"""Strict, provider-neutral parsing for the bounded synthetic result contract."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


STRUCTURED_RESULT_CONTRACT_SCHEMA = "structured-result-contract-r1"
SYNTHETIC_RESULT_KEYS = ("nonce", "line_count", "field_value", "checksum_prefix")
_NONCE = re.compile(r"^[a-f0-9]{24}$")
_CHECKSUM = re.compile(r"^[a-f0-9]{8}$")


class StructuredResultContractError(ValueError):
    """Raised when a public result is absent, ambiguous, malformed or not exact."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True)
class StructuredResultEvidence:
    value: Mapping[str, Any]
    source: str
    source_digest: str | None


def _canonical_digest(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_synthetic_result(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the exact synthetic result before privacy sanitization."""

    if not isinstance(value, Mapping):
        raise StructuredResultContractError("RESULT_NOT_OBJECT", "structured result must be an object")
    actual = set(value)
    expected = set(SYNTHETIC_RESULT_KEYS)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        raise StructuredResultContractError("MISSING_REQUIRED_FIELDS", f"structured result is missing fields: {missing}")
    if extra:
        raise StructuredResultContractError("EXTRA_FIELDS", f"structured result has unsupported fields: {extra}")
    nonce = value["nonce"]
    if not isinstance(nonce, str) or not _NONCE.fullmatch(nonce):
        raise StructuredResultContractError("FIELD_TYPE_OR_PATTERN", "nonce is not a lowercase 24-character hex value")
    line_count = value["line_count"]
    if isinstance(line_count, bool) or not isinstance(line_count, int) or line_count <= 0:
        raise StructuredResultContractError("FIELD_TYPE_OR_RANGE", "line_count must be a positive integer")
    field_value = value["field_value"]
    if not isinstance(field_value, str) or not field_value:
        raise StructuredResultContractError("FIELD_TYPE_OR_RANGE", "field_value must be non-empty text")
    checksum_prefix = value["checksum_prefix"]
    if not isinstance(checksum_prefix, str) or not _CHECKSUM.fullmatch(checksum_prefix):
        raise StructuredResultContractError("FIELD_TYPE_OR_PATTERN", "checksum_prefix is not an eight-character hex value")
    return {key: value[key] for key in SYNTHETIC_RESULT_KEYS}


def _candidate_objects(value: Any, path: str = "event") -> list[tuple[str, Mapping[str, Any]]]:
    candidates: list[tuple[str, Mapping[str, Any]]] = []
    if isinstance(value, Mapping):
        candidates.append((path, value))
        for key, child in value.items():
            candidates.extend(_candidate_objects(child, f"{path}.{key}"))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            candidates.extend(_candidate_objects(child, f"{path}[{index}]"))
    return candidates


def extract_synthetic_result(events: Sequence[Mapping[str, Any]]) -> StructuredResultEvidence:
    """Find exactly one strict synthetic object in public event envelopes."""

    if not isinstance(events, (list, tuple)) or not events:
        raise StructuredResultContractError("NO_PUBLIC_EVENTS", "public events did not contain a result")
    valid: list[StructuredResultEvidence] = []
    candidate_errors: list[StructuredResultContractError] = []
    for event_index, event in enumerate(events):
        for path, candidate in _candidate_objects(event, f"events[{event_index}]"):
            if set(SYNTHETIC_RESULT_KEYS).issubset(candidate):
                try:
                    value = validate_synthetic_result(candidate)
                except StructuredResultContractError as exc:
                    candidate_errors.append(exc)
                    continue
                valid.append(StructuredResultEvidence(value, path, None))
            for key in ("text", "content", "message"):
                text = candidate.get(key)
                if not isinstance(text, str) or not text.strip():
                    continue
                try:
                    parsed = json.loads(text.strip())
                except json.JSONDecodeError as exc:
                    if any(marker in text for marker in SYNTHETIC_RESULT_KEYS):
                        candidate_errors.append(StructuredResultContractError("JSON_NOT_EXACT", str(exc)))
                    continue
                if not isinstance(parsed, Mapping):
                    continue
                if set(SYNTHETIC_RESULT_KEYS).issubset(parsed):
                    try:
                        value = validate_synthetic_result(parsed)
                    except StructuredResultContractError as exc:
                        candidate_errors.append(exc)
                        continue
                    source_digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
                    valid.append(StructuredResultEvidence(value, f"{path}.{key}", source_digest))
    if not valid:
        if candidate_errors:
            first = candidate_errors[0]
            raise StructuredResultContractError(first.code, str(first))
        raise StructuredResultContractError("RESULT_NOT_FOUND", "public events did not contain the exact synthetic result object")
    digests = {_canonical_digest(item.value) for item in valid}
    if len(digests) > 1:
        raise StructuredResultContractError("AMBIGUOUS_RESULTS", "public events contained multiple distinct synthetic results")
    return valid[0]


__all__ = [
    "STRUCTURED_RESULT_CONTRACT_SCHEMA",
    "SYNTHETIC_RESULT_KEYS",
    "StructuredResultContractError",
    "StructuredResultEvidence",
    "extract_synthetic_result",
    "validate_synthetic_result",
]
