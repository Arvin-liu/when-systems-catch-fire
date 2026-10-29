"""R4 metric-disclosure and relay-receipt repair — acceptance/attack tests.

These encode the narrow repair contract authorized by the relay repair task:
closed-set 27-item capability classification, governance terminology separation,
contradiction-lifecycle semantics, schema cleanup, and red-line adherence.

Run with pytest from the repository root. No private corpus content is embedded.
"""

import hashlib
import json
import os
import re
import shutil
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

from arr_r4_self_reflection import run  # noqa: E402
from arr_r4_self_reflection.runner import REPAIR_TERMINAL_VERDICT  # noqa: E402
from arr_r4_self_reflection.capability_classifier import (  # noqa: E402
    CAPABILITY_CLOSED_SET_SIZE,
    CAPABILITY_DIMENSION_REGISTRY,
    PRIMARY_DIMENSIONS,
    classify_capability_coverage,
    validate_closed_set_invariants,
)
from arr_r4_self_reflection.metric_consistency import MetricContradictionEngine  # noqa: E402
from arr_r4_self_reflection.taxonomy import (  # noqa: E402
    EVIDENCE_AXIS,
    GOVERNANCE_AXIS,
    PIPELINE_AXIS,
    SEMANTIC_AXIS,
)
from .r4_fixtures import (  # noqa: E402
    R4_CAPABILITY_ITEM_IDS,
    build_synthetic_evidence,
    r3_like_reports,
    r4_capability_matrix,
    synthetic_envelope,
    synthetic_receipt,
)


def _build_evidence_with_real_matrix(root, n=50, seed=1):
    build_synthetic_evidence(root, n, seed)
    with open(os.path.join(root, "CAPABILITY_COVERAGE_MATRIX.json"), "w", encoding="utf-8") as fh:
        json.dump(r4_capability_matrix(), fh, ensure_ascii=False, indent=2)


def _run_on(root, n=50):
    out = tempfile.mkdtemp()
    try:
        return run(root, out, "REPAIR_TASK", "REPAIR_CONTROL",
                   terminal_verdict=REPAIR_TERMINAL_VERDICT)
    finally:
        shutil.rmtree(out, ignore_errors=True)


# --------------------------------------------------------------------------
# Closed-set 27-item classification contract
# --------------------------------------------------------------------------

def test_closed_set_has_exactly_27_ids():
    assert CAPABILITY_CLOSED_SET_SIZE == 27
    assert len(R4_CAPABILITY_ITEM_IDS) == 27


def test_registry_maps_all_27_ids():
    assert set(CAPABILITY_DIMENSION_REGISTRY) == set(R4_CAPABILITY_ITEM_IDS)


def test_registry_size_is_27():
    assert len(CAPABILITY_DIMENSION_REGISTRY) == 27


def test_exactly_one_primary_dimension_each():
    for cid in R4_CAPABILITY_ITEM_IDS:
        assert cid in CAPABILITY_DIMENSION_REGISTRY
        assert CAPABILITY_DIMENSION_REGISTRY[cid] in PRIMARY_DIMENSIONS


def test_no_id_maps_to_two_dimensions():
    seen = {}
    for cid, dim in CAPABILITY_DIMENSION_REGISTRY.items():
        seen.setdefault(cid, set()).add(dim)
    assert all(len(v) == 1 for v in seen.values())


def test_classify_operational_count_17():
    c = classify_capability_coverage(r4_capability_matrix())
    assert c["dimensions"]["OPERATIONAL"]["item_count"] == 17


def test_classify_semantic_count_4():
    c = classify_capability_coverage(r4_capability_matrix())
    assert c["dimensions"]["SEMANTIC"]["item_count"] == 4


def test_classify_evidence_count_3():
    c = classify_capability_coverage(r4_capability_matrix())
    assert c["dimensions"]["EVIDENCE"]["item_count"] == 3


def test_classify_governance_count_3():
    c = classify_capability_coverage(r4_capability_matrix())
    assert c["dimensions"]["GOVERNANCE"]["item_count"] == 3


def test_classify_dimension_sum_27():
    c = classify_capability_coverage(r4_capability_matrix())
    total = sum(c["dimensions"][d]["item_count"] for d in PRIMARY_DIMENSIONS)
    assert total == 27


def test_classify_no_unclassified_on_real_matrix():
    c = classify_capability_coverage(r4_capability_matrix())
    assert c["closed_set"]["unclassified_total"] == 0
    assert c["closed_set"]["unclassified_items"] == []


