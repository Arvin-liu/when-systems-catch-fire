#!/usr/bin/env python3
"""Check whether a serialized receiver handoff matches its public source receipt."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve()
IGNITION_ROOT = HERE.parents[1]
sys.path.insert(0, str(IGNITION_ROOT))

from agent_federation.approval_handoff import (  # noqa: E402
    ApprovalHandoffError,
    accept_handoff,
    build_handoff_bundle,
)
from agent_federation.contracts import (  # noqa: E402
    FederatedHandoffBundle,
    FederatedResultReceipt,
)


TOOL_ID = "collaboration.preflight_receiver_handoff"
TOOL_VERSION = "0.1.0"
INPUT_SCHEMA_VERSION = "receiver-handoff-preflight-r0"
MAX_INPUT_BYTES = 262_144
INPUT_KEYS = {
    "schema_version",
    "source_receipt",
    "handoff_bundle",
    "target_executor_id",
    "target_capabilities",
    "workspace_reobserved",
    "observed_artifact_refs",
}
CLAIM_CEILING = (
    "Checks a public FederatedResultReceipt's canonical self-digest, verifies that a serialized "
    "FederatedHandoffBundle is the projection produced from that receipt, and runs the existing "
    "capability/re-observation precheck. It does not authenticate receipt origin, observe a workspace, "
    "authorize or execute actions, enforce runtime isolation, or establish task correctness."
)


class DuplicateJSONKey(ValueError):
    """Raised when an input object repeats a JSON key."""


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
    findings: list[dict[str, str]],
    *,
    workspace_reobserved: bool | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "receiver-handoff-preflight-result-r0",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "status": status,
        "checks": checks,
        "findings": findings,
        "receipt_authenticity": "NOT_ESTABLISHED_UNKEYED_DIGEST",
        "workspace_reobservation": (
            "NOT_EVALUATED"
            if workspace_reobserved is None
            else "CALLER_ASSERTED_NOT_INDEPENDENTLY_OBSERVED"
            if workspace_reobserved
            else "NOT_ASSERTED"
        ),
        "execution_authorized": False,
        "runtime_enforcement_status": "NOT_EVALUATED",
        "claim_ceiling": CLAIM_CEILING,
    }


def _string_list(value: Any, field: str) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) and bool(item.strip()) for item in value)


def _input_error(code: str, path: str) -> tuple[dict[str, Any], int]:
    return _base_result(
        "INPUT_INVALID",
        {
            "source_receipt_canonical_digest": "NOT_RUN",
            "handoff_bundle_binding": "NOT_RUN",
            "receiver_capability_and_reobservation": "NOT_RUN",
        },
        [_finding(code, path)],
    ), 2


def _bundle_projection(receipt: FederatedResultReceipt, bundle: FederatedHandoffBundle) -> FederatedHandoffBundle:
    receipt_unresolveds = set(receipt.unresolveds)
    additional_unresolveds = tuple(value for value in bundle.unresolveds if value not in receipt_unresolveds)
    return build_handoff_bundle(
        handoff_id=bundle.handoff_id,
        source_receipt=receipt,
        goal=bundle.goal,
        pending_work=bundle.pending_work,
        allowed_capabilities=bundle.allowed_capabilities,
        workspace_refs=bundle.workspace_refs,
        acceptance_criteria=bundle.acceptance_criteria,
        operational_memory_capsule_refs=bundle.operational_memory_capsule_refs,
        unresolveds=additional_unresolveds,
    )


def evaluate(document: Any) -> tuple[dict[str, Any], int]:
    """Return a bounded preflight result and process status; never execute a takeover."""
    if not isinstance(document, dict):
        return _input_error("INPUT_MUST_BE_OBJECT", "$")
    if set(document) != INPUT_KEYS:
        return _input_error("INPUT_KEYS_MISMATCH", "$")
    if document.get("schema_version") != INPUT_SCHEMA_VERSION:
        return _input_error("INPUT_SCHEMA_VERSION_UNSUPPORTED", "$/schema_version")
    if not isinstance(document.get("source_receipt"), dict):
        return _input_error("SOURCE_RECEIPT_MUST_BE_OBJECT", "$/source_receipt")
    if not isinstance(document.get("handoff_bundle"), dict):
        return _input_error("HANDOFF_BUNDLE_MUST_BE_OBJECT", "$/handoff_bundle")
    if not isinstance(document.get("target_executor_id"), str) or not document["target_executor_id"].strip():
        return _input_error("TARGET_EXECUTOR_ID_INVALID", "$/target_executor_id")
    if not _string_list(document.get("target_capabilities"), "target_capabilities"):
        return _input_error("TARGET_CAPABILITIES_INVALID", "$/target_capabilities")
    if not isinstance(document.get("workspace_reobserved"), bool):
        return _input_error("WORKSPACE_REOBSERVED_MUST_BE_BOOLEAN", "$/workspace_reobserved")
    if not _string_list(document.get("observed_artifact_refs"), "observed_artifact_refs"):
        return _input_error("OBSERVED_ARTIFACT_REFS_INVALID", "$/observed_artifact_refs")
    if len(document["target_capabilities"]) != len(set(document["target_capabilities"])):
        return _input_error("TARGET_CAPABILITIES_DUPLICATE", "$/target_capabilities")
    if len(document["observed_artifact_refs"]) != len(set(document["observed_artifact_refs"])):
        return _input_error("OBSERVED_ARTIFACT_REFS_DUPLICATE", "$/observed_artifact_refs")

    try:
        receipt = FederatedResultReceipt.from_dict(document["source_receipt"])
    except (TypeError, ValueError, KeyError, RecursionError):
        return _input_error("SOURCE_RECEIPT_INVALID", "$/source_receipt")
    try:
        bundle = FederatedHandoffBundle.from_dict(document["handoff_bundle"])
    except (TypeError, ValueError, KeyError, RecursionError):
        return _input_error("HANDOFF_BUNDLE_INVALID", "$/handoff_bundle")

    try:
        expected_bundle = _bundle_projection(receipt, bundle)
    except (ApprovalHandoffError, TypeError, ValueError, KeyError):
        return _base_result(
            "SOURCE_RECEIPT_NOT_HANDOFFABLE",
            {
                "source_receipt_canonical_digest": "PASS",
                "handoff_bundle_binding": "NOT_RUN",
                "receiver_capability_and_reobservation": "NOT_RUN",
            },
            [_finding("SOURCE_RECEIPT_CANNOT_BUILD_HANDOFF", "$/source_receipt")],
            workspace_reobserved=document["workspace_reobserved"],
        ), 2

    actual = bundle.to_dict()
    expected = expected_bundle.to_dict()
    mismatched_fields = [key for key in expected if actual.get(key) != expected[key]]
    if mismatched_fields:
        return _base_result(
            "SOURCE_RECEIPT_BUNDLE_MISMATCH",
            {
                "source_receipt_canonical_digest": "PASS",
                "handoff_bundle_binding": "FAIL",
                "receiver_capability_and_reobservation": "NOT_RUN",
            },
            [_finding("HANDOFF_NOT_SOURCE_RECEIPT_PROJECTION", f"$/handoff_bundle/{key}") for key in mismatched_fields[:32]],
            workspace_reobserved=document["workspace_reobserved"],
        ), 2

    if not receipt.handoff_eligibility.eligible:
        return _base_result(
            "HANDOFF_NOT_ELIGIBLE",
            {
                "source_receipt_canonical_digest": "PASS",
                "handoff_bundle_binding": "PASS",
                "receiver_capability_and_reobservation": "NOT_RUN",
            },
            [_finding("SOURCE_RECEIPT_DECLARES_HANDOFF_INELIGIBLE", "$/source_receipt/handoff_eligibility/eligible")],
            workspace_reobserved=document["workspace_reobserved"],
        ), 2

    try:
        decision = accept_handoff(
            bundle,
            document["target_executor_id"],
            document["target_capabilities"],
            workspace_reobserved=document["workspace_reobserved"],
            source_receipt_verified=True,
            observed_artifact_refs=document["observed_artifact_refs"],
        )
    except (ApprovalHandoffError, TypeError, ValueError, KeyError):
        return _input_error("RECEIVER_PREFLIGHT_INPUT_INVALID", "$/target_executor_id")

    status = "PREFLIGHT_READY_NO_AUTHORITY" if decision.status == "ACCEPTED" else decision.status
    result = _base_result(
        status,
        {
            "source_receipt_canonical_digest": "PASS",
            "handoff_bundle_binding": "PASS",
            "receiver_capability_and_reobservation": decision.status,
        },
        [] if decision.status == "ACCEPTED" else [_finding("RECEIVER_TAKEOVER_PRECONDITION_NOT_MET", "$/target_capabilities")],
        workspace_reobserved=document["workspace_reobserved"],
    )
    result["receiver_reason"] = decision.reason
    return result, 0 if decision.status == "ACCEPTED" else 2


def _read_stdin() -> Any:
    data = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    if len(data) > MAX_INPUT_BYTES:
        raise ValueError("input exceeds the 262144-byte limit")
    return json.loads(data.decode("utf-8"), object_pairs_hook=_unique_object)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded handoff preflight object from stdin")
    parser.parse_args(argv)
    try:
        document = _read_stdin()
        result, code = evaluate(document)
    except DuplicateJSONKey:
        result, code = _input_error("DUPLICATE_JSON_KEY", "$")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError):
        result, code = _input_error("INPUT_UNAVAILABLE_OR_INVALID", "$")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
