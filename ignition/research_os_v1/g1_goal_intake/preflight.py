"""Read-only Goal intake projection over existing Steering records.

This module accepts only an explicitly selected local synthetic fixture. It
never authenticates an Owner, consults a canonical registry, changes a Goal,
creates a completion decision, or dispatches work.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

from agent_runtime.steering import (
    AuthorityProvenance,
    CompletionContract,
    GoalDriftGuard,
    GoalEpisodeBinder,
    GoalRecord,
    IntentRecord,
    SteeringValidationError,
)


REQUEST_SCHEMA = "ignition.research_os_v1.g1_goal_intake.request.v1"
REPORT_SCHEMA = "ignition.research_os_v1.g1_goal_intake.report.v1"
_MAX_INPUT_BYTES = 1_000_000
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_PROHIBITED_TEXT = (
    "api_key",
    "access_token",
    "client_secret",
    "password",
    "chain-of-thought",
    "hidden reasoning",
    "raw_prompt",
    "prompt_body",
    "prompt",
)
_ORIGINS = {
    "USER_SUBMITTED_UNVERIFIED",
    "OWNER_DECLARED",
    "OWNER_APPROVED_DERIVED",
    "SYSTEM_DERIVED_PROPOSAL",
    "EXTERNAL_REQUESTED_PROPOSAL",
    "HISTORICAL_IMPORTED",
}
_STOP_VALUES = {"STOP": 2, "OWNER_REVIEW": 1}
_STOP_KEYS = {
    "budget_exhausted",
    "stale_or_unbound",
    "owner_authority_required",
    "executor_unavailable",
}

_SOURCE_REFS = {
    "work_order": {
        "ref": "Arvin-liu/when-systems-catch-fire@846d567d834159e97a5d44be1cf10f4d25b93acc:ignition/research_os_v1/g1_goal_intake/WORK-ORDER.md",
        "blob_sha": "1e941e6b9cafc9fc0ef8c75b8e449f92b930456a",
    },
    "steering_contract": {
        "ref": "Arvin-liu/when-systems-catch-fire@846d567d834159e97a5d44be1cf10f4d25b93acc:ignition/docs/architecture/os-steering-intent-r1.md",
        "blob_sha": "3bb668d1628c8e015405dd22de6f0b66175b16ba",
    },
    "steering_implementation": {
        "ref": "Arvin-liu/when-systems-catch-fire@846d567d834159e97a5d44be1cf10f4d25b93acc:ignition/agent_runtime/steering.py",
        "blob_sha": "ae73bd1d5e7f18e1dfde2b438fdc88128b02e19d",
    },
}


class _DuplicateKey(ValueError):
    pass


class _Findings:
    def __init__(self) -> None:
        self.invalid: list[dict[str, str]] = []
        self.blocked: list[dict[str, str]] = []
        self.authority: list[dict[str, str]] = []

    def add(self, category: str, code: str, path: str) -> None:
        row = {"category": category, "code": code, "path": path}
        target = {
            "invalid_input": self.invalid,
            "stale_or_unbound": self.blocked,
            "owner_authority": self.authority,
        }[category]
        if row not in target:
            target.append(row)

    def ordered(self) -> list[dict[str, str]]:
        rows = self.invalid + self.blocked + self.authority
        return sorted(rows, key=lambda row: (row["category"], row["path"], row["code"]))


def _pairs_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKey("duplicate JSON key")
        result[key] = value
    return result


def _reject_non_json_constant(_: str) -> Any:
    raise ValueError("non-finite JSON number")


def _closed_object(
    value: Any,
    *,
    required: set[str],
    optional: set[str] | None = None,
    path: str,
    findings: _Findings,
    missing_category: str = "invalid_input",
    missing_code: str = "missing_required_field",
) -> bool:
    if not isinstance(value, dict):
        findings.add("invalid_input", "object_required", path)
        return False
    allowed = required | (optional or set())
    valid = True
    if set(value) - allowed:
        findings.add("invalid_input", "unknown_field", path)
        valid = False
    if required - set(value):
        findings.add(missing_category, missing_code, path)
        valid = False
    return valid


def _safe_text(value: Any, path: str, findings: _Findings) -> bool:
    if not isinstance(value, str) or not value.strip() or len(value) > 2000:
        findings.add("invalid_input", "bounded_text_required", path)
        return False
    lowered = value.casefold()
    if any(marker in lowered for marker in _PROHIBITED_TEXT):
        findings.add("invalid_input", "prohibited_private_material", path)
        return False
    return True


def _compact_token(value: str) -> str:
    """Normalize case and separators for fail-closed shortcut comparisons."""

    return re.sub(r"[^a-z0-9]", "", value.casefold())


def _safe_id(value: Any, path: str, findings: _Findings, *, missing_is_blocked: bool = True) -> bool:
    category = "stale_or_unbound" if missing_is_blocked else "invalid_input"
    if not isinstance(value, str) or not _SAFE_ID.fullmatch(value):
        findings.add(category, "stable_identifier_missing_or_invalid", path)
        return False
    if any(marker in value.casefold() for marker in _PROHIBITED_TEXT):
        findings.add("invalid_input", "prohibited_private_material", path)
        return False
    return True


def _positive_int(value: Any, path: str, findings: _Findings, *, missing_is_blocked: bool = False) -> bool:
    category = "stale_or_unbound" if missing_is_blocked else "invalid_input"
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        findings.add(category, "positive_integer_required", path)
        return False
    return True


def _string_list(
    value: Any,
    path: str,
    findings: _Findings,
    *,
    nonempty: bool = True,
    ascii_tokens: bool = False,
) -> bool:
    if not isinstance(value, list) or (nonempty and not value) or len(value) > 32:
        findings.add("invalid_input", "bounded_string_list_required", path)
        return False
    valid = True
    seen: set[str] = set()
    for item in value:
        if not _safe_text(item, path, findings):
            valid = False
            continue
        if ascii_tokens and not item.isascii():
            findings.add("invalid_input", "ascii_policy_token_required", path)
            valid = False
        if item in seen:
            findings.add("invalid_input", "duplicate_list_value", path)
            valid = False
        seen.add(item)
    return valid


def _report(
    *,
    raw_sha256: str,
    status: str,
    structural_outcome: str,
    findings: _Findings,
    bindings: dict[str, Any] | None = None,
    drift_guard: dict[str, Any] | None = None,
    episode_projection: dict[str, Any] | None = None,
    request_summary: dict[str, Any] | None = None,
    authority_claims: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "schema": REPORT_SCHEMA,
        "preflight_status": status,
        "structural_outcome": structural_outcome,
        "raw_request_sha256": raw_sha256,
        "findings": findings.ordered(),
        "request_summary": request_summary or {},
        "bindings": bindings or {},
        "drift_guard": drift_guard or {
            "evaluated": False,
            "scope": "not_evaluated_without_closed_lineage",
            "memory_conflict_checked": False,
        },
        "episode_binding_projection": episode_projection or {
            "created": False,
            "canonical_binding_created": False,
        },
        "authority": {
            "claims_observed": sorted(set(authority_claims or [])),
            "owner_identity": "NOT_AUTHENTICATED",
            "trust_roots": "UNKNOWN",
            "source_currentness": "UNVERIFIED_OFFLINE",
            "owner_review_required": True,
        },
        "effects": {
            "canonical_records_written": False,
            "goal_lifecycle_mutated": False,
            "completion_decision_evaluated": False,
            "approval_receipt_created": False,
            "dispatch": False,
        },
        "source_refs": _SOURCE_REFS,
    }


def evaluate_request(raw_bytes: bytes) -> dict[str, Any]:
    """Return a deterministic report for exact request bytes without side effects."""

    if not isinstance(raw_bytes, bytes):
        raw_bytes = b""
    raw_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    findings = _Findings()
    if len(raw_bytes) > _MAX_INPUT_BYTES:
        findings.add("invalid_input", "input_exceeds_size_limit", "input")
        return _report(
            raw_sha256=raw_sha256,
            status="INVALID_INPUT",
            structural_outcome="INVALID_INPUT",
            findings=findings,
        )
    try:
        decoded = raw_bytes.decode("utf-8")
        payload = json.loads(
            decoded,
            object_pairs_hook=_pairs_without_duplicates,
            parse_constant=_reject_non_json_constant,
        )
    except _DuplicateKey:
        findings.add("invalid_input", "duplicate_json_key", "input")
        return _report(raw_sha256=raw_sha256, status="INVALID_INPUT", structural_outcome="INVALID_INPUT", findings=findings)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError):
        findings.add("invalid_input", "malformed_json", "input")
        return _report(raw_sha256=raw_sha256, status="INVALID_INPUT", structural_outcome="INVALID_INPUT", findings=findings)

    envelope_required = {"schema", "request", "bindings", "snapshots"}
    if not _closed_object(payload, required=envelope_required, path="envelope", findings=findings):
        return _report(raw_sha256=raw_sha256, status="INVALID_INPUT", structural_outcome="INVALID_INPUT", findings=findings)
    if payload.get("schema") != REQUEST_SCHEMA:
        findings.add("invalid_input", "unsupported_request_schema", "schema")

    request_fields = {
        "research_question",
        "declared_origin",
        "deliverables",
        "success_predicates",
        "allowed_source_kinds",
        "budget_envelopes",
        "allowed_executors",
        "stop_conditions",
        "claim_ceiling",
    }
    if not _closed_object(payload.get("request"), required=request_fields, path="request", findings=findings):
        return _report(raw_sha256=raw_sha256, status="INVALID_INPUT", structural_outcome="INVALID_INPUT", findings=findings)

    binding_fields = {
        "intent_id",
        "intent_version",
        "goal_id",
        "goal_version",
        "completion_contract_id",
        "objective_digest",
        "parent_goal_id",
        "parent_goal_version",
        "proposal_episode_id",
        "proposal_run_ids",
    }
    _closed_object(
        payload.get("bindings"),
        required=binding_fields,
        path="bindings",
        findings=findings,
        missing_category="stale_or_unbound",
        missing_code="binding_missing",
    )
    if not isinstance(payload.get("bindings"), dict):
        return _report(raw_sha256=raw_sha256, status="INVALID_INPUT", structural_outcome="INVALID_INPUT", findings=findings)

    snapshot_fields = {"intent", "goal", "completion_contract", "parent_goal"}
    _closed_object(
        payload.get("snapshots"),
        required=snapshot_fields,
        path="snapshots",
        findings=findings,
        missing_category="stale_or_unbound",
        missing_code="lineage_snapshot_missing",
    )
    if not isinstance(payload.get("snapshots"), dict):
        return _report(raw_sha256=raw_sha256, status="INVALID_INPUT", structural_outcome="INVALID_INPUT", findings=findings)

    request = payload["request"]
    bindings_input = payload["bindings"]
    snapshots = payload["snapshots"]

    for key in ("research_question", "claim_ceiling"):
        _safe_text(request.get(key), f"request.{key}", findings)
    declared_origin = request.get("declared_origin")
    if not isinstance(declared_origin, str) or declared_origin not in _ORIGINS:
        findings.add("invalid_input", "unknown_declared_origin", "request.declared_origin")
    for key in ("deliverables", "success_predicates", "allowed_source_kinds", "allowed_executors"):
        _string_list(request.get(key), f"request.{key}", findings, ascii_tokens=key != "deliverables")

    budget_fields = {"branches", "reviews"}
    _closed_object(request.get("budget_envelopes"), required=budget_fields, path="request.budget_envelopes", findings=findings)
    if isinstance(request.get("budget_envelopes"), dict):
        for key in budget_fields:
            _positive_int(request["budget_envelopes"].get(key), f"request.budget_envelopes.{key}", findings)

    _closed_object(
        request.get("stop_conditions"),
        required=_STOP_KEYS,
        path="request.stop_conditions",
        findings=findings,
    )
    if isinstance(request.get("stop_conditions"), dict):
        for key in _STOP_KEYS:
            value = request["stop_conditions"].get(key)
            if not isinstance(value, str) or value not in _STOP_VALUES:
                findings.add("invalid_input", "contradictory_or_unknown_stop_condition", f"request.stop_conditions.{key}")

    for key in ("intent_id", "goal_id", "completion_contract_id", "proposal_episode_id"):
        _safe_id(bindings_input.get(key), f"bindings.{key}", findings)
    for key in ("intent_version", "goal_version"):
        _positive_int(bindings_input.get(key), f"bindings.{key}", findings, missing_is_blocked=True)
    objective_digest = bindings_input.get("objective_digest")
    if not isinstance(objective_digest, str):
        findings.add("stale_or_unbound", "objective_digest_missing", "bindings.objective_digest")
    elif not _SHA256.fullmatch(objective_digest):
        findings.add("invalid_input", "objective_digest_malformed", "bindings.objective_digest")
    parent_id = bindings_input.get("parent_goal_id")
    if parent_id is not None and not _safe_id(parent_id, "bindings.parent_goal_id", findings):
        pass
    parent_version = bindings_input.get("parent_goal_version")
    if parent_version is not None:
        _positive_int(parent_version, "bindings.parent_goal_version", findings, missing_is_blocked=True)
    run_ids = bindings_input.get("proposal_run_ids")
    if "proposal_run_ids" not in bindings_input:
        findings.add("stale_or_unbound", "binding_missing", "bindings.proposal_run_ids")
    elif not _string_list(run_ids, "bindings.proposal_run_ids", findings):
        pass
    elif any(not _SAFE_ID.fullmatch(item) for item in run_ids):
        findings.add("invalid_input", "proposal_run_identifier_invalid", "bindings.proposal_run_ids")

    intent_input = snapshots.get("intent")
    goal_input = snapshots.get("goal")
    contract_input = snapshots.get("completion_contract")
    parent_input = snapshots.get("parent_goal")

    intent_fields = {
        "schema", "intent_id", "statement", "namespace", "provenance", "status", "scope", "version",
        "supersedes_intent_id", "created_at", "updated_at",
    }
    goal_fields = {
        "schema", "goal_id", "intent_id", "statement", "namespace", "completion_contract_id", "provenance",
        "status", "version", "parent_goal_id", "supersedes_goal_id", "created_at", "updated_at", "objective_digest",
    }
    provenance_fields = {"source_type", "actor_ref", "authority_id", "reason", "evidence_refs", "authorized"}
    contract_fields = {
        "schema", "contract_id", "acceptance_predicates", "required_evidence_types", "completion_authority",
        "forbidden_shortcuts", "review_window_ref",
    }

    if intent_input is None or goal_input is None:
        findings.add("stale_or_unbound", "lineage_snapshot_missing", "snapshots.intent_or_goal")
    if contract_input is None:
        findings.add("stale_or_unbound", "completion_contract_missing", "snapshots.completion_contract")

    maps_are_closed = True
    if intent_input is not None:
        maps_are_closed &= _closed_object(intent_input, required=intent_fields, path="snapshots.intent", findings=findings)
        if isinstance(intent_input, dict):
            maps_are_closed &= _closed_object(intent_input.get("provenance"), required=provenance_fields, path="snapshots.intent.provenance", findings=findings)
    if goal_input is not None:
        maps_are_closed &= _closed_object(goal_input, required=goal_fields, path="snapshots.goal", findings=findings)
        if isinstance(goal_input, dict):
            maps_are_closed &= _closed_object(goal_input.get("provenance"), required=provenance_fields, path="snapshots.goal.provenance", findings=findings)
    if contract_input is not None:
        maps_are_closed &= _closed_object(contract_input, required=contract_fields, path="snapshots.completion_contract", findings=findings)
    for label, record in (("intent", intent_input), ("goal", goal_input), ("parent_goal", parent_input)):
        if isinstance(record, dict) and record.get("schema") != f"os-steering-intent-obligation-r1.{label if label != 'parent_goal' else 'goal'}":
            findings.add("invalid_input", "steering_snapshot_schema_mismatch", f"snapshots.{label}.schema")
    for label, record in (("intent", intent_input), ("goal", goal_input), ("parent_goal", parent_input)):
        if not isinstance(record, dict):
            continue
        provenance = record.get("provenance")
        if isinstance(provenance, dict):
            if not isinstance(provenance.get("authorized"), bool):
                findings.add("invalid_input", "provenance_authorized_boolean_required", f"snapshots.{label}.provenance.authorized")
            if not isinstance(provenance.get("evidence_refs"), list):
                findings.add("invalid_input", "provenance_evidence_list_required", f"snapshots.{label}.provenance.evidence_refs")
    if isinstance(contract_input, dict):
        for key in ("acceptance_predicates", "required_evidence_types", "forbidden_shortcuts"):
            _string_list(contract_input.get(key), f"snapshots.completion_contract.{key}", findings, ascii_tokens=True)
    if parent_input is not None:
        maps_are_closed &= _closed_object(parent_input, required=goal_fields, path="snapshots.parent_goal", findings=findings)
        if isinstance(parent_input, dict):
            maps_are_closed &= _closed_object(parent_input.get("provenance"), required=provenance_fields, path="snapshots.parent_goal.provenance", findings=findings)

    if not maps_are_closed or findings.invalid:
        return _report(raw_sha256=raw_sha256, status="INVALID_INPUT", structural_outcome="INVALID_INPUT", findings=findings)

    intent: IntentRecord | None = None
    goal: GoalRecord | None = None
    parent_goal: GoalRecord | None = None
    contract: CompletionContract | None = None
    try:
        if isinstance(intent_input, dict):
            intent = IntentRecord.from_dict(intent_input)
        if isinstance(goal_input, dict):
            goal = GoalRecord.from_dict(goal_input)
        if isinstance(parent_input, dict):
            parent_goal = GoalRecord.from_dict(parent_input)
        if isinstance(contract_input, dict):
            if contract_input.get("schema") != "os-steering-intent-obligation-r1.completion-contract":
                findings.add("invalid_input", "completion_contract_schema_mismatch", "snapshots.completion_contract.schema")
            contract = CompletionContract(
                contract_id=contract_input["contract_id"],
                acceptance_predicates=tuple(contract_input["acceptance_predicates"]),
                required_evidence_types=tuple(contract_input["required_evidence_types"]),
                completion_authority=contract_input["completion_authority"],
                forbidden_shortcuts=tuple(contract_input["forbidden_shortcuts"]),
                review_window_ref=contract_input["review_window_ref"],
            )
    except (KeyError, TypeError, ValueError, SteeringValidationError):
        findings.add("invalid_input", "steering_snapshot_invalid", "snapshots")
        return _report(raw_sha256=raw_sha256, status="INVALID_INPUT", structural_outcome="INVALID_INPUT", findings=findings)

    if findings.invalid:
        return _report(raw_sha256=raw_sha256, status="INVALID_INPUT", structural_outcome="INVALID_INPUT", findings=findings)
    if intent is None or goal is None or contract is None:
        return _report(
            raw_sha256=raw_sha256,
            status="BLOCKED_STALE_OR_UNBOUND",
            structural_outcome="BLOCKED_STALE_OR_UNBOUND",
            findings=findings,
        )

    bindings_report: dict[str, Any] = {
        "intent_id": intent.intent_id,
        "intent_version_snapshot": intent.version,
        "intent_version_declared": bindings_input.get("intent_version"),
        "goal_id": goal.goal_id,
        "goal_version_snapshot": goal.version,
        "goal_version_declared": bindings_input.get("goal_version"),
        "completion_contract_id_snapshot": contract.contract_id,
        "completion_contract_id_goal": goal.completion_contract_id,
        "completion_contract_id_declared": bindings_input.get("completion_contract_id"),
        "objective_digest_computed": goal.objective_digest(),
        "objective_digest_goal_snapshot": goal_input.get("objective_digest") if isinstance(goal_input, dict) else None,
        "objective_digest_declared": objective_digest,
        "parent_goal_id_snapshot": goal.parent_goal_id,
        "parent_goal_id_declared": parent_id,
        "parent_goal_version_declared": parent_version,
    }
    for id_key, version_key, record_value, label in (
        ("intent_id", "intent_version", intent.intent_id, "intent"),
        ("goal_id", "goal_version", goal.goal_id, "goal"),
    ):
        if bindings_input.get(id_key) != record_value:
            findings.add("stale_or_unbound", f"{label}_id_mismatch", f"bindings.{id_key}")
        record_version = intent.version if label == "intent" else goal.version
        if bindings_input.get(version_key) != record_version:
            findings.add("stale_or_unbound", f"{label}_version_mismatch", f"bindings.{version_key}")

    if goal.intent_id != intent.intent_id:
        findings.add("stale_or_unbound", "goal_intent_binding_mismatch", "snapshots.goal.intent_id")
    if goal.namespace != intent.namespace:
        findings.add("stale_or_unbound", "intent_goal_namespace_mismatch", "snapshots.goal.namespace")
    if bindings_input.get("completion_contract_id") != contract.contract_id or goal.completion_contract_id != contract.contract_id:
        findings.add("stale_or_unbound", "completion_contract_binding_mismatch", "bindings.completion_contract_id")
    computed_digest = goal.objective_digest()
    if goal_input.get("objective_digest") != computed_digest or objective_digest != computed_digest:
        findings.add("stale_or_unbound", "objective_digest_mismatch", "bindings.objective_digest")
    if request.get("research_question") != goal.statement:
        findings.add("stale_or_unbound", "research_question_objective_mismatch", "request.research_question")

    _validate_scope_and_request(request, intent.scope, contract, findings)
    _validate_parent(goal, parent_goal, parent_input, bindings_input, findings)

    if intent.status == "SUPERSEDED" or intent.supersedes_intent_id is not None:
        findings.add("stale_or_unbound", "intent_superseded_lineage_requires_reconciliation", "snapshots.intent")
    if goal.status == "SUPERSEDED" or goal.supersedes_goal_id is not None:
        findings.add("stale_or_unbound", "goal_superseded_lineage_requires_reconciliation", "snapshots.goal")
    if parent_goal and (parent_goal.status == "SUPERSEDED" or parent_goal.supersedes_goal_id is not None):
        findings.add("stale_or_unbound", "parent_goal_superseded_lineage_requires_reconciliation", "snapshots.parent_goal")
    if intent.status != "PROPOSED" or goal.status != "PROPOSED" or (parent_goal and parent_goal.status != "PROPOSED"):
        findings.add("stale_or_unbound", "snapshot_not_proposal_only", "snapshots")

    authority_claims: list[str] = []
    if isinstance(request.get("declared_origin"), str) and request.get("declared_origin") in {"OWNER_DECLARED", "OWNER_APPROVED_DERIVED"}:
        authority_claims.append("request_declares_owner_origin")
    for label, provenance in (
        ("intent", intent.provenance),
        ("goal", goal.provenance),
        ("parent_goal", parent_goal.provenance if parent_goal else None),
    ):
        if provenance and (provenance.source_type in {"OWNER_DECLARED", "OWNER_APPROVED_DERIVED"} or provenance.authorized):
            authority_claims.append(f"{label}_snapshot_claims_owner_authority")
    if intent.status != "PROPOSED" or goal.status != "PROPOSED" or (parent_goal and parent_goal.status != "PROPOSED"):
        authority_claims.append("snapshot_claims_nonproposal_lifecycle_state")
    findings.add("owner_authority", "unknown_trust_roots", "authority")
    findings.add("owner_authority", "source_currentness_unverified", "authority")
    if authority_claims:
        findings.add("owner_authority", "owner_claim_unverified", "authority")

    drift_guard: dict[str, Any] = {
        "evaluated": False,
        "scope": "not_evaluated_without_closed_digest_binding",
        "memory_conflict_checked": False,
    }
    if isinstance(objective_digest, str) and _SHA256.fullmatch(objective_digest):
        try:
            drift = GoalDriftGuard().inspect(
                "preflight-drift-report",
                goal,
                objective_digest,
                contract.acceptance_predicates,
                tuple(request["success_predicates"]),
                superseded_reference=goal.supersedes_goal_id,
                memory_conflict=False,
                created_at="1970-01-01T00:00:00+00:00",
            )
            drift_guard = {
                "evaluated": True,
                "scope": "supplied_untrusted_snapshots_and_request_only",
                "outcome": drift.outcome,
                "reason_codes": list(drift.reasons),
                "expected_objective_digest": drift.expected_objective_digest,
                "observed_objective_digest": drift.observed_objective_digest,
                "memory_conflict_checked": False,
            }
        except (TypeError, ValueError, SteeringValidationError):
            findings.add("invalid_input", "drift_projection_invalid", "bindings.objective_digest")

    episode_projection: dict[str, Any] | None = None
    if not findings.invalid and not findings.blocked and goal.status == "PROPOSED":
        try:
            binder = GoalEpisodeBinder()
            projection = binder.bind(
                goal,
                bindings_input["proposal_episode_id"],
                tuple(run_ids),
                created_at="1970-01-01T00:00:00+00:00",
            )
            episode_projection = {
                "created": True,
                "projection_only": True,
                "canonical_binding_created": False,
                "binding_id": projection.binding_id,
                "objective_digest": projection.objective_digest,
                "handoff_identity_digest": projection.handoff_identity_digest,
                "completion_inference": projection.completion_inference,
            }
        except (KeyError, TypeError, ValueError, SteeringValidationError):
            findings.add("invalid_input", "episode_binding_projection_invalid", "bindings.proposal_episode_id")

    raw_budgets = request.get("budget_envelopes")
    safe_budgets = {}
    if isinstance(raw_budgets, dict):
        for key in ("branches", "reviews"):
            value = raw_budgets.get(key)
            if isinstance(value, int) and not isinstance(value, bool) and value > 0:
                safe_budgets[key] = value
    request_summary: dict[str, Any] = {
        "declared_origin": request.get("declared_origin") if isinstance(request.get("declared_origin"), str) and request.get("declared_origin") in _ORIGINS else "INVALID_OR_UNAVAILABLE",
        "research_question_sha256": hashlib.sha256(str(request.get("research_question", "")).encode("utf-8")).hexdigest(),
        "deliverable_count": len(request.get("deliverables", [])) if isinstance(request.get("deliverables"), list) else None,
        "proposed_success_predicates": list(request.get("success_predicates", [])),
        "allowed_source_kinds": list(request.get("allowed_source_kinds", [])),
        "budget_envelopes": safe_budgets,
        "allowed_executors": list(request.get("allowed_executors", [])),
        "required_evidence_types": list(contract.required_evidence_types),
        "completion_authority": contract.completion_authority,
        "forbidden_shortcuts": list(contract.forbidden_shortcuts),
        "claim_ceiling": request.get("claim_ceiling") if isinstance(request.get("claim_ceiling"), str) and len(request.get("claim_ceiling", "")) <= 2000 and not any(marker in request.get("claim_ceiling", "").casefold() for marker in _PROHIBITED_TEXT) else "INVALID_OR_UNAVAILABLE",
    }
    if findings.invalid:
        status = structural = "INVALID_INPUT"
    elif findings.blocked:
        status = structural = "BLOCKED_STALE_OR_UNBOUND"
    else:
        structural = "CANDIDATE_STRUCTURALLY_VALID_PROPOSAL_ONLY"
        status = "REQUIRES_OWNER_AUTHORITY"
    return _report(
        raw_sha256=raw_sha256,
        status=status,
        structural_outcome=structural,
        findings=findings,
        bindings=bindings_report,
        drift_guard=drift_guard,
        episode_projection=episode_projection,
        request_summary=request_summary,
        authority_claims=authority_claims,
    )


def _validate_scope_and_request(
    request: Mapping[str, Any],
    scope: Any,
    contract: CompletionContract,
    findings: _Findings,
) -> None:
    scope_fields = {
        "allowed_deliverables",
        "allowed_source_kinds",
        "allowed_executors",
        "budget_envelopes",
        "stop_conditions",
        "claim_ceiling",
    }
    if not _closed_object(scope, required=scope_fields, path="snapshots.intent.scope", findings=findings):
        return
    assert isinstance(scope, dict)
    for key in ("allowed_deliverables", "allowed_source_kinds", "allowed_executors"):
        _string_list(scope.get(key), f"snapshots.intent.scope.{key}", findings, ascii_tokens=key != "allowed_deliverables")
    _safe_text(scope.get("claim_ceiling"), "snapshots.intent.scope.claim_ceiling", findings)
    if (
        isinstance(scope.get("allowed_deliverables"), list)
        and all(isinstance(item, str) for item in scope["allowed_deliverables"])
        and isinstance(request.get("deliverables"), list)
        and all(isinstance(item, str) for item in request["deliverables"])
    ):
        if not set(request["deliverables"]).issubset(set(scope["allowed_deliverables"])):
            findings.add("invalid_input", "deliverable_policy_expansion", "request.deliverables")
    for key in ("allowed_source_kinds", "allowed_executors"):
        asked = request.get(key)
        allowed = scope.get(key)
        if (
            isinstance(asked, list)
            and all(isinstance(item, str) for item in asked)
            and isinstance(allowed, list)
            and all(isinstance(item, str) for item in allowed)
            and not set(asked).issubset(set(allowed))
        ):
            findings.add("invalid_input", f"{key}_policy_expansion", f"request.{key}")
    if request.get("claim_ceiling") != scope.get("claim_ceiling"):
        findings.add("invalid_input", "claim_ceiling_expansion_or_mismatch", "request.claim_ceiling")

    scope_budgets = scope.get("budget_envelopes")
    request_budgets = request.get("budget_envelopes")
    if not _closed_object(scope_budgets, required={"branches", "reviews"}, path="snapshots.intent.scope.budget_envelopes", findings=findings):
        return
    if isinstance(scope_budgets, dict) and isinstance(request_budgets, dict):
        for key in ("branches", "reviews"):
            maximum = scope_budgets.get(key)
            asked = request_budgets.get(key)
            if not _positive_int(maximum, f"snapshots.intent.scope.budget_envelopes.{key}", findings):
                continue
            if isinstance(asked, int) and not isinstance(asked, bool) and asked > maximum:
                findings.add("invalid_input", "budget_envelope_expansion", f"request.budget_envelopes.{key}")

    scope_stops = scope.get("stop_conditions")
    request_stops = request.get("stop_conditions")
    if not _closed_object(scope_stops, required=_STOP_KEYS, path="snapshots.intent.scope.stop_conditions", findings=findings):
        return
    if isinstance(scope_stops, dict) and isinstance(request_stops, dict):
        for key in _STOP_KEYS:
            inherited = scope_stops.get(key)
            proposed = request_stops.get(key)
            if (
                not isinstance(inherited, str)
                or inherited not in _STOP_VALUES
                or not isinstance(proposed, str)
                or proposed not in _STOP_VALUES
            ):
                findings.add("invalid_input", "contradictory_or_unknown_stop_condition", f"request.stop_conditions.{key}")
            elif _STOP_VALUES[proposed] < _STOP_VALUES[inherited]:
                findings.add("invalid_input", "stop_condition_weakens_inherited_rule", f"request.stop_conditions.{key}")

    proposed_predicates = request.get("success_predicates")
    if isinstance(proposed_predicates, list) and all(isinstance(item, str) for item in proposed_predicates):
        normalized_predicates = {_compact_token(item) for item in proposed_predicates}
        normalized_shortcuts = {_compact_token(item) for item in contract.forbidden_shortcuts}
        has_run_pass = any("runpass" in item for item in normalized_predicates)
        has_goal_completion = any(
            "goalcomplete" in item or "goalsatisfied" in item
            for item in normalized_predicates
        )
        # This non-promotion invariant is fixed by the G1 work order. The
        # supplied contract is untrusted input and cannot remove it.
        if has_run_pass:
            findings.add("invalid_input", "forbidden_completion_shortcut", "request.success_predicates")
        if has_run_pass and has_goal_completion:
            findings.add("invalid_input", "run_pass_cannot_infer_goal_completion", "request.success_predicates")
        if set(proposed_predicates) != set(contract.acceptance_predicates):
            findings.add("invalid_input", "completion_predicate_policy_expansion_or_loss", "request.success_predicates")
        if normalized_predicates.intersection(normalized_shortcuts):
            findings.add("invalid_input", "forbidden_completion_shortcut", "request.success_predicates")


def _validate_parent(
    goal: GoalRecord,
    parent_goal: GoalRecord | None,
    parent_input: Any,
    bindings: Mapping[str, Any],
    findings: _Findings,
) -> None:
    declared_parent = bindings.get("parent_goal_id")
    declared_version = bindings.get("parent_goal_version")
    if goal.parent_goal_id is None:
        if declared_parent is not None or declared_version is not None or parent_input is not None:
            findings.add("stale_or_unbound", "unexpected_parent_binding", "bindings.parent_goal_id")
        return
    if declared_parent is None or declared_version is None or parent_goal is None:
        findings.add("stale_or_unbound", "parent_goal_unbound", "bindings.parent_goal_id")
        return
    if declared_parent != goal.parent_goal_id or parent_goal.goal_id != goal.parent_goal_id:
        findings.add("stale_or_unbound", "parent_goal_id_mismatch", "bindings.parent_goal_id")
    if declared_version != parent_goal.version:
        findings.add("stale_or_unbound", "parent_goal_version_mismatch", "bindings.parent_goal_version")
    if parent_goal.namespace != goal.namespace:
        findings.add("stale_or_unbound", "parent_namespace_requires_verified_delegation", "snapshots.parent_goal.namespace")
    if parent_goal.parent_goal_id is not None:
        findings.add("stale_or_unbound", "parent_ancestor_lineage_unbound", "snapshots.parent_goal.parent_goal_id")
    if parent_goal.goal_id == goal.goal_id:
        findings.add("stale_or_unbound", "goal_cannot_parent_itself", "snapshots.parent_goal.goal_id")
    if isinstance(parent_input, dict) and parent_input.get("objective_digest") != parent_goal.objective_digest():
        findings.add("stale_or_unbound", "parent_objective_digest_mismatch", "snapshots.parent_goal.objective_digest")


def _render_markdown(report: Mapping[str, Any]) -> str:
    status = report["preflight_status"]
    structural = report["structural_outcome"]
    bindings = report.get("bindings", {})
    request = report.get("request_summary", {})
    findings = report.get("findings", [])
    refs = report.get("source_refs", {})

    def display_list(key: str) -> str:
        values = request.get(key, [])
        if not isinstance(values, list) or not values or not all(isinstance(item, str) for item in values):
            return "unknown"
        return ", ".join(values)

    action = "fix malformed input" if status == "INVALID_INPUT" else "Owner review required"
    lines = [
        "# Offline Goal intake preflight",
        "",
        f"- Preflight status: {status}",
        f"- Structural result: {structural}",
        f"- Exact input SHA-256: {report['raw_request_sha256']}",
        f"- Intent binding: {bindings.get('intent_id', 'UNBOUND')}@{bindings.get('intent_version_declared', 'UNBOUND')}",
        f"- Goal binding: {bindings.get('goal_id', 'UNBOUND')}@{bindings.get('goal_version_declared', 'UNBOUND')}",
        f"- Completion Contract: {bindings.get('completion_contract_id_declared', 'UNBOUND')}",
        f"- Objective digest match: {bindings.get('objective_digest_declared') == bindings.get('objective_digest_computed')}",
        f"- Parent Goal: {bindings.get('parent_goal_id_declared') or 'none'}",
        f"- Proposed success predicates: {display_list('proposed_success_predicates')}",
        f"- Allowed source kinds: {display_list('allowed_source_kinds')}",
        f"- Required evidence types: {display_list('required_evidence_types')}",
        f"- Proposed budget envelope: branches={request.get('budget_envelopes', {}).get('branches', 'unknown')}, reviews={request.get('budget_envelopes', {}).get('reviews', 'unknown')}",
        f"- Claim ceiling: {request.get('claim_ceiling', 'unknown')}",
        f"- Completion authority in supplied contract: {request.get('completion_authority', 'unknown')}; forbidden shortcuts: {display_list('forbidden_shortcuts')}",
        f"- Owner identity: {report['authority']['owner_identity']}; source currentness: {report['authority']['source_currentness']}",
        f"- Required action: {action}",
        "- Canonical writes: false; Goal lifecycle mutation: false; completion decision: false; dispatch: false.",
        "",
        "## Findings",
        "",
    ]
    if findings:
        lines.extend(f"- {item['category']}: {item['code']} ({item['path']})" for item in findings)
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Source anchors",
        "",
    ])
    for key, label in (("work_order", "Work order"), ("steering_contract", "Steering contract"), ("steering_implementation", "Steering implementation")):
        source = refs.get(key, {})
        if isinstance(source, dict) and source.get("ref"):
            lines.append(f"- {label}: `{source['ref']}` (blob `{source.get('blob_sha', 'unknown')}`)")
    lines.extend([
        "",
        "A clear drift projection is limited to the supplied snapshot bytes. This offline adapter cannot prove ownership or currentness.",
        "",
    ])
    return "\n".join(lines)


def _allowlisted_input(path_text: str) -> Path:
    fixture_root = (Path(__file__).resolve().parent / "fixtures").resolve()
    candidate = Path(path_text)
    if not candidate.is_absolute():
        candidate = Path(os.path.abspath(Path.cwd() / candidate))
    else:
        candidate = Path(os.path.abspath(candidate))
    try:
        relative = candidate.relative_to(fixture_root)
    except ValueError as exc:
        raise ValueError("input path is outside the synthetic fixture allowlist") from exc
    current = fixture_root
    for component in relative.parts:
        current = current / component
        if current.is_symlink():
            raise ValueError("input must not traverse symlinks")
    try:
        candidate.resolve(strict=True).relative_to(fixture_root)
    except (OSError, ValueError) as exc:
        raise ValueError("input path resolves outside the synthetic fixture allowlist") from exc
    if not candidate.is_file():
        raise ValueError("input must be a regular, non-symlink fixture file")
    return candidate


def _new_report_dir(path_text: str) -> Path:
    raw = Path(path_text)
    raw_absolute = Path(os.path.abspath(raw if raw.is_absolute() else Path.cwd() / raw))
    if raw_absolute.is_symlink():
        raise ValueError("report directory cannot be a symlink")
    try:
        path = raw_absolute.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise ValueError("report directory path cannot be resolved safely") from exc
    allowed_roots = {Path(tempfile.gettempdir()).resolve()}
    conventional_tmp = Path("/tmp")
    if conventional_tmp.exists():
        allowed_roots.add(conventional_tmp.resolve())
    if not any(path != root and root in path.parents for root in allowed_roots):
        raise ValueError("report directory must be below an allowed temporary output root")
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        raise ValueError("report directory must be new or empty")
    path.mkdir(parents=True, exist_ok=True)
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline, read-only V1 Goal intake preflight")
    parser.add_argument("--input", required=True, help="local JSON fixture under this package's fixtures directory")
    parser.add_argument("--report-dir", required=True, help="new or empty local directory for two report files")
    args = parser.parse_args(argv)
    try:
        input_path = _allowlisted_input(args.input)
        report_dir = _new_report_dir(args.report_dir)
        with input_path.open("rb") as stream:
            raw = stream.read(_MAX_INPUT_BYTES + 1)
        report = evaluate_request(raw)
        json_path = report_dir / "admission-report.json"
        markdown_path = report_dir / "summary.md"
        with json_path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
        with markdown_path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(_render_markdown(report))
    except (OSError, ValueError) as exc:
        print(f"g1-goal-intake: {exc}", file=sys.stderr)
        return 2
    print(f"preflight_status={report['preflight_status']}")
    print(f"structural_outcome={report['structural_outcome']}")
    print(f"report={json_path}")
    print(f"summary={markdown_path}")
    return 0