def test_classify_invariant_ok_real():
    c = classify_capability_coverage(r4_capability_matrix())
    assert c["closed_set"]["invariant_ok"] is True
    assert validate_closed_set_invariants(c) is True


def test_classify_primary_overlap_zero():
    c = classify_capability_coverage(r4_capability_matrix())
    assert c["closed_set"]["primary_overlap_total"] == 0


def test_classify_deterministic_under_reorder():
    import random
    items = r4_capability_matrix()["items"]
    shuffled = list(items)
    random.Random(7).shuffle(shuffled)
    m2 = dict(r4_capability_matrix())
    m2["items"] = shuffled
    a = classify_capability_coverage(r4_capability_matrix())
    b = classify_capability_coverage(m2)
    for d in PRIMARY_DIMENSIONS:
        assert sorted(a["dimensions"][d]["items"]) == sorted(b["dimensions"][d]["items"])
    assert a["closed_set"] == b["closed_set"]


def test_unknown_capability_id_fails_closed():
    m = r4_capability_matrix()
    m["items"] = m["items"] + [{"id": "future_capability_unknown", "pass": True}]
    c = classify_capability_coverage(m)
    assert c["closed_set"]["unclassified_total"] == 1
    assert c["closed_set"]["invariant_ok"] is False
    assert validate_closed_set_invariants(c) is False


def test_missing_capability_id_fails_closed():
    m = r4_capability_matrix()
    m["items"] = m["items"][:-1]  # drop one
    m["total_items"] = 27
    c = classify_capability_coverage(m)
    assert c["closed_set"]["classified_total"] == 26
    assert c["closed_set"]["invariant_ok"] is False


def test_semantic_dimension_not_measured():
    c = classify_capability_coverage(r4_capability_matrix())
    assert c["dimensions"]["SEMANTIC"]["measured"] is False
    assert c["dimensions"]["SEMANTIC"]["status"] == "not_measured"


def test_operational_evidence_governance_measured():
    c = classify_capability_coverage(r4_capability_matrix())
    for d in ("OPERATIONAL", "EVIDENCE", "GOVERNANCE"):
        assert c["dimensions"][d]["measured"] is True
        assert c["dimensions"][d]["status"] == "pass"


def test_schema_version_v2():
    c = classify_capability_coverage(r4_capability_matrix())
    assert c["schema"] == "r4/capability_coverage_reinterpretation/v2"


# --------------------------------------------------------------------------
# Engine integration: deterministic projections (fail until engine repaired)
# --------------------------------------------------------------------------

def test_runner_capability_closed_set():
    root = tempfile.mkdtemp()
    try:
        _build_evidence_with_real_matrix(root, n=50)
        a = _run_on(root, n=50)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    cap = a["capability_reinterpretation"]
    assert cap["closed_set"]["invariant_ok"] is True
    assert cap["closed_set"]["classified_total"] == 27
    assert cap["dimensions"]["OPERATIONAL"]["item_count"] == 17
    assert cap["dimensions"]["SEMANTIC"]["item_count"] == 4
    assert cap["dimensions"]["EVIDENCE"]["item_count"] == 3
    assert cap["dimensions"]["GOVERNANCE"]["item_count"] == 3


def test_runner_malformed_field_absent():
    root = tempfile.mkdtemp()
    try:
        _build_evidence_with_real_matrix(root, n=50)
        a = _run_on(root, n=50)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    assert "dimension_dimension_disclosure_defect" not in a["capability_reinterpretation"]
    assert a["capability_reinterpretation"]["capability_dimension_disclosure_defect_present"] is False


def test_runner_governance_safety_invariant_present():
    root = tempfile.mkdtemp()
    try:
        _build_evidence_with_real_matrix(root, n=50)
        a = _run_on(root, n=50)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    gov = a["capability_reinterpretation"]["governance_safety_invariant"]
    assert "safety_boundary_held_objects" in gov
    assert gov["safety_boundary_held_objects"] == 50  # equals total objects, orthogonal to enum
    assert "boundary_held" not in a["capability_reinterpretation"].get("governance_coverage", {})


def test_runner_evidence_quality_outcome_orthogonal():
    root = tempfile.mkdtemp()
    try:
        _build_evidence_with_real_matrix(root, n=50)
        a = _run_on(root, n=50)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    eq = a["capability_reinterpretation"]["evidence_quality_outcome"]
    assert eq["independently_supported_count"] == 0


