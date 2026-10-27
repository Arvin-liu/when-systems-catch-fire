"""Review / Stop / Escalation gates (Checkpoint C).

Seven independent review gates plus a deterministic stop/escalation
recommendation. The gates consume a structured episode and a diagnosis from the
Checkpoint B engine. They are *necessary but not sufficient*: passing all gates
does not by itself authorize publication or completion; owner/GPT acceptance
(gate 7) remains required.

Gate vocabulary (architecture doc §5.7):
  1. source_provenance       - every evidence obligation satisfied / not applicable
  2. method_calculation      - no NUMERIC_CLAIM_NOT_RECOMPUTED finding
  3. source_dependence       - no SOURCE_DEPENDENCE_HIGH finding
  4. adversarial_claim       - no ADVERSARIAL_REVIEW_MISSING finding
  5. claim_ceiling           - no CLAIM_EXCEEDS_EVIDENCE finding
  6. high_stakes_escalation  - high-stakes episodes must be ESCALATED_TO_GPT_OWNER
  7. owner_gpt_acceptance    - state at CANDIDATE_COMPLETE or ESCALATED_TO_GPT_OWNER
"""

from __future__ import annotations

from typing import Any

GATE_NAMES: list[str] = [
    "source_provenance",
    "method_calculation",
    "source_dependence",
    "adversarial_claim",
    "claim_ceiling",
    "high_stakes_escalation",
    "owner_gpt_acceptance",
]

_ESCALATED = "ESCALATED_TO_GPT_OWNER"
_CANDIDATE = "CANDIDATE_COMPLETE"
_INSUFFICIENT = "INSUFFICIENT_EVIDENCE_COMPLETE"

# Integrity / claim-ceiling failures that force escalation regardless of other gates.
_FORCED_ESCALATION_CODES = {
    "CLAIM_EXCEEDS_EVIDENCE",
    "PREMATURE_COMPLETION",
    "UNAUTHORIZED_EARLY_CLOSEOUT",
    "READING_TIME_SCOPE_INCONSISTENT",
    "TIMESTAMP_BATCH_NOT_PROOF_OF_READING",
    "PRIMARY_SOURCE_MISSING",
}


def _has_finding(diagnosis: dict, code: str) -> bool:
    return any(f["gap_code"] == code for f in diagnosis.get("findings", []))


def gate_source_provenance(ep: dict, diagnosis: dict) -> dict:
    obs = ep.get("evidence_obligations", []) or []
    unsatisfied = [o for o in obs if o["status"] in ("OPEN", "PARTIAL", "BLOCKED_WITH_EVIDENCE")]
    passed = not unsatisfied
    detail = (
        "all evidence obligations satisfied or not applicable"
        if passed
        else "unsatisfied obligations: "
        + ", ".join(o["obligation_id"] for o in unsatisfied)
    )
    return {"gate": "source_provenance", "passed": passed, "detail": detail}


def gate_method_calculation(ep: dict, diagnosis: dict) -> dict:
    passed = not _has_finding(diagnosis, "NUMERIC_CLAIM_NOT_RECOMPUTED")
    return {
        "gate": "method_calculation",
        "passed": passed,
        "detail": "numeric claims recomputed" if passed else "NUMERIC_CLAIM_NOT_RECOMPUTED present",
    }


def gate_source_dependence(ep: dict, diagnosis: dict) -> dict:
    passed = not _has_finding(diagnosis, "SOURCE_DEPENDENCE_HIGH")
    return {
        "gate": "source_dependence",
        "passed": passed,
        "detail": "source independence verified" if passed else "SOURCE_DEPENDENCE_HIGH present",
    }


def gate_adversarial_claim(ep: dict, diagnosis: dict) -> dict:
    passed = not _has_finding(diagnosis, "ADVERSARIAL_REVIEW_MISSING")
    return {
        "gate": "adversarial_claim",
        "passed": passed,
        "detail": "adversarial review present" if passed else "ADVERSARIAL_REVIEW_MISSING present",
    }


