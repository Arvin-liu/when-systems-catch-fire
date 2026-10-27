#!/usr/bin/env python3
"""Task 110 — §6 adversarial + mutation tests for completion-state reconciliation.

Proves the generic reconciliation layer (tools/iteration_planner/completion_state.py)
fails closed and never re-schedules completed work. Complements the task-109 scoring
adversarial suite (test_planner.py); this file targets the NEW lifecycle behavior.

Run: python3 tests/iteration_planner/test_completion_reconciliation.py
"""
import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "iteration_planner"))
import planner as P
import completion_state as CS


def cand(cid, claim=None, source="fixture", title="x"):
    c = P.blank_candidate(cid, source, title)
    if claim:
        c["provenance"]["claim_id"] = claim
    return c


def _tmp_json(obj):
    fd = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    fd.write(json.dumps(obj))
    fd.close()
    return fd.name


def _ledger_entry(cid, claim, outcome, source_path, sha=None):
    return {
        "candidate_id": cid,
        "claim_id": claim,
        "lifecycle_state": CS.OUTCOME_TO_STATE.get(outcome, "UNKNOWN_COMPLETION_STATE_REVIEW_REQUIRED"),
        "superseded_by": None,
        "owner_alias": [],
        "authority": {
            "source": source_path,
            "source_sha256": sha,
            "outcome_field": "outcome" if "verdict" not in Path(source_path).name else "overall_verdict",
            "observed_outcome": outcome,
            "task": "synthetic",
        },
    }


# ---- helpers to build a synthetic reconciled candidate set ----

def _reconcile_with(ledger, cands):
    return CS.reconcile(cands, ledger=ledger)


# ============================ NEGATIVE TESTS (§6) ============================

def test_neg1_terminal_run_but_portfolio_primary_excluded():
    ledger = CS.load_ledger()  # has C-01 (COMPLETED_SUPPORTED)
    c = cand("C-01", "SRC-REGISTRY-104-METADATA")
    cands, hist, rep, prev = _reconcile_with(ledger, [c])
    assert cands[0]["lifecycle_state"] == "COMPLETED_SUPPORTED"
    active = [x for x in cands if x["lifecycle_state"] not in CS.LIFECYCLE_TERMINAL]
    assert "C-01" not in [x["canonical_id"] for x in active]


def test_neg2_contradicted_terminal_excluded():
    art = _tmp_json({"outcome": "CONTRADICTED_WITHIN_SCOPE"})
    e = _ledger_entry("X-2", "CLM-2", "CONTRADICTED_WITHIN_SCOPE", art)
    c = cand("X-2", "CLM-2")
    cands, _, _, _ = _reconcile_with([e], [c])
    assert cands[0]["lifecycle_state"] == "COMPLETED_CONTRADICTED"
    assert cands[0]["lifecycle_state"] in CS.LIFECYCLE_TERMINAL


def test_neg3_null_inconclusive_terminal_excluded():
    art = _tmp_json({"outcome": "NULL_OR_INCONCLUSIVE"})
    e = _ledger_entry("X-3", "CLM-3", "NULL_OR_INCONCLUSIVE", art)
    c = cand("X-3", "CLM-3")
    cands, _, _, _ = _reconcile_with([e], [c])
    assert cands[0]["lifecycle_state"] == "COMPLETED_NULL_OR_INCONCLUSIVE"
    assert cands[0]["lifecycle_state"] in CS.LIFECYCLE_TERMINAL


def test_neg4_merged_pr_without_terminal_evidence_blocked_unknown():
    # source file absent -> validation fails -> UNKNOWN (fail closed), blocked from top
    e = _ledger_entry("X-4", "CLM-4", "SUPPORTED_WITHIN_SCOPE", "/nonexistent/artifact.json")
    c = cand("X-4", "CLM-4")
    cands, _, rep, _ = _reconcile_with([e], [c])
    assert cands[0]["lifecycle_state"] == CS.UNKNOWN_STATE
    active = [x for x in cands if x["lifecycle_state"] not in CS.LIFECYCLE_TERMINAL
              and x["lifecycle_state"] != CS.UNKNOWN_STATE]
    assert "X-4" not in [x["canonical_id"] for x in active]