def test_runner_public_summary_matches_capability():
    root = tempfile.mkdtemp()
    try:
        _build_evidence_with_real_matrix(root, n=50)
        a = _run_on(root, n=50)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    priv = a["capability_reinterpretation"]
    pub = a["public_summary"]["capability_reinterpretation"]
    assert pub["closed_set"] == priv["closed_set"]
    assert pub["dimensions"] == priv["dimensions"]


def test_runner_no_false_27_of_27_operational():
    root = tempfile.mkdtemp()
    try:
        _build_evidence_with_real_matrix(root, n=50)
        a = _run_on(root, n=50)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    cap = a["capability_reinterpretation"]
    # Operational is only 17 of 27; must NOT be claimed as 27/27 operational.
    assert cap["dimensions"]["OPERATIONAL"]["item_count"] == 17
    # The public aggregate must not carry a "27/27 pass" operational claim.
    blob = json.dumps(a["public_summary"])
    assert "27/27 pass" not in blob
    assert "operational_coverage: 27/27" not in blob


def test_runner_evidence_dimension_count_3_not_zero():
    root = tempfile.mkdtemp()
    try:
        _build_evidence_with_real_matrix(root, n=50)
        a = _run_on(root, n=50)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    # The 3 EVIDENCE guardrail items must be counted as classified, not dropped.
    assert a["capability_reinterpretation"]["dimensions"]["EVIDENCE"]["item_count"] == 3


# --------------------------------------------------------------------------
# Contradiction lifecycle semantics (fail until engine repaired)
# --------------------------------------------------------------------------

def _audit():
    fas = {
        "pipeline": {s: 0 for s in PIPELINE_AXIS},
        "semantic": {s: 0 for s in SEMANTIC_AXIS},
        "evidence": {s: 0 for s in EVIDENCE_AXIS},
        "governance": {s: 0 for s in GOVERNANCE_AXIS},
    }
    fas["semantic"]["SEMANTIC_REPRESENTATION_LIMITED"] = 836
    fas["evidence"]["INDEPENDENTLY_SUPPORTED"] = 0
    return [c.to_dict() for c in MetricContradictionEngine(r3_like_reports(), fas).audit()]


def test_all_contradictions_disposition_assigned():
    for c in _audit():
        assert c["lifecycle"]["disposition_assigned"] is True
        assert c["lifecycle"]["classification_resolved"] is True


def test_m1_lifecycle_no_underlying_defect():
    c = next(x for x in _audit() if x["contradiction_id"] == "M1_SUCCESS_VS_SEMANTIC")
    assert c["lifecycle"]["underlying_defect_present"] is False
    assert c["lifecycle"]["underlying_defect_repaired"] is False


def test_m2_lifecycle_no_underlying_defect():
    c = next(x for x in _audit() if x["contradiction_id"] == "M2_UNKNOWN_RETENTION")
    assert c["lifecycle"]["underlying_defect_present"] is False


def test_m6_lifecycle_no_underlying_defect():
    c = next(x for x in _audit() if x["contradiction_id"] == "M6_CORPUS_SIZE_VS_SOURCES")
    assert c["lifecycle"]["underlying_defect_present"] is False


def test_m3_lifecycle_underlying_defect_unrepaired():
    c = next(x for x in _audit() if x["contradiction_id"] == "M3_CRASH_RECOVERY_RATE")
    assert c["lifecycle"]["underlying_defect_present"] is True
    assert c["lifecycle"]["underlying_defect_repaired"] is False
    assert c["lifecycle"]["followup_required"] is True
    assert "R3" in c["lifecycle"]["followup_route"]


def test_m4_lifecycle_underlying_defect_unrepaired():
    c = next(x for x in _audit() if x["contradiction_id"] == "M4_INCREMENTAL_SELECTIVITY")
    assert c["lifecycle"]["underlying_defect_present"] is True
    assert c["lifecycle"]["underlying_defect_repaired"] is False
    assert c["lifecycle"]["followup_required"] is True


def test_m5_lifecycle_historical_r3_defect_distinguished():
    c = next(x for x in _audit() if x["contradiction_id"] == "M5_CAPABILITY_ALL_PASS")
    assert c["lifecycle"]["underlying_defect_present"] is True
    assert c["lifecycle"]["underlying_defect_repaired"] is False
    # The route must distinguish the historical R3 reporting defect from the
    # current R4 disclosure state (which this repair fixes).
    assert "historical" in c["lifecycle"]["followup_route"].lower()
    assert "R4" in c["lifecycle"]["followup_route"]


