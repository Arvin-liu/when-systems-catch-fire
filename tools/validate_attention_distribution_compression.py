#!/usr/bin/env python3
"""Validate 121Q13 attention, distribution, and compression control surfaces."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str) -> object:
    with (ROOT / path).open(encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: str) -> list[dict]:
    rows = []
    with (ROOT / path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise AssertionError(f"{path}:{line_number}: invalid JSONL: {exc}") from exc
    return rows


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_baseline() -> None:
    baseline = load_json("data/architecture/121q13-baseline.json")
    require(baseline["stacked_on"]["head"] == "338cfff999e26dce623c6c55d810587db4a668ba", "unexpected Q12 stacked base")
    require(baseline["q13_scope"]["adds_truth_layer"] is False, "Q13 must not add a truth layer")
    require(baseline["guard"]["ai_sampling_is_fact_evidence"] is False, "AI sampling cannot be fact evidence")
    require(baseline["guard"]["action_choice_is_mechanism_truth"] is False, "action choice cannot be mechanism truth")
    require(baseline["guard"]["new_terms_are_theory_upgrade"] is False, "new terms cannot be theory upgrade")
    frozen = baseline["frozen_boundaries"]
    require(not frozen["psi0_definitions_modified"], "Psi0 frozen boundary violated")
    require(not frozen["project_state_085_modified"], "085 frozen boundary violated")
    require(not frozen["legacy_tables_modified"], "legacy table boundary violated")
    require(not frozen["historical_evidence_cards_modified"], "historical evidence card boundary violated")


def validate_gap_matrix() -> None:
    matrix = load_json("data/architecture/121q13-gap-matrix.json")["matrix"]
    require(len(matrix) >= 6, "gap matrix must cover six Q13 gaps")
    require(all(row["not_duplicate"] is True for row in matrix), "gap matrix must mark non-duplication")


def validate_attention() -> None:
    taxonomy = load_json("data/architecture/attractor-taxonomy.json")
    require(len(taxonomy["taxonomy"]) >= 7, "attractor taxonomy incomplete")
    allowed = set(taxonomy["allowed_non_absorption_results"])
    require("frame_external_residue" in allowed, "frame external residue must be allowed")
    audits = sorted((ROOT / "data/architecture/attention-audits").glob("*.json"))
    require(len(audits) == 3, "expected three attention audits")
    statuses = set()
    for path in audits:
        audit = load_json(str(path.relative_to(ROOT)))
        require(audit["history_mode"] == "read_only", f"{path}: audit must be read_only")
        delta = audit["iteration_delta"]
        statuses.add(delta["delta_status"])
        for key in (
            "new_evidence",
            "new_discriminating_test",
            "changed_mechanism_map",
            "narrowed_boundary",
            "changed_capability",
            "changed_action",
            "expanded_option_space",
            "unresolved_residue",
        ):
            require(key in delta, f"{path}: missing {key}")
        require(delta["required_response"], f"{path}: required response missing")
    require("INFORMATION_GAIN" in statuses, "must include a real-deepening audit")
    require("PARTIAL_DELTA" in statuses, "must include repeated repair / partial delta audit")


def validate_distribution() -> None:
    samples = load_jsonl("data/architecture/distribution/121q13-sample-envelopes.jsonl")
    require(len(samples) >= 2, "sample envelopes missing")
    for sample in samples:
        if sample["sampler_type"] == "ai_model":
            require(sample["provenance_class"] in {"hypothesis", "interpretation", "review"}, "AI sample promoted outside allowed channels")
            require("not external fact evidence" in sample["evidence_boundary"], "AI sample boundary must reject fact evidence")
    dist = load_json("data/architecture/distribution/121q13-hypothesis-distribution.json")
    require(dist["sample_refs"], "hypothesis distribution sample refs missing")
    require("not fact evidence" in dist["sensitivity_summary"], "distribution must state sample stability is not fact evidence")
    dcr = load_json("data/architecture/distribution/121q13-decision-collapse.json")
    require(dcr["threshold_used"] == "ACTION", "121Q13 implementation should use action threshold")
    require(dcr["truth_claim_made"] is False, "decision collapse must not make truth claim")
    thresholds = load_json("data/architecture/thresholds/action-claim-scale-thresholds.json")["thresholds"]
    require({row["id"] for row in thresholds} == {"ACTION", "CLAIM", "SCALE"}, "threshold set mismatch")
    ledger = load_jsonl("data/architecture/distribution/121q13-narrative-provenance-ledger.jsonl")
    require(all(row["not_overwritten"] is True for row in ledger), "narrative provenance must preserve uncertainty")


def validate_chunks() -> None:
    audits = load_json("data/architecture/chunk-audits/high-frequency-terms.json")["audits"]
    terms = {audit["term"] for audit in audits}
    for required in ("涌现 / emergence", "收敛 / convergence", "同构 / isomorphism", "元协议 / meta-protocol", "机制 / mechanism"):
        require(required in terms, f"missing chunk audit for {required}")
    for audit in audits:
        require(audit["expandability"]["sources"], f"{audit['term']}: sources missing")
        require(audit["expandability"]["variables"], f"{audit['term']}: variables missing")
        require(audit["expandability"]["paths"], f"{audit['term']}: paths missing")
        require(audit["expandability"]["conditions"], f"{audit['term']}: conditions missing")
        require(audit["expandability"]["failure_boundaries"], f"{audit['term']}: failure boundaries missing")
        require(audit["generativity"]["new_questions_or_tests"], f"{audit['term']}: generativity missing")
        require(audit["compression_utility"]["restorable_details"] is True, f"{audit['term']}: details must be restorable")
        require(audit["inquiry_continuation"]["next_questions"], f"{audit['term']}: inquiry continuation missing")
        require("theory upgrade" not in audit["claim_boundary"].lower(), f"{audit['term']}: claim boundary must not imply theory upgrade")


def validate_run_state() -> None:
    state = load_json("data/architecture/121q13-run-state.json")
    require(state["draft_pr"] == 48, "run-state must point to Draft PR #48")
    require(len(state["steps"]) == 4, "run-state must contain four steps")
    require(all(step["status"] == "complete" for step in state["steps"]), "all macro steps must be complete")
    ledger = load_jsonl("data/architecture/121q13-ledger.jsonl")
    require([row["step"] for row in ledger] == ["000", "001", "002", "003"], "ledger must contain steps 000-003")


def main() -> int:
    try:
        validate_baseline()
        validate_gap_matrix()
        validate_attention()
        validate_distribution()
        validate_chunks()
        validate_run_state()
    except AssertionError as exc:
        print(f"121Q13 validation failed: {exc}", file=sys.stderr)
        return 1
    print("121Q13 attention/distribution/compression validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
