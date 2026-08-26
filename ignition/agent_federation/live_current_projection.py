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
from agent_federation.live_reconciliation_events import LiveReconciliationEventLedger
from agent_federation.live_state_dimensions import derive_live_state_dimensions, validate_live_state_dimensions


LEGACY_LIVE_CURRENT_PROJECTION_SCHEMA = "live-current-projection-r1"
TYPED_R2_LIVE_CURRENT_PROJECTION_SCHEMA = "live-current-projection-r2"
LIVE_CURRENT_PROJECTION_SCHEMA = "live-current-projection-r3"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class LiveCurrentProjectionError(RuntimeError):
    """Raised when the ledger cannot produce a safe deterministic projection."""


def _schema_validate(document: Mapping[str, Any], *, schema_version: str) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:  # pragma: no cover - clean bootstrap fallback
        return
    if schema_version == LEGACY_LIVE_CURRENT_PROJECTION_SCHEMA:
        filename = "live-current-projection-r1.schema.json"
    elif schema_version == TYPED_R2_LIVE_CURRENT_PROJECTION_SCHEMA:
        filename = "live-current-projection-r2.schema.json"
    else:
        filename = "live-current-projection-r3.schema.json"
    schema_path = Path(__file__).resolve().parents[1] / "schemas/operations" / filename
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except OSError as exc:  # pragma: no cover - packaging failure
        raise LiveCurrentProjectionError("live Current projection schema is unavailable") from exc
    # R2 is checked below with the same strict field contract because its
    # schema references the historical R1 document for shared fragments.
    if schema_version in {TYPED_R2_LIVE_CURRENT_PROJECTION_SCHEMA, LIVE_CURRENT_PROJECTION_SCHEMA}:
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