def test_lifecycle_fields_present_for_all():
    required = {"disposition_assigned", "classification_resolved", "underlying_defect_present",
                "underlying_defect_repaired", "followup_required", "followup_route"}
    for c in _audit():
        assert required.issubset(set(c["lifecycle"].keys()))


def test_public_wording_classification_complete_not_all_fixed():
    root = tempfile.mkdtemp()
    try:
        _build_evidence_with_real_matrix(root, n=50)
        a = _run_on(root, n=50)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    blob = json.dumps(a["public_summary"])
    # Public artifacts may say "classification complete" / "received dispositions"
    # but must not imply all underlying defects are fixed.
    assert "all defects fixed" not in blob.lower()
    assert "all underlying defects repaired" not in blob.lower()


# --------------------------------------------------------------------------
# Governance terminology separation (four-axis primary vs orthogonal safety)
# --------------------------------------------------------------------------

def _build_governance_controlled(root, n=836, boundary_held=27, seed=0):
    import random
    rnd = random.Random(seed)
    receipts_dir = os.path.join(root, "receipts")
    envelopes_dir = os.path.join(root, "envelopes")
    os.makedirs(receipts_dir, exist_ok=True)
    os.makedirs(envelopes_dir, exist_ok=True)
    for i in range(n):
        key = f"g_{i:08d}"
        is_boundary = i < boundary_held
        rec = synthetic_receipt(key, "link", "SECONDARY_ARCHIVE_CLAIM",
                                 source_ref_present=is_boundary, inference_labeled=False)
        if is_boundary:
            rec["rights_boundary"] = "public"
        else:
            rec["rights_boundary"] = "private"
            rec["source_ref_present"] = False
        env = synthetic_envelope(key, "link", "SECONDARY_ARCHIVE_CLAIM",
                                 source_ref_present=rec["source_ref_present"], inference_labeled=False)
        with open(os.path.join(receipts_dir, key + ".json"), "w", encoding="utf-8") as fh:
            json.dump(rec, fh)
        with open(os.path.join(envelopes_dir, key + ".json"), "w", encoding="utf-8") as fh:
            json.dump(env, fh)
    # Minimal ledgers so ingestion + contradiction engine do not crash.
    agg = {"corpus_notes_selected": n, "outcome_counts": {"SUCCESS": n},
           "crash_recovery_success_rate": 0.0, "incremental_selectivity": 0.0,
           "unknown_retention": 0, "promote_calls": 0, "evolve_calls": 0,
           "real_world_actions": 0, "public_private_content_leaks": 0}
    with open(os.path.join(root, "AGGREGATE_METRICS.json"), "w", encoding="utf-8") as fh:
        json.dump(agg, fh)
    with open(os.path.join(root, "CORPUS_RUN_LEDGER.json"), "w", encoding="utf-8") as fh:
        json.dump({"crash_recovery_success_rate": 1.0, "incremental_selectivity": 1.0 / n}, fh)
    with open(os.path.join(root, "CAPABILITY_COVERAGE_MATRIX.json"), "w", encoding="utf-8") as fh:
        json.dump(r4_capability_matrix(), fh)
    with open(os.path.join(root, "INDEPENDENT_SOURCE_ESTIMATE.json"), "w", encoding="utf-8") as fh:
        json.dump({"estimate": 9, "distinct_source_hosts": 9, "notes_with_source": 27}, fh)
    with open(os.path.join(root, "TEMPORAL_AMBIGUITY_LEDGER.json"), "w", encoding="utf-8") as fh:
        json.dump({"unknown_event_time_count": 449, "temporal_ambiguity_rate": 0.5}, fh)
    with open(os.path.join(root, "SOURCE_DEPENDENCY_GRAPH.json"), "w", encoding="utf-8") as fh:
        json.dump({"host_map": {}, "shared_source_derivatives": {}}, fh)
    with open(os.path.join(root, "FALSE_CONSENSUS_CASES.json"), "w", encoding="utf-8") as fh:
        json.dump({"cases": [], "false_consensus_risk": 0}, fh)
    with open(os.path.join(root, "CRASH_RECOVERY_REPORT.json"), "w", encoding="utf-8") as fh:
        json.dump({"all_resume_complete": True, "scenarios": []}, fh)
    with open(os.path.join(root, "INCREMENTAL_RERUN_REPORT.json"), "w", encoding="utf-8") as fh:
        json.dump({"reprocessed_on_change": 1, "selective": True}, fh)
    with open(os.path.join(root, "REPLAY_AND_DRIFT_REPORT.json"), "w", encoding="utf-8") as fh:
        json.dump({"replay_idempotent": True, "duplicate_receipts": 0}, fh)
    with open(os.path.join(root, "FAILURE_ATTRIBUTION_LEDGER.json"), "w", encoding="utf-8") as fh:
        json.dump({"failures": 0, "quarantines": 0}, fh)
    with open(os.path.join(root, "COUNTERS.json"), "w", encoding="utf-8") as fh:
        json.dump({"PROMOTE_CALLS": 0, "EVOLVE_CALLS": 0, "REAL_WORLD_ACTIONS": 0}, fh)


