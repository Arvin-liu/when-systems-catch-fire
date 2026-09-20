#!/usr/bin/env python3
"""Mechanical validator for the task-local Method-Use Trace R0 adapter.

This validator is deliberately small and offline. It checks structural lineage
and evidence ceilings; it does not run a model, Successor, or Evaluator.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

TASK_ID = "IGNITION-20260920-190"
CLAIM_CEILING = "METHOD_USE_TRACE_IS_EVIDENCE_ARTIFACT_NOT_CAPABILITY_PROOF"
KINDS = [
    "METHOD_CANDIDATE",
    "SELECTION_RATIONALE",
    "CONTEXT",
    "METHOD_USE_EVENT",
    "OBSERVED_OUTCOME_OR_FAILURE",
    "REVISION_OR_DISPOSITION",
]
HEX64 = re.compile(r"^[0-9a-f]{64}$")
COMMON = {
    "segment_id", "segment_kind", "source_ref", "source_sha256",
    "exact_locator", "summary", "uncertainty", "claim_ceiling",
}
OPTIONAL = {
    "candidate_ref", "selected_candidate_ref", "rationale",
    "alternatives_considered", "context_ref", "constraints",
    "used_candidate_ref", "input_ref", "expected_observation",
    "use_order", "use_segment_ref", "outcome_type", "observed_outcome",
    "confounders", "causal_attribution", "revision_type",
    "revision_rationale", "disposition", "target_candidate_ref",
    "rollback_ref",
}
TOP_KEYS = {
    "artifact_type", "schema_version", "task_id", "trace_id", "is_synthetic",
    "segments", "claim_ceiling", "authority_status", "canonical_claim_ids",
    "canonical_promotion", "successor_status", "evaluator_status",
}

class TraceError(ValueError):
    pass

def require(condition: bool, message: str) -> None:
    if not condition:
        raise TraceError(message)

def load(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)

def validate_trace(trace: dict[str, Any]) -> None:
    require(isinstance(trace, dict), "trace is not an object")
    require(set(trace) <= TOP_KEYS, "trace has an unknown top-level field")
    for key in (
        "artifact_type", "schema_version", "task_id", "trace_id",
        "is_synthetic", "segments", "claim_ceiling", "authority_status",
        "canonical_claim_ids", "canonical_promotion", "successor_status",
        "evaluator_status",
    ):
        require(key in trace, "missing top-level field: " + key)
    require(trace["artifact_type"] == "EVALUATION_EVIDENCE", "wrong artifact type")
    require(trace["schema_version"] == "method-use-trace-r0", "wrong schema version")
    require(trace["task_id"] == TASK_ID, "wrong task id")
    require(trace["is_synthetic"] is True, "trace must be synthetic")
    require(trace["claim_ceiling"] == CLAIM_CEILING, "claim ceiling drift")
    require(trace["authority_status"] == "RESEARCH_ONLY", "authority drift")
    require(trace["canonical_claim_ids"] == [], "canonical claim IDs are not empty")
    require(trace["canonical_promotion"] == "NONE", "canonical promotion is not NONE")
    require(trace["successor_status"] == "NOT_RUN", "Successor status drift")
    require(trace["evaluator_status"] == "NOT_RUN", "Evaluator status drift")
    segments = trace["segments"]
    require(isinstance(segments, list) and len(segments) == 6, "trace must contain six ordered segments")
    require([s.get("segment_kind") for s in segments] == KINDS, "segment order/kinds are not the required chain")
    ids = [s.get("segment_id") for s in segments]
    require(all(isinstance(item, str) and item for item in ids), "segment IDs are missing")
    require(len(set(ids)) == len(ids), "segment IDs are not unique")
    candidate = segments[0]
    selection = segments[1]
    context = segments[2]
    use = segments[3]
    outcome = segments[4]
    revision = segments[5]
    for index, segment in enumerate(segments):
        require(isinstance(segment, dict), "segment %d is not an object" % index)
        require(set(segment) <= COMMON | OPTIONAL, "segment %d has an unknown field" % index)
        for key in COMMON:
            require(key in segment, "segment %d missing %s" % (index, key))
        require(isinstance(segment["source_ref"], str) and len(segment["source_ref"]) >= 3, "segment %d source ref invalid" % index)
        require(bool(HEX64.fullmatch(segment["source_sha256"])), "segment %d source fingerprint invalid" % index)
        require(isinstance(segment["exact_locator"], str) and len(segment["exact_locator"]) >= 3, "segment %d locator invalid" % index)
        require(isinstance(segment["summary"], str) and len(segment["summary"]) >= 10, "segment %d summary invalid" % index)
        uncertainty = segment["uncertainty"]
        require(isinstance(uncertainty, dict), "segment %d uncertainty invalid" % index)
        require(uncertainty.get("status") in {"KNOWN", "OBSERVED", "SUPPORTED", "HYPOTHESIS", "UNKNOWN", "NOT_MEASURED", "INCONCLUSIVE"}, "segment %d uncertainty status invalid" % index)
        require(isinstance(uncertainty.get("basis"), list), "segment %d uncertainty basis invalid" % index)
        require(isinstance(uncertainty.get("open_questions"), list), "segment %d open questions invalid" % index)
        ceiling = segment["claim_ceiling"]
        require(isinstance(ceiling, dict), "segment %d claim ceiling invalid" % index)
        require(ceiling.get("authority_status") == "OBSERVATION_ONLY", "segment %d authority is not observation-only" % index)
        require(isinstance(ceiling.get("allowed_claims"), list) and ceiling["allowed_claims"], "segment %d allowed claims missing" % index)
        require(isinstance(ceiling.get("forbidden_inferences"), list) and ceiling["forbidden_inferences"], "segment %d forbidden inferences missing" % index)
    candidate_ref = candidate.get("candidate_ref")
    require(isinstance(candidate_ref, str) and candidate_ref, "candidate ref missing")
    require(selection.get("selected_candidate_ref") == candidate_ref, "selection is not linked to candidate")
    require(isinstance(selection.get("rationale"), str) and len(selection["rationale"]) >= 10, "selection rationale missing")
    require(isinstance(selection.get("alternatives_considered"), list) and selection["alternatives_considered"], "alternatives missing")
    require(context.get("context_ref") == selection["segment_id"], "context does not link to selection")
    require(isinstance(context.get("constraints"), list) and context["constraints"], "context constraints missing")
    require(use.get("used_candidate_ref") == candidate_ref, "use is not linked to candidate")
    require(use.get("input_ref") == context["segment_id"], "use is not linked to context")
    require(isinstance(use.get("expected_observation"), str) and len(use["expected_observation"]) >= 10, "expected observation missing")
    require(isinstance(use.get("use_order"), int) and use["use_order"] >= 1, "use order missing")
    require(outcome.get("use_segment_ref") == use["segment_id"], "outcome is not linked to use")
    require(outcome.get("outcome_type") in {"OBSERVED_OUTCOME", "FAILURE", "NO_DISCRIMINATING_OBSERVATION"}, "outcome type missing")
    require(isinstance(outcome.get("observed_outcome"), str) and len(outcome["observed_outcome"]) >= 10, "observed outcome missing")
    require(isinstance(outcome.get("confounders"), list) and outcome["confounders"], "confounders missing")
    require(outcome.get("causal_attribution") in {"NOT_ESTABLISHED", "SUPPORTED_WITHIN_SYNTHETIC_TRACE", "UNKNOWN"}, "causal attribution missing")
    require(outcome.get("causal_attribution") != "ESTABLISHED", "causal attribution overclaim")
    require(isinstance(revision.get("revision_type"), str), "revision type missing")
    require(isinstance(revision.get("revision_rationale"), str) and len(revision["revision_rationale"]) >= 10, "revision rationale missing")
    require(revision.get("disposition") in {"ADOPT", "REJECT", "COEXIST", "UNRESOLVED", "REVISE", "NO_REVISION", "SUPERSEDE"}, "disposition missing")
    require(revision.get("target_candidate_ref") in {candidate_ref, None}, "revision target is not bound to candidate")

def self_test() -> None:
    ceiling = {
        "authority_status": "OBSERVATION_ONLY",
        "allowed_claims": ["synthetic structural lineage only"],
        "forbidden_inferences": ["capability", "causation", "inheritance"],
    }
    def seg(segment_id: str, kind: str, **extra: Any) -> dict[str, Any]:
        value = {
            "segment_id": segment_id, "segment_kind": kind,
            "source_ref": "synthetic://self-test/" + segment_id,
            "source_sha256": "0" * 64, "exact_locator": "self-test:" + segment_id,
            "summary": "Synthetic self-test segment with bounded evidence.",
            "uncertainty": {"status": "OBSERVED", "basis": ["synthetic fixture"], "open_questions": ["future evaluator"]},
            "claim_ceiling": ceiling,
        }
        value.update(extra)
        return value
    trace = {
        "artifact_type": "EVALUATION_EVIDENCE", "schema_version": "method-use-trace-r0",
        "task_id": TASK_ID, "trace_id": "self-test", "is_synthetic": True,
        "segments": [
            seg("candidate", "METHOD_CANDIDATE", candidate_ref="method:self-test"),
            seg("selection", "SELECTION_RATIONALE", selected_candidate_ref="method:self-test", rationale="The bounded probe matches the stated constraint.", alternatives_considered=["template-only answer"]),
            seg("context", "CONTEXT", context_ref="selection", constraints=["reversible synthetic run"]),
            seg("use", "METHOD_USE_EVENT", used_candidate_ref="method:self-test", input_ref="context", expected_observation="The probe should separate the two synthetic explanations.", use_order=1),
            seg("outcome", "OBSERVED_OUTCOME_OR_FAILURE", use_segment_ref="use", outcome_type="OBSERVED_OUTCOME", observed_outcome="The probe produced a distinguishable synthetic observation.", confounders=["synthetic measurement noise"], causal_attribution="NOT_ESTABLISHED"),
            seg("revision", "REVISION_OR_DISPOSITION", revision_type="NO_REVISION", revision_rationale="The bounded observation did not require a method change.", disposition="NO_REVISION", target_candidate_ref="method:self-test", rollback_ref=None),
        ],
        "claim_ceiling": CLAIM_CEILING, "authority_status": "RESEARCH_ONLY",
        "canonical_claim_ids": [], "canonical_promotion": "NONE",
        "successor_status": "NOT_RUN", "evaluator_status": "NOT_RUN",
    }
    validate_trace(trace)
    broken = json.loads(json.dumps(trace))
    broken["segments"][1].pop("selected_candidate_ref")
    try:
        validate_trace(broken)
    except TraceError:
        return
    raise TraceError("self-test did not reject a broken selection link")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", type=Path)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--expect-invalid", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
            print("METHOD_USE_TRACE_R0_SELF_TEST_OK")
            return 0
        if args.path is None:
            parser.error("path is required unless --self-test is used")
        trace = load(args.path)
        validate_trace(trace)
    except (OSError, json.JSONDecodeError, TraceError) as exc:
        if args.expect_invalid:
            print("EXPECTED_INVALID:" + str(exc))
            return 0
        print("INVALID:" + str(exc))
        return 1
    if args.expect_invalid:
        print("UNEXPECTED_VALID")
        return 1
    print("VALID:" + str(args.path))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
