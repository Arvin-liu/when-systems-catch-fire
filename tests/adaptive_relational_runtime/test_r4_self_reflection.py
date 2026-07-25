"""R4 self-reflection acceptance tests (R4 task §10).

These tests cover four-axis derivation, metric-contradiction dispositions,
analyzers, the closed-set guarantee, determinism, and red-line counters. They
use synthetic fixtures and in-memory R3-like reports; none embed the private
corpus. Run with pytest from the repository root.
"""

import hashlib
import json
import os
import shutil
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

from arr_r4_self_reflection import (  # noqa: E402
    FourAxisDeriver,
    MetricContradictionEngine,
    SealedEvidenceIngestor,
    run,
)
from arr_r4_self_reflection.taxonomy import (  # noqa: E402
    ARCH_CANDIDATE_DISPOSITION,
    DEFAULT_ARCH_DISPOSITION,
    GOVERNANCE_AXIS,
    METRIC_DISPOSITIONS,
    PIPELINE_AXIS,
    SEMANTIC_AXIS,
    EVIDENCE_AXIS,
)
from .r4_fixtures import (  # noqa: E402
    build_synthetic_evidence,
    r3_like_reports,
    synthetic_envelope,
    synthetic_receipt,
)

R4_FAS = {
    "pipeline": {s: 0 for s in PIPELINE_AXIS},
    "semantic": {s: 0 for s in SEMANTIC_AXIS},
    "evidence": {s: 0 for s in EVIDENCE_AXIS},
    "governance": {s: 0 for s in GOVERNANCE_AXIS},
}
R4_FAS["semantic"]["SEMANTIC_REPRESENTATION_SUFFICIENT"] = 0
R4_FAS["semantic"]["SEMANTIC_REPRESENTATION_LIMITED"] = 836
R4_FAS["evidence"]["INDEPENDENTLY_SUPPORTED"] = 0


def _derive(claim_class="SECONDARY_ARCHIVE_CLAIM", source_ref_present=False,
            inference_labeled=False, outcome="SUCCESS", rights="private",
            real_world=False, promote=False, evolve=False, independent=False):
    rec = synthetic_receipt("k", "link", claim_class, source_ref_present, inference_labeled,
                            outcome=outcome, rights_boundary=rights)
    rec["real_world_action"] = real_world
    rec["promote_called"] = promote
    rec["evolve_called"] = evolve
    if independent:
        rec["independent_verified"] = True
    env = synthetic_envelope("k", "link", claim_class, source_ref_present, inference_labeled)
    return FourAxisDeriver().derive(rec, env)


# ---- pipeline axis -------------------------------------------------------

def test_pipeline_complete_on_success():
    r = _derive(outcome="SUCCESS")
    assert r.pipeline.status == "PIPELINE_COMPLETE"


def test_pipeline_partial():
    r = _derive(outcome="PARTIAL")
    assert r.pipeline.status == "PIPELINE_PARTIAL"


def test_pipeline_failed():
    r = _derive(outcome="FAILED")
    assert r.pipeline.status == "PIPELINE_FAILED"


def test_pipeline_quarantined_on_unknown():
    r = _derive(outcome="WEIRD")
    assert r.pipeline.status == "PIPELINE_QUARANTINED"


# ---- semantic axis -------------------------------------------------------

def test_semantic_limited_when_inference_labeled():
    r = _derive(inference_labeled=True)
    assert r.semantic.status == "SEMANTIC_REPRESENTATION_LIMITED"


def test_semantic_limited_when_transcript_inference():
    r = _derive(claim_class="TRANSCRIPT_INFERENCE", inference_labeled=False)
    assert r.semantic.status == "SEMANTIC_REPRESENTATION_LIMITED"


def test_semantic_not_attempted_when_no_inference_and_archive():
    r = _derive(claim_class="SECONDARY_ARCHIVE_CLAIM", inference_labeled=False)
    assert r.semantic.status == "SEMANTIC_NOT_ATTEMPTED"


def test_semantic_not_attempted_when_no_inference_and_author():
    r = _derive(claim_class="AUTHOR_OBSERVATION", inference_labeled=False)
    assert r.semantic.status == "SEMANTIC_NOT_ATTEMPTED"


