"""R4 attack tests mapping to R4 task §10 explicit acceptance requirements.

Each requirement in §10 is asserted as an independent, reproducible check. These
complement (not duplicate) the structural tests in test_r4_self_reflection.py.
"""

import json
import os
import tempfile

from arr_r4_self_reflection import FourAxisDeriver, run
from arr_r4_self_reflection.analyzers import (
    analyze_evidence_ceiling,
    analyze_false_consensus,
    analyze_source_dependency,
    analyze_temporal,
)
from .r4_fixtures import build_synthetic_evidence, r3_like_reports, synthetic_envelope, synthetic_receipt


def _derive(claim_class, source_ref_present=False, inference_labeled=False, outcome="SUCCESS"):
    rec = synthetic_receipt("k", "link", claim_class, source_ref_present, inference_labeled, outcome=outcome)
    env = synthetic_envelope("k", "link", claim_class, source_ref_present, inference_labeled)
    return FourAxisDeriver().derive(rec, env)


# --- closed set exactly 836/836 -----------------------------------------

def test_closed_set_exactly_836():
    d = tempfile.mkdtemp()
    try:
        build_synthetic_evidence(d, 836, seed=11)
        from arr_r4_self_reflection import SealedEvidenceIngestor
        ing = SealedEvidenceIngestor(d).ingest()
        a = ing.validate_closed_set()
        assert a["receipts_total"] == 836
        assert a["envelopes_total"] == 836
    finally:
        import shutil
        shutil.rmtree(d)


def test_no_extra_or_missing_identity():
    d = tempfile.mkdtemp()
    try:
        build_synthetic_evidence(d, 836, seed=12)
        from arr_r4_self_reflection import SealedEvidenceIngestor
        ing = SealedEvidenceIngestor(d).ingest()
        a = ing.validate_closed_set()
        assert a["missing_input_identities"] == 0
        assert a["extra_input_identities"] == 0
        assert a["count_delta"] == 0
    finally:
        import shutil
        shutil.rmtree(d)


# --- deterministic rerun identical digests ------------------------------

def test_deterministic_rerun_identical():
    d = tempfile.mkdtemp()
    o1, o2 = tempfile.mkdtemp(), tempfile.mkdtemp()
    try:
        build_synthetic_evidence(d, 200, seed=21)
        run(d, o1, "T", "c")
        run(d, o2, "T", "c")
        import hashlib
        h1 = hashlib.sha256(open(os.path.join(o1, "METRIC_CONTRADICTION_LEDGER.json"), "rb").read()).hexdigest()
        h2 = hashlib.sha256(open(os.path.join(o2, "METRIC_CONTRADICTION_LEDGER.json"), "rb").read()).hexdigest()
        assert h1 == h2
    finally:
        import shutil
        for x in (d, o1, o2):
            shutil.rmtree(x)


# --- every object exactly four axis statuses ---------------------------

def test_every_object_four_axes():
    d, o = tempfile.mkdtemp(), tempfile.mkdtemp()
    try:
        build_synthetic_evidence(d, 77, seed=31)
        run(d, o, "T", "c")
        ledger = json.load(open(os.path.join(o, "FOUR_AXIS_OBJECT_LEDGER.json")))
        for rec in ledger["records"]:
            assert set(rec.keys()) >= {"object_key", "pipeline", "semantic", "evidence", "governance"}
            for ax in ("pipeline", "semantic", "evidence", "governance"):
                assert "status" in rec[ax]
    finally:
        import shutil
        for x in (d, o):
            shutil.rmtree(x)


# --- pipeline success cannot imply semantic sufficiency -----------------

def test_pipeline_success_not_semantic_sufficiency():
    for cc in ("AUTHOR_OBSERVATION", "SECONDARY_ARCHIVE_CLAIM", "TRANSCRIPT_INFERENCE"):
        r = _derive(cc, outcome="SUCCESS")
        assert r.pipeline.status == "PIPELINE_COMPLETE"
        assert r.semantic.status != "SEMANTIC_REPRESENTATION_SUFFICIENT"


# --- unknown time retained and counted ---------------------------------

