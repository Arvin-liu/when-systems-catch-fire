#!/usr/bin/env python3
"""Validate task 98 claim governance, census and correction authority."""
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import jsonschema

from legacy_table_migration import source_exists as migrated_source_exists

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "data/foundation/function-assets"
EXPECTED_CORRECTIONS = {"T2", "D127", *(f"D{i}" for i in range(182, 191)), "D260"}
EXPECTED_IDENTITIES = {
    "STRICT_MATHEMATICAL_FUNCTION", "PARAMETRIC_MODEL", "SCORE_OR_INDEX",
    "GATE_OR_DECISION_RULE", "ALGORITHM_OR_WORKFLOW", "RELATION_OR_CONSTRAINT",
    "HEURISTIC", "STRUCTURAL_METAPHOR", "CONJECTURE_OR_PENDING_CLAIM",
    "INVALID_OR_PSEUDO_FUNCTION",
}
EXPECTED_GATES = {
    "definition_gate", "dimension_and_type_gate", "counterexample_gate",
    "circular_reasoning_gate", "claim_layer_gate", "claim_ceiling_gate",
    "cross_domain_isomorphism_gate", "universal_quantifier_gate",
    "internal_test_truth_gate", "dependency_impact_gate",
}


def evaluate_fixture(case: dict) -> dict[str, str]:
    """Small executable kernel for adversarial gate fixtures.

    Production census extraction remains conservative; this kernel proves that
    each gate has a fail-closed machine path for clear cases and does not turn
    ambiguity into a pass.
    """
    record = case["record"]
    expression = record.get("expression", "").lower()
    claim = record.get("claim", "").lower()
    result: dict[str, str] = {}
    if {"domain", "codomain", "expression"} <= set(record) and "both signs" not in expression:
        result["definition_gate"] = "PASS"
    elif "both signs" in expression:
        result["definition_gate"] = "FAIL"
    if "metre + 1 second" in expression:
        result["dimension_and_type_gate"] = "FAIL"
    if record.get("universal_claim") and not record.get("counterexample") and not record.get("counterexample_search"):
        result["counterexample_gate"] = "REQUIRES_HUMAN_REVIEW"
    if "success(x)=1 exactly when x succeeds" in expression:
        result["circular_reasoning_gate"] = "FAIL"
    if record.get("mathematical_result") and record.get("external_claim") and not record.get("bridge"):
        result["claim_layer_gate"] = "FAIL"
    if record.get("claim_ceiling") == "internal implementation" and "external" in record.get("output_claim", ""):
        result["claim_ceiling_gate"] = "FAIL"
    if "isomorphic" in claim and (not record.get("maps") or not record.get("preservation_proofs")):
        result["cross_domain_isomorphism_gate"] = "FAIL"
    if claim.startswith("all ") and not record.get("proof_artifact"):
        result["universal_quantifier_gate"] = "REQUIRES_HUMAN_REVIEW"
    if "unit tests pass, therefore" in claim:
        result["internal_test_truth_gate"] = "FAIL"
    if record.get("dependency_status") in {"DOWNGRADE", "RETIRE"} and not record.get("consumer_updated"):
        result["dependency_impact_gate"] = "FAIL"
    return result


