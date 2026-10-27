#!/usr/bin/env python3
"""Check whether a caller-selected prior execution can be reused as a reference."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any

from jsonschema import Draft202012Validator


TOOL_ID = "knowledge.preflight_executed_experience_reuse"
TOOL_VERSION = "0.1.0"
MAX_INPUT_BYTES = 131_072
MAX_ARTIFACT_BYTES = 1_048_576
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas/operations/toolbox-executed-experience-preflight-r0.schema.json"
REPO_ROOT = Path(__file__).resolve().parents[2]
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
TIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
CLAIM_CEILING = (
    "Checks a caller-selected, locally byte-bound execution-receipt artifact for structural consistency and exact task, "
    "environment, source-scope, version, outcome-label, and expiry matches. It does not authenticate the run, actor, "
    "environment, effect, source authority, permission, or outcome truth; execute or select a tool; persist a skill; "
    "or authorize reuse beyond an optional reference in an exactly matching declared scope."
)


class ExperienceError(ValueError):
    pass


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ExperienceError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ExperienceError("NONFINITE_JSON_NUMBER:" + value)


def _load_json(raw: bytes, *, maximum: int) -> Any:
    if len(raw) > maximum:
        raise ExperienceError("INPUT_TOO_LARGE")
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExperienceError("INVALID_JSON") from exc


def _utc(value: str, field: str) -> datetime:
    if not isinstance(value, str) or not TIME_RE.fullmatch(value):
        raise ExperienceError(field + " must be a canonical UTC timestamp")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ExperienceError(field + " must be a valid UTC timestamp") from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        raise ExperienceError(field + " must be canonical")
    return parsed


def _schema_errors(payload: Any) -> list[dict[str, str]]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(payload),
        key=lambda error: (list(map(str, error.absolute_path)), error.validator or ""),
    )
    return [
        {"code": "INPUT_SCHEMA_INVALID", "path": "$" + ("/" + "/".join(map(str, error.absolute_path)) if error.absolute_path else "")}
        for error in errors[:64]
    ]


def _read_repo_artifact(relative_path: str) -> tuple[str, bytes | None]:
    """Read one bounded regular ignition/ file without following symlinks."""
    if not isinstance(relative_path, str) or "\\" in relative_path or relative_path.startswith("/"):
        return "PATH_REJECTED", None
    parts = tuple(relative_path.split("/"))
    if len(parts) < 2 or parts[0] != "ignition" or any(part in {"", ".", ".."} for part in parts):
        return "PATH_REJECTED", None
    if any(not re.fullmatch(r"[A-Za-z0-9._-]+", part) for part in parts):
        return "PATH_REJECTED", None
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptors: list[int] = []
    try:
        directory_fd = os.open(str(REPO_ROOT), flags)
        descriptors.append(directory_fd)
        for component in parts[:-1]:
            try:
                info = os.stat(component, dir_fd=directory_fd, follow_symlinks=False)
            except FileNotFoundError:
                return "MISSING", None
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                return "PATH_REJECTED", None
            directory_fd = os.open(component, flags, dir_fd=directory_fd)
            descriptors.append(directory_fd)
        leaf = parts[-1]
        try:
            info = os.stat(leaf, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            return "MISSING", None
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            return "PATH_REJECTED", None
        if info.st_size > MAX_ARTIFACT_BYTES:
            return "TOO_LARGE", None
        file_fd = os.open(leaf, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=directory_fd)
        descriptors.append(file_fd)
        opened = os.fstat(file_fd)
        if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
            return "READ_ERROR", None
        chunks: list[bytes] = []
        count = 0
        while True:
            chunk = os.read(file_fd, min(65_536, MAX_ARTIFACT_BYTES + 1 - count))
            if not chunk:
                break
            chunks.append(chunk)
            count += len(chunk)
            if count > MAX_ARTIFACT_BYTES:
                return "TOO_LARGE", None
        return "READ", b"".join(chunks)
    except OSError:
        return "READ_ERROR", None
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _decision(card: dict[str, Any], task: dict[str, Any], evaluated_at: datetime) -> dict[str, Any]:
    base = {
        "experience_id": card["experience_id"],
        "decision": "WITHHOLD",
        "reason": "UNASSESSED",
        "evidence_status": "NOT_READ",
        "task_family_match": card["task_family"] == task["task_family"],
        "environment_match": card["environment_ref"] == task["environment_ref"],
        "source_scope_match": card["source_scope_id"] == task["source_scope_id"],
        "can_execute": False,
        "can_authorize": False,
    }
    expiry = _utc(card["expires_at_utc"], "experiences[].expires_at_utc")
    if evaluated_at >= expiry:
        base.update(decision="WITHHOLD", reason="EXPIRED_BEFORE_EVIDENCE_READ", evidence_status="NOT_READ_EXPIRED")
        return base
    if not all(base[name] for name in ("task_family_match", "environment_match", "source_scope_match")):
        base.update(decision="REVIEW_REQUIRED", reason="TRANSFER_SCOPE_DIFFERS", evidence_status="NOT_READ_SCOPE_MISMATCH")
        return base

    state, raw = _read_repo_artifact(card["evidence_artifact"]["path"])
    if state != "READ" or raw is None:
        base.update(decision="WITHHOLD", reason="EVIDENCE_" + state, evidence_status=state)
        return base
    observed = hashlib.sha256(raw).hexdigest()
    if observed != card["evidence_artifact"]["sha256"]:
        base.update(decision="WITHHOLD", reason="EVIDENCE_DIGEST_MISMATCH", evidence_status="DIGEST_MISMATCH")
        return base
    base["evidence_status"] = "LOCAL_BYTES_MATCH"
    try:
        artifact = _load_json(raw, maximum=MAX_ARTIFACT_BYTES)
    except ExperienceError:
        base.update(decision="WITHHOLD", reason="EVIDENCE_JSON_INVALID", evidence_status="INVALID_JSON")
        return base
    receipt = artifact.get("receipt_output") if isinstance(artifact, dict) else None
    receipt_input = artifact.get("receipt_input") if isinstance(artifact, dict) else None
    execution = receipt_input.get("execution") if isinstance(receipt_input, dict) else None
    if not isinstance(receipt, dict) or not isinstance(execution, dict):
        base.update(decision="WITHHOLD", reason="RECEIPT_NOT_FOUND", evidence_status="RECEIPT_NOT_FOUND")
        return base
    if (
        receipt.get("schema_version") != "toolbox-execution-effect-receipt-output-r0"
        or receipt.get("findings") != []
        or receipt.get("execution_status") != "COMPLETED"
        or receipt.get("outcome_status") != "OUTCOME_RECORDED_CALLER_DECLARATION"
        or receipt.get("execution_authorized") is not False
        or receipt.get("outcome_truth") != "NOT_ESTABLISHED"
        or receipt.get("source_authentication") != "NOT_PERFORMED"
        or receipt.get("tool_id") != "maintenance.preflight_execution_effect_receipt"
        or receipt.get("tool_version") != "0.1.0"
        or execution.get("status") != "COMPLETED"
        or receipt.get("input_sha256") != artifact.get("receipt_input_sha256")
        or receipt_input.get("task_ref") != artifact.get("task_ref")
        or receipt.get("run_id") != execution.get("run_id")
        or receipt.get("task_ref") != artifact.get("task_ref")
    ):
        base.update(decision="WITHHOLD", reason="RECEIPT_BINDING_INVALID", evidence_status="RECEIPT_BINDING_INVALID")
        return base
    actual_identity = {
        "task_ref": receipt.get("task_ref"),
        "tool_id": execution.get("tool_id"),
        "tool_version": execution.get("tool_version"),
        "source_sha256": execution.get("source_sha256"),
        "environment_ref": execution.get("environment_ref"),
    }
    declared_identity = {key: card[key] for key in actual_identity}
    if actual_identity != declared_identity:
        base.update(decision="WITHHOLD", reason="DECLARED_IDENTITY_MISMATCH", evidence_status="IDENTITY_MISMATCH")
        return base
    effect_states = receipt.get("effect_states")
    input_observations = receipt_input.get("observations")
    observation_rows = [row for row in input_observations if isinstance(row, dict)] if isinstance(input_observations, list) else []
    raw_observed_states = [row.get("effect_state") for row in observation_rows]
    observed_states = sorted(set(raw_observed_states)) if all(isinstance(state, str) for state in raw_observed_states) else None
    observation_ids = [row.get("observation_id") for row in observation_rows]
    bound_ids = receipt.get("bound_observation_ids")
    observation_bindings_valid = (
        isinstance(bound_ids, list)
        and all(isinstance(item, str) for item in observation_ids)
        and all(isinstance(item, str) for item in bound_ids)
        and sorted(set(observation_ids)) == sorted(set(bound_ids))
    )
    if (
        not isinstance(effect_states, list)
        or len(effect_states) != 1
        or effect_states[0] != card["outcome_claim"]
        or observed_states != effect_states
        or not observation_bindings_valid
    ):
        base.update(decision="WITHHOLD", reason="OUTCOME_LABEL_MISMATCH_OR_AMBIGUOUS", evidence_status="OUTCOME_MISMATCH")
        return base
    if card["outcome_claim"] == "EFFECT_ABSENT" and receipt.get("failure_preservation_declared") is not True:
        base.update(decision="REVIEW_REQUIRED", reason="NEGATIVE_EFFECT_WITHOUT_PRESERVED_FAILURE", evidence_status="FAILURE_NOT_PRESERVED")
        return base
    if card["outcome_claim"] == "EFFECT_ABSENT" and not any(
        row.get("failure_record_ref") and row.get("failure_record_sha256") and row.get("first_failure_preserved")
        for row in observation_rows
    ):
        base.update(decision="REVIEW_REQUIRED", reason="NEGATIVE_EFFECT_MISSING_FAILURE_BINDING", evidence_status="FAILURE_NOT_PRESERVED")
        return base
    if card["outcome_claim"] == "EFFECT_PRESENT":
        base.update(decision="OPTIONAL_REFERENCE_ONLY", reason="EXACT_DECLARED_SCOPE_AND_EFFECT_RECEIPT_MATCH")
    elif card["outcome_claim"] == "EFFECT_ABSENT":
        base.update(decision="COUNTEREXAMPLE_ONLY", reason="PRESERVED_NEGATIVE_EXPERIENCE_MUST_NOT_BE_REUSED_AS_SUCCESS")
    else:
        base.update(decision="REVIEW_REQUIRED", reason="OUTCOME_UNKNOWN")
    return base


def evaluate(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ExperienceError("INPUT_MUST_BE_OBJECT")
    errors = _schema_errors(payload)
    if errors:
        raise ExperienceError("INPUT_SCHEMA_INVALID")
    evaluated_at = _utc(payload["evaluated_at_utc"], "evaluated_at_utc")
    decisions = [_decision(card, payload["task"], evaluated_at) for card in payload["experiences"]]
    return {
        "schema_version": "toolbox-executed-experience-result-r0",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "evaluated_at_utc": payload["evaluated_at_utc"],
        "evaluation_time_source": "CALLER_SUPPLIED_NOT_AUTHENTICATED",
        "task_id": payload["task"]["task_id"],
        "experience_decisions": decisions,
        "execution_authorized": False,
        "reuse_authorized": False,
        "claim_ceiling": CLAIM_CEILING,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", help="Read one JSON request from stdin")
    args = parser.parse_args()
    if not args.stdin:
        parser.error("--stdin is required")
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    try:
        payload = _load_json(raw, maximum=MAX_INPUT_BYTES)
        result = evaluate(payload)
    except ExperienceError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
