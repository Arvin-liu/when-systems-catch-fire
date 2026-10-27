"""Round 6 — Bounded live pilot: sleep timing and health (TASK.md Round 6).

Freezes the exact Round 6 question and drives it through the IMPLEMENTED
queue/capability interfaces (Round 2 SerialQueue + Round 3 EpisodeController +
Round 4 SufficiencyEvaluator), preserving a full machine trace.

Per TASK.md Round 6 the pilot may legitimately end as a sufficient candidate,
insufficient evidence, budget pause, blocker, or GPT escalation, and it must
only START when "required tool access is available without unresolved approval
blocking". The deep-research capability's adapters are OFFLINE-SAFE by design
(Rounds 1-3): they never reach the public web. No live public-web tool is wired
into the runtime in this sandbox, so a genuine LIVE evidence-gathering pilot
cannot be executed here. The pilot therefore:
  * still exercises the real queue + episode interfaces end-to-end (proving the
    assembled pipeline is stable and deterministic);
  * preserves a complete machine trace (episode event log + queue state +
    pilot report);
  * terminates honestly as BLOCKED_WITH_EVIDENCE, recording the EXACT evidence
    of why the live pilot could not run, and carrying the limitation forward to
    the Round 7 Codex handoff (exact resume commands included).

It does NOT attempt unattended public-web work (TASK.md: "Do not start or
continue public-web work when an approval window is waiting unattended").
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "tools"))

from research_os import kernel as K  # noqa: E402
from deep_research import adapters as A  # noqa: E402
from deep_research import records as R  # noqa: E402
from deep_research import episode_loop as E  # noqa: E402
from deep_research import queue_runtime as Q  # noqa: E402

PACK = "SYSTEMATIC_EVIDENCE_SYNTHESIS"

# Exact frozen question (TASK.md Round 6).
FROZEN_QUESTION = (
    "For adults obtaining approximately 7-8 hours of sleep, what causal or "
    "near-causal health effects are supported for consistently late sleep "
    "timing or delayed circadian phase, separately from sleep duration, "
    "chronotype and social jetlag?"
)

# Research boundaries (TASK.md Round 6).
BOUNDARIES = [
    "capability evaluation, not individualized medical advice",
    "distinguish timing, phase, chronotype, social jetlag and duration",
    "prioritize randomized interventions, natural/quasi-experiments and longitudinal designs",
    "cross-sectional evidence stays within an association ceiling",
    "mechanisms are separate from demonstrated clinical outcomes",
    "search contrary/null evidence",
    "expose unsupported conclusions",
]

# Candidate discovery set used to exercise the real search path (offline:
# discovery records DISCOVERED access; no content is fetched live).
DISCOVERED = [
    {"url": "https://pubmed.ncbi.nlm.nih.gov/?term=late+sleep+timing+health"},
    {"url": "https://pubmed.ncbi.nlm.nih.gov/?term=delayed+circadian+phase+mortality"},
    {"url": "https://pubmed.ncbi.nlm.nih.gov/?term=evening+chronotype+metabolic"},
]

NOW = "2026-08-04T08:30:00Z"


def run_pilot(trace_dir: Path) -> dict:
    """Drive the frozen question through the real interfaces; return a report.

    Always terminates as BLOCKED_WITH_EVIDENCE in this offline sandbox, with the
    exact evidence recorded. Writes the full machine trace under ``trace_dir``.
    """
    trace_dir = Path(trace_dir)
    trace_dir.mkdir(parents=True, exist_ok=True)

    ctrl = E.EpisodeController(adapters=A.build_default_adapters())

    # ---- queue layer (Round 2) -------------------------------------------
    cand = R.make_topic_candidate(
        candidate_id="cand-sleep-timing",
        proposed_question=FROZEN_QUESTION,
        proposed_strategy_pack=PACK,
        materiality=0.9, expected_information_gain=0.8, tractability=0.5,
    )
    campaign = R.make_campaign(
        campaign_id="camp-round6-sleep",
        stop_conditions={"owner_stop": False, "queue_empty_stops": False,
                         "safety_blocker_stops": True},
    )
    q = Q.SerialQueue(campaign=campaign, items=[], owner="workbuddy")
    item = q.add_candidate(cand, queue_item_id="cand-sleep-timing")
    selected = q.select_next(now_iso=NOW)
    assert selected is not None and selected["queue_item_id"] == "cand-sleep-timing", \
        "queue must select the frozen question"

    # ---- episode layer (Round 3 + 4) -------------------------------------
    ep = K.new_episode("ep-round6-sleep", "v1", "deep_research", PACK)
    brief = R.make_brief(
        question=FROZEN_QUESTION,
        question_version="v1",
        strategy_pack=PACK,
        frozen=True,
    )
    ctrl.freeze_scope(ep, brief)  # INTAKE -> QUESTION_FROZEN
    # A primary-source obligation is opened; it cannot be satisfied offline.
    ctrl.plan_obligations(ep, [R.make_evidence_obligation(
        obligation_id="obl-1", claim_id="unasserted", obligation_class="PRIMARY_SOURCE",
        severity="HIGH", status="OPEN")])  # -> EVIDENCE_GATHERING

    # Real search path (offline: DISCOVERED access only, no fetch).
    ctrl.do_search(ep, "web",
                   "late sleep timing delayed circadian phase health 7 8 hours",
                   discovered=DISCOVERED)
    # Real open path on a discovered source (offline: NONE access + error).
    ctrl.do_open(ep, "web", "web:https://pubmed.ncbi.nlm.nih.gov/?term=late+sleep+timing+health",
                 "https://pubmed.ncbi.nlm.nih.gov/?term=late+sleep+timing+health",
                 content=None)

    # In-episode evaluation (transparent, Round 4).
    in_episode_decision = ctrl.evaluate(ep)

    # ---- pilot-level blocker (exact evidence) ----------------------------
    none_sources = [s for s in ep.get("source_identities", [])
                     if s.get("access_level") == "NONE"]
    evidence = [
        "deep-research capability adapters are OFFLINE-SAFE by design (Rounds 1-3): "
        "WebAdapter/PdfAdapter open() with no supplied content returns NONE access "
        "and an offline error; they never reach the public web.",
        "no live public-web tool is wired into the runtime in this sandbox; the only "
        "search path records DISCOVERED access and performs no fetch.",
        f"{len(none_sources)} load-bearing source(s) resolved to NONE access on open "
        "(no content available offline): "
        + (", ".join(s["source_id"] for s in none_sources) or "n/a"),
        "the opened primary-source obligation (obl-1, HIGH) remains OPEN because no "
        "live evidence could be gathered; it cannot be satisfied offline.",
        "TASK.md Round 6 precondition 'required tool access is available' is NOT met, "
        "so the live evidence-gathering pilot must not start (no unattended public-web work).",
    ]

    # Record the blocker on the episode and finalize to BLOCKED (valid from ANALYSIS).
    ep.setdefault("blockers", []).append({
        "blocker_id": "blk-round6-offline-no-live-tool",
        "kind": "BLOCKED_WITH_EVIDENCE",
        "reason": "live public-web evidence tooling unavailable in offline sandbox",
        "evidence": evidence,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    finalized = ctrl.finalize(ep, "BLOCKED_WITH_EVIDENCE")
    assert finalized, "episode must finalize to BLOCKED"

    # ---- machine trace ---------------------------------------------------
    ep_path = trace_dir / "episode.json"
    q_path = trace_dir / "queue.json"
    report_path = trace_dir / "PILOT-REPORT.json"

    K.save(ep, ep_path)
    q_state = {
        "campaign": q.campaign,
        "items": q.items,
        "stats": q.stats,
        "owner": q.owner,
    }
    q_path.write_text(json.dumps(q_state, indent=2), encoding="utf-8")

    report = {
        "round": 6,
        "frozen_question": FROZEN_QUESTION,
        "boundaries": BOUNDARIES,
        "strategy_pack": PACK,
        "queue_item_id": item["queue_item_id"],
        "episode_id": ep["episode_id"],
        "in_episode_decision": in_episode_decision["decision"],
        "pilot_outcome": "BLOCKED_WITH_EVIDENCE",
        "episode_terminal_state": ep["state"],
        "evidence": evidence,
        "machine_trace_refs": {
            "episode": str(ep_path),
            "queue": str(q_path),
        },
        "resume_commands_for_round7_codex": [
            "wire a live public-web adapter (or authorized tool) into "
            "deep_research.adapters.build_default_adapters()",
            "re-run: python3 tools/deep_research/run_round6_pilot.py  # with live tool",
            "on live access, the opened obligation obl-1 can be SATISFIED and the "
            "SufficiencyEvaluator re-run; pilot may then end as sufficient / "
            "insufficient / budget-pause instead of blocker",
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # ---- self-check (deterministic, no crash) ---------------------------
    assert ep_path.exists() and q_path.exists() and report_path.exists(), \
        "machine trace must be fully written"
    assert report["pilot_outcome"] == "BLOCKED_WITH_EVIDENCE"
    assert ep["state"] == "BLOCKED"
    return report


def main() -> None:
    trace_dir = (REPO_ROOT / "data" / "operations" / "iterations" / "115"
                 / "candidate" / "workbuddy-takeover" / "round6-trace")
    report = run_pilot(trace_dir)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