def _typed_attempt_summary(
    record: Mapping[str, Any],
    reconciliation_status: str | None = None,
    observation_outcome: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if observation_outcome is not None:
        record = dict(record)
        record["observation_typing"] = observation_outcome
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
        "reconciliation_status": reconciliation_status or record["reconciliation_status"], "record_hash": record["record_hash"],
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
        if summary["reconciliation_status"] not in {
            "NOT_REQUIRED", "OPEN", "REQUIRES_RECONCILIATION", "CLOSED", "OPEN_REQUIRES_EVIDENCE",
            "TERMINAL_UNRECOVERABLE_EFFECT_UNKNOWN", "TERMINAL_UNRECOVERABLE_OBSERVATION_INCOMPLETE",
            "CLOSED_NO_LIVE_DISPATCH", "CLOSED_RECONCILED",
        }:
            raise LiveCurrentProjectionError("typed summary reconciliation status is invalid")
    if not isinstance(summary["record_hash"], str) or not SHA256_RE.fullmatch(summary["record_hash"]):
        raise LiveCurrentProjectionError("attempt summary record hash is invalid")


def _validate_projection_common(value: dict[str, Any], *, typed: bool, r3: bool = False, check_digest: bool) -> dict[str, Any]:
    expected_schema = LIVE_CURRENT_PROJECTION_SCHEMA if r3 else TYPED_R2_LIVE_CURRENT_PROJECTION_SCHEMA if typed else LEGACY_LIVE_CURRENT_PROJECTION_SCHEMA
    if value.get("schema_version") != expected_schema:
        raise LiveCurrentProjectionError("live Current projection schema version mismatch")
    if value.get("contract_id") != "LIVE_CURRENT_STATE_DERIVATION_INVARIANT":
        raise LiveCurrentProjectionError("live Current projection contract mismatch")
    required = {
        "schema_version", "contract_id", "source_ledger", "counts", "per_executor", "latest_attempt_per_executor",
        "latest_validated_completion", "current_live_ceiling", "obligation", "next_eligible_action", "attempts", "claim_ceiling", "projection_digest",
    }
    if r3:
        required.update({"live_state_dimensions", "compatibility_projection"})
    if set(value) != required:
        raise LiveCurrentProjectionError("live Current projection fields are not canonical")
    source = value["source_ledger"]
    source_keys = {"path", "record_count", "head_hash"}
    if typed:
        source_keys.add("reconciliation_events")
        if isinstance(value.get("source_ledger"), dict) and "observation_events" in value["source_ledger"]:
            source_keys.add("observation_events")
        if isinstance(value.get("source_ledger"), dict) and "inference_observation_events" in value["source_ledger"]:
            source_keys.add("inference_observation_events")
    if not isinstance(source, dict) or set(source) != source_keys:
        raise LiveCurrentProjectionError("source ledger metadata is invalid")
    if not isinstance(source["path"], str) or not source["path"] or not isinstance(source["record_count"], int) or source["record_count"] < 0:
        raise LiveCurrentProjectionError("source ledger metadata is invalid")
    if not isinstance(source["head_hash"], str) or not SHA256_RE.fullmatch(source["head_hash"]):
        raise LiveCurrentProjectionError("source ledger head hash is invalid")
    if typed:
        events = source["reconciliation_events"]
        if not isinstance(events, dict) or set(events) != {"path", "event_count", "head_hash"}:
            raise LiveCurrentProjectionError("reconciliation event metadata is invalid")
        if not isinstance(events["path"], str) or not events["path"] or not isinstance(events["event_count"], int) or events["event_count"] < 0:
            raise LiveCurrentProjectionError("reconciliation event metadata is invalid")
        if not isinstance(events["head_hash"], str) or not SHA256_RE.fullmatch(events["head_hash"]):
            raise LiveCurrentProjectionError("reconciliation event head hash is invalid")
        if "observation_events" in source:
            observation_events = source["observation_events"]
            if not isinstance(observation_events, dict) or set(observation_events) != {"path", "event_count", "head_hash"}:
                raise LiveCurrentProjectionError("observation event metadata is invalid")
            if not isinstance(observation_events["path"], str) or not observation_events["path"] or not isinstance(observation_events["event_count"], int) or observation_events["event_count"] < 0:
                raise LiveCurrentProjectionError("observation event metadata is invalid")
            if not isinstance(observation_events["head_hash"], str) or not SHA256_RE.fullmatch(observation_events["head_hash"]):
                raise LiveCurrentProjectionError("observation event head hash is invalid")
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
    obligation_keys = {"obligation_id", "state", "reason", "unreconciled_attempt_ids"}
    if r3:
        obligation_keys.add("closure_condition")
    if not isinstance(obligation, dict) or set(obligation) != obligation_keys:
        raise LiveCurrentProjectionError("live obligation projection is invalid")
    if obligation["obligation_id"] != "LIVE_EXTERNAL_INVOCATION" or obligation["state"] not in {"OPEN", "CLOSED"}:
        raise LiveCurrentProjectionError("live obligation state is invalid")
    if not isinstance(obligation["unreconciled_attempt_ids"], list):
        raise LiveCurrentProjectionError("unreconciled attempt list is invalid")
    if len(obligation["unreconciled_attempt_ids"]) != counts["unreconciled_count"]:
        raise LiveCurrentProjectionError("unreconciled count does not match obligation")
    if r3 and obligation["closure_condition"] != "FIRST_EXACT_BOUND_LIVE_READONLY_VALIDATED_COMPLETION":
        raise LiveCurrentProjectionError("live obligation closure condition is invalid")
    action = value["next_eligible_action"]
    if not isinstance(action, dict) or set(action) != {"status", "action", "blocker_summary"}:
        raise LiveCurrentProjectionError("next eligible action projection is invalid")
    if not all(isinstance(action[key], str) and action[key] for key in action):
        raise LiveCurrentProjectionError("next eligible action contains an empty field")
    if not isinstance(value["claim_ceiling"], str) or not value["claim_ceiling"]:
        raise LiveCurrentProjectionError("claim ceiling is missing")
    if r3:
        try:
            dimensions = validate_live_state_dimensions(value["live_state_dimensions"])
        except ValueError as exc:
            raise LiveCurrentProjectionError(f"live state dimensions are invalid: {exc}") from exc
        compatibility = value["compatibility_projection"]
        if not isinstance(compatibility, dict) or set(compatibility) != {"field", "status", "value", "semantics"}:
            raise LiveCurrentProjectionError("compatibility projection is invalid")
        if compatibility["field"] != "current_live_ceiling" or compatibility["status"] != "DEPRECATED_COMPATIBILITY_ALIAS":
            raise LiveCurrentProjectionError("current_live_ceiling is not marked as a compatibility alias")
        if compatibility["value"] != value["current_live_ceiling"] or not isinstance(compatibility["semantics"], str) or not compatibility["semantics"]:
            raise LiveCurrentProjectionError("compatibility projection does not bind to current_live_ceiling")
        if dimensions["next_eligible_action"] != value["next_eligible_action"]["action"]:
            raise LiveCurrentProjectionError("dimension next action disagrees with action projection")
        if dimensions["validated_completion_status"] == "VALIDATED" and counts["validated_completion_count"] == 0:
            raise LiveCurrentProjectionError("validated dimension disagrees with completion count")
        if dimensions["validated_completion_status"] == "NOT_VALIDATED" and counts["validated_completion_count"] != 0:
            raise LiveCurrentProjectionError("not-validated dimension disagrees with completion count")
        if dimensions["live_process_observation_status"] == "OBSERVED" and value["current_live_ceiling"] == "LIVE_EXTERNAL_INVOCATION_NOT_OBSERVED":
            raise LiveCurrentProjectionError("process-observed projection cannot use invocation-not-observed ceiling")
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
    if schema_version not in {LEGACY_LIVE_CURRENT_PROJECTION_SCHEMA, TYPED_R2_LIVE_CURRENT_PROJECTION_SCHEMA, LIVE_CURRENT_PROJECTION_SCHEMA}:
        raise LiveCurrentProjectionError("live Current projection schema version mismatch")
    _schema_validate(value, schema_version=schema_version)
    return _validate_projection_common(
        value,
        typed=schema_version in {TYPED_R2_LIVE_CURRENT_PROJECTION_SCHEMA, LIVE_CURRENT_PROJECTION_SCHEMA},
        r3=schema_version == LIVE_CURRENT_PROJECTION_SCHEMA,
        check_digest=check_digest,
    )


def _build_projection(
    records: list[dict[str, Any]],
    *,
    typed: bool,
    source_path: str,
    audit: Mapping[str, Any],
    reconciliation_status_by_attempt: Mapping[str, str] | None = None,
    reconciliation_source_path: str = "NOT_APPLICABLE",
    reconciliation_audit: Mapping[str, Any] | None = None,
    observation_outcome_by_attempt: Mapping[str, Mapping[str, Any]] | None = None,
    observation_source_path: str | None = None,
    observation_audit: Mapping[str, Any] | None = None,
    projection_schema: str = TYPED_R2_LIVE_CURRENT_PROJECTION_SCHEMA,
    inference_observation_source_path: str | None = None,
    inference_observation_audit: Mapping[str, Any] | None = None,
    inference_status_by_attempt: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    if projection_schema not in {LEGACY_LIVE_CURRENT_PROJECTION_SCHEMA, TYPED_R2_LIVE_CURRENT_PROJECTION_SCHEMA, LIVE_CURRENT_PROJECTION_SCHEMA}:
        raise LiveCurrentProjectionError("unsupported typed live Current projection schema")
    r3 = projection_schema == LIVE_CURRENT_PROJECTION_SCHEMA
    status_by_attempt = reconciliation_status_by_attempt or {}
    observation_overlay = observation_outcome_by_attempt or {}
    summaries = [
        (_typed_attempt_summary(record, status_by_attempt.get(record["attempt_id"]), observation_overlay.get(record["attempt_id"])) if typed else _legacy_attempt_summary(record))
        for record in records
    ]
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
    unreconciled = [summary for summary in summaries if summary["reconciliation_status"] in {"OPEN", "REQUIRES_RECONCILIATION", "OPEN_REQUIRES_EVIDENCE"}]
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
        process_observed = any(summary["live_process_started"] is True for summary in summaries) if typed else False
        ceiling = "LIVE_EXTERNAL_PROCESS_OBSERVED_NO_VALIDATED_COMPLETION" if process_observed and r3 else "LIVE_EXTERNAL_INVOCATION_NOT_OBSERVED"
        obligation_state = "OPEN"
        action = {"status": "ADMISSION_REQUIRED", "action": "RUN_DYNAMIC_EXECUTOR_ADMISSION", "blocker_summary": "No validated completion is present and no historical attempt is available to close the obligation."}
        if r3 and process_observed:
            action = {"status": "ADMISSION_REQUIRED", "action": "RUN_DYNAMIC_EXECUTOR_ADMISSION", "blocker_summary": "A live process observation exists but no exact-bound validated completion is present; repair/admit an eligible executor before any bounded attempt."}
    live_state_dimensions: dict[str, Any] | None = None
    if r3:
        explicit_inference = inference_status_by_attempt or {}
        per_attempt_dimensions: list[dict[str, Any]] = []
        for summary in summaries:
            observation = {
                "live_dispatch_calls": summary["live_dispatch_calls"],
                "live_dispatch_started": summary["live_dispatch_started"],
                "live_process_started": summary["live_process_started"],
                "live_process_return_code": summary["live_process_return_code"],
            }
            per_attempt_dimensions.append(derive_live_state_dimensions(
                observation,
                reconciliation_status=summary["reconciliation_status"],
                validated_completion=summary["state"] == "COMPLETED_VALIDATED",
                explicit_inference_status=explicit_inference.get(summary["attempt_id"]),
                next_action=action["action"],
            ))
        def aggregate(field: str, ordered: tuple[str, ...], default: str) -> str:
            values = [item[field] for item in per_attempt_dimensions]
            for candidate in ordered:
                if candidate in values:
                    return candidate
            return default
        live_state_dimensions = {
            "schema_version": "live-state-dimensions-r1",
            "live_dispatch_observation_status": aggregate("live_dispatch_observation_status", ("OBSERVED", "UNKNOWN", "NOT_OBSERVED"), "UNKNOWN"),
            "live_process_observation_status": aggregate("live_process_observation_status", ("OBSERVED", "UNKNOWN", "NOT_OBSERVED"), "UNKNOWN"),
            "inference_observation_status": aggregate("inference_observation_status", ("OBSERVED", "NOT_OBSERVED", "UNKNOWN", "NOT_APPLICABLE_PRE_PROCESS"), "UNKNOWN"),
            "validated_completion_status": "VALIDATED" if validated else "NOT_VALIDATED",
            "reconciliation_blocker_status": "OPEN" if unreconciled else "NONE",
            "next_eligible_action": action["action"],
        }
        validate_live_state_dimensions(live_state_dimensions)
    projection = {
        "schema_version": projection_schema if typed else LEGACY_LIVE_CURRENT_PROJECTION_SCHEMA,
        "contract_id": "LIVE_CURRENT_STATE_DERIVATION_INVARIANT",
        "source_ledger": {
            "path": source_path,
            "record_count": audit["record_count"],
            "head_hash": audit["head_hash"],
            **({
                "reconciliation_events": {
                    "path": reconciliation_source_path,
                    "event_count": (reconciliation_audit or {}).get("record_count", 0),
                    "head_hash": (reconciliation_audit or {}).get("head_hash", "0" * 64),
                }
            } if typed else {}),
            **({
                "observation_events": {
                    "path": observation_source_path,
                    "event_count": (observation_audit or {}).get("record_count", 0),
                    "head_hash": (observation_audit or {}).get("head_hash", "0" * 64),
                }
            } if typed and observation_source_path is not None else {}),
            **({
                "inference_observation_events": {
                    "path": inference_observation_source_path,
                    "event_count": (inference_observation_audit or {}).get("record_count", 0),
                    "head_hash": (inference_observation_audit or {}).get("head_hash", "0" * 64),
                }
            } if r3 and inference_observation_source_path is not None else {}),
        },
        "counts": {
            "total_attempts": len(summaries), "validated_completion_count": len(validated), "unreconciled_count": len(unreconciled),
            "observation_incomplete_count": state_counts.get("OBSERVATION_INCOMPLETE", 0),
            "complete_evidence_count": sum(summary["evidence_completeness"] == "COMPLETE" for summary in summaries),
            "incomplete_evidence_count": sum(summary["evidence_completeness"] == "INCOMPLETE" for summary in summaries),
        },
        "per_executor": per_executor, "latest_attempt_per_executor": latest_per_executor,
        "latest_validated_completion": validated[-1] if validated else None, "current_live_ceiling": ceiling,
        "obligation": {
            "obligation_id": "LIVE_EXTERNAL_INVOCATION", "state": obligation_state,
            "reason": f"Ledger-derived live state: {len(unreconciled)} unreconciled attempt(s), {len(validated)} validated completion(s), {state_counts.get('OBSERVATION_INCOMPLETE', 0)} observation-incomplete attempt(s).",
            "unreconciled_attempt_ids": [summary["attempt_id"] for summary in unreconciled],
            **({"closure_condition": "FIRST_EXACT_BOUND_LIVE_READONLY_VALIDATED_COMPLETION"} if r3 else {}),
        },
        "next_eligible_action": action, "attempts": summaries,
        "claim_ceiling": (
            "Deterministic repository-local live attempt observation projection only; no external truth, production readiness, Owner acceptance or epistemic upgrade is inferred."
            if typed else
            "Deterministic repository-local live attempt projection only; no external truth, production readiness, Owner acceptance or epistemic upgrade is inferred."
        ),
    }
    if r3:
        projection["live_state_dimensions"] = live_state_dimensions
        projection["compatibility_projection"] = {
            "field": "current_live_ceiling",
            "status": "DEPRECATED_COMPATIBILITY_ALIAS",
            "value": ceiling,
            "semantics": "Compatibility projection only; live_state_dimensions is canonical for process, inference, completion and reconciliation meaning.",
        }
    projection["projection_digest"] = sha256_json(_unsigned(projection))
    return _validate_projection_common(projection, typed=typed, r3=r3, check_digest=True)


def build_live_current_projection(
    ledger_path: str | Path,
    *,
    source_path: str = "ignition/data/operations/iterations/139/live-attempt-ledger.jsonl",
    legacy: bool = False,
    reconciliation_events_path: str | Path | None = None,
    observation_events_path: str | Path | None = None,
    projection_schema: str = TYPED_R2_LIVE_CURRENT_PROJECTION_SCHEMA,
    inference_observation_events_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build a typed R2 projection, or a compatibility R1 projection."""

    if legacy and (reconciliation_events_path is not None or projection_schema != TYPED_R2_LIVE_CURRENT_PROJECTION_SCHEMA):
        raise LiveCurrentProjectionError("historical R1 projection cannot consume a reconciliation overlay")
    if projection_schema not in {TYPED_R2_LIVE_CURRENT_PROJECTION_SCHEMA, LIVE_CURRENT_PROJECTION_SCHEMA}:
        raise LiveCurrentProjectionError("unsupported live Current projection schema")
    ledger = LiveAttemptLedger(ledger_path)
    records = ledger.records()
    status_by_attempt: dict[str, str] = {}
    reconciliation_audit: dict[str, Any] | None = None
    reconciliation_source_path = "NOT_APPLICABLE"
    observation_outcome_by_attempt: dict[str, dict[str, Any]] = {}
    observation_audit: dict[str, Any] | None = None
    observation_source_path = None
    inference_status_by_attempt: dict[str, str] = {}
    inference_observation_audit: dict[str, Any] | None = None
    inference_observation_source_path = None
    if reconciliation_events_path is not None:
        event_ledger = LiveReconciliationEventLedger(reconciliation_events_path)
        events = event_ledger.records()
        records_by_attempt = {record["attempt_id"]: record for record in records}
        for event in events:
            source_record = records_by_attempt.get(event["attempt_id"])
            state = event["reconciliation_state"]
            if source_record is None:
                raise LiveCurrentProjectionError("reconciliation event references an unknown attempt")
            if event["task_id"] != source_record["task_id"] or event["prior_record_hash"] != source_record["record_hash"]:
                raise LiveCurrentProjectionError("reconciliation event does not bind to the source ledger record")
            if event["attempt_id"] in status_by_attempt:
                raise LiveCurrentProjectionError("duplicate reconciliation overlay attempt")
            status_by_attempt[event["attempt_id"]] = state["reconciliation_status"]
        reconciliation_audit = event_ledger.audit()
        reconciliation_source_path = str(reconciliation_events_path)
    if observation_events_path is not None:
        from agent_federation.live_observation_events import LiveObservationEventLedger

        observation_ledger = LiveObservationEventLedger(observation_events_path)
        observation_events = observation_ledger.records()
        records_by_attempt = {record["attempt_id"]: record for record in records}
        for event in observation_events:
            source_record = records_by_attempt.get(event["attempt_id"])
            if source_record is None:
                raise LiveCurrentProjectionError("observation event references an unknown attempt")
            if (
                event["task_id"] != source_record["task_id"]
                or event["dispatch_id"] != source_record["dispatch_id"]
                or event["prior_record_hash"] != source_record["record_hash"]
            ):
                raise LiveCurrentProjectionError("observation event does not bind to the source ledger record")
            if event["attempt_id"] in observation_outcome_by_attempt:
                raise LiveCurrentProjectionError("duplicate observation outcome overlay attempt")
            observation_outcome_by_attempt[event["attempt_id"]] = event["observation_outcome"]
        observation_audit = observation_ledger.audit()
        observation_source_path = str(observation_events_path)
    if inference_observation_events_path is not None:
        inference_path = Path(inference_observation_events_path)
        if not inference_path.is_file():
            raise LiveCurrentProjectionError("inference observation overlay is unavailable")
        try:
            raw_events = [json.loads(line) for line in inference_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        except (OSError, json.JSONDecodeError) as exc:
            raise LiveCurrentProjectionError("inference observation overlay is unreadable") from exc
        records_by_attempt = {record["attempt_id"]: record for record in records}
        seen: set[str] = set()
        for event in raw_events:
            if not isinstance(event, dict) or set(event) != {"task_id", "dispatch_id", "attempt_id", "prior_record_hash", "inference_observation_status"}:
                raise LiveCurrentProjectionError("inference observation overlay fields are not canonical")
            record = records_by_attempt.get(event["attempt_id"])
            if record is None or event["task_id"] != record["task_id"] or event["dispatch_id"] != record["dispatch_id"] or event["prior_record_hash"] != record["record_hash"]:
                raise LiveCurrentProjectionError("inference observation overlay does not bind to the source record")
            if event["attempt_id"] in seen or event["inference_observation_status"] not in {"OBSERVED", "NOT_OBSERVED", "UNKNOWN", "NOT_APPLICABLE_PRE_PROCESS"}:
                raise LiveCurrentProjectionError("inference observation overlay is duplicated or invalid")
            seen.add(event["attempt_id"])
            inference_status_by_attempt[event["attempt_id"]] = event["inference_observation_status"]
        inference_observation_source_path = str(inference_path)
        inference_observation_audit = {"record_count": len(raw_events), "head_hash": sha256_json(raw_events) if raw_events else "0" * 64}
    return _build_projection(
        records,
        typed=not legacy,
        source_path=source_path,
        audit=ledger.audit(),
        reconciliation_status_by_attempt=status_by_attempt,
        reconciliation_source_path=reconciliation_source_path,
        reconciliation_audit=reconciliation_audit,
        observation_outcome_by_attempt=observation_outcome_by_attempt,
        observation_source_path=observation_source_path,
        observation_audit=observation_audit,
        projection_schema=projection_schema if not legacy else LEGACY_LIVE_CURRENT_PROJECTION_SCHEMA,
        inference_observation_source_path=inference_observation_source_path,
        inference_observation_audit=inference_observation_audit,
        inference_status_by_attempt=inference_status_by_attempt,
    )


__all__ = [
    "LEGACY_LIVE_CURRENT_PROJECTION_SCHEMA", "TYPED_R2_LIVE_CURRENT_PROJECTION_SCHEMA",
    "LIVE_CURRENT_PROJECTION_SCHEMA", "LiveCurrentProjectionError",
    "build_live_current_projection", "validate_projection",
]
