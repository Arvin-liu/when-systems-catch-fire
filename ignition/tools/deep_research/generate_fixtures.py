"""Deep Research Capability — canonical positive fixture generator (Round 1).

Emits one valid example record per Deep Research Capability type into
``tests/fixtures/deep_research/round1/positive/``. The fixtures are produced by
``records.make_record`` so they are guaranteed schema-valid and stay consistent
with the generated schemas (canonical-output principle: never hand-edit, always
generate). They double as human-readable example documents.

Run from the repository root:
    python3 tools/deep_research/generate_fixtures.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))
from deep_research.records import make_record  # noqa: E402


OUT_DIR = REPO_ROOT / "tests" / "fixtures" / "deep_research" / "round1" / "positive"

# (record_name, overrides) — each override yields a schema-valid example.
POSITIVE_EXAMPLES = [
    ("research-topic-candidate", {
        "candidate_id": "cand-SLEEP-TIMING",
        "proposed_question": "What is the optimal sleep-timing window for adult sustained cognitive recovery?",
        "source_of_seed": "TRUSTED_RECENT_SIGNAL",
        "proposed_strategy_pack": "sleep-timing-v1",
        "materiality": 0.8,
        "expected_information_gain": 0.7,
        "tractability": 0.6,
        "access": 0.7,
        "freshness": 0.9,
        "cost": 1.5,
        "risk": 0.2,
        "diversity": 0.5,
        "status": "CANDIDATE",
    }),
    ("research-brief", {
        "brief_id": "brief-SLEEP-TIMING",
        "question_version": "v1",
        "question": "What is the optimal sleep-timing window for adult sustained cognitive recovery?",
        "scope": {
            "population": "healthy adults 18-65",
            "object": "sleep onset/offset timing relative to circadian markers",
            "timeframe": "2020-2026",
            "outcomes": ["cognitive recovery", "next-day alertness"],
            "prohibited_overreach": ["mortality claims", "clinical treatment guidance"],
        },
        "strategy_pack": "sleep-timing-v1",
        "source_family_priorities": ["RCT", "cohort"],
        "frozen": True,
    }),
    ("research-plan", {
        "plan_id": "plan-SLEEP-TIMING",
        "brief_id": "brief-SLEEP-TIMING",
        "obligations": [
            {"obligation_id": "obl-PRIMARY", "claim_id": "claim-1", "obligation_class": "PRIMARY_SOURCE", "status": "OPEN"},
        ],
        "subquestions": ["Does midpoint-of-sleep timing predict recovery?"],
        "search_strategy": "systematic search of RCT/cohort on sleep timing",
        "stop_criteria": ["all HIGH obligations satisfied", "gate SOURCE_PROVENANCE passed"],
    }),
    ("evidence-obligation", {
        "obligation_id": "obl-PRIMARY",
        "claim_id": "claim-1",
        "obligation_class": "PRIMARY_SOURCE",
        "status": "SATISFIED",
        "severity": "HIGH",
        "satisfied_by": ["src-RCT-001"],
        "ceiling_impact": "BOUNDED_STRONG",
    }),
    # source-record with opened=true MUST carry inspected_scope (fail-closed satisfied)
    ("source-record", {
        "source_id": "src-RCT-001",
        "kind": "clinical_trial",
        "source_family": "RCT",
        "discovery_method": "systematic_search",
        "opened": True,
        "access_level": "FULL_TEXT",
        "inspected_scope": "full-text methods + results tables 1-3",
        "opened_at": "2026-02-01T00:00:00Z",
        "independence_group": "independent_author",
    }),
    # source-record with opened absent (condition not triggered)
    ("source-record", {
        "source_id": "src-DISCOVERED-002",
        "access_level": "DISCOVERED",
    }),
    ("research-action", {
        "action_id": "act-001",
        "action_code": "SEARCH_PRIMARY_SOURCE",
        "objective": "locate primary RCTs on sleep timing",
        "prohibited_claims": ["do not assert effect size"],
    }),
    ("executor-observation", {
        "observation_id": "obs-001",
        "action_id": "act-001",
        "observations": ["found 3 RCTs matching criteria"],
        "source_identities": [{"source_id": "src-RCT-001", "access_level": "FULL_TEXT"}],
        "access_level": "FULL_TEXT",
        "calculation_result": None,
        "errors": [],
        "provenance": [{"step": "search", "tool": "web"}],
        "timestamps": {"started": "2026-02-01T00:00:00Z", "ended": "2026-02-01T00:05:00Z"},
    }),
    ("claim-evidence-record", {
        "claim_id": "claim-1",
        "claim_text": "Later sleep midpoint is associated with slower same-day cognitive recovery in adults.",
        "claim_ceiling": "QUALIFIED",
        "supporting_obligations": ["obl-PRIMARY"],
        "source_relations": [{"source_id": "src-RCT-001", "supports": True}],
        "entailed_by_source": True,
        "faithfulness": 0.8,
        "groundedness": 0.75,
        "status": "UNDER_REVIEW",
    }),
    ("research-trace-event", {
        "event_id": "evt-0001",
        "timestamp": "2026-02-01T00:00:00Z",
        "type": "ACTION_DISPATCH",
        "actor": "kernel",
        "payload_sha256": "a" * 64,
        "round": 1,
        "phase": "evidence_gathering",
    }),
    # sufficiency decision STOP_SUFFICIENT_CANDIDATE MUST carry hard_gates_passed=true
    ("research-sufficiency-decision", {
        "decision_id": "suff-001",
        "episode_id": "ep-SLEEP-TIMING",
        "hard_gates_passed": True,
        "failed_hard_gates": [],
        "sufficiency_vector": {"source_provenance": 1.0, "adversarial_claim": 0.9},
        "decision": "STOP_SUFFICIENT_CANDIDATE",
        "rationale": "all HIGH obligations satisfied, gates passed",
        "deterministic_inputs": True,
        "model_proposed": False,
    }),
    ("research-sufficiency-decision", {
        "decision_id": "suff-002",
        "episode_id": "ep-SLEEP-TIMING",
        "hard_gates_passed": False,
        "failed_hard_gates": ["ADVERSARIAL_CLAIM"],
        "decision": "CONTINUE_RESEARCH",
        "deterministic_inputs": True,
        "model_proposed": False,
    }),
    ("research-episode-result", {
        "result_id": "res-001",
        "episode_id": "ep-SLEEP-TIMING",
        "brief_id": "brief-SLEEP-TIMING",
        "final_state": "CANDIDATE_COMPLETE",
        "claims": [{"claim_id": "claim-1", "claim_ceiling": "QUALIFIED"}],
        "source_records": [{"source_id": "src-RCT-001"}],
        "obligations_status": {"SATISFIED": 1, "OPEN": 0},
        "sufficiency_decision": {"decision": "STOP_SUFFICIENT_CANDIDATE"},
        "report_ref": "reports/.../sleep-timing.md",
        "machine_trace_ref": "data/.../sleep-timing-trace.jsonl",
    }),
    ("research-queue-item", {
        "queue_item_id": "qi-001",
        "topic_candidate": {"candidate_id": "cand-SLEEP-TIMING"},
        "episode_id": "ep-SLEEP-TIMING",
        "lease": {"owner": "workbuddy", "expiry": "2026-02-02T00:00:00Z", "claim_id": "lease-001"},
        "status": "ACTIVE",
        "checkpoint_commit": "abc123",
        "priority_factors": {"materiality": 0.8},
    }),
    ("research-campaign", {
        "campaign_id": "camp-SLEEP-HEALTH",
        "items": [{"queue_item_id": "qi-001"}],
        "stop_conditions": {"queue_empty_stops": True, "max_episodes": 12, "safety_blocker_stops": True},
        "status": "RUNNING",
    }),
]


def write_all() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    for name, overrides in POSITIVE_EXAMPLES:
        obj = make_record(name, **overrides)
        # filename: <record>__<candidate_id|decision_id|...>.json for uniqueness
        tag = (
            overrides.get("candidate_id")
            or overrides.get("brief_id")
            or overrides.get("obligation_id")
            or overrides.get("source_id")
            or overrides.get("action_id")
            or overrides.get("observation_id")
            or overrides.get("claim_id")
            or overrides.get("event_id")
            or overrides.get("decision_id")
            or overrides.get("result_id")
            or overrides.get("queue_item_id")
            or overrides.get("campaign_id")
            or f"ex{written}"
        )
        path = OUT_DIR / f"{name}__{tag}.json"
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        written += 1
    return written


if __name__ == "__main__":
    n = write_all()
    print(f"wrote {n} positive deep-research fixtures to {OUT_DIR}")