def gate_claim_ceiling(ep: dict, diagnosis: dict) -> dict:
    passed = not _has_finding(diagnosis, "CLAIM_EXCEEDS_EVIDENCE")
    return {
        "gate": "claim_ceiling",
        "passed": passed,
        "detail": "claim ceiling within evidence" if passed else "CLAIM_EXCEEDS_EVIDENCE present",
    }


def gate_high_stakes_escalation(ep: dict, diagnosis: dict) -> dict:
    if not ep.get("high_stakes"):
        return {"gate": "high_stakes_escalation", "passed": True, "detail": "not a high-stakes episode"}
    passed = ep.get("state") == _ESCALATED
    return {
        "gate": "high_stakes_escalation",
        "passed": passed,
        "detail": "escalated to GPT/owner" if passed else "high-stakes episode not escalated to GPT/owner",
    }


def gate_owner_gpt_acceptance(ep: dict, diagnosis: dict) -> dict:
    passed = ep.get("state") in (_CANDIDATE, _ESCALATED)
    return {
        "gate": "owner_gpt_acceptance",
        "passed": passed,
        "detail": "at CANDIDATE_COMPLETE or ESCALATED_TO_GPT_OWNER" if passed else "owner/GPT acceptance not recorded",
    }


def evaluate_gates(ep: dict, diagnosis: dict | None = None) -> dict:
    """Evaluate all seven gates and report pass/fail.

    If `diagnosis` is omitted it is computed from the episode.
    """
    if diagnosis is None:
        from . import diagnosis as dx

        diagnosis = dx.diagnose(ep)
    results = {name: globals()[f"gate_{name}"](ep, diagnosis) for name in GATE_NAMES}
    all_pass = all(r["passed"] for r in results.values())
    return {
        "episode_id": ep.get("episode_id"),
        "gates": results,
        "all_gates_pass": all_pass,
        "note": "passing gates is necessary but not sufficient; owner/GPT acceptance remains required",
    }


def recommend(ep: dict, diagnosis: dict | None = None, gates_result: dict | None = None) -> dict:
    """Deterministic stop/escalation recommendation from the episode state.

    Returns an action in {ESCALATE, PAUSE_CHECKPOINT, STOP_INSUFFICIENT,
    READY_FOR_ACCEPTANCE, DONE_INSUFFICIENT, CONTINUE} plus reasons.
    """
    if diagnosis is None:
        from . import diagnosis as dx

        diagnosis = dx.diagnose(ep)
    if gates_result is None:
        gates_result = evaluate_gates(ep, diagnosis)

    codes = {f["gap_code"] for f in diagnosis.get("findings", [])}
    gates = gates_result["gates"]

    forced = sorted(codes & _FORCED_ESCALATION_CODES)
    if forced:
        return {"action": "ESCALATE", "reasons": [f"integrity/claim failure: {c}" for c in forced]}
    if not gates["high_stakes_escalation"]["passed"]:
        return {"action": "ESCALATE", "reasons": ["high-stakes episode not escalated to GPT/owner"]}

    if gates_result["all_gates_pass"]:
        state = ep.get("state")
        if state == _INSUFFICIENT:
            return {"action": "DONE_INSUFFICIENT", "reasons": ["reliable insufficient-evidence terminal reached"]}
        if state in (_CANDIDATE, _ESCALATED):
            return {"action": "READY_FOR_ACCEPTANCE", "reasons": ["all gates pass; owner/GPT acceptance required"]}
        return {"action": "CONTINUE", "reasons": ["all gates pass; continue toward a candidate"]}

    if "ATTRACTOR_LOOP_RISK" in codes:
        return {"action": "ESCALATE", "reasons": ["attractor loop risk detected"]}
    if "NO_INFORMATION_GAIN" in codes:
        return {"action": "PAUSE_CHECKPOINT", "reasons": ["no information gain; pause and checkpoint"]}
    return {"action": "CONTINUE", "reasons": ["gates failing; address open obligations / findings"]}
