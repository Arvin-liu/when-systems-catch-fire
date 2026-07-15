#!/usr/bin/env python3
"""Validate the 121Q12 effectual-action and mechanism-adjudication overlay."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_CALIBRATION_KEYS = {
    "external_source",
    "repository_artifact",
    "executable_test_or_CI",
    "real_world_response",
    "human_judgment",
    "independent_model_or_review",
}

CLAIM_CEILINGS = {
    "artifact_created",
    "schema_validated",
    "workflow_passed",
    "implementation_observed",
    "mechanism_plausible",
    "mechanism_discriminated",
    "causal_identification_pending",
    "insufficient_evidence",
}

POSITIVE_WORDS = {
    "complete",
    "correct",
    "excellent",
    "breakthrough",
    "revolutionary",
    "mature",
    "green",
    "accepted",
    "verified",
}


def load_json(path: str) -> object:
    with (ROOT / path).open(encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: str) -> list[object]:
    rows: list[object] = []
    with (ROOT / path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                rows.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise AssertionError(f"{path}:{line_number}: invalid JSONL: {exc}") from exc
    return rows


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_effectual_record(record: dict, source: str) -> None:
    required = {
        "current_state_ref",
        "who_we_are",
        "what_we_know",
        "whom_we_can_reach",
        "available_assets",
        "reversible_action",
        "affordable_loss",
        "real_commitments",
        "expected_state_change",
        "information_gain",
        "capability_gain",
        "real_commitment_gain",
        "option_space_gain",
        "surprise_observed",
        "next_state_update",
        "conditions",
        "charter_gate",
    }
    require(required <= record.keys(), f"{source}: effectual record missing {sorted(required - record.keys())}")
    require(record.get("mode") in {"EFFECTUAL", "CAUSAL"}, f"{source}: invalid mode")
    require(record.get("mode_reason"), f"{source}: mode switch reason missing")
    loss_keys = {"time", "money", "ai_quota", "reputation", "maintenance_load", "opportunity_cost", "sleep_or_attention"}
    require(loss_keys <= record["affordable_loss"].keys(), f"{source}: affordable loss dimensions incomplete")
    condition_keys = {"stop", "pivot", "scale", "rollback"}
    require(condition_keys <= record["conditions"].keys(), f"{source}: stop/pivot/scale/rollback incomplete")
    charter_keys = {
        "affected_subjects",
        "expected_benefit",
        "cost_bearers",
        "reversibility",
        "harm_visibility",
        "maintainer_sustainability",
        "evidence_threshold_for_scaling",
        "gate_status",
    }
    require(charter_keys <= record["charter_gate"].keys(), f"{source}: Charter Gate fields incomplete")
    for commitment in record["real_commitments"]:
        require(commitment.get("resource") and commitment.get("verification"), f"{source}: real commitment lacks resource or verification")


def validate_mechanism_map(record: dict, source: str, expected_phase: str) -> None:
    required = {
        "phenomenon",
        "question",
        "variables_or_components",
        "observed_changes",
        "candidate_paths",
        "directionality",
        "boundary_conditions",
        "mediators",
        "moderators",
        "alternative_mechanisms",
        "counterfactuals",
        "observable_predictions",
        "distinguishing_tests",
        "evidence_for",
        "evidence_against",
        "unknowns",
        "value_conflicts",
        "claim_ceiling",
        "downgrade_conditions",
    }
    require(required <= record.keys(), f"{source}: mechanism map missing {sorted(required - record.keys())}")
    require(record.get("review_phase") == expected_phase, f"{source}: expected phase {expected_phase}")
    require(record["claim_ceiling"] in CLAIM_CEILINGS, f"{source}: invalid claim ceiling")
    require(record["alternative_mechanisms"], f"{source}: strongest alternatives missing")
    require(record["distinguishing_tests"], f"{source}: distinguishing tests missing")
    require(record["downgrade_conditions"], f"{source}: downgrade conditions missing")
    require("value_conflicts" in record, f"{source}: value conflicts must be separate")


def validate_pilots() -> None:
    pilot_dir = ROOT / "data/architecture/pilots"
    pilot_paths = sorted(pilot_dir.glob("*.json"))
    require(len(pilot_paths) == 3, "expected exactly three historical pilot records")
    expected = {"PILOT-121Q7-MAIL-STORM", "PILOT-121Q4-NODE-DRIFT", "PILOT-121Q8-CHARTER-LICENSING"}
    seen = set()
    for path in pilot_paths:
        pilot = load_json(str(path.relative_to(ROOT)))
        source = str(path.relative_to(ROOT))
        seen.add(pilot["id"])
        require(pilot.get("history_mode") == "read_only", f"{source}: pilot must be read_only")
        validate_effectual_record(pilot["effectual_action_record"], source)
        validate_mechanism_map(pilot["m0"], source, "M0_PRE_ACTION_SKETCH")
        validate_mechanism_map(pilot["m1"], source, "M1_POST_ACTION_ADJUDICATION")
        require(pilot.get("observed_result"), f"{source}: observed result missing")
        require(pilot.get("strongest_residual_counterevidence"), f"{source}: residual counterevidence missing")
    require(seen == expected, f"pilot set mismatch: {sorted(seen)}")


def validate_calibration() -> None:
    record = load_json("data/architecture/calibration/121q12-output-calibration.json")
    review = record["stance_blind_review"]
    require(set(review["reviewer_input"]) == {"artifact", "claim", "evidence", "mechanism_map", "failure_conditions"}, "stance-blind reviewer input incomplete")
    require(review["not_deception"] is True, "stance-blind review must state not_deception=true")
    require(set(record["calibration_sources"].keys()) == REQUIRED_CALIBRATION_KEYS, "calibration source categories mismatch")
    require(record["positive_claim_bindings"], "positive claim bindings missing")
    bound_words = {item["word"].lower() for item in record["positive_claim_bindings"]}
    require(POSITIVE_WORDS & bound_words, "positive evaluation bindings must include at least one governed word")
    for item in record["positive_claim_bindings"]:
        for key in ("object", "criterion", "version", "evidence", "boundary"):
            require(item.get(key), f"positive binding for {item.get('word')} missing {key}")
    require(record["strongest_residual_countermechanism"], "strongest residual countermechanism missing")
    require(record["non_sycophancy_status"] in {"PASS", "CONSTRAINED_PASS", "FAIL", "PENDING"}, "invalid non-sycophancy status")


def validate_run_state() -> None:
    state = load_json("data/architecture/121q12-run-state.json")
    require(state["draft_pr"] == 47, "run-state must point to Draft PR #47")
    require(state["base_main_head"] == "8189dde91d0adbb7957c8aa642bc76d14afe6534", "unexpected base main head")
    require(len(state["steps"]) == 5, "run-state must contain five macro steps")
    statuses = {step["step"]: step["status"] for step in state["steps"]}
    require(statuses == {"000": "complete", "001": "complete", "002": "complete", "003": "complete", "004": "complete"}, "all steps must be complete")
    ledger = load_jsonl("data/architecture/121q12-ledger.jsonl")
    require([row["step"] for row in ledger] == ["000", "001", "002", "003", "004"], "ledger must contain steps 000-004 in order")


def validate_baseline() -> None:
    baseline = load_json("data/architecture/121q12-baseline.json")
    require(baseline["architecture_audit"]["truth_relationships_changed"] is False, "overlay must not change truth relationships")
    frozen = baseline["frozen_boundaries"]
    require(not frozen["psi0_definitions_modified"], "Psi0 boundary violated")
    require(not frozen["project_state_085_modified"], "085 boundary violated")
    require(not frozen["legacy_tables_modified"], "legacy table boundary violated")
    require(not frozen["historical_evidence_cards_modified"], "evidence card boundary violated")


def main() -> int:
    try:
        validate_baseline()
        validate_pilots()
        validate_calibration()
        validate_run_state()
    except AssertionError as exc:
        print(f"121Q12 overlay validation failed: {exc}", file=sys.stderr)
        return 1
    print("121Q12 overlay validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