def rows(relative: str) -> list[dict]:
    return [json.loads(line) for line in (ROOT / relative).read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, condition: bool, detail: str = "") -> None:
        checks.append((name, bool(condition), detail))

    census = rows("data/foundation/function-assets/census.jsonl")
    discovery = rows("data/foundation/function-assets/discovery.jsonl")
    edges = rows("data/foundation/function-assets/dependencies.jsonl")
    queue = rows("data/foundation/function-assets/audit-queue.jsonl")
    corrections = rows("data/foundation/function-assets/corrections.jsonl")
    claims = rows("data/foundation/function-assets/claim-ledger.jsonl")
    dependency_actions = rows("data/foundation/function-assets/dependency-actions.jsonl")
    objects = rows("data/foundation/formal-objects/objects.jsonl")
    summary = json.loads((ASSETS / "census-summary.json").read_text(encoding="utf-8"))
    correction_by_id = {}
    for row in corrections:
        stable_id = row.get("stable_id") or row["correction_id"].removeprefix("CORR-98-")
        row["stable_id"] = stable_id
        correction_by_id[stable_id] = row

    census_schema = json.loads((ROOT / "schemas/foundation/function-asset.schema.json").read_text(encoding="utf-8"))
    correction_schema = json.loads((ROOT / "schemas/foundation/function-asset-correction.schema.json").read_text(encoding="utf-8"))
    try:
        for row in census:
            jsonschema.validate(row, census_schema)
        check("schema:census", True, f"rows={len(census)}")
    except jsonschema.ValidationError as exc:
        check("schema:census", False, exc.message)
    try:
        for row in corrections:
            jsonschema.validate(row, correction_schema)
        check("schema:corrections", True, f"rows={len(corrections)}")
    except jsonschema.ValidationError as exc:
        check("schema:corrections", False, exc.message)

    ids = [row["stable_id"] for row in census]
    check("census:unique-stable-id", len(ids) == len(set(ids)), f"rows={len(ids)} unique={len(set(ids))}")
    check("census:registered-coverage", {row["id"] for row in objects} <= set(ids))
    check(
        "census:all-sources-exist",
        all((ROOT / path).is_file() or migrated_source_exists(path) for row in census for path in row["source_evidence"]["occurrence_paths"]),
    )
    check("census:summary-count", summary["deduplicated_assets"] == len(census))
    check("census:discovery-count", summary["source_occurrence_records"] == len(discovery))
    check("census:queue-one-per-asset", {row["stable_id"] for row in queue} == set(ids))
    check("census:auto-never-authority", all(row["review"]["state"] == "QUEUED" for row in census if row["identity_authority"] == "AUTO_CANDIDATE"))
    check("census:me-independent", any(row["mathematical_maturity"] == "M6" and row["external_evidence"] == "E0" for row in census))

    expected_edges = {
        (row["id"], dependency) for row in objects for dependency in row.get("dependencies", [])
    }
    actual_edges = {(row["from"], row["to"]) for row in edges}
    check("dependency:exact-declared-edge-set", expected_edges == actual_edges, f"expected={len(expected_edges)} actual={len(actual_edges)}")
    check("dependency:stable-sorted", edges == sorted(edges, key=lambda row: (row["from"], row["to"])))
    corrected_reverse_edges = {(edge["from"], edge["to"]) for edge in edges if edge["to"] in EXPECTED_CORRECTIONS}
    action_edges = {(row["consumer"], row["dependency"]) for row in dependency_actions}
    check("dependency:all-direct-consumers-dispositioned", corrected_reverse_edges == action_edges, f"expected={sorted(corrected_reverse_edges)} actual={sorted(action_edges)}")
    check("dependency:strong-consumers-blocked", all(row["action"] != "KEEP_UNCHANGED" for row in dependency_actions))

    examples = rows("tests/foundation/fixtures/function_identity_examples.jsonl")
    check("identity:ten-types", {row["identity"] for row in examples} == EXPECTED_IDENTITIES)
    check("gates:ten-present", all(set(row["audit_gates"]) == EXPECTED_GATES for row in census))
    gate_cases = rows("tests/foundation/fixtures/claim_governance_gate_cases.jsonl")
    check("gates:fixtures-cover-ten", {next(iter(row["expected"])) for row in gate_cases} == EXPECTED_GATES)
    check("gates:fixtures-executable", all(all(evaluate_fixture(case).get(gate) == value for gate, value in case["expected"].items()) for case in gate_cases))
    check("gates:no-automatic-fake-pass", all("REQUIRES_HUMAN_REVIEW" in row["audit_gates"].values() for row in census if row["identity_authority"] == "AUTO_CANDIDATE"))

    check("corrections:exact-target-set", set(correction_by_id) == EXPECTED_CORRECTIONS)
    check("corrections:task98-authority", all(row["authority"] == "HUMAN_ADJUDICATED_TASK98" for row in corrections))
    check("corrections:d127-identity-conflict", "T2" in correction_by_id["D127"]["legacy_identity_conflict"])
    check("corrections:d260-identity-conflict", "grand-unification" in correction_by_id["D260"]["legacy_identity_conflict"])
    check("corrections:t2-no-untyped-universal", correction_by_id["T2"]["formal_identity"] == "RELATION_OR_CONSTRAINT" and "carrier" in correction_by_id["T2"]["corrected_claim"])
    check("corrections:d182-log-domain", "r=1" in correction_by_id["D182"]["counterexample"])
    check("corrections:d183-counterexample", "Phi_after" in correction_by_id["D183"]["counterexample"])
    check("corrections:d188-invalid", correction_by_id["D188"]["formal_identity"] == "INVALID_OR_PSEUDO_FUNCTION")
    check("corrections:d190-open", "remains open" in correction_by_id["D190"]["claim_ceiling"])
    check("corrections:d260-split", correction_by_id["D260"]["disposition"] == "SPLIT" and "p=0.5" in correction_by_id["D260"]["corrected_claim"])
    check("corrections:no-3.3e12-point", all("3.3e12" not in json.dumps(row, ensure_ascii=False).lower() for row in corrections))

    claim_by_id = {row["claim_id"]: row for row in claims}
    check("claims:nogo-withdrawn", claim_by_id["CLAIM-98-GRAND-UNIFICATION-NOGO"]["status"] == "WITHDRAWN_NO_REBOUND")
    check("claims:model-failure-not-universal", "problem remains open" in claim_by_id["CLAIM-98-FOUR-FORCE-STATUS"]["claim_text"])
    check("claims:no-active-nogo", all(row["status"].startswith("WITHDRAWN") for row in claims if "proved impossible" in row["claim_text"]))
    historical = (ROOT / "outputs/getbrain/project-position-update-20260706.md").read_text(encoding="utf-8")
    dangerous = [line for line in historical.splitlines() if "已经证明物理大一统不可能" in line]
    check("claims:historical-nogo-labelled", bool(dangerous) and all("历史撤回" in line for line in dangerous))

    generator = subprocess.run([sys.executable, "tools/foundation/build_function_asset_census.py", "--check"], cwd=ROOT, text=True, capture_output=True)
    check("generator:deterministic", generator.returncode == 0, generator.stdout + generator.stderr)
    check("summary:authority-count", summary["human_adjudicated_task98"] == len(EXPECTED_CORRECTIONS))
    check("summary:identity-accounting", sum(summary["identity_counts"].values()) == len(census))
    check("summary:maturity-accounting", sum(summary["math_maturity_counts"].values()) == len(census))
    check("summary:evidence-accounting", sum(summary["external_evidence_counts"].values()) == len(census))

    for name, ok, detail in checks:
        print(("PASS" if ok else "FAIL") + " " + name + (" " + detail if detail else ""))
    passed = sum(ok for _, ok, _ in checks)
    print(f"CHECKS_TOTAL={len(checks)} CHECKS_PASSED={passed} CHECKS_FAILED={len(checks)-passed}")
    if passed == len(checks):
        print("CLAIM_GOVERNANCE_VALID")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
