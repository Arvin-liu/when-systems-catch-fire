"""Research OS core tests (Checkpoint B).

Self-contained runner: no external test framework required. Run with:

    python3 tests/test_research_os.py

Covers: state-machine validation, obligation waiver rule, deterministic diagnosis,
inspectable scheduler, executor no-self-approval contract, and the negative
completion guarantees (source count / elapsed time / report length / executor
success must NOT cause completion).
"""

import sys
from pathlib import Path

# Make the package importable without modifying repo structure.
TOOLS = str(Path(__file__).resolve().parents[1] / "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import research_os.kernel as kernel
import research_os.obligation_graph as og
import research_os.diagnosis as dx
import research_os.scheduler as scheduler
import research_os.executor_contract as ec


_FAILS = []


def check(name, cond, detail=""):
    if cond:
        print(f"PASS  {name}")
    else:
        print(f"FAIL  {name}  {detail}")
        _FAILS.append(name)


def fresh_ep(**kw):
    return kernel.new_episode(
        kw.get("id", "ep-test"),
        kw.get("question", "q1"),
        kw.get("type", "test"),
        kw.get("pack", "QUANTITATIVE_DATA_RECONCILIATION"),
    )


def test_state_machine():
    ep = fresh_ep()
    check("init state INTAKE", ep["state"] == "INTAKE")
    illegal = False
    try:
        kernel.transition(ep, "CANDIDATE_COMPLETE")
    except ValueError:
        illegal = True
    check("illegal jump INTAKE->CANDIDATE_COMPLETE rejected", illegal)
    kernel.transition(ep, "QUESTION_FROZEN")
    kernel.transition(ep, "EVIDENCE_GATHERING")
    check("legal INTAKE->QUESTION_FROZEN->EVIDENCE_GATHERING", ep["state"] == "EVIDENCE_GATHERING")
    check("event log append-only grows", kernel.event_count(ep) >= 3)
    # terminal state blocks non-REOPENED transitions
    ep2 = fresh_ep()
    kernel.transition(ep2, "QUESTION_FROZEN")
    kernel.transition(ep2, "EVIDENCE_GATHERING")
    kernel.transition(ep2, "INSUFFICIENT_EVIDENCE_COMPLETE")
    check("INSUFFICIENT_EVIDENCE_COMPLETE is terminal", kernel.is_terminal(ep2))
    blocked = False
    try:
        kernel.transition(ep2, "ANALYSIS")
    except ValueError:
        blocked = True
    check("terminal state blocks illegal transition", blocked)
    kernel.transition(ep2, "REOPENED")
    check("terminal -> REOPENED allowed", ep2["state"] == "REOPENED")


def test_waiver_rule():
    ep = fresh_ep()
    og.add_claim(ep, "c1", "X reduces Y", "BOUNDED_STRONG")
    og.add_obligation(ep, "o1", "c1", "PRIMARY_SOURCE", "OPEN")
    og.add_obligation(ep, "o2", "c1", "FULL_TEXT_OR_METHODS_OR_SUPPLEMENT", "WAIVED_WITH_REASON",
                      evidence_refs=["n/a"])
    check("waiver raises ceiling detected", og.waiver_raises_ceiling(ep, "c1"))
    diag = dx.diagnose(ep)
    codes = {f["gap_code"] for f in diag["findings"]}
    check("CLAIM_EXCEEDS_EVIDENCE emitted on illegal waiver", "CLAIM_EXCEEDS_EVIDENCE" in codes, str(codes))


def test_diagnosis_gaps():
    ep = fresh_ep()
    og.add_claim(ep, "c1", "X reduces Y", "TENTATIVE")
    og.add_obligation(ep, "o1", "c1", "PRIMARY_SOURCE", "OPEN")
    diag = dx.diagnose(ep)
    codes = {f["gap_code"] for f in diag["findings"]}
    check("PRIMARY_SOURCE_MISSING from OPEN obligation", "PRIMARY_SOURCE_MISSING" in codes, str(codes))

    ep2 = fresh_ep()
    ep2["calculations_required"] = ["recompute_rr"]
    diag2 = dx.diagnose(ep2)
    codes2 = {f["gap_code"] for f in diag2["findings"]}
    check("NUMERIC_CLAIM_NOT_RECOMPUTED from missing calc", "NUMERIC_CLAIM_NOT_RECOMPUTED" in codes2, str(codes2))

    ep3 = fresh_ep()
    diag3 = dx.diagnose(ep3)
    codes3 = {f["gap_code"] for f in diag3["findings"]}
    check("NEGATIVE_EVIDENCE_NOT_SEARCHED default", "NEGATIVE_EVIDENCE_NOT_SEARCHED" in codes3, str(codes3))

    ep4 = fresh_ep()
    og.add_claim(ep4, "c1", "X reduces Y", "TENTATIVE")
    og.add_obligation(ep4, "o1", "c1", "PRIMARY_SOURCE", "OPEN")
    kernel.transition(ep4, "QUESTION_FROZEN")
    kernel.transition(ep4, "EVIDENCE_GATHERING")
    kernel.transition(ep4, "ANALYSIS")
    kernel.transition(ep4, "CHALLENGE")
    kernel.transition(ep4, "REVISION")
    kernel.transition(ep4, "CANDIDATE_COMPLETE")
    diag4 = dx.diagnose(ep4)
    codes4 = {f["gap_code"] for f in diag4["findings"]}
    check("PREMATURE_COMPLETION with open obligations", "PREMATURE_COMPLETION" in codes4, str(codes4))


def test_scheduler_selection():
    ep = fresh_ep()
    og.add_claim(ep, "c1", "X reduces Y", "TENTATIVE")
    og.add_obligation(ep, "o1", "c1", "PRIMARY_SOURCE", "OPEN")
    sel = scheduler.plan(ep)
    check("scheduler selects gap-addressing action", sel["selected_action"] in ("SEARCH_PRIMARY_SOURCE", "FETCH_FULL_TEXT"),
          sel["selected_action"])
    check("selection rationale has all required fields",
          all(k in sel["selection_rationale"] for k in
              ["prerequisite_gaps_addressed", "expected_information_gain", "discriminating_power",
               "cost_and_available_resources", "reversibility", "dependency_ordering",
               "risk_high_stakes_multiplier", "rejected_alternatives_and_why",
               "observation_that_would_change_next_decision"]))

    ep2 = fresh_ep()
    ep2["high_stakes"] = True
    sel2 = scheduler.plan(ep2)
    check("HUMAN_JUDGMENT_REQUIRED -> ESCALATE_TO_GPT_OWNER", sel2["selected_action"] == "ESCALATE_TO_GPT_OWNER",
          sel2["selected_action"])

    ep3 = fresh_ep()
    ep3["information_delta"] = {"delta_status": "NO_INFORMATION_GAIN", "required_response": "stop"}
    sel3 = scheduler.plan(ep3)
    check("NO_INFORMATION_GAIN -> pause/stop (not completion)",
          sel3["selected_action"] in ("PAUSE_AND_CHECKPOINT", "STOP_WITH_INSUFFICIENT_EVIDENCE"),
          sel3["selected_action"])


def test_executor_no_self_approval():
    good = {
        "observations": ["did X"],
        "source_identities": ["src1"],
        "access_level": "public",
        "calculation_result": None,
        "errors": [],
        "provenance": {"agent": "codex"},
        "timestamps": ["2026-08-03T00:00:00Z"],
    }
    check("valid return accepted", ec.validate_return(good) is good)
    rejected = False
    try:
        ec.validate_return({**good, "self_approved": True})
    except ValueError:
        rejected = True
    check("self-approval rejected", rejected)
    missing = False
    try:
        ec.validate_return({"observations": []})
    except ValueError:
        missing = True
    check("missing required fields rejected", missing)
    spec = ec.build_dispatch_spec(fresh_ep(), "SEARCH_PRIMARY_SOURCE")
    check("dispatch spec prohibits claim ceiling raise",
          any("claim ceiling" in p for p in spec["prohibited_claims"]))


def test_negative_completion_guarantees():
    # Many sources + long report + executor 'success' must NOT complete an episode.
    ep = fresh_ep()
    ep["source_identities"] = [f"src{i}" for i in range(50)]  # 50 sources
    ep["report_length_words"] = 12000  # long report
    ep["elapsed_time_hours"] = 0.7  # 43 minutes
    og.add_claim(ep, "c1", "strong claim", "BOUNDED_STRONG")
    og.add_obligation(ep, "o1", "c1", "PRIMARY_SOURCE", "OPEN")
    # Executor returns 'success' but with no real evidence.
    ret = {
        "observations": ["completed successfully"],
        "source_identities": ["secondary-news"],
        "access_level": "public",
        "calculation_result": None,
        "errors": [],
        "provenance": {"agent": "x"},
        "timestamps": ["2026-08-03T00:00:00Z"],
    }
    kernel.observe(ep, ret, actor="cli")  # must not self-approve / complete
    check("observe does not change state to terminal", not kernel.is_terminal(ep), ep["state"])
    check("observe does not alter state value", ep["state"] == "INTAKE", ep["state"])
    diag = dx.diagnose(ep)
    codes = {f["gap_code"] for f in diag["findings"]}
    check("open obligation still flagged after 'success'", "PRIMARY_SOURCE_MISSING" in codes, str(codes))
    check("claim ceiling not auto-raised by success", ep["candidate_claims"][0]["claim_ceiling"] == "BOUNDED_STRONG")


def test_r1_like_replay_rejected():
    ep = fresh_ep(pack="PUBLIC_CLAIM_FACT_CHECK")
    ep["source_timestamps_identical"] = True
    ep["reading_integrity"] = {"declared_reading_window_hours": 0.7, "minimum_required_reading_hours": 8.0}
    ep["campaign_closeout_before_deadline"] = True
    og.add_claim(ep, "c1", "night-shift study shows strong effect", "BOUNDED_STRONG")
    og.add_obligation(ep, "o1", "c1", "PRIMARY_SOURCE", "OPEN")
    og.add_obligation(ep, "o2", "c1", "NUMERIC_RECOMPUTATION", "OPEN")
    diag = dx.diagnose(ep)
    codes = {f["gap_code"] for f in diag["findings"]}
    for expected in ("TIMESTAMP_BATCH_NOT_PROOF_OF_READING", "READING_TIME_SCOPE_INCONSISTENT",
                     "UNAUTHORIZED_EARLY_CLOSEOUT", "PRIMARY_SOURCE_MISSING",
                     "NUMERIC_CLAIM_NOT_RECOMPUTED", "CLAIM_EXCEEDS_EVIDENCE"):
        check(f"R1 replay detects {expected}", expected in codes, str(codes))
    sel = scheduler.plan(ep, diag)
    check("R1 replay never selects PUBLISH_CANDIDATE_PACKET", sel["selected_action"] != "PUBLISH_CANDIDATE_PACKET",
          sel["selected_action"])


def main():
    test_state_machine()
    test_waiver_rule()
    test_diagnosis_gaps()
    test_scheduler_selection()
    test_executor_no_self_approval()
    test_negative_completion_guarantees()
    test_r1_like_replay_rejected()
    print()
    if _FAILS:
        print(f"{len(_FAILS)} FAILURE(S): {_FAILS}")
        return 1
    print("ALL RESEARCH OS CORE TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