def test_unknown_time_retained():
    rec = synthetic_receipt("k", "link", "SECONDARY_ARCHIVE_CLAIM", False, False)
    assert rec["temporal"]["event_time"] == "UNKNOWN"
    res = analyze_temporal(r3_like_reports())
    assert res["unknown_event_time_count"] == 449
    assert res["unknown_retained_in_receipts"] is True


# --- source-dependent claims cannot become independent support ---------

def test_source_dependent_not_independent():
    r = _derive("SECONDARY_ARCHIVE_CLAIM")
    assert r.evidence.status == "SOURCE_DEPENDENT"
    assert r.evidence.status != "INDEPENDENTLY_SUPPORTED"


# --- repeated notes / source paraphrases do not inflate corroboration --

def test_repeated_notes_do_not_inflate():
    res = analyze_source_dependency(r3_like_reports())
    assert res["independent_source_estimate"] == 9
    assert res["independent_source_estimate"] < 836
    # the same key appearing under multiple hosts is reported, not added as new sources
    assert "repeated_note_keys_across_hosts" in res


# --- transcript inference cannot become speaker belief or verified fact -

def test_transcript_inference_not_belief_or_fact():
    r = _derive("TRANSCRIPT_INFERENCE", inference_labeled=True)
    assert r.evidence.status == "TRANSCRIPT_OR_INTERPRETER_INFERENCE"
    assert r.evidence.status != "AUTHOR_OR_SPEAKER_REPORT"
    assert r.evidence.status != "INDEPENDENTLY_SUPPORTED"
    assert r.semantic.status != "SEMANTIC_REPRESENTATION_SUFFICIENT"


# --- all mandatory metric contradictions receive dispositions ----------

def test_all_mandatory_contradictions_dispositioned():
    d, o = tempfile.mkdtemp(), tempfile.mkdtemp()
    try:
        build_synthetic_evidence(d, 15, seed=41)
        a = run(d, o, "T", "c")
        assert a["counters"]["METRIC_CONTRADICTIONS_TOTAL"] == 6
        assert a["counters"]["METRIC_CONTRADICTIONS_UNRESOLVED"] == 0
        for c in a["contradictions"]:
            assert c["disposition"]
    finally:
        import shutil
        for x in (d, o):
            shutil.rmtree(x)


# --- metric rate denominators/numerators explicit -----------------------

def test_metric_denominators_explicit():
    res = analyze_temporal(r3_like_reports())
    # rate is reported together with the absolute count, making the denominator explicit
    assert "unknown_event_time_count" in res and "temporal_ambiguity_rate" in res
    assert 0.0 < res["temporal_ambiguity_rate"] <= 1.0
    assert res["unknown_event_time_count"] == 449


# --- crash/incremental reconcile with demo reports ----------------------

def test_crash_incremental_reconcile_with_demos():
    from arr_r4_self_reflection.metric_consistency import MetricContradictionEngine
    eng = MetricContradictionEngine(r3_like_reports(), {})
    m3 = [c for c in eng.audit() if c.contradiction_id == "M3_CRASH_RECOVERY_RATE"][0]
    m4 = [c for c in eng.audit() if c.contradiction_id == "M4_INCREMENTAL_SELECTIVITY"][0]
    assert m3.observed_values["run_ledger_crash_recovery_success_rate"] == 1.0
    assert m3.observed_values["crash_report_all_resume_complete"] is True
    assert m4.observed_values["run_ledger_incremental_selectivity"] == 0.0011961722488038277
    assert m4.observed_values["incremental_rerun_reprocessed_on_change"] == 1


# --- capability coverage distinguishes operational/semantic/evidence/governance

def test_capability_distinguishes_dimensions():
    from arr_r4_self_reflection.runner import _build_capability_reinterpretation
    res = _build_capability_reinterpretation(r3_like_reports(), {})
    for dim in ("OPERATIONAL", "SEMANTIC", "EVIDENCE", "GOVERNANCE"):
        assert dim in res["dimensions"]
    assert res["dimensions"]["SEMANTIC"]["measured"] is False


# --- architecture-candidate gate rejects single-case / lower-level -----

