"""Deep Research Capability — bounded inner research episode loop (Round 3).

Implements one episode cycle:
  freeze scope -> plan obligations -> search -> open/read -> extract ->
  analyze/recompute -> challenge -> revise -> evaluate sufficiency -> report/checkpoint

It is built directly on the inherited Research OS kernel
(``research_os.kernel``): ``new_episode`` / ``transition`` / ``observe`` /
``record_action_selection`` / ``is_terminal`` / ``save`` / ``load``. The kernel
is the single authority for state transitions and for the executor
no-self-approval contract, so this module can never mark an episode complete or
raise a claim ceiling on its own — those are gate/owner decisions.

The sufficiency evaluator is PLUGGABLE: Round 3 supplies a minimal placeholder
(obligation-coverage only); Round 4 replaces it with the hard-gate + vector
algorithm. The loop calls ``evaluate`` and only finalizes to a terminal state
when the evaluator returns a stop decision.

Security rules enforced here (per TASK.md Round 3):
* every adapter return is an executor observation under contract (no
  self_approved / mark_episode_complete / claim_ceiling);
* external content is treated as data; prompt-injection is flagged by the
  adapters and quarantined, never executed as instruction;
* a material gap after synthesis returns the episode to EVIDENCE_GATHERING.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "tools"))

from research_os import kernel as K
from research_os import registries as REG
from deep_research import adapters as A
from deep_research import records as R

# A kernel-valid default strategy pack (used when a candidate supplies none or
# supplies a non-kernel pack string). Real packs are the data/research-os/
# strategy-packs/<CODE>.json stems.
DEFAULT_STRATEGY_PACK = "SYSTEMATIC_EVIDENCE_SYNTHESIS"


def _safe_pack(code: str) -> str:
    """Return ``code`` if it is a kernel-valid strategy pack, else the default."""
    try:
        REG.assert_strategy_pack(code)
        return code
    except Exception:
        return DEFAULT_STRATEGY_PACK

# Terminal decisions the loop may finalize to (never self-approved; owner/gate
# adjudicated upstream). CONTINUE/PAUSE/ESCALATE keep the episode non-terminal.
_FINALIZE_MAP = {
    "STOP_SUFFICIENT_CANDIDATE": "CANDIDATE_COMPLETE",
    "STOP_INSUFFICIENT_EVIDENCE": "INSUFFICIENT_EVIDENCE_COMPLETE",
    "BLOCKED_WITH_EVIDENCE": "BLOCKED",
    "ESCALATE_GPT_OWNER": "ESCALATED_TO_GPT_OWNER",
}


# ---------------------------------------------------------------------------
# Obligation / claim operations (missing from PR #190)
# ---------------------------------------------------------------------------
def add_obligation(ep: dict, claim_id: str, obligation_class: str,
                   severity: str = "MEDIUM", status: str = "OPEN") -> dict:
    """Add an evidence obligation tied to a claim (kernel vocabulary enforced)."""
    obl = R.make_evidence_obligation(
        obligation_id=f"obl-{len(ep.get('evidence_obligations', [])) + 1:03d}",
        claim_id=claim_id, obligation_class=obligation_class,
        severity=severity, status=status,
    )
    ep.setdefault("evidence_obligations", []).append(obl)
    K._append_event(ep, "obligation_added", {"obligation_id": obl["obligation_id"]},
                    actor="kernel")
    return obl


def set_obligation_status(ep: dict, obligation_id: str, status: str) -> bool:
    for obl in ep.get("evidence_obligations", []):
        if obl.get("obligation_id") == obligation_id:
            obl["status"] = status
            K._append_event(ep, "obligation_status",
                            {"obligation_id": obligation_id, "status": status},
                            actor="kernel")
            return True
    return False


def add_claim(ep: dict, claim_text: str, claim_ceiling: str,
              claim_id: Optional[str] = None) -> dict:
    """Record a candidate claim. ``claim_ceiling`` is OWNER_ADJUDICATED — the loop
    only ever stores what the evaluator/owner sets; it never raises it."""
    cid = claim_id or f"claim-{len(ep.get('candidate_claims', [])) + 1:03d}"
    claim = R.make_claim_evidence_record(
        claim_id=cid, claim_text=claim_text, claim_ceiling=claim_ceiling,
        status="CANDIDATE",
    )
    ep.setdefault("candidate_claims", []).append(claim)
    K._append_event(ep, "claim_added", {"claim_id": cid, "claim_ceiling": claim_ceiling},
                    actor="kernel")
    return claim


# ---------------------------------------------------------------------------
# Minimal sufficiency evaluator (Round 3 placeholder; Round 4 replaces)
# ---------------------------------------------------------------------------
def _placeholder_sufficiency(ep: dict) -> dict:
    obls = ep.get("evidence_obligations", [])
    open_severe = [o for o in obls if o.get("status") != "SATISFIED"
                   and o.get("severity") in ("HIGH", "CRITICAL")]
    if open_severe:
        return {"decision": "CONTINUE_RESEARCH", "hard_gates_passed": False,
                "failed_hard_gates": [o["obligation_id"] for o in open_severe]}
    return {"decision": "STOP_SUFFICIENT_CANDIDATE", "hard_gates_passed": True,
            "failed_hard_gates": []}


# ---------------------------------------------------------------------------
# Episode controller
# ---------------------------------------------------------------------------
class EpisodeController:
    def __init__(self, adapters: Optional[dict] = None,
                 sufficiency_evaluator: Callable[[dict], dict] = None,
                 checkpoint_dir: Optional[str] = None):
        self.adapters = adapters or A.build_default_adapters()
        self.sufficiency = sufficiency_evaluator or _placeholder_sufficiency
        self.checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else None

    # -- scope / plan -------------------------------------------------------
    def freeze_scope(self, ep: dict, brief: dict) -> dict:
        K.transition(ep, "QUESTION_FROZEN")
        ep["brief"] = brief
        return ep

    def plan_obligations(self, ep: dict, obligations: list[dict]) -> dict:
        for o in obligations:
            ep.setdefault("evidence_obligations", []).append(o)
        K.transition(ep, "EVIDENCE_GATHERING")
        return ep

    # -- actions (each returns an executor observation under contract) -------
    def do_search(self, ep: dict, adapter_name: str, query: str,
                  discovered: list[dict] | None = None) -> dict:
        obs = self.adapters[adapter_name].search(query, discovered)
        K.observe(ep, obs)
        K.record_action_selection(ep, {"selected_action": "SEARCH_PRIMARY_SOURCE",
                                       "query": query})
        return obs

    def do_open(self, ep: dict, adapter_name: str, source_id: str, locator: str,
                content: str | None = None) -> dict:
        obs = self.adapters[adapter_name].open(source_id, locator, content=content)
        K.observe(ep, obs)
        K.record_action_selection(ep, {"selected_action": "FETCH_FULL_TEXT",
                                       "source_id": source_id})
        # record exact source identity + inspected scope (fail-closed)
        ep.setdefault("source_identities", []).append({
            "source_id": source_id,
            "access_level": obs["access_level"],
            "inspected_scope": (obs.get("provenance") or [{}])[-1].get("inspected_scope"),
        })
        return obs

    def do_calc(self, ep: dict, code: str, inputs: dict | None = None) -> dict:
        obs = self.adapters["calc"].observation(code, inputs)
        K.observe(ep, obs)
        K.record_action_selection(ep, {"selected_action": "RECOMPUTE_RESULT", "code": code})
        return obs

    # -- analysis / challenge / revise --------------------------------------
    def challenge(self, ep: dict) -> dict:
        K.transition(ep, "CHALLENGE")
        return ep

    def revise(self, ep: dict) -> dict:
        K.transition(ep, "REVISION")
        return ep

    # -- sufficiency + finalize ---------------------------------------------
    def evaluate(self, ep: dict) -> dict:
        if ep["state"] not in ("ANALYSIS",):
            K.transition(ep, "ANALYSIS")
        return self.sufficiency(ep)

    def finalize(self, ep: dict, decision: str) -> bool:
        """Finalize to a terminal state only when the evaluator decides so.
        Returns True if finalized; False if the episode remains non-terminal
        (CONTINUE / PAUSE / ESCALATE handled by caller)."""
        target = _FINALIZE_MAP.get(decision)
        if target is None:
            return False
        K.transition(ep, target)
        return True

    # -- checkpoint ---------------------------------------------------------
    def checkpoint(self, ep: dict) -> Optional[str]:
        if not self.checkpoint_dir:
            return None
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        path = self.checkpoint_dir / f"{ep['episode_id']}.json"
        K.save(ep, path)
        return str(path)

    # -- bounded run over a scripted plan -----------------------------------
    def run_plan(self, ep: dict, plan: list[dict], max_steps: int = 50) -> dict:
        """Execute a scripted plan. Each action: {type: search|open|calc, ...}.
        Flow: ensure the episode is gathering, dispatch available actions, then
        run the analysis cycle (ANALYSIS -> CHALLENGE -> ANALYSIS[evaluate] ->
        REVISION). If the evaluator finalizes, stop. If it continues and more
        actions remain, return to EVIDENCE_GATHERING and gather them; if no
        actions remain, stop honestly in BLOCKED (never spin)."""
        steps = 0
        idx = 0
        # A freshly frozen episode (QUESTION_FROZEN) enters gathering with no
        # explicit obligations (e.g. queue-driven episodes run from a brief).
        if ep["state"] == "QUESTION_FROZEN":
            K.transition(ep, "EVIDENCE_GATHERING")
        while not K.is_terminal(ep) and steps < max_steps:
            steps += 1
            if ep["state"] == "EVIDENCE_GATHERING" and idx < len(plan):
                action = plan[idx]
                idx += 1
                self._dispatch(ep, action)
                self.checkpoint(ep)
                continue
            # No (more) actions to run: move into analysis.
            if ep["state"] == "EVIDENCE_GATHERING":
                K.transition(ep, "ANALYSIS")  # EVIDENCE_GATHERING -> ANALYSIS
            # Analysis cycle: ANALYSIS -> CHALLENGE -> ANALYSIS(evaluate) -> REVISION
            if ep["state"] == "ANALYSIS":
                self.challenge(ep)  # ANALYSIS -> CHALLENGE
            decision = self.evaluate(ep)  # CHALLENGE -> ANALYSIS
            self.revise(ep)  # ANALYSIS -> REVISION
            if self.finalize(ep, decision["decision"]):
                self.checkpoint(ep)
                break
            # Not finalized. Decide: gather more, or stop honestly.
            if idx < len(plan):
                # Material gap remains; return to gathering for the next action.
                K.transition(ep, "ANALYSIS")  # REVISION -> ANALYSIS
                K.transition(ep, "EVIDENCE_GATHERING")  # ANALYSIS -> EVIDENCE_GATHERING
            else:
                # Insufficient and no further actions: honest BLOCKED from ANALYSIS.
                K.transition(ep, "ANALYSIS")  # REVISION -> ANALYSIS
                K.transition(ep, "BLOCKED")  # ANALYSIS -> BLOCKED
                self.checkpoint(ep)
                break
        return ep

    def _dispatch(self, ep: dict, action: dict) -> dict:
        t = action["type"]
        if t == "search":
            return self.do_search(ep, action["adapter"], action["query"],
                                  action.get("discovered"))
        if t == "open":
            return self.do_open(ep, action["adapter"], action["source_id"],
                                action["locator"], action.get("content"))
        if t == "calc":
            return self.do_calc(ep, action["code"], action.get("inputs"))
        raise ValueError(f"unknown action type: {t}")


# ---------------------------------------------------------------------------
# Pause / resume / replay (queue-facing ops)
# ---------------------------------------------------------------------------
def pause_episode(ep: dict) -> dict:
    K.transition(ep, "PAUSED_RESUMABLE")
    return ep


def resume_episode(ep: dict, to_state: str = "EVIDENCE_GATHERING") -> dict:
    K.transition(ep, to_state)
    return ep


def replay_events(ep: dict) -> list[dict]:
    """Return the immutable event log for transparent replay."""
    return ep.get("event_log", [])
