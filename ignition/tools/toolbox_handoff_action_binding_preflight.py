#!/usr/bin/env python3
"""Check caller-supplied handoff, action, approval, lease, and receiver bindings."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any

from jsonschema import Draft202012Validator


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve()
IGNITION_ROOT = HERE.parents[1]
sys.path.insert(0, str(IGNITION_ROOT))
sys.path.insert(0, str(HERE.parent))

from agent_federation.contracts import (  # noqa: E402
    ExecutorDescriptor,
    FederatedHandoffBundle,
    FederatedResultReceipt,
)
from agent_runtime.actions import ExecutionPacket  # noqa: E402
from agent_runtime.control import (  # noqa: E402
    ApprovalDecisionR1,
    ApprovalRequestR1,
    ExecutionLease,
)
from toolbox_receiver_handoff_preflight import evaluate as evaluate_receiver_preflight  # noqa: E402


TOOL_ID = "collaboration.preflight_handoff_action_binding"
TOOL_VERSION = "0.1.0"
INPUT_SCHEMA_VERSION = "handoff-action-binding-preflight-r0"
OUTPUT_SCHEMA_VERSION = "handoff-action-binding-preflight-result-r0"
MAX_INPUT_BYTES = 262_144
MAX_FINDINGS = 64
SCHEMA_PATH = IGNITION_ROOT / "schemas/operations/toolbox-handoff-action-binding-input-r0.schema.json"
CLAIM_CEILING = (
    "Checks exact consistency among caller-supplied Federation receipt/handoff, one local ExecutionPacket, "
    "its approval request/decision and execution lease, a caller-supplied receiver descriptor, and explicit "
    "artifact/state/version expectations. It does not authenticate any record or actor, establish that a state "
    "observation is current, accept a handoff, grant authority, invoke a runtime, prove an external effect, or "
    "establish task correctness or scientific validity."
)


class DuplicateJSONKey(ValueError):
    """Raised when a JSON object repeats a key."""


class InputError(ValueError):
    """Raised for malformed or out-of-contract input."""


def _reject_constant(value: str) -> None:
    raise InputError("NONFINITE_JSON_NUMBER:" + value)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJSONKey
        result[key] = value
    return result


def _finding(code: str, path: str) -> dict[str, str]:
    return {"code": code, "path": path}


def _base_result(
    status: str,
    checks: dict[str, str],
    source_handoff_preflight: dict[str, Any],
    findings: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "status": status,
        "checks": checks,
        "source_handoff_preflight": source_handoff_preflight,
        "findings": findings[:MAX_FINDINGS],
        "authorization_record_authenticity": "NOT_AUTHENTICATED_CALLER_SUPPLIED_RECORDS",
        "receipt_authenticity": "NOT_ESTABLISHED_UNKEYED_DIGEST",
        "task_state_observation": "CALLER_DECLARED_REVISION_COMPARISON_ONLY",
        "handoff_accepted": False,
        "execution_authorized": False,
        "runtime_invoked": False,
        "claim_ceiling": CLAIM_CEILING,
    }


def _schema_findings(document: Any) -> list[dict[str, str]]:
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        errors = sorted(
            Draft202012Validator(schema).iter_errors(document),
            key=lambda item: (list(map(str, item.absolute_path)), item.validator or ""),
        )
    except (OSError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise InputError("INPUT_SCHEMA_UNAVAILABLE_OR_INVALID") from exc
    return [
        _finding(
            "INPUT_SCHEMA_INVALID",
            "$" + ("/" + "/".join(map(str, error.absolute_path)) if error.absolute_path else ""),
        )
        for error in errors[:MAX_FINDINGS]
    ]


def _compare(checks: dict[str, str], findings: list[dict[str, str]], name: str, ok: bool, code: str, path: str) -> None:
    checks[name] = "MATCH" if ok else "MISMATCH"
    if not ok:
        findings.append(_finding(code, path))


def evaluate(document: Any) -> tuple[dict[str, Any], int]:
    """Compare exact caller-declared bindings; never accept or execute the handoff."""
    empty_checks = {
        "receipt_to_handoff_projection": "NOT_RUN",
        "receiver_capability_and_reobservation": "NOT_RUN",
        "pending_action_id": "NOT_RUN",
        "target_artifact_and_source_digest": "NOT_RUN",
        "source_revision": "NOT_RUN",
        "task_state_revision": "NOT_RUN",
        "approval_request_decision_packet": "NOT_RUN",
        "authorization_reference": "NOT_RUN",
        "execution_lease_packet": "NOT_RUN",
        "packet_handoff_context": "NOT_RUN",
        "receiver_identity_and_interface_version": "NOT_RUN",
        "native_resume_compatibility": "NOT_RUN",
        "external_session_reference_support": "NOT_RUN",
    }
    empty_source = {"status": "NOT_RUN", "checks": {}}
    if not isinstance(document, dict):
        result = _base_result("INPUT_INVALID", empty_checks, empty_source, [_finding("INPUT_MUST_BE_OBJECT", "$")])
        return result, 2
    schema_findings = _schema_findings(document)
    if schema_findings:
        result = _base_result("INPUT_INVALID", empty_checks, empty_source, schema_findings)
        return result, 2

    expected = document["expected"]
    try:
        receipt = FederatedResultReceipt.from_dict(document["source_receipt"])
        bundle = FederatedHandoffBundle.from_dict(document["handoff_bundle"])
        receiver = ExecutorDescriptor.from_dict(document["receiver_descriptor"])
        packet = ExecutionPacket.from_dict(document["execution_packet"])
        approval_request = ApprovalRequestR1.from_dict(document["approval_request"])
        approval_decision = ApprovalDecisionR1.from_dict(document["approval_decision"])
        lease = ExecutionLease.from_dict(document["execution_lease"])
    except (TypeError, ValueError, KeyError, RecursionError) as exc:
        result = _base_result(
            "INPUT_INVALID",
            empty_checks,
            empty_source,
            [_finding("TYPED_RECORD_INVALID", "$/records")],
        )
        return result, 2

    checks = dict(empty_checks)
    findings: list[dict[str, str]] = []

    receiver_input = {
        "schema_version": "receiver-handoff-preflight-r0",
        "source_receipt": receipt.to_dict(),
        "handoff_bundle": bundle.to_dict(),
        "target_executor_id": receiver.executor_id,
        "target_capabilities": list(receiver.capability_tokens),
        "workspace_reobserved": document["workspace_reobserved"],
        "observed_artifact_refs": document["observed_artifact_refs"],
    }
    source_result, source_code = evaluate_receiver_preflight(receiver_input)
    checks["receipt_to_handoff_projection"] = source_result["checks"].get("handoff_bundle_binding", "NOT_RUN")
    receiver_precondition = source_result["checks"].get("receiver_capability_and_reobservation", "NOT_RUN")
    # The existing preflight uses ACCEPTED for this declared precondition result;
    # keep the composite tool's top-level wording from sounding like handoff acceptance.
    checks["receiver_capability_and_reobservation"] = "PASS" if receiver_precondition == "ACCEPTED" else receiver_precondition
    if source_code != 0:
        findings.append(_finding("SOURCE_HANDOFF_OR_RECEIVER_PREFLIGHT_BLOCKED", "$/handoff_bundle"))

    _compare(
        checks,
        findings,
        "pending_action_id",
        packet.action_id in bundle.pending_work,
        "ACTION_ID_NOT_EXACTLY_DECLARED_PENDING",
        "$/execution_packet/action_id",
    )

    payload = dict(packet.payload)
    target_ref = expected["target_artifact_ref"]
    target_sha = expected["target_artifact_sha256"]
    artifact_rows = [item.to_dict() for item in (*receipt.artifact_refs, *bundle.artifact_refs)]
    receipt_refs = {item.ref: item.sha256 for item in receipt.artifact_refs}
    bundle_refs = {item.ref: item.sha256 for item in bundle.artifact_refs}
    _compare(
        checks,
        findings,
        "target_artifact_and_source_digest",
        bool(artifact_rows)
        and receipt_refs.get(target_ref) == target_sha
        and bundle_refs.get(target_ref) == target_sha
        and payload.get("handoff_target_artifact_ref") == target_ref
        and payload.get("handoff_target_artifact_sha256") == target_sha,
        "TARGET_ARTIFACT_OR_SOURCE_DIGEST_NOT_BOUND",
        "$/expected/target_artifact_ref",
    )

    _compare(
        checks,
        findings,
        "source_revision",
        payload.get("handoff_source_revision") == expected["source_revision"],
        "SOURCE_REVISION_NOT_BOUND_TO_ACTION_PACKET",
        "$/expected/source_revision",
    )

    _compare(
        checks,
        findings,
        "task_state_revision",
        payload.get("handoff_task_state_revision") == expected["task_state_revision"]
        and expected["task_state_revision"] == expected["receiver_observed_task_state_revision"],
        "TASK_STATE_REVISION_MISSING_OR_MISMATCHED",
        "$/expected/task_state_revision",
    )

    packet_digest = packet.action_digest
    approval_request_matches = (
        approval_request.run_id == packet.run_id
        and approval_request.action_id == packet.action_id
        and approval_request.action_digest == packet_digest
        and tuple(approval_request.requested_capabilities) == tuple(packet.required_capabilities)
        and tuple(approval_request.requested_reads) == tuple(packet.requested_reads)
        and tuple(approval_request.requested_writes) == tuple(packet.requested_writes)
        and approval_request.status == "ALLOWED"
    )
    decision_matches = (
        approval_decision.request_id == approval_request.request_id
        and approval_decision.run_id == packet.run_id
        and approval_decision.action_digest == packet_digest
        and approval_decision.decision == "ALLOW"
    )
    caps_within_declarations = (
        set(packet.required_capabilities) <= set(bundle.allowed_capabilities)
        and set(packet.required_capabilities) <= set(receiver.capability_tokens)
    )
    _compare(
        checks,
        findings,
        "approval_request_decision_packet",
        approval_request_matches and decision_matches and caps_within_declarations,
        "APPROVAL_OR_CAPABILITY_BINDING_MISMATCH",
        "$/approval_request",
    )
    _compare(
        checks,
        findings,
        "authorization_reference",
        expected["authorization_ref"] == approval_decision.decision_id
        and payload.get("handoff_authorization_ref") == expected["authorization_ref"],
        "AUTHORIZATION_REFERENCE_MISMATCH",
        "$/expected/authorization_ref",
    )

    lease_matches = (
        lease.run_id == packet.run_id
        and lease.action_id == packet.action_id
        and lease.idempotency_key == packet.idempotency_key
        and lease.packet_digest == packet_digest
        and lease.lease_id == approval_request.lease_id
        and lease.executor_class_id == receiver.executor_id
        and lease.status == "ACTIVE"
        and lease.issued_at <= time.time() < lease.expires_at
    )
    _compare(
        checks,
        findings,
        "packet_handoff_context",
        payload.get("handoff_action_id") == packet.action_id
        and payload.get("handoff_receiver_executor_id") == expected["receiver_executor_id"]
        and payload.get("handoff_receiver_adapter_version") == expected["receiver_adapter_version"],
        "ACTION_PACKET_CONTEXT_MISMATCH",
        "$/execution_packet/payload",
    )

    _compare(
        checks,
        findings,
        "execution_lease_packet",
        lease_matches,
        "EXECUTION_LEASE_NOT_BOUND_TO_PACKET_AND_RECEIVER",
        "$/execution_lease",
    )

    _compare(
        checks,
        findings,
        "receiver_identity_and_interface_version",
        receiver.executor_id == expected["receiver_executor_id"]
        and receiver.adapter_version == expected["receiver_adapter_version"]
        and payload.get("handoff_receiver_executor_id") == receiver.executor_id
        and payload.get("handoff_receiver_adapter_version") == receiver.adapter_version,
        "RECEIVER_INTERFACE_VERSION_MISMATCH",
        "$/expected/receiver_adapter_version",
    )

    native_resume_ok = not expected["native_resume_required"] or receiver.native_resume_support
    checks["native_resume_compatibility"] = (
        "SUPPORTED" if expected["native_resume_required"] and native_resume_ok
        else "NOT_REQUIRED" if not expected["native_resume_required"]
        else "UNSUPPORTED"
    )
    if not native_resume_ok:
        findings.append(_finding("RECEIVER_DOES_NOT_DECLARE_NATIVE_RESUME", "$/receiver_descriptor/native_resume_support"))

    unsupported_session_kinds = sorted(
        {item.kind for item in bundle.external_session_refs} - set(receiver.external_session_refs)
    )
    checks["external_session_reference_support"] = "PASS" if not unsupported_session_kinds else "UNSUPPORTED"
    if unsupported_session_kinds:
        findings.append(_finding("RECEIVER_SESSION_REFERENCE_KIND_UNSUPPORTED", "$/handoff_bundle/external_session_refs"))

    status = "DECLARED_BINDINGS_MATCH_NO_AUTHORITY" if not findings else "BLOCKED_OR_INCOMPLETE"
    result = _base_result(status, checks, source_result, findings)
    return result, 0 if not findings else 2


def _read_stdin() -> Any:
    data = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    if len(data) > MAX_INPUT_BYTES:
        raise InputError("INPUT_EXCEEDS_BYTE_LIMIT")
    return json.loads(
        data.decode("utf-8"),
        object_pairs_hook=_unique_object,
        parse_constant=_reject_constant,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True)
    parser.parse_args()
    try:
        document = _read_stdin()
        result, code = evaluate(document)
    except DuplicateJSONKey:
        result = _base_result(
            "INPUT_INVALID",
            {
                "receipt_to_handoff_projection": "NOT_RUN",
                "receiver_capability_and_reobservation": "NOT_RUN",
                "pending_action_id": "NOT_RUN",
                "target_artifact_and_source_digest": "NOT_RUN",
                "source_revision": "NOT_RUN",
                "task_state_revision": "NOT_RUN",
                "approval_request_decision_packet": "NOT_RUN",
                "authorization_reference": "NOT_RUN",
                "execution_lease_packet": "NOT_RUN",
                "packet_handoff_context": "NOT_RUN",
                "receiver_identity_and_interface_version": "NOT_RUN",
                "native_resume_compatibility": "NOT_RUN",
                "external_session_reference_support": "NOT_RUN",
            },
            {"status": "NOT_RUN", "checks": {}},
            [_finding("DUPLICATE_JSON_KEY", "$")],
        )
        code = 2
    except (InputError, UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        result = _base_result(
            "INPUT_INVALID",
            {
                "receipt_to_handoff_projection": "NOT_RUN",
                "receiver_capability_and_reobservation": "NOT_RUN",
                "pending_action_id": "NOT_RUN",
                "target_artifact_and_source_digest": "NOT_RUN",
                "source_revision": "NOT_RUN",
                "task_state_revision": "NOT_RUN",
                "approval_request_decision_packet": "NOT_RUN",
                "authorization_reference": "NOT_RUN",
                "execution_lease_packet": "NOT_RUN",
                "packet_handoff_context": "NOT_RUN",
                "receiver_identity_and_interface_version": "NOT_RUN",
                "native_resume_compatibility": "NOT_RUN",
                "external_session_reference_support": "NOT_RUN",
            },
            {"status": "NOT_RUN", "checks": {}},
            [_finding("INPUT_INVALID_OR_OVERSIZED", "$")],
        )
        code = 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