def test_semantic_never_sufficient_from_pipeline_success():
    for cc in ("AUTHOR_OBSERVATION", "SECONDARY_ARCHIVE_CLAIM", "TRANSCRIPT_INFERENCE"):
        r = _derive(claim_class=cc, outcome="SUCCESS", inference_labeled=True)
        assert r.semantic.status != "SEMANTIC_REPRESENTATION_SUFFICIENT"


def test_semantic_never_sufficient_any_input():
    for cc in ("AUTHOR_OBSERVATION", "SECONDARY_ARCHIVE_CLAIM", "TRANSCRIPT_INFERENCE"):
        for inf in (True, False):
            r = _derive(claim_class=cc, inference_labeled=inf)
            assert r.semantic.status in SEMANTIC_AXIS
            assert r.semantic.status != "SEMANTIC_REPRESENTATION_SUFFICIENT"


# ---- evidence axis -------------------------------------------------------

def test_evidence_source_dependent_for_archive():
    r = _derive(claim_class="SECONDARY_ARCHIVE_CLAIM")
    assert r.evidence.status == "SOURCE_DEPENDENT"


def test_evidence_author_for_observation():
    r = _derive(claim_class="AUTHOR_OBSERVATION")
    assert r.evidence.status == "AUTHOR_OR_SPEAKER_REPORT"


def test_evidence_transcript_for_inference():
    r = _derive(claim_class="TRANSCRIPT_INFERENCE")
    assert r.evidence.status == "TRANSCRIPT_OR_INTERPRETER_INFERENCE"


def test_evidence_independent_only_when_flag_true():
    r = _derive(independent=True)
    assert r.evidence.status == "INDEPENDENTLY_SUPPORTED"


def test_evidence_independent_never_without_flag():
    r = _derive(claim_class="SECONDARY_ARCHIVE_CLAIM")
    assert r.evidence.status != "INDEPENDLY_SUPPORTED"
    assert r.evidence.status == "SOURCE_DEPENDENT"


def test_evidence_independent_zero_across_classes_without_flag():
    for cc in ("AUTHOR_OBSERVATION", "SECONDARY_ARCHIVE_CLAIM", "TRANSCRIPT_INFERENCE"):
        r = _derive(claim_class=cc)
        assert r.evidence.status != "INDEPENDENTLY_SUPPORTED"


# ---- governance axis -----------------------------------------------------

def test_governance_boundary_held_when_source_present():
    r = _derive(source_ref_present=True)
    assert r.governance.status == "BOUNDARY_HELD"


def test_governance_consent_limited_when_private_no_source():
    r = _derive(source_ref_present=False, rights="private")
    assert r.governance.status == "CONSENT_OR_RIGHTS_LIMITED"


def test_governance_action_prohibited_when_real_world():
    r = _derive(real_world=True)
    assert r.governance.status == "ACTION_PROHIBITED"


def test_governance_action_prohibited_when_promote():
    r = _derive(promote=True)
    assert r.governance.status == "ACTION_PROHIBITED"


def test_governance_action_prohibited_when_evolve():
    r = _derive(evolve=True)
    assert r.governance.status == "ACTION_PROHIBITED"


# ---- invariants ----------------------------------------------------------

def test_pipeline_success_never_implies_semantic_sufficient():
    r = _derive(outcome="SUCCESS")
    assert r.pipeline.status == "PIPELINE_COMPLETE"
    assert r.semantic.status != "SEMANTIC_REPRESENTATION_SUFFICIENT"


def test_exactly_four_axes():
    r = _derive()
    assert len(r.axes()) == 4


def test_each_axis_exactly_one_status():
    r = _derive()
    expected = {"pipeline": PIPELINE_AXIS, "semantic": SEMANTIC_AXIS,
                "evidence": EVIDENCE_AXIS, "governance": GOVERNANCE_AXIS}
    for ax in r.axes():
        assert ax.status in expected[ax.axis]


# ---- metric contradictions ----------------------------------------------

def _engine():
    return MetricContradictionEngine(r3_like_reports(), R4_FAS)


def test_m1_disposition():
    c = [x for x in _engine().audit() if x.contradiction_id == "M1_SUCCESS_VS_SEMANTIC"][0]
    assert c.disposition == "DEFINITION_CORRECT_VALUE_MISREAD"


def test_m2_disposition():
    c = [x for x in _engine().audit() if x.contradiction_id == "M2_UNKNOWN_RETENTION"][0]
    assert c.disposition == "DEFINITION_CORRECT_VALUE_MISREAD"