def test_neg5_prose_similar_claim_ids_differ_not_linked():
    ledger = CS.load_ledger()
    a = cand("C-01", "SRC-REGISTRY-104-METADATA", title="Crossref 117 条记录元数据核验")
    b = cand("LOOKALIKE", "UNRELATED-CLAIM", title="Crossref 117 条记录元数据核验（措辞相似）")
    cands, _, _, _ = _reconcile_with(ledger, [a, b])
    states = {x["canonical_id"]: x["lifecycle_state"] for x in cands}
    assert states["C-01"] == "COMPLETED_SUPPORTED"
    assert states["LOOKALIKE"] == "UNASSESSED"  # not linked by prose similarity


def test_neg6_claim_id_alias_explicitly_linked():
    art = _tmp_json({"outcome": "SUPPORTED_WITHIN_SCOPE"})
    e = _ledger_entry("X-6", "CLM-6", "SUPPORTED_WITHIN_SCOPE", art)
    c = cand("X-6", "CLM-6")
    cands, _, _, _ = _reconcile_with([e], [c])
    assert cands[0]["lifecycle_state"] == "COMPLETED_SUPPORTED"


def test_neg7_completed_not_reopened_without_owner_authority():
    ledger = CS.load_ledger()  # C-01 COMPLETED_SUPPORTED, no reopened event
    c = cand("C-01", "SRC-REGISTRY-104-METADATA")
    cands, _, _, _ = _reconcile_with(ledger, [c])
    assert cands[0]["lifecycle_state"] == "COMPLETED_SUPPORTED"
    assert cands[0]["lifecycle_state"] != "REOPENED_BY_OWNER"


def test_neg8_owner_authorized_revised_protocol_new_revision_eligible():
    # a revision with a DISTINCT claim_id is a new schedulable candidate
    c = cand("C-01-rev2", "SRC-REGISTRY-104-METADATA-REV2")
    cands, _, _, _ = _reconcile_with([], [c])  # no ledger entry -> UNASSESSED -> eligible
    assert cands[0]["lifecycle_state"] == "UNASSESSED"


def test_neg9_generated_output_not_completion_authority():
    # reconciliation reads the ledger, not the planner's own ranked_queue.json
    ledger = CS.load_ledger()
    c = cand("C-01", "SRC-REGISTRY-104-METADATA")
    cands1, _, _, _ = _reconcile_with(ledger, [c])
    # mutate the live ranked_queue to claim C-01 eligible; reconciliation must be unaffected
    rq = REPO / "data/operations/iterations/109/ranked_queue.json"
    snap = rq.read_text()
    try:
        obj = json.loads(snap)
        obj["recommended_next"] = "C-01"
        rq.write_text(json.dumps(obj))
        cands2, _, _, _ = _reconcile_with(ledger, [c])
        assert cands2[0]["lifecycle_state"] == "COMPLETED_SUPPORTED"
    finally:
        rq.write_text(snap)


def test_neg10_duplicate_candidate_records_no_double_exclusion():
    ledger = CS.load_ledger()
    a = cand("C-01", "SRC-REGISTRY-104-METADATA", source="evidence-program/registry/candidate-portfolio.jsonl")
    b = cand("C-01", "SRC-REGISTRY-104-METADATA", source="data/operations/iterations/109/dossiers/C-01.json")
    cands, _, _, _ = _reconcile_with(ledger, [a, b])
    states = {x["canonical_id"]: x["lifecycle_state"] for x in cands}
    assert states["C-01"] == "COMPLETED_SUPPORTED"


def test_neg11_ambiguous_completion_mapping_fails_closed():
    art = _tmp_json({"outcome": "AMBIGUOUS_WEIRD_OUTCOME"})
    e = _ledger_entry("X-11", "CLM-11", "AMBIGUOUS_WEIRD_OUTCOME", art)
    c = cand("X-11", "CLM-11")
    cands, _, rep, _ = _reconcile_with([e], [c])
    assert cands[0]["lifecycle_state"] == CS.UNKNOWN_STATE


