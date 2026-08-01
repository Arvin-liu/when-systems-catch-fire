#!/usr/bin/env python3
"""Task 109 — adversarial + mutation tests for the iteration planner.

These tests prove the planner does NOT commit the ten prohibited behaviors in
contract §8, and stays robust under mutations (weights, missing fields, duplicate
sources, blocked dependencies, inflated narrative text).

Run: python3 tests/iteration_planner/test_planner.py
"""
import json
import sys
from pathlib import Path

REPO = Path("/Users/zhiyuan/WorkBuddy/Claw/arr-r2-formal")
sys.path.insert(0, str(REPO / "tools/iteration_planner"))
import planner as P

MODEL = P.load_model()


def mk(cid, fi, source="fixture", cls=None, prereq=False, title="x"):
    c = P.blank_candidate(cid, source, title)
    c["factor_inputs"] = dict(fi)
    c["prerequisite_unresolved"] = prereq
    if cls:
        c["class"] = cls
    P.classify(c)
    return c


def base_fi(over=None):
    fi = {
        "harm_if_wrong": 0.5, "dependency_centrality": 0.5, "falsifiability": 0.5,
        "data_availability": 0.5, "expected_information_gain": 0.5, "evidence_cost": 0.5,
        "risk_inverted": 0.5, "maturity_gap": 0.5, "owner_relevance": 0.5,
        "duplication_inverted": 0.5, "substantive_score": 0.5,
    }
    if over:
        fi.update(over)
    return fi


def sc(c):
    P.score(c, MODEL)
    return c["aggregate_score"]


# ---- §8 prohibited behaviors ----

def test_grand_does_not_beat_bounded():
    physics = mk("PHYS", base_fi({"falsifiability": 0.2, "data_availability": 0.2,
                                  "evidence_cost": 0.85, "expected_information_gain": 0.9,
                                  "harm_if_wrong": 0.9, "substantive_score": 0.9}),
                title="四种基本相互作用统一（宏大叙事）")
    pilot = mk("PILOT", base_fi({"falsifiability": 0.95, "data_availability": 1.0,
                                 "evidence_cost": 0.2, "expected_information_gain": 0.6,
                                 "harm_if_wrong": 0.6, "substantive_score": 0.95}),
               title="crossref 完整性试点")
    assert sc(pilot) > sc(physics), "bounded falsifiable pilot must outrank grand untestable physics"


def test_more_files_does_not_raise_rank():
    a = mk("DUP-A", base_fi(), source="fixture/x.md")
    b = mk("DUP-B", base_fi(), source="fixture/y.md")  # identical factors, different source file
    assert abs(sc(a) - sc(b)) < 1e-9, "appearing in more files must not change score"


def test_do_not_schedule_blocked():
    c = mk("DNS", base_fi(), cls="DO_NOT_SCHEDULE")
    P.score(c, MODEL)
    assert c["blocked_reason"] == "DO_NOT_SCHEDULE"


def test_severe_defect_not_ignored_for_effort():
    defect = mk("DEFECT", base_fi({"harm_if_wrong": 0.95, "falsifiability": 0.9,
                                   "data_availability": 0.9, "evidence_cost": 0.9,
                                   "substantive_score": 0.85}), cls="IMPLEMENTATION_DEFECT")
    meta = mk("META", base_fi({"harm_if_wrong": 0.5, "evidence_cost": 0.2,
                               "substantive_score": 0.20}), cls="GOVERNANCE_OR_PROPAGATION_DEFECT")
    assert sc(defect) > sc(meta), "severe high-effort defect must outrank low-effort meta gap"


def test_unresolved_prerequisite_blocked():
    c = mk("PRE", base_fi({"falsifiability": 1.0, "data_availability": 1.0, "evidence_cost": 0.1}),
           prereq=True)
    P.score(c, MODEL)
    assert c["blocked_reason"] == "UNRESOLVED_PREREQUISITE"


def test_semantic_similarity_not_dependency():
    a = mk("SIM-A", base_fi(), title="门函数投影的一致性条件")
    b = mk("SIM-B", base_fi(), title="门函数投影的半经典极限")
    P.score(a, MODEL)
    assert b["canonical_id"] not in a["dependencies"], "semantic similarity must not create dependency edge"


def test_missing_fields_recorded():
    c = mk("MISS", {"harm_if_wrong": 0.8}, source="fixture")
    P.score(c, MODEL)
    assert "falsifiability" in c["missing_fields"], "missing factor must be recorded, not hidden"
    assert c["factor_vector"]["falsifiability"] == MODEL["missing_data_behavior"]["untestable_prior"]


def test_anti_meta_cap():
    meta = mk("META2", base_fi({"substantive_score": 0.9}), cls="GOVERNANCE_OR_PROPAGATION_DEFECT")
    P.score(meta, MODEL)
    assert meta["factor_vector"]["substantive_vs_meta"] <= MODEL["anti_meta_rule"]["cap_value"]


def test_recommendation_not_auto_task110():
    ranked = json.load(open(REPO / "data/operations/iterations/109/ranked_queue.json"))
    dl = json.load(open(REPO / "data/operations/iterations/109/decision_log.json"))
    assert dl["recommended_is_auto_task_110"] is False
    assert ranked["recommended_next"] is not None


# ---- mutation tests ----

def test_mutation_weights_invariant():
    # swap two weights; invariant (pilot > physics, meta < defect) must still hold
    m2 = json.loads(json.dumps(MODEL))
    w = m2["factors"]
    w[0]["weight"], w[1]["weight"] = w[1]["weight"], w[0]["weight"]
    physics = mk("PHYS", base_fi({"falsifiability": 0.2, "data_availability": 0.2, "evidence_cost": 0.85,
                                  "expected_information_gain": 0.9, "harm_if_wrong": 0.9, "substantive_score": 0.9}))
    pilot = mk("PILOT", base_fi({"falsifiability": 0.95, "data_availability": 1.0, "evidence_cost": 0.2,
                                 "expected_information_gain": 0.6, "harm_if_wrong": 0.6, "substantive_score": 0.95}))
    P.score(physics, m2); P.score(pilot, m2)
    assert pilot["aggregate_score"] > physics["aggregate_score"]


def test_mutation_inflated_narrative():
    c1 = mk("NAR-1", base_fi({"harm_if_wrong": 0.6}), title="普通试点")
    c2 = mk("NAR-2", base_fi({"harm_if_wrong": 0.6}),
            title="极其重要！！！革命性突破！！！必须立即执行！！！（修辞膨胀）")
    assert abs(sc(c1) - sc(c2)) < 1e-9, "adversarially inflated narrative text must not change score"


def test_mutation_blocked_dependency():
    c = mk("BLK", base_fi({"falsifiability": 1.0, "data_availability": 1.0, "evidence_cost": 0.0}),
           prereq=True)
    P.score(c, MODEL)
    assert c["blocked_reason"] is not None


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