def test_m3_disposition_aggregation_defect():
    c = [x for x in _engine().audit() if x.contradiction_id == "M3_CRASH_RECOVERY_RATE"][0]
    assert c.disposition == "AGGREGATION_DEFECT"


def test_m4_disposition_aggregation_defect():
    c = [x for x in _engine().audit() if x.contradiction_id == "M4_INCREMENTAL_SELECTIVITY"][0]
    assert c.disposition == "AGGREGATION_DEFECT"


def test_m5_disposition_reporting_defect():
    c = [x for x in _engine().audit() if x.contradiction_id == "M5_CAPABILITY_ALL_PASS"][0]
    assert c.disposition == "REPORTING_DEFECT"


def test_m6_disposition():
    c = [x for x in _engine().audit() if x.contradiction_id == "M6_CORPUS_SIZE_VS_SOURCES"][0]
    assert c.disposition == "DEFINITION_CORRECT_VALUE_MISREAD"


def test_all_six_contradictions_present():
    ids = {c.contradiction_id for c in _engine().audit()}
    assert ids == {
        "M1_SUCCESS_VS_SEMANTIC", "M2_UNKNOWN_RETENTION", "M3_CRASH_RECOVERY_RATE",
        "M4_INCREMENTAL_SELECTIVITY", "M5_CAPABILITY_ALL_PASS", "M6_CORPUS_SIZE_VS_SOURCES",
    }


def test_no_unresolved_contradiction():
    for c in _engine().audit():
        assert c.disposition in METRIC_DISPOSITIONS


def test_each_contradiction_has_evidence_refs():
    for c in _engine().audit():
        assert len(c.evidence_refs) >= 1


def test_m3_cites_run_ledger_and_aggregate():
    c = [x for x in _engine().audit() if x.contradiction_id == "M3_CRASH_RECOVERY_RATE"][0]
    joined = " ".join(c.evidence_refs)
    assert "CORPUS_RUN_LEDGER" in joined and "AGGREGATE_METRICS" in joined


def test_m4_cites_run_ledger_and_aggregate():
    c = [x for x in _engine().audit() if x.contradiction_id == "M4_INCREMENTAL_SELECTIVITY"][0]
    joined = " ".join(c.evidence_refs)
    assert "CORPUS_RUN_LEDGER" in joined and "AGGREGATE_METRICS" in joined


# ---- analyzers -----------------------------------------------------------

def test_source_dependency_estimate():
    from arr_r4_self_reflection.analyzers import analyze_source_dependency
    res = analyze_source_dependency(r3_like_reports())
    assert res["independent_source_estimate"] == 9
    assert res["primary_limitation_class"] == "SOURCE_DEPENDENCY_LIMITATION"


def test_false_consensus_risk():
    from arr_r4_self_reflection.analyzers import analyze_false_consensus
    res = analyze_false_consensus(r3_like_reports())
    assert res["false_consensus_risk"] == 4
    assert res["not_a_runtime_defect"] is True


def test_temporal_unknown_count():
    from arr_r4_self_reflection.analyzers import analyze_temporal
    res = analyze_temporal(r3_like_reports())
    assert res["unknown_event_time_count"] == 449
    assert res["primary_limitation_class"] == "TEMPORAL_LIMITATION"


def test_evidence_ceiling_independently_supported_zero():
    from arr_r4_self_reflection.analyzers import analyze_evidence_ceiling
    res = analyze_evidence_ceiling(r3_like_reports(), R4_FAS)
    assert res["independently_verified_claim_class"] == 0
    assert res["evidence_axis_distribution"]["INDEPENDENTLY_SUPPORTED"] == 0


def test_limitation_attribution_has_exclusion():
    from arr_r4_self_reflection.analyzers import analyze_limitation_attribution
    res = analyze_limitation_attribution(r3_like_reports(), R4_FAS)
    assert res["count"] >= 5
    for lim in res["limitations"]:
        assert lim["exclusion"]  # non-empty exclusion record


def test_capability_reinterpretation_semantic_zero():
    from arr_r4_self_reflection.runner import _build_capability_reinterpretation
    res = _build_capability_reinterpretation(r3_like_reports(), {})
    assert res["dimensions"]["SEMANTIC"]["measured"] is False
    assert res["dimensions"]["SEMANTIC"]["item_count"] == 0


# ---- closed-set + determinism (scaling to 836) --------------------------