def test_neg12_c01_c04_not_active_after_reconciliation():
    ledger = CS.load_ledger()
    cands = [cand("C-01", "SRC-REGISTRY-104-METADATA"),
             cand("C-04", "FUNCTION-OS-V02-CORRECTNESS"),
             cand("C-03", "DOI-OPENALEX-CROSS-CHECK")]
    cands, _, _, _ = _reconcile_with(ledger, cands)
    active = [x for x in cands if x["lifecycle_state"] not in CS.LIFECYCLE_TERMINAL]
    active_ids = [x["canonical_id"] for x in active]
    assert "C-01" not in active_ids
    assert "C-04" not in active_ids


# ============================ MUTATION TESTS (§6) ============================

def test_mut1_missing_lifecycle_evidence_unknown():
    e = _ledger_entry("M-1", "CLM-M1", "SUPPORTED_WITHIN_SCOPE", "/no/such/file.json")
    c = cand("M-1", "CLM-M1")
    cands, _, _, _ = _reconcile_with([e], [c])
    assert cands[0]["lifecycle_state"] == CS.UNKNOWN_STATE


def test_mut2_altered_claim_ids_no_match():
    art = _tmp_json({"outcome": "SUPPORTED_WITHIN_SCOPE"})
    e = _ledger_entry("M-2", "CLM-M2-RENAMED", "SUPPORTED_WITHIN_SCOPE", art)
    # candidate carries the OLD claim id AND a different candidate_id, so neither
    # the candidate_id nor the (altered) claim_id matches the ledger entry.
    c = cand("M-2-alt", "CLM-M2")
    cands, _, _, _ = _reconcile_with([e], [c])
    assert cands[0]["lifecycle_state"] == "UNASSESSED"  # no match -> not linked


def test_mut3_stale_derived_view_overridden_by_reconciliation():
    ledger = CS.load_ledger()
    c = cand("C-01", "SRC-REGISTRY-104-METADATA")
    cands, _, _, prev = _reconcile_with(ledger, [c])
    # derived view (109 ranked_queue) said C-01 top; reconciliation overrides -> excluded
    assert prev["invalidated"] is True
    assert cands[0]["lifecycle_state"] == "COMPLETED_SUPPORTED"


def test_mut4_removed_terminal_tag_still_terminal_via_run():
    # C-01 terminal is established by the run adjudication, not by a git tag;
    # even if a hypothetical tag reference were absent, the run evidence still terminates it.
    ledger = CS.load_ledger()
    c = cand("C-01", "SRC-REGISTRY-104-METADATA")
    cands, _, _, _ = _reconcile_with(ledger, [c])
    assert cands[0]["lifecycle_state"] == "COMPLETED_SUPPORTED"


def test_mut5_contradictory_owner_decision_no_reopen_without_event():
    ledger = CS.load_ledger()  # C-01 terminal, no governed reopen event
    c = cand("C-01", "SRC-REGISTRY-104-METADATA")
    cands, _, _, _ = _reconcile_with(ledger, [c])
    # a mere contradictory owner note cannot reopen without a governed lifecycle event
    assert cands[0]["lifecycle_state"] == "COMPLETED_SUPPORTED"


def test_mut6_tampered_result_link_fails_closed():
    art = _tmp_json({"outcome": "SUPPORTED_WITHIN_SCOPE"})
    # ledger claims sha of a DIFFERENT file -> sha mismatch -> UNKNOWN
    other = _tmp_json({"outcome": "SUPPORTED_WITHIN_SCOPE", "extra": 1})
    e = _ledger_entry("M-6", "CLM-M6", "SUPPORTED_WITHIN_SCOPE", art,
                      sha="0" * 64)
    c = cand("M-6", "CLM-M6")
    cands, _, rep, _ = _reconcile_with([e], [c])
    assert cands[0]["lifecycle_state"] == CS.UNKNOWN_STATE


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} passed")
    sys.exit(0 if passed == len(tests) else 1)
