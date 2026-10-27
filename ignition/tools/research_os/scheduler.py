"""Inspectable Next-Action Scheduler (Checkpoint B).

Deterministic baseline scheduler over the finite 24-action vocabulary. No LLM is
required. LLM proposals are only optional candidate inputs and are never the sole
selector or validator. Selection is inspectable: prerequisite gaps addressed,
expected information gain, discriminating power, cost, reversibility, dependency
ordering, risk multiplier, rejected alternatives, and the observation that would
change the next decision.
"""

from __future__ import annotations

from typing import Any

from . import diagnosis as dx
from . import registries as R

# Default discriminating power by action category (1=low, 2=medium, 3=high).
DEFAULT_DP = {
    "QUESTION": 2,
    "SOURCE": 2,
    "READ": 2,
    "COMPUTE": 3,
    "RECONCILE": 3,
    "DEPENDENCE": 2,
    "REPLICATION": 2,
    "CHALLENGE": 3,
    "REVIEW": 3,
    "CLAIM": 2,
    "CONTROL": 1,
    "ESCALATION": 2,
    "STOP": 3,
    "PUBLISH": 1,
}

COST_SCORE = {"low": 2, "medium": 1, "high": 0}

# Action prerequisite ordering: an action scores lower until its dependency is done.
DEPENDENCIES = {
    "RECOMPUTE_RESULT": ["LOCATE_RAW_DATA"],
    "REPRODUCE_ANALYSIS": ["LOCATE_ANALYSIS_CODE"],
    "BUILD_DEFINITION_CROSSWALK": ["READ_METHODS"],
    "COMPARE_OUTCOMES_OR_DENOMINATORS": ["BUILD_DEFINITION_CROSSWALK"],
}


def _dp_label(meta: dict) -> str:
    v = DEFAULT_DP.get(meta["category"], 1)
    return "high" if v >= 3 else ("medium" if v == 2 else "low")


def plan(ep: dict, diagnosis: dict | None = None) -> dict:
    if diagnosis is None:
        diagnosis = dx.diagnose(ep)
    gaps = {f["gap_code"] for f in diagnosis.get("findings", [])}
    human_required = "HUMAN_JUDGMENT_REQUIRED" in gaps
    no_gain = "NO_INFORMATION_GAIN" in gaps
    taken = set(ep.get("actions_taken", []) or [])

    candidates: list[tuple[str, int, list[str]]] = []
    for code, meta in R.ACTION_BY_CODE.items():
        score = 0
        addressed = [g for g in meta["typical_gaps"] if g in gaps]
        if addressed:
            score += sum(R.SEVERITY_RANK[R.GAP_BY_CODE[g]["severity"]] for g in addressed) * 2
        score += DEFAULT_DP.get(meta["category"], 1)
        score += COST_SCORE.get(meta["cost_class"], 1)
        if meta["reversible"]:
            score += 1
        for dep in DEPENDENCIES.get(code, []):
            if dep not in taken:
                score -= 3
        if meta["requires_human"] and not human_required:
            score -= 2
        if code == "ESCALATE_TO_GPT_OWNER" and human_required:
            score += 10
        if code == "STOP_WITH_INSUFFICIENT_EVIDENCE" and no_gain:
            score += 8
        if code == "PAUSE_AND_CHECKPOINT" and no_gain:
            score += 4
        candidates.append((code, score, addressed))

    ranked = sorted(candidates, key=lambda x: (-x[1], x[0]))
    selected = None
    for code, score, addressed in ranked:
        if score > 0:
            selected = code
            break
    if selected is None:
        # Nothing actionable -> suggest a resumable pause, never a completion.
        selected = "PAUSE_AND_CHECKPOINT"
        selected_score = 0
        addressed = []
    else:
        selected_score = dict((c, s) for c, s, _ in ranked)[selected]

    meta = R.ACTION_BY_CODE[selected]
    rationale = {
        "prerequisite_gaps_addressed": addressed,
        "expected_information_gain": "high" if addressed else "low",
        "discriminating_power": _dp_label(meta),
        "cost_and_available_resources": {"cost_class": meta["cost_class"]},
        "reversibility": "reversible" if meta["reversible"] else "irreversible",
        "dependency_ordering": DEPENDENCIES.get(selected, []),
        "risk_high_stakes_multiplier": 3.0 if meta["requires_human"] else 1.0,
        "rejected_alternatives_and_why": [
            {"action": c, "why": f"score {s} lower than selected {selected_score}"}
            for c, s, _ in ranked
            if c != selected and s > 0
        ][:5],
        "observation_that_would_change_next_decision": (
            f"if {meta['typical_gaps']} resolved, select next from remaining gaps"
        ),
    }
    return {
        "episode_id": ep.get("episode_id"),
        "selected_action": selected,
        "selection_rationale": rationale,
        "ranked_candidates": [
            {"action": c, "score": s} for c, s, _ in ranked if s > 0
        ][:8],
    }


def mark_action_taken(ep: dict, action_code: str) -> dict:
    R.assert_action(action_code)
    ep.setdefault("actions_taken", []).append(action_code)
    return ep