def test_closed_set_836():
    d = tempfile.mkdtemp()
    try:
        build_synthetic_evidence(d, 836, seed=1)
        ing = SealedEvidenceIngestor(d).ingest()
        audit = ing.validate_closed_set()
        assert audit["receipts_total"] == 836
        assert audit["envelopes_total"] == 836
        assert audit["closed_set_ok"] is True
        assert audit["missing_input_identities"] == 0
        assert audit["extra_input_identities"] == 0
    finally:
        shutil.rmtree(d)


def test_no_extra_missing_identity_small():
    d = tempfile.mkdtemp()
    try:
        build_synthetic_evidence(d, 10, seed=2)
        ing = SealedEvidenceIngestor(d).ingest()
        audit = ing.validate_closed_set()
        assert audit["missing_input_identities"] == 0
        assert audit["extra_input_identities"] == 0
    finally:
        shutil.rmtree(d)


def test_deterministic_rerun_digest_equal():
    d1, d2 = tempfile.mkdtemp(), tempfile.mkdtemp()
    o1, o2 = tempfile.mkdtemp(), tempfile.mkdtemp()
    try:
        build_synthetic_evidence(d1, 50, seed=7)
        build_synthetic_evidence(d2, 50, seed=7)
        run(d1, o1, "T", "c0")
        run(d2, o2, "T", "c0")
        p1 = os.path.join(o1, "FOUR_AXIS_OBJECT_LEDGER.json")
        p2 = os.path.join(o2, "FOUR_AXIS_OBJECT_LEDGER.json")
        h1 = hashlib.sha256(open(p1, "rb").read()).hexdigest()
        h2 = hashlib.sha256(open(p2, "rb").read()).hexdigest()
        assert h1 == h2
    finally:
        for x in (d1, d2, o1, o2):
            shutil.rmtree(x)


def test_four_axis_records_count_matches():
    d, o = tempfile.mkdtemp(), tempfile.mkdtemp()
    try:
        build_synthetic_evidence(d, 123, seed=3)
        run(d, o, "T", "c0")
        ledger = json.load(open(os.path.join(o, "FOUR_AXIS_OBJECT_LEDGER.json")))
        assert ledger["records_total"] == 123
        assert len(ledger["records"]) == 123
    finally:
        shutil.rmtree(d)
        shutil.rmtree(o)


def test_public_summary_no_private_content():
    d, o = tempfile.mkdtemp(), tempfile.mkdtemp()
    try:
        build_synthetic_evidence(d, 40, seed=4)
        analysis = run(d, o, "TASK", "cccc")
        pub = analysis["public_summary"]
        blob = json.dumps(pub)
        # No private reconstruction features in public projection.
        assert "event_time" not in blob
        assert pub["terminal_verdict"] == "ARR_R4_WAIC_SELF_REFLECTION_DRAFT_AWAITING_EXTERNAL_REVIEW"
    finally:
        shutil.rmtree(d)
        shutil.rmtree(o)


def test_counters_red_lines_zero():
    d, o = tempfile.mkdtemp(), tempfile.mkdtemp()
    try:
        build_synthetic_evidence(d, 30, seed=5)
        analysis = run(d, o, "TASK", "cccc")
        c = analysis["counters"]
        assert c["EVOLVE_CALLS"] == 0
        assert c["PROMOTE_CALLS"] == 0
        assert c["REAL_WORLD_ACTIONS"] == 0
        assert c["WAIC_CORPUS_RERUNS"] == 0
        assert c["MAIN_CHANGES"] == 0
        assert c["FORCE_PUSHES"] == 0
        assert c["HISTORY_REWRITES"] == 0
        assert c["ARCHITECTURE_CANDIDATES_TOTAL"] == 0
        assert c["R5_STARTED"] == 0
        assert c["EXTERNAL_ACCEPTANCE_CLAIMED"] == 0
    finally:
        shutil.rmtree(d)
        shutil.rmtree(o)


def test_metric_contradictions_all_resolved():
    d, o = tempfile.mkdtemp(), tempfile.mkdtemp()
    try:
        build_synthetic_evidence(d, 20, seed=6)
        analysis = run(d, o, "TASK", "cccc")
        assert analysis["counters"]["METRIC_CONTRADICTIONS_TOTAL"] == 6
        assert analysis["counters"]["METRIC_CONTRADICTIONS_UNRESOLVED"] == 0
    finally:
        shutil.rmtree(d)
        shutil.rmtree(o)
