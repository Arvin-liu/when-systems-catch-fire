"""Sanitized, provider-neutral failure diagnostics for bounded live attempts."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping, Sequence

from agent_kernel.contracts import sha256_json


FAILURE_FORENSICS_SCHEMA = "failure-forensics-capsule-r1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ABSOLUTE_PATH_RE = re.compile(r"(?:^|\s)/(?:Users|private|var|tmp|home|Volumes|System|Applications)(?:/|$)")
PRIVATE_MARKERS = (
    "access_token", "api_key", "bearer ", "client_secret", "password", "secret",
    "hidden reasoning", "chain-of-thought", "chain of thought", "raw_prompt", "full_prompt",
)

DIAGNOSTIC_CLASSES = frozenset({
    "CLI_ARGV_REJECTED",
    "OUTPUT_SCHEMA_REJECTED",
    "STARTUP_PERMISSION_FAILURE",
    "AUTH_PUBLIC_STATUS_FAILURE",
    "TRANSPORT_FAILURE",
    "PROCESS_EXIT_NONZERO_NO_STRUCTURED_RESULT",
    "STRUCTURED_RESULT_PARSE_FAILURE",
    "STRUCTURED_RESULT_SCHEMA_FAILURE",
    "OBSERVATION_INCOMPLETE",
    "UNKNOWN_UNCLASSIFIED",
})
STATUS_VALUES = frozenset({"PASS", "FAIL", "NOT_RUN", "UNKNOWN"})
STRUCTURED_OUTPUT_STATUSES = frozenset({"PRESENT", "ABSENT", "MALFORMED", "SCHEMA_MISMATCH", "UNKNOWN"})
SPOOL_RETENTION_STATUSES = frozenset({
    "RETAINED_UNTIL_DURABLE_RECEIPT", "CLEANED_AFTER_DURABLE_RECEIPT", "NOT_INITIALIZED", "UNKNOWN",
})
SPOOL_DISPOSAL_STATUSES = frozenset({"PENDING", "CLEANED", "RETAINED", "UNKNOWN"})
BOUNDARY_STATUSES = frozenset({"UNCHANGED", "UNCHANGED_REFERENCE", "CLEANED", "MUTATED", "REQUIRES_RECONCILIATION", "NOT_OBSERVED", "UNKNOWN", "NOT_CONFIGURED"})


class FailureForensicsError(ValueError):
    """Raised when a sanitized failure capsule is unsafe or incomplete."""


def _digest_or_unrecovered(value: Any) -> str:
    if value is None:
        return "UNRECOVERED"
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise FailureForensicsError("stream digests must be SHA-256 values or null")
    return value


def public_argv_shape(argv: Sequence[str] | None) -> dict[str, Any]:
    """Return option shape only; no argv value or path is retained."""

    if argv is None:
        payload = {"status": "UNAVAILABLE"}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        return {
            "status": "UNAVAILABLE",
            "argv_shape_digest": digest,
            "option_set_fingerprint": digest,
            "option_names": [],
            "argument_count": 0,
            "option_count": 0,
            "path_argument_count": 0,
            "secret_values_omitted": True,
        }
    if not isinstance(argv, (list, tuple)) or any(not isinstance(item, str) or not item for item in argv):
        raise FailureForensicsError("argv must be a sequence of non-empty strings")
    option_names = sorted({item for item in argv if item.startswith("-") and not item.startswith("/")})
    shape: list[str] = []
    path_count = 0
    for index, item in enumerate(argv):
        if index == 0:
            shape.append("EXECUTABLE")
        elif item.startswith("-"):
            shape.append("OPTION")
        elif item.startswith("/"):
            shape.append("PATH_VALUE")
            path_count += 1
        else:
            shape.append("POSITIONAL_VALUE")
    shape_payload = {"shape": shape, "option_names": option_names}
    return {
        "status": "SHAPE_ONLY",
        "argv_shape_digest": sha256_json(shape_payload),
        "option_set_fingerprint": sha256_json(option_names),
        "option_names": option_names,
        "argument_count": len(argv),
        "option_count": len(option_names),
        "path_argument_count": path_count,
        "secret_values_omitted": True,
    }


def classify_failure(
    *,
    process_return_code: int | None,
    timed_out: bool,
    parser_status: str,
    schema_status: str,
    structured_output_status: str,
    transport_error: bool = False,
    startup_error: bool = False,
    permission_error: bool = False,
    auth_error: bool = False,
) -> str:
    if transport_error:
        return "TRANSPORT_FAILURE"
    if auth_error:
        return "AUTH_PUBLIC_STATUS_FAILURE"
    if permission_error:
        return "STARTUP_PERMISSION_FAILURE"
    if startup_error:
        return "STARTUP_PERMISSION_FAILURE"
    if timed_out:
        return "OBSERVATION_INCOMPLETE"
    if parser_status == "FAIL":
        return "STRUCTURED_RESULT_PARSE_FAILURE"
    if schema_status == "FAIL" or structured_output_status == "SCHEMA_MISMATCH":
        return "STRUCTURED_RESULT_SCHEMA_FAILURE"
    if process_return_code not in (None, 0) and structured_output_status in {"ABSENT", "MALFORMED", "UNKNOWN"}:
        return "PROCESS_EXIT_NONZERO_NO_STRUCTURED_RESULT"
    if structured_output_status == "MALFORMED":
        return "STRUCTURED_RESULT_PARSE_FAILURE"
    if structured_output_status == "SCHEMA_MISMATCH":
        return "STRUCTURED_RESULT_SCHEMA_FAILURE"
    return "UNKNOWN_UNCLASSIFIED"


def _scan_capsule(value: Any, field: str = "capsule") -> None:
    if isinstance(value, str):
        lowered = value.casefold()
        if any(marker in lowered for marker in PRIVATE_MARKERS):
            raise FailureForensicsError(f"{field} contains private material")
        if ABSOLUTE_PATH_RE.search(value):
            raise FailureForensicsError(f"{field} contains an absolute path")
        return
    if value is None or isinstance(value, (bool, int, float)):
        return
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str) or not key.strip():
                raise FailureForensicsError(f"{field} contains an invalid key")
            lowered = key.casefold().replace("_", " ")
            safe_redaction_key = lowered in {"secret values omitted", "secret content stored", "raw private output stored"}
            if not safe_redaction_key and any(marker in lowered for marker in ("raw output", "raw prompt", "secret", "token", "password", "hidden reasoning")):
                raise FailureForensicsError(f"{field}.{key} is not a sanitized field")
            _scan_capsule(child, f"{field}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _scan_capsule(child, f"{field}[{index}]")
        return
    raise FailureForensicsError(f"{field} contains a non-JSON value")


def _unsigned(capsule: Mapping[str, Any]) -> dict[str, Any]:
    return {key: capsule[key] for key in sorted(capsule) if key != "capsule_digest"}


def validate_failure_forensics_capsule(document: Mapping[str, Any], *, check_digest: bool = True) -> dict[str, Any]:
    if not isinstance(document, Mapping):
        raise FailureForensicsError("failure forensics capsule must be an object")
    value = json.loads(json.dumps(document, ensure_ascii=False))
    required = {
        "schema_version", "task_id", "dispatch_id", "attempt_id", "executor_id", "adapter_id",
        "executor_version", "interface_digest", "argv_public_shape", "process", "streams",
        "parser", "schema", "structured_output", "diagnostic_class", "redaction",
        "runtime_boundary", "inference_observation_status", "raw_spool", "knowledge",
        "claim_ceiling", "capsule_digest",
    }
    if set(value) != required:
        raise FailureForensicsError("failure forensics capsule fields are not canonical")
    if value["schema_version"] != FAILURE_FORENSICS_SCHEMA:
        raise FailureForensicsError("failure forensics schema version mismatch")
    for field in ("task_id", "dispatch_id", "attempt_id", "executor_id", "adapter_id", "executor_version", "claim_ceiling"):
        if not isinstance(value[field], str) or not value[field].strip():
            raise FailureForensicsError(f"{field} is missing")
    if not isinstance(value["interface_digest"], str) or not SHA256_RE.fullmatch(value["interface_digest"]):
        raise FailureForensicsError("interface_digest must be a SHA-256 digest")
    argv_shape = value["argv_public_shape"]
    if not isinstance(argv_shape, dict) or set(argv_shape) != {
        "status", "argv_shape_digest", "option_set_fingerprint", "option_names", "argument_count",
        "option_count", "path_argument_count", "secret_values_omitted",
    }:
        raise FailureForensicsError("argv public shape is invalid")
    if argv_shape["status"] not in {"SHAPE_ONLY", "UNAVAILABLE"} or not isinstance(argv_shape["option_names"], list) or any(not isinstance(item, str) for item in argv_shape["option_names"]):
        raise FailureForensicsError("argv public shape status or options are invalid")
    for field in ("argv_shape_digest", "option_set_fingerprint"):
        if not isinstance(argv_shape[field], str) or not SHA256_RE.fullmatch(argv_shape[field]):
            raise FailureForensicsError(f"argv public shape {field} is invalid")
    for field in ("argument_count", "option_count", "path_argument_count"):
        if not isinstance(argv_shape[field], int) or isinstance(argv_shape[field], bool) or argv_shape[field] < 0:
            raise FailureForensicsError(f"argv public shape {field} is invalid")
    if argv_shape["secret_values_omitted"] is not True:
        raise FailureForensicsError("argv secret values must be omitted")
    process = value["process"]
    if not isinstance(process, dict) or set(process) != {"return_code", "duration_ms", "timed_out", "process_group_status", "cleanup_status"}:
        raise FailureForensicsError("process forensics fields are invalid")
    if process["return_code"] is not None and (not isinstance(process["return_code"], int) or isinstance(process["return_code"], bool)):
        raise FailureForensicsError("process return code is invalid")
    if process["duration_ms"] is not None and (not isinstance(process["duration_ms"], (int, float)) or isinstance(process["duration_ms"], bool) or process["duration_ms"] < 0):
        raise FailureForensicsError("process duration is invalid")
    if not isinstance(process["timed_out"], bool) or not isinstance(process["process_group_status"], str) or not isinstance(process["cleanup_status"], str):
        raise FailureForensicsError("process lifecycle fields are invalid")
    streams = value["streams"]
    if not isinstance(streams, dict) or set(streams) != {"stdout_byte_count", "stdout_digest", "stderr_byte_count", "stderr_digest"}:
        raise FailureForensicsError("stream forensics fields are invalid")
    for count in ("stdout_byte_count", "stderr_byte_count"):
        if not isinstance(streams[count], int) or isinstance(streams[count], bool) or streams[count] < 0:
            raise FailureForensicsError(f"{count} is invalid")
    for digest in ("stdout_digest", "stderr_digest"):
        if streams[digest] != "UNRECOVERED" and (not isinstance(streams[digest], str) or not SHA256_RE.fullmatch(streams[digest])):
            raise FailureForensicsError(f"{digest} is invalid")
    for section in ("parser", "schema"):
        status = value[section]
        if not isinstance(status, dict) or set(status) != {"status", "error_class"} or status["status"] not in STATUS_VALUES or not isinstance(status["error_class"], str):
            raise FailureForensicsError(f"{section} forensics fields are invalid")
    structured = value["structured_output"]
    if not isinstance(structured, dict) or set(structured) != {"status", "present"} or structured["status"] not in STRUCTURED_OUTPUT_STATUSES or not isinstance(structured["present"], bool):
        raise FailureForensicsError("structured output forensics fields are invalid")
    if value["diagnostic_class"] not in DIAGNOSTIC_CLASSES:
        raise FailureForensicsError("diagnostic class is invalid")
    redaction = value["redaction"]
    if not isinstance(redaction, dict) or set(redaction) != {"status", "raw_private_output_stored", "absolute_paths_redacted", "secret_content_stored"}:
        raise FailureForensicsError("redaction fields are invalid")
    if redaction != {"status": "PASS", "raw_private_output_stored": False, "absolute_paths_redacted": True, "secret_content_stored": False}:
        raise FailureForensicsError("failure forensics redaction gate is not closed")
    boundary = value["runtime_boundary"]
    if not isinstance(boundary, dict) or set(boundary) != {"runtime_scratch_status", "auth_source_status", "workspace_status"}:
        raise FailureForensicsError("runtime boundary fields are invalid")
    if any(boundary[field] not in BOUNDARY_STATUSES for field in boundary):
        raise FailureForensicsError("runtime boundary status is invalid")
    if value["inference_observation_status"] not in {"OBSERVED", "NOT_OBSERVED", "UNKNOWN", "NOT_APPLICABLE_PRE_PROCESS"}:
        raise FailureForensicsError("inference observation status is invalid")
    spool = value["raw_spool"]
    if not isinstance(spool, dict) or set(spool) != {"initialized", "retention_status", "disposal_status"} or not isinstance(spool["initialized"], bool):
        raise FailureForensicsError("raw spool forensics fields are invalid")
    if spool["retention_status"] not in SPOOL_RETENTION_STATUSES or spool["disposal_status"] not in SPOOL_DISPOSAL_STATUSES:
        raise FailureForensicsError("raw spool status is invalid")
    knowledge = value["knowledge"]
    if not isinstance(knowledge, dict) or set(knowledge) != {"known", "unknown", "not_inferable"} or any(not isinstance(knowledge[field], list) or any(not isinstance(item, str) or not item for item in knowledge[field]) for field in knowledge):
        raise FailureForensicsError("knowledge classification is invalid")
    if not isinstance(value["capsule_digest"], str) or not SHA256_RE.fullmatch(value["capsule_digest"]):
        raise FailureForensicsError("capsule digest is invalid")
    _scan_capsule(value)
    if check_digest and value["capsule_digest"] != sha256_json(_unsigned(value)):
        raise FailureForensicsError("capsule digest does not match immutable content")
    return value


def build_failure_forensics_capsule(
    *,
    task_id: str,
    dispatch_id: str,
    attempt_id: str,
    executor_id: str,
    adapter_id: str,
    executor_version: str,
    interface_digest: str,
    argv: Sequence[str] | None,
    process_return_code: int | None,
    duration_ms: float | None,
    timed_out: bool,
    process_group_status: str,
    cleanup_status: str,
    stdout_byte_count: int,
    stdout_digest: str | None,
    stderr_byte_count: int,
    stderr_digest: str | None,
    parser_status: str,
    parser_error_class: str,
    schema_status: str,
    schema_error_class: str,
    structured_output_status: str,
    structured_output_present: bool,
    diagnostic_class: str | None = None,
    transport_error: bool = False,
    startup_error: bool = False,
    permission_error: bool = False,
    auth_error: bool = False,
    runtime_scratch_status: str = "UNKNOWN",
    auth_source_status: str = "UNKNOWN",
    workspace_status: str = "UNKNOWN",
    inference_observation_status: str = "UNKNOWN",
    raw_spool_initialized: bool = False,
    raw_spool_retention_status: str = "UNKNOWN",
    raw_spool_disposal_status: str = "UNKNOWN",
    known: Sequence[str] = (),
    unknown: Sequence[str] = (),
    not_inferable: Sequence[str] = (),
    claim_ceiling: str = "Sanitized repository-local failure diagnostics only; no private inference, validated completion or external truth is inferred.",
) -> dict[str, Any]:
    if parser_status not in STATUS_VALUES or schema_status not in STATUS_VALUES:
        raise FailureForensicsError("parser and schema statuses must be canonical")
    if structured_output_status not in STRUCTURED_OUTPUT_STATUSES:
        raise FailureForensicsError("structured output status is invalid")
    if diagnostic_class is None:
        diagnostic_class = classify_failure(
            process_return_code=process_return_code,
            timed_out=timed_out,
            parser_status=parser_status,
            schema_status=schema_status,
            structured_output_status=structured_output_status,
            transport_error=transport_error,
            startup_error=startup_error,
            permission_error=permission_error,
            auth_error=auth_error,
        )
    capsule = {
        "schema_version": FAILURE_FORENSICS_SCHEMA,
        "task_id": task_id,
        "dispatch_id": dispatch_id,
        "attempt_id": attempt_id,
        "executor_id": executor_id,
        "adapter_id": adapter_id,
        "executor_version": executor_version,
        "interface_digest": interface_digest,
        "argv_public_shape": public_argv_shape(argv),
        "process": {
            "return_code": process_return_code,
            "duration_ms": duration_ms,
            "timed_out": timed_out,
            "process_group_status": process_group_status,
            "cleanup_status": cleanup_status,
        },
        "streams": {
            "stdout_byte_count": stdout_byte_count,
            "stdout_digest": _digest_or_unrecovered(stdout_digest),
            "stderr_byte_count": stderr_byte_count,
            "stderr_digest": _digest_or_unrecovered(stderr_digest),
        },
        "parser": {"status": parser_status, "error_class": parser_error_class},
        "schema": {"status": schema_status, "error_class": schema_error_class},
        "structured_output": {"status": structured_output_status, "present": structured_output_present},
        "diagnostic_class": diagnostic_class,
        "redaction": {
            "status": "PASS",
            "raw_private_output_stored": False,
            "absolute_paths_redacted": True,
            "secret_content_stored": False,
        },
        "runtime_boundary": {
            "runtime_scratch_status": runtime_scratch_status,
            "auth_source_status": auth_source_status,
            "workspace_status": workspace_status,
        },
        "inference_observation_status": inference_observation_status,
        "raw_spool": {
            "initialized": raw_spool_initialized,
            "retention_status": raw_spool_retention_status,
            "disposal_status": raw_spool_disposal_status,
        },
        "knowledge": {
            "known": list(known),
            "unknown": list(unknown),
            "not_inferable": list(not_inferable),
        },
        "claim_ceiling": claim_ceiling,
    }
    capsule["capsule_digest"] = sha256_json(capsule)
    return validate_failure_forensics_capsule(capsule)


def update_spool_disposition(capsule: Mapping[str, Any], *, retention_status: str, disposal_status: str) -> dict[str, Any]:
    value = json.loads(json.dumps(capsule, ensure_ascii=False))
    value["raw_spool"]["retention_status"] = retention_status
    value["raw_spool"]["disposal_status"] = disposal_status
    value["capsule_digest"] = sha256_json(_unsigned(value))
    return validate_failure_forensics_capsule(value)


__all__ = [
    "DIAGNOSTIC_CLASSES", "FAILURE_FORENSICS_SCHEMA", "FailureForensicsError",
    "build_failure_forensics_capsule", "classify_failure", "public_argv_shape",
    "update_spool_disposition", "validate_failure_forensics_capsule",
]