def test_primary_governance_distribution_27_809():
    root = tempfile.mkdtemp()
    try:
        _build_governance_controlled(root, n=836, boundary_held=27)
        a = _run_on(root, n=836)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    gov = a["four_axis_summary"]["governance"]
    assert gov["BOUNDARY_HELD"] == 27
    assert gov["CONSENT_OR_RIGHTS_LIMITED"] == 809
    assert gov["ACTION_PROHIBITED"] == 0
    assert gov["BOUNDARY_HELD"] + gov["CONSENT_OR_RIGHTS_LIMITED"] + gov["ACTION_PROHIBITED"] == 836


def test_safety_boundary_held_objects_orthogonal_836():
    root = tempfile.mkdtemp()
    try:
        _build_governance_controlled(root, n=836, boundary_held=27)
        a = _run_on(root, n=836)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    inv = a["capability_reinterpretation"]["governance_safety_invariant"]
    assert inv["safety_boundary_held_objects"] == 836
    assert inv["safety_boundary_held_objects"] != inv.get("BOUNDARY_HELD", None)


# --------------------------------------------------------------------------
# Red-line adherence: no R5 / PROMOTE / EVOLVE / Main / Ready / merge
# --------------------------------------------------------------------------

def test_redline_counters_zero():
    root = tempfile.mkdtemp()
    try:
        _build_evidence_with_real_matrix(root, n=50)
        a = _run_on(root, n=50)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    c = a["counters"]
    assert c["EVOLVE_CALLS"] == 0
    assert c["PROMOTE_CALLS"] == 0
    assert c["REAL_WORLD_ACTIONS"] == 0
    assert c["MAIN_CHANGES"] == 0
    assert c["R5_STARTED"] == 0
    assert c["FORCE_PUSHES"] == 0
    assert c["HISTORY_REWRITES"] == 0
    assert c["EXTERNAL_ACCEPTANCE_CLAIMED"] == 0
    assert c["PRIVATE_CONTENT_PUBLICATION_EVENTS"] == 0


def test_terminal_verdict_is_repair_not_r5():
    root = tempfile.mkdtemp()
    try:
        _build_evidence_with_real_matrix(root, n=50)
        a = _run_on(root, n=50)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    assert "REPAIR" in a["public_summary"]["terminal_verdict"]
    assert "R5" not in a["public_summary"]["terminal_verdict"]


def test_engine_does_not_mutate_sealed_input():
    root = tempfile.mkdtemp()
    try:
        _build_evidence_with_real_matrix(root, n=50)
        before = {}
        for fn in os.listdir(root):
            p = os.path.join(root, fn)
            if os.path.isfile(p):
                with open(p, "rb") as fh:
                    before[fn] = hashlib.sha256(fh.read()).hexdigest()
        _run_on(root, n=50)
        after = {}
        for fn in os.listdir(root):
            p = os.path.join(root, fn)
            if os.path.isfile(p):
                with open(p, "rb") as fh:
                    after[fn] = hashlib.sha256(fh.read()).hexdigest()
        assert before == after
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_no_private_content_leak_in_public_summary():
    root = tempfile.mkdtemp()
    try:
        _build_evidence_with_real_matrix(root, n=50)
        a = _run_on(root, n=50)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    blob = json.dumps(a["public_summary"])
    # The public projection must never carry note titles, raw text, transcript
    # content, URL lists or reconstructive features.
    assert "privacy_boundary" in a["public_summary"]
    assert a["public_summary"]["privacy_boundary"].lower().startswith("no private")
    # Synthetic object keys (private-ish identifiers: syn_<8 digits> / g_<8 digits>)
    # must not leak into the projection. We match the exact key pattern, not the
    # bare prefix, so legitimate field names like "underlying_defect_present"
    # (which contains "g_") are not falsely flagged.
    assert not re.search(r"(syn|g)_\d{8}", blob)
