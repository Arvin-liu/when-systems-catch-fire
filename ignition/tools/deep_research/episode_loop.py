"""Deep Research Capability — bounded inner research episode loop (Round 3 + 4).

Implements one episode cycle:
  freeze scope -> plan obligations -> search -> open/read -> extract ->
  analyze/recompute -> challenge -> revise -> evaluate sufficiency -> report/checkpoint

It is built directly on the inherited Research OS kernel
(``research_os.kernel``): ``new_episode`` / ``transition`` / ``observe`` /
``record_action_selection`` / ``is_terminal`` / ``save`` / ``load``. The kernel
is the single authority for state transitions and for the executor
no-self-approval contract, so this module can never mark an episode complete or
raise a claim ceiling on its own — those are gate/owner decisions.

The sufficiency evaluator (Round 4) is transparent: it enforces the hard gates
and computes a multidimensional sufficiency vector, then decides. The loop calls
``evaluate`` and only finalizes to a terminal state when the evaluator returns a
stop decision. No scalar score alone authorizes completion.

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
# Transparent sufficiency evaluator (Round 4): hard gates + sufficiency vector
# ---------------------------------------------------------------------------
# Material claims are those asserted at/above these ceilings — they MUST be
# evidenced (observations, independent families, recomputation, contrary search).
_MATERIAL_CEILINGS = ("BOUNDED_STRONG", "QUALIFIED")

# Severity -> ordinal (for the unresolved-gap-severity dimension).
_SEV_SCORE = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}

# Strategy-pack-specific thresholds for each sufficiency-vector dimension.
# A dimension is "met" only when its value >= its threshold. Every dimension
# must be met AND every hard gate must pass before STOP_SUFFICIENT_CANDIDATE is
# permitted. NO scalar score alone authorizes completion. Unknown packs fall
# back to the default thresholds (registry-driven).
_SUFFICIENCY_THRESHOLDS = {
    DEFAULT_STRATEGY_PACK: {
        "obligation_coverage": 1.0,
        "claim_support_faithfulness": 0.8,
        "independent_family_coverage": 1.0,   # requires >=2 families when material claims exist
        "contrary_null_coverage": 1.0,        # required when material claims exist
        "method_data_recomputation_coverage": 1.0,
        "claim_ceiling_stability": 1.0,
        "unresolved_gap_severity": 0.0,       # no open HIGH/CRITICAL obligation
        "marginal_information_gain": 0.0,
    },
}


def _pack_thresholds(pack: str) -> dict:
    return _SUFFICIENCY_THRESHOLDS.get(_safe_pack(pack)) or \
        _SUFFICIENCY_THRESHOLDS[DEFAULT_STRATEGY_PACK]


class SufficiencyEvaluator:
    """Transparent, inspectable sufficiency evaluator.

    Produces a decision record containing the hard-gate results, the full
    sufficiency vector, and a human-readable reason. Replaces the Round 3
    obligation-coverage placeholder and satisfies TASK.md Round 4.
    """

    def __init__(self, thresholds: Optional[dict] = None):
        self.thresholds = thresholds

    # -- episode introspection helpers ------------------------------------
    @staticmethod
    def _material_claims(ep: dict) -> list[dict]:
        return [c for c in ep.get("candidate_claims", [])
                if c.get("claim_ceiling") in _MATERIAL_CEILINGS]

    @staticmethod
    def _families(ep: dict) -> set:
        fams = set()
        for s in ep.get("source_identities", []):
            sid = s.get("source_id", "") or ""
            fams.add(sid.split(":", 1)[0] or "unknown")
        return fams

    @staticmethod
    def _gate(gid: str, passed: bool, detail: str) -> dict:
        return {"gate": gid, "passed": bool(passed), "detail": detail}

    # -- hard gates -------------------------------------------------------
    def hard_gates(self, ep: dict) -> list[dict]:
        obs = ep.get("observations", [])
        obls = ep.get("evidence_obligations", [])
        mat = self._material_claims(ep)

        # 1. scope frozen (a frozen scope always carries a brief)
        gates = [self._gate("scope_frozen",
                            bool(ep.get("brief")),
                            "episode scope must be frozen (brief present)")]
        # 2. unsupported material claim (material claim with no gathered observation)
        gates.append(self._gate("unsupported_material_claim",
                                not (bool(mat) and len(obs) == 0),
                                "material claims require gathered observations"))
        # 3. open burden-bearing severe obligation
        open_severe = [o for o in obls
                       if o.get("status") != "SATISFIED" and o.get("severity") in ("HIGH", "CRITICAL")]
        gates.append(self._gate("open_burden_bearing_severe_obligation",
                                not open_severe, "no open HIGH/CRITICAL obligation"))
        # 4. unresolved load-bearing source identity / access scope
        bad_src = [s for s in ep.get("source_identities", [])
                   if s.get("access_level") in (None, "NONE") or not s.get("inspected_scope")]
        gates.append(self._gate("unresolved_source_identity", not bad_src,
                                "all source identities resolved with inspected scope"))
        # 5. citation attribution mismatch (abstract-only source behind a material claim)
        abstract_only = [s for s in ep.get("source_identities", [])
                         if s.get("access_level") == "ABSTRACT_ONLY"]
        gates.append(self._gate("citation_attribution_mismatch",
                                not (bool(abstract_only) and bool(mat)),
                                "abstract-only sources must not back material claims"))
        # 6. false independence across one source family
        gates.append(self._gate("false_independence_same_family",
                                not (bool(mat) and len(self._families(ep)) <= 1),
                                "material claims need >=2 independent source families"))
        # 7. high-stakes evidence-route failure (failed tool/calc behind a material claim)
        errored = any(o.get("errors") for o in obs)
        gates.append(self._gate("high_stakes_evidence_route_failure",
                                not (bool(mat) and errored),
                                "no failed required computation/tool behind material claims"))
        # 8. unresolved prompt injection / provenance contamination
        injection = any((p.get("injection_detected")
                         for o in obs for p in (o.get("provenance") or [])))
        gates.append(self._gate("unresolved_prompt_injection", not injection,
                                "no unresolved prompt-injection / provenance contamination"))
        # 9. blocked evidence route (load-bearing source with NONE access)
        none_src = [s for s in ep.get("source_identities", [])
                    if s.get("access_level") == "NONE"]
        gates.append(self._gate("blocked_evidence_route", not none_src,
                                "no load-bearing source with NONE access"))
        # 10. missing required calculation/method inspection without ceiling reduction
        requires_calc = bool(ep.get("requires_recomputation"))
        has_calc = any(o.get("calculation_result") is not None for o in obs)
        gates.append(self._gate("missing_required_calc_without_ceiling_reduction",
                                not (requires_calc and not has_calc),
                                "quantitative claim needs recomputation or ceiling reduction"))
        return gates

    # -- sufficiency vector ------------------------------------------------
    def sufficiency_vector(self, ep: dict, thresh: dict) -> list[dict]:
        obs = ep.get("observations", [])
        obls = ep.get("evidence_obligations", [])
        mat = self._material_claims(ep)

        cov = (sum(1 for o in obls if o.get("status") == "SATISFIED") / len(obls)) if obls else 1.0
        supported = (sum(1 for _ in mat if len(obs) > 0) / len(mat)) if mat else 1.0
        fams = self._families(ep)
        indep = (1.0 if len(fams) >= 2 else 0.0) if mat else 1.0
        contrary = (1.0 if ep.get("contrary_evidence_sought") else 0.0) if mat else 1.0
        calcs = [o for o in obs if o.get("calculation_result") is not None]
        recov = (sum(1 for c in calcs if not c["calculation_result"].get("errors")) / len(calcs)) \
            if calcs else 1.0
        stable = (1.0 if not any(c.get("claim_ceiling") == "NOT_ASSERTED" for c in mat) else 0.0) \
            if mat else 1.0
        gap = max([_SEV_SCORE.get(o.get("severity", "LOW"), 0) for o in obls
                   if o.get("status") != "SATISFIED"], default=0)
        gap_dim = 1.0 - (gap / 3.0)
        mig = 1.0 if obs else 0.0

        dims = [
            ("obligation_coverage", cov),
            ("claim_support_faithfulness", supported),
            ("independent_family_coverage", indep),
            ("contrary_null_coverage", contrary),
            ("method_data_recomputation_coverage", recov),
            ("claim_ceiling_stability", stable),
            ("unresolved_gap_severity", gap_dim),
            ("marginal_information_gain", mig),
        ]
        vec = []
        for name, val in dims:
            t = thresh.get(name, 1.0)
            vec.append({"dimension": name, "value": round(float(val), 4),
                        "threshold": t, "met": bool(val >= t - 1e-9)})
        return vec

    # -- decision ---------------------------------------------------------
    def evaluate(self, ep: dict) -> dict:
        pack = _safe_pack(ep.get("strategy_pack") or DEFAULT_STRATEGY_PACK)
        thresh = self.thresholds or _pack_thresholds(pack)
        gates = self.hard_gates(ep)
        failed = [g for g in gates if not g["passed"]]
        vector = self.sufficiency_vector(ep, thresh)

        if failed:
            ids = {g["gate"] for g in failed}
            if ids & {"unresolved_prompt_injection", "high_stakes_evidence_route_failure"}:
                decision = "ESCALATE_GPT_OWNER"
            elif "blocked_evidence_route" in ids:
                decision = "BLOCKED_WITH_EVIDENCE"
            else:
                decision = "CONTINUE_RESEARCH"
        else:
            if all(v["met"] for v in vector):
                decision = "STOP_SUFFICIENT_CANDIDATE"
            elif next((v for v in vector if v["dimension"] == "marginal_information_gain"),
                      {"value": 1.0})["value"] == 0.0:
                decision = "STOP_INSUFFICIENT_EVIDENCE"
            else:
                decision = "CONTINUE_RESEARCH"

        return {
            "decision": decision,
            "registry_pack": pack,
            "hard_gates": gates,
            "sufficiency_vector": vector,
            "failed_gates": [g["gate"] for g in failed],
            "reason": self._reason(decision, failed, vector),
        }

    @staticmethod
    def _reason(decision: str, failed: list[dict], vector: list[dict]) -> str:
        if failed:
            return "hard gate(s) failed: " + ", ".join(g["gate"] for g in failed)
        unmet = [v["dimension"] for v in vector if not v["met"]]
        if decision == "STOP_SUFFICIENT_CANDIDATE":
            return "all hard gates passed; sufficiency vector met"
        return f"insufficient (unmet: {', '.join(unmet)})" if unmet else decision


def evaluate_sufficiency(ep: dict, thresholds: Optional[dict] = None) -> dict:
    """Module-level entry point used as the controller's default evaluator."""
    return SufficiencyEvaluator(thresholds=thresholds).evaluate(ep)


# Backward-compatible alias (Round 3 code referenced the placeholder name).
def _placeholder_sufficiency(ep: dict) -> dict:
    return evaluate_sufficiency(ep)


# ---------------------------------------------------------------------------
# Episode controller
# ---------------------------------------------------------------------------
class EpisodeController:
    def __init__(self, adapters: Optional[dict] = None,
                 sufficiency_evaluator: Callable[[dict], dict] = None,
                 checkpoint_dir: Optional[str] = None):
        self.adapters = adapters or A.build_default_adapters()
        self.sufficiency = sufficiency_evaluator or evaluate_sufficiency
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
        decision = self.sufficiency(ep)
        ep.setdefault("sufficiency_decision", decision)
        return decision

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