def test_gate_rejects_single_case_and_lower_level():
    from arr_r4_self_reflection.arch_gate import decide
    from arr_r4_self_reflection.taxonomy import DEFAULT_ARCH_DISPOSITION
    single = {c: True for c in [
        "reproducible_from_sealed_evidence", "cross_source_or_class_breadth",
        "not_explained_by_lower_level", "measurable_loss_or_misclassification",
        "primitives_cannot_represent", "lower_cost_adapter_insufficient",
        "explicit_non_goals_risk_rollback", "independent_audit_agrees"]}
    single["cross_source_or_class_breadth"] = False
    assert decide(single)[0] == DEFAULT_ARCH_DISPOSITION
    lower = dict(single)
    lower["cross_source_or_class_breadth"] = True
    lower["not_explained_by_lower_level"] = False
    assert decide(lower)[0] == DEFAULT_ARCH_DISPOSITION


# --- no candidate creates an EVOLVE call --------------------------------

def test_no_candidate_creates_evolve():
    d, o = tempfile.mkdtemp(), tempfile.mkdtemp()
    try:
        build_synthetic_evidence(d, 12, seed=51)
        a = run(d, o, "T", "c")
        assert a["counters"]["EVOLVE_CALLS"] == 0
        assert a["architecture_register"]["candidates_total"] == 0
    finally:
        import shutil
        for x in (d, o):
            shutil.rmtree(x)


# --- public projection contains no private content ----------------------

def test_public_projection_no_private_content():
    d, o = tempfile.mkdtemp(), tempfile.mkdtemp()
    try:
        build_synthetic_evidence(d, 16, seed=61)
        a = run(d, o, "T", "c")
        blob = json.dumps(a["public_summary"])
        assert "raw_text" not in blob
        assert "transcript" not in blob.lower() or "transcript_inference" not in blob.lower()
        assert a["public_summary"]["privacy_boundary"]
    finally:
        import shutil
        for x in (d, o):
            shutil.rmtree(x)


# --- real-world / PROMOTE / EVOLVE / Ready / merge / Main remain zero --

def test_red_lines_remain_zero():
    d, o = tempfile.mkdtemp(), tempfile.mkdtemp()
    try:
        build_synthetic_evidence(d, 18, seed=71)
        a = run(d, o, "T", "c")
        c = a["counters"]
        for k in ("REAL_WORLD_ACTIONS", "PROMOTE_CALLS", "EVOLVE_CALLS",
                  "FORMAL_READY_PRS", "FORMAL_MERGES", "MAIN_CHANGES",
                  "FORCE_PUSHES", "HISTORY_REWRITES"):
            assert c[k] == 0
    finally:
        import shutil
        for x in (d, o):
            shutil.rmtree(x)


# --- changed-path propagation residue zero (R3 property preserved) -----

def test_path_propagation_residue_zero():
    cap = r3_like_reports()["CAPABILITY_COVERAGE_MATRIX"]
    ids = {i["id"] for i in cap["items"]}
    assert "changed_path_propagation_residue_zero" in ids
    assert "ambiguous_path_mapping_zero" in ids
    for i in cap["items"]:
        if i["id"] in ("changed_path_propagation_residue_zero", "ambiguous_path_mapping_zero"):
            assert i["pass"] is True


# --- CI receipt artifact produced, honestly not falsely green ----------

def test_ci_receipt_artifact_present():
    d, o = tempfile.mkdtemp(), tempfile.mkdtemp()
    try:
        build_synthetic_evidence(d, 14, seed=81)
        run(d, o, "T", "c")
        ci = json.load(open(os.path.join(o, "CI_RECEIPT.json")))
        for k in ("local_static_gate", "exact_head_r4_ci", "foundation_validation",
                  "q33_governance_validation"):
            assert k in ci
        # must not falsely claim success before publish
        assert ci["exact_head_r4_ci"] in ("PENDING_PUBLISH", "success")
    finally:
        import shutil
        for x in (d, o):
            shutil.rmtree(x)


# --- evidence ceiling: corpus size is not evidence count ---------------

def test_corpus_size_not_evidence_count():
    ceil = analyze_evidence_ceiling(r3_like_reports(), {
        "evidence": {"INDEPENDENTLY_SUPPORTED": 0, "SOURCE_DEPENDENT": 545,
                     "AUTHOR_OR_SPEAKER_REPORT": 276, "TRANSCRIPT_OR_INTERPRETER_INFERENCE": 15}})
    assert ceil["independently_verified_claim_class"] == 0
    assert ceil["evidence_axis_distribution"]["INDEPENDENTLY_SUPPORTED"] == 0
