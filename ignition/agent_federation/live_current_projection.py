"""Deterministic Current live-attempt projections.

R1 remains readable for historical Task139 artifacts. New projections use R2
typed observation fields so a public probe/transport code is never presented
as an unscoped live-process return code.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
import re
from typing import Any, Mapping

from agent_kernel.contracts import sha256_json
from agent_federation.live_attempt_ledger import LiveAttemptLedger
from agent_federation.live_observation_plane import derive_observation_outcome, validate_observation_outcome


LEGACY_LIVE_CURRENT_PROJECTION_SCHEMA = "live-current-projection-r1"
LIVE_CURRENT_PROJECTION_SCHEMA = "live-current-projection-r2"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class LiveCurrentProjectionError(RuntimeError):
    """Raised when the ledger cannot produce a safe deterministic projection."""


def _schema_validate(document: Mapping[str, Any], *, schema_version: str) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:  # pragma: no cover - clean bootstrap fallback
        return
    filename = "live-current-projection-r1.schema.json" if schema_version == LEGACY_LIVE_CURRENT_PROJECTION_SCHEMA else "live-current-projection-r2.schema.json"
    schema_path = Path(__file__).resolve().parents[1] / "schemas/operations" / filename
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except OSError as exc:  # pragma: no cover - packaging failure
        raise LiveCurrentProjectionError("live Current projection schema is unavailable") from exc
    # R2 is checked below with the same strict field contract because its
    # schema references the historical R1 document for shared fragments.
    if schema_version == LIVE_CURRENT_PROJECTION_SCHEMA:
        return
    errors = sorted(Draft202012Validator(schema).iter_errors(document), key=lambda error: list(error.path))
    if errors:
        error = errors[0]
        raise LiveCurrentProjectionError(f"live Current projection schema violation at {error.json_path}: {error.message}")


def _unsigned(document: Mapping[str, Any]) -> dict[str, Any]:
    return {key: document[key] for key in sorted(document) if key != "projection_digest"}


def _legacy_attempt_summary(record: Mapping[str, Any]) -> dict[str, Any]:
    process = record["process"]
    events = record["public_events"]
    structured = record["structured_result"]
    validator = record["validator"]
    return {
        "sequence": record["sequence"], "task_id": record["task_id"], "dispatch_id": record["dispatch_id"],
        "attempt_id": record["attempt_id"], "executor_id": record["executor_id"], "adapter_id": record["adapter_id"],
        "state": process["state"], "return_code": process["return_code"], "timed_out": process["timed_out"],
        "evidence_completeness": record["evidence_completeness"], "capture_completeness": events["capture_completeness"],
        "structured_result_present": structured["present"], "validator_status": validator["status"],
        "reconciliation_status": record["reconciliation_status"], "record_hash": record["record_hash"],
    }


def _typed_attempt_summary(record: Mapping[str, Any]) -> dict[str, Any]:
    process = record["process"]
    events = record["public_events"]
    typed = validate_observation_outcome(derive_observation_outcome(record))
    return {
        "sequence": record["sequence"], "task_id": record["task_id"], "dispatch_id": record["dispatch_id"],
        "attempt_id": record["attempt_id"], "executor_id": record["executor_id"], "adapter_id": record["adapter_id"],
        "state": process["state"], "timed_out": process["timed_out"],
        "evidence_completeness": record["evidence_completeness"], "capture_completeness": events["capture_completeness"],
        "probe_return_code": typed["probe_return_code"], "transport_return_code": typed["transport_return_code"],
        "public_probe_calls": typed["public_probe_calls"], "live_dispatch_calls": typed["live_dispatch_calls"],
        "live_dispatch_started": typed["live_dispatch_started"], "live_process_started": typed["live_process_started"],
        "live_process_return_code": typed["live_process_return_code"], "capture_initialized": typed["capture_initialized"],
        "structured_result_present": typed["structured_result_present"], "validator_status": typed["validator_status"],
        "legacy_record_return_code_preserved": typed["legacy_record_return_code_preserved"],
        "legacy_return_code_scope": typed["legacy_return_code_scope"],
        "reconciliation_status": record["reconciliation_status"], "record_hash": record["record_hash"],
    }


def _validate_summary(summary: Mapping[str, Any], *, typed: bool) -> None:
    legacy_required = {
        "sequence", "task_id", "dispatch_id", "attempt_id", "executor_id", "adapter_id", "state", "return_code",
        "timed_out", "evidence_completeness", "capture_completeness", "structured_result_present", "validator_status",
        "reconciliation_status", "record_hash",
    }
    typed_required = {
        "sequence", "task_id", "dispatch_id", "attempt_id", "executor_id", "adapter_id", "state", "timed_out",
        "evidence_completeness", "capture_completeness", "probe_return_code", "transport_return_code", "public_probe_calls",
        "live_dispatch_calls", "live_dispatch_started", "live_process_started", "live_process_return_code", "capture_initialized",
        "structured_result_present", "validator_status", "legacy_record_return_code_preserved", "legacy_return_code_scope",
        "reconciliation_status", "record_hash",
    }
    required = typed_required if typed else legacy_required
    if set(summary) != required:
        raise LiveCurrentProjectionError("attempt summary fields are not canonical")
    if not isinstance(summary["sequence"], int) or summary["sequence"] < 0:
        raise LiveCurrentProjectionError("attempt summary sequence is invalid")
    if not isinstance(summary["timed_out"], bool) or not isinstance(summary["structured_result_present"], bool):
        raise LiveCurrentProjectionError("attempt summary boolean field is invalid")
    if typed:
        for field in ("public_probe_calls", "live_dispatch_calls"):
            value = summary[field]
            if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
                raise LiveCurrentProjectionError(f"attempt summary {field} is invalid")
        for field in ("live_dispatch_started", "live_process_started", "capture_initialized"):
            if summary[field] is not None and not isinstance(summary[field], bool):
                raise LiveCurrentProjectionError(f"attempt summary {field} is invalid")
        for field in ("probe_return_code", "transport_return_code", "live_process_return_code"):
            if summary[field] is not None and (not isinstance(summary[field], int) or isinstance(summary[field], bool)):
                raise LiveCurrentProjectionError(f"attempt summary {field} is invalid")
        if summary["live_process_started"] is False and summary["live_process_return_code"] is not None:
            raise LiveCurrentProjectionError("typed summary exposes a live-process return code without a started process")
        if summary["live_dispatch_calls"] == 0 and (summary["live_dispatch_started"] is not False or summary["live_process_started"] is not False):
            raise LiveCurrentProjectionError("typed summary exposes a process despite zero live dispatch calls")
    if not isinstance(summary["record_hash"], str) or not SHA256_RE.fullmatch(summary["record_hash"]):
        raise LiveCurrentProjectionError("attempt summary record hash is invalid")


def _validate_projection_common(value: dict[str, Any], *, typed: bool, check_digest: bool) -> dict[str, Any]:
    expected_schema = LIVE_CURRENT_PROJECTION_SCHEMA if typed else LEGACY_LIVE_CURRENT_PROJECTION_SCHEMA
    if value.get("schema_version") != expected_schema:
        raise LiveCurrentProjectionError("live Current projection schema version mismatch")
    if value.get("contract_id") != "LIVE_CURRENT_STATE_DERIVATION_INVARIANT":
        raise LiveCurrentProjectionError("live Current projection contract mismatch")
    required = {
        "schema_version", "contract_id", "source_ledger", "counts", "per_executor", "latest_attempt_per_executor",
        "latest_validated_completion", "current_live_ceiling", "obligation", "next_eligible_action", "attempts", "claim_ceiling", "projection_digest",
    }
    if set(value) != required:
        raise LiveCurrentProjectionError("live Current projection fields are not canonical")
    source = value["source_ledger"]
    if not isinstance(source, dict) or set(source) != {"path", "record_count", "head_hash"}:
        raise LiveCurrentProjectionError("source ledger metadata is invalid")
    if not isinstance(source["path"], str) or not source["path"] or not isinstance(source["record_count"], int) or source["record_count"] < 0:
        raise LiveCurrentProjectionError("source ledger metadata is invalid")
    if not isinstance(source["head_hash"], str) or not SHA256_RE.fullmatch(source["head_hash"]):
        raise LiveCurrentProjectionError("source ledger head hash is invalid")
    counts = value["counts"]
    count_fields = {"total_attempts", "validated_completion_count", "unreconciled_count", "observation_incomplete_count", "complete_evidence_count", "incomplete_evidence_count"}
    if not isinstance(counts, dict) or set(counts) != count_fields or any(not isinstance(counts[key], int) or counts[key] < 0 for key in count_fields):
        raise LiveCurrentProjectionError("live attempt counts are invalid")
    if counts["total_attempts"] != len(value["attempts"]):
        raise LiveCurrentProjectionError("total attempt count does not match attempt summaries")
    if source["record_count"] != counts["total_attempts"]:
        raise LiveCurrentProjectionError("source ledger count does not match projection count")
    for summary in value["attempts"]:
        _validate_summary(summary, typed=typed)
    if [summary["sequence"] for summary in value["attempts"]] != list(range(counts["total_attempts"])):
        raise LiveCurrentProjectionError("attempt summaries are not in ledger sequence order")
    if not isinstance(value["per_executor"], dict) or not isinstance(value["latest_attempt_per_executor"], dict):
        raise LiveCurrentProjectionError("executor projections are invalid")
    for executor_id, entry in value["per_executor"].items():
        if not isinstance(executor_id, str) or not isinstance(entry, dict) or set(entry) != {"attempt_count", "state_counts", "attempt_ids"}:
            raise LiveCurrentProjectionError("per-executor projection is invalid")
        if entry["attempt_count"] != len(entry["attempt_ids"]):
            raise LiveCurrentProjectionError("per-executor attempt count is invalid")
        if not isinstance(entry["state_counts"], dict) or sum(entry["state_counts"].values()) != entry["attempt_count"]:
            raise LiveCurrentProjectionError("per-executor state counts are invalid")
    if value["latest_validated_completion"] is not None:
        _validate_summary(value["latest_validated_completion"], typed=typed)
        if value["latest_validated_completion"]["state"] != "COMPLETED_VALIDATED":
            raise LiveCurrentProjectionError("latest validated completion has an incompatible state")
    obligation = value["obligation"]
    if not isinstance(obligation, dict) or set(obligation) != {"obligation_id", "state", "reason", "unreconciled_attempt_ids"}:
        raise LiveCurrentProjectionError("live obligation projection is invalid")
    if obligation["obligation_id"] != "LIVE_EXTERNAL_INVOCATION" or obligation["state"] not in {"OPEN", "CLOSED"}:
        raise LiveCurrentProjectionError("live obligation state is invalid")
    if not isinstance(obligation["unreconciled_attempt_ids"], list):
        raise LiveCurrentProjectionError("unreconciled attempt list is invalid")
    if len(obligation["unreconciled_attempt_ids"]) != counts["unreconciled_count"]:
        raise LiveCurrentProjectionError("unreconciled count does not match obligation")
    action = value["next_eligible_action"]
    if not isinstance(action, dict) or set(action) != {"status", "action", "blocker_summary"}:
        raise LiveCurrentProjectionError("next eligible action projection is invalid")
    if not all(isinstance(action[key], str) and action[key] for key in action):
        raise LiveCurrentProjectionError("next eligible action contains an empty field")
    if not isinstance(value["claim_ceiling"], str) or not value["claim_ceiling"]:
        raise LiveCurrentProjectionError("claim ceiling is missing")
    if check_digest:
        digest = value["projection_digest"]
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            raise LiveCurrentProjectionError("projection digest is invalid")
        if digest != sha256_json(_unsigned(value)):
            raise LiveCurrentProjectionError("projection digest does not match content")
    return value


def validate_projection(document: Mapping[str, Any], *, check_digest: bool = True) -> dict[str, Any]:
    """Validate a historical R1 or typed R2 projection."""

    if not isinstance(document, Mapping):
        raise LiveCurrentProjectionError("live Current projection must be an object")
    value = json.loads(json.dumps(document, ensure_ascii=False))
    schema_version = value.get("schema_version")
    if schema_version not in {LEGACY_LIVE_CURRENT_PROJECTION_SCHEMA, LIVE_CURRENT_PROJECTION_SCHEMA}:
        raise LiveCurrentProjectionError("live Current projection schema version mismatch")
    _schema_validate(value, schema_version=schema_version)
    return _validate_projection_common(value, typed=schema_version == LIVE_CURRENT_PROJECTION_SCHEMA, check_digest=check_digest)


def _build_projection(records: list[dict[str, Any]], *, typed: bool, source_path: str, audit: Mapping[str, Any]) -> dict[str, Any]:
    summaries = [(_typed_attempt_summary(record) if typed else _legacy_attempt_summary(record)) for record in records]
    state_counts = Counter(summary["state"] for summary in summaries)
    per_executor_records: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for summary in summaries:
        per_executor_records[summary["executor_id"]].append(summary)
    per_executor: dict[str, Any] = {}
    latest_per_executor: dict[str, dict[str, Any]] = {}
    for executor_id in sorted(per_executor_records):
        rows = per_executor_records[executor_id]
        per_executor[executor_id] = {"attempt_count": len(rows), "state_counts": dict(sorted(Counter(row["state"] for row in rows).items())), "attempt_ids": [row["attempt_id"] for row in rows]}
        latest_per_executor[executor_id] = rows[-1]
    unreconciled = [summary for summary, record in zip(summaries, records) if record["reconciliation_status"] in {"OPEN", "REQUIRES_RECONCILIATION"}]
    validated = [summary for summary, record in zip(summaries, records) if record["process"]["state"] == "COMPLETED_VALIDATED"]
    if unreconciled:
        ceiling = "LIVE_EXTERNAL_INVOCATION_OPEN_NO_VALIDATED_COMPLETION"
        obligation_state = "OPEN"
        action = {"status": "BLOCKED_UNTIL_RECONCILIATION", "action": "RECONCILE_UNRECOVERED_ATTEMPTS", "blocker_summary": f"{len(unreconciled)} attempt(s) remain unreconciled and the validated completion count is {len(validated)}; no retry or completion claim is eligible from this projection."}
    elif validated:
        ceiling = "LIVE_EXTERNAL_INVOCATION_VALIDATED_COMPLETION_OBSERVED"
        obligation_state = "CLOSED"
        action = {"status": "STOP_AFTER_FIRST_VALIDATED_COMPLETION", "action": "STOP_LIVE_INVOCATION", "blocker_summary": "A validated completion is present; no additional live invocation is eligible."}
    else:
        ceiling = "LIVE_EXTERNAL_INVOCATION_NOT_OBSERVED"
        obligation_state = "OPEN"
        action = {"status": "ADMISSION_REQUIRED", "action": "RUN_DYNAMIC_EXECUTOR_ADMISSION", "blocker_summary": "No validated completion is present and no historical attempt is available to close the obligation."}
    projection = {
        "schema_version": LIVE_CURRENT_PROJECTION_SCHEMA if typed else LEGACY_LIVE_CURRENT_PROJECTION_SCHEMA,
        "contract_id": "LIVE_CURRENT_STATE_DERIVATION_INVARIANT",
        "source_ledger": {"path": source_path, "record_count": audit["record_count"], "head_hash": audit["head_hash"]},
        "counts": {
            "total_attempts": len(summaries), "validated_completion_count": len(validated), "unreconciled_count": len(unreconciled),
            "observation_incomplete_count": state_counts.get("OBSERVATION_INCOMPLETE", 0),
            "complete_evidence_count": sum(summary["evidence_completeness"] == "COMPLETE" for summary in summaries),
            "incomplete_evidence_count": sum(summary["evidence_completeness"] == "INCOMPLETE" for summary in summaries),
        },
        "per_executor": per_executor, "latest_attempt_per_executor": latest_per_executor,
        "latest_validated_completion": validated[-1] if validated else None, "current_live_ceiling": ceiling,
        "obligation": {"obligation_id": "LIVE_EXTERNAL_INVOCATION", "state": obligation_state, "reason": f"Ledger-derived live state: {len(unreconciled)} unreconciled attempt(s), {len(validated)} validated completion(s), {state_counts.get('OBSERVATION_INCOMPLETE', 0)} observation-incomplete attempt(s).", "unreconciled_attempt_ids": [summary["attempt_id"] for summary in unreconciled]},
        "next_eligible_action": action, "attempts": summaries,
        "claim_ceiling": (
            "Deterministic repository-local live attempt observation projection only; no external truth, production readiness, Owner acceptance or epistemic upgrade is inferred."
            if typed else
            "Deterministic repository-local live attempt projection only; no external truth, production readiness, Owner acceptance or epistemic upgrade is inferred."
        ),
    }
    projection["projection_digest"] = sha256_json(_unsigned(projection))
    return _validate_projection_common(projection, typed=typed, check_digest=True)


def build_live_current_projection(
    ledger_path: str | Path,
    *,
    source_path: str = "ignition/data/operations/iterations/139/live-attempt-ledger.jsonl",
    legacy: bool = False,
) -> dict[str, Any]:
    """Build a typed R2 projection, or a compatibility R1 projection."""

    ledger = LiveAttemptLedger(ledger_path)
    records = ledger.records()
    return _build_projection(records, typed=not legacy, source_path=source_path, audit=ledger.audit())


__all__ = ["LEGACY_LIVE_CURRENT_PROJECTION_SCHEMA", "LIVE_CURRENT_PROJECTION_SCHEMA", "LiveCurrentProjectionError", "build_live_current_projection", "validate_projection"]
