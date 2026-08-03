"""Deterministic Epistemic Gap Diagnosis Engine (Checkpoint B).

Diagnoses a structured episode state and emits gap findings. The engine inspects
structured fields and the obligation graph; it does NOT rely on regex classification
of free prose as its primary capability. Every finding cites a gap code from
data/research-os/gap-codes.json, supplies evidence, severity, the affected
claim/obligation, and candidate correcting actions.

24 gap codes are reachable:
- 14 via obligation-class -> gap-code mapping (data/research-os/obligation-classes.json)
- the remainder via structured episode fields (reading integrity, timestamps,
  source chain, calculations, negative-evidence search, information delta,
  claim ceiling, human judgment, adversarial review, premature/early closeout,
  and explicit scope flags).
"""

from __future__ import annotations

from typing import Any

from . import kernel
from . import obligation_graph as og
from . import registries as R

ENGINE_VERSION = "0.1"


def diagnose(ep: dict) -> dict:
    findings: list[dict] = []
    seen: set[str] = set()

    def add(code: str, severity: str, evidence: str, affected: str, actions: list[str]) -> None:
        R.assert_gap(code)
        if code in seen:
            return
        seen.add(code)
        findings.append(
            {
                "gap_code": code,
                "severity": severity,
                "evidence": evidence,
                "affected": affected,
                "correcting_actions": actions,
                "detection_method": "structured_inspection",
            }
        )

    gap_meta = R.GAP_BY_CODE

    # 1. Obligation-driven gaps (class -> gap code).
    for o in ep.get("evidence_obligations", []):
        if o["status"] in ("OPEN", "PARTIAL", "BLOCKED_WITH_EVIDENCE"):
            g = R.CLASS_TO_GAP.get(o["class"])
            if g:
                add(
                    g,
                    gap_meta[g]["severity"],
                    f"obligation {o['obligation_id']} (class {o['class']}) status={o['status']}",
                    f"obligation:{o['obligation_id']}",
                    list(gap_meta[g].get("correcting_actions", [])),
                )

    # 2. Claim ceiling vs obligations (waiver can never raise a ceiling).
    for c in ep.get("candidate_claims", []):
        cid = c["claim_id"]
        if og.waiver_raises_ceiling(ep, cid):
            add(
                "CLAIM_EXCEEDS_EVIDENCE",
                "CRITICAL",
                f"claim {cid} ceiling={c['claim_ceiling']} supported by WAIVED obligation while other obligations unsatisfied",
                f"claim:{cid}",
                ["DOWNGRADE_CLAIM", "ESCALATE_TO_GPT_OWNER", "RUN_ADVERSARIAL_REVIEW"],
            )
        elif c["claim_ceiling"] in ("QUALIFIED", "BOUNDED_STRONG"):
            unsat = og.unsatisfied_for_claim(ep, cid)
            if unsat:
                add(
                    "CLAIM_EXCEEDS_EVIDENCE",
                    "CRITICAL",
                    f"claim {cid} ceiling={c['claim_ceiling']} but {len(unsat)} obligation(s) unsatisfied",
                    f"claim:{cid}",
                    ["DOWNGRADE_CLAIM", "RUN_ADVERSARIAL_REVIEW"],
                )

    # 3. Numeric recomputation (covers NUMERIC_CLAIM_NOT_RECOMPUTED).
    req = ep.get("calculations_required", []) or []
    done = ep.get("calculations_completed", []) or []
    missing = [c for c in req if c not in done]
    if missing:
        add(
            "NUMERIC_CLAIM_NOT_RECOMPUTED",
            gap_meta["NUMERIC_CLAIM_NOT_RECOMPUTED"]["severity"],
            f"calculations required but not completed: {missing}",
            "episode",
            ["RECOMPUTE_RESULT", "REPRODUCE_ANALYSIS", "LOCATE_RAW_DATA"],
        )

    # 4. Negative / null / contradictory evidence search.
    nes = ep.get("negative_evidence_search_state", {}) or {}
    if not nes.get("searched", False):
        add(
            "NEGATIVE_EVIDENCE_NOT_SEARCHED",
            gap_meta["NEGATIVE_EVIDENCE_NOT_SEARCHED"]["severity"],
            "negative/null/contradictory evidence search not performed",
            "episode",
            ["SEEK_NULL_OR_CONTRADICTORY_RESULT", "SEEK_REPLICATION"],
        )

    # 5. Reading time vs scope integrity (R1 failure mode).
    ri = ep.get("reading_integrity", {}) or {}
    dw = ri.get("declared_reading_window_hours")
    mw = ri.get("minimum_required_reading_hours")
    if dw is not None and mw is not None and dw < mw:
        add(
            "READING_TIME_SCOPE_INCONSISTENT",
            gap_meta["READING_TIME_SCOPE_INCONSISTENT"]["severity"],
            f"declared reading window {dw}h < minimum required {mw}h for claimed scope",
            "episode",
            ["ESCALATE_TO_GPT_OWNER", "PAUSE_AND_CHECKPOINT"],
        )

    # 6. Identical/batch timestamps cannot prove reading (R1 failure mode).
    if ep.get("source_timestamps_identical") or ep.get("batch_timestamps_without_reading_evidence"):
        add(
            "TIMESTAMP_BATCH_NOT_PROOF_OF_READING",
            gap_meta["TIMESTAMP_BATCH_NOT_PROOF_OF_READING"]["severity"],
            "identical/batch timestamps cannot demonstrate actual reading of sources",
            "episode",
            ["CHECK_SOURCE_DEPENDENCE", "ESCALATE_TO_GPT_OWNER"],
        )

    # 7. Source-chain dependence.
    if ep.get("source_chain_single"):
        add(
            "SOURCE_DEPENDENCE_HIGH",
            gap_meta["SOURCE_DEPENDENCE_HIGH"]["severity"],
            "multiple sources derive from a single primary chain",
            "episode",
            ["CHECK_SOURCE_DEPENDENCE", "SEARCH_PRIMARY_SOURCE"],
        )

    # 8. Explicit scope flags (deterministic, set by fixtures / R1 packets).
    if ep.get("access_scope_unverified"):
        add("ACCESS_SCOPE_UNVERIFIED", gap_meta["ACCESS_SCOPE_UNVERIFIED"]["severity"],
            "claimed access scope not independently verified", "episode", ["FREEZE_OR_NARROW_QUESTION"])
    if ep.get("methods_or_supplement_missing"):
        add("METHODS_OR_SUPPLEMENT_MISSING", gap_meta["METHODS_OR_SUPPLEMENT_MISSING"]["severity"],
            "methods or supplementary material not read", "episode", ["READ_METHODS", "READ_SUPPLEMENT"])
    if ep.get("object_or_denominator_mismatch"):
        add("OBJECT_OR_DENOMINATOR_MISMATCH", gap_meta["OBJECT_OR_DENOMINATOR_MISMATCH"]["severity"],
            "compared objects/denominators not equivalent", "episode",
            ["BUILD_DEFINITION_CROSSWALK", "COMPARE_OUTCOMES_OR_DENOMINATORS", "RECOMPUTE_RESULT"])
    if ep.get("temporal_scope_mismatch"):
        add("TEMPORAL_SCOPE_MISMATCH", gap_meta["TEMPORAL_SCOPE_MISMATCH"]["severity"],
            "temporal scope differs from claim", "episode", ["FREEZE_OR_NARROW_QUESTION"])

    # 9. Premature completion.
    if ep.get("state") == "CANDIDATE_COMPLETE" and og.open_obligations(ep):
        add(
            "PREMATURE_COMPLETION",
            "CRITICAL",
            f"CANDIDATE_COMPLETE declared with {len(og.open_obligations(ep))} open obligations",
            "episode",
            ["REOPENED", "ESCALATE_TO_GPT_OWNER"],
        )

    # 10. Unauthorized early closeout.
    if ep.get("campaign_closeout_before_deadline"):
        add(
            "UNAUTHORIZED_EARLY_CLOSEOUT",
            "CRITICAL",
            "campaign closeout before authorized deadline",
            "episode",
            ["REOPENED", "ESCALATE_TO_GPT_OWNER"],
        )

    # 11. Q13 IterationDelta information-gain / attractor signals.
    delta = ep.get("information_delta")
    if isinstance(delta, dict):
        ds = delta.get("delta_status")
        if ds == "NO_INFORMATION_GAIN":
            add("NO_INFORMATION_GAIN", gap_meta["NO_INFORMATION_GAIN"]["severity"],
                "recent iterations produced no information delta", "episode",
                ["PAUSE_AND_CHECKPOINT", "BRANCH_QUESTION", "STOP_WITH_INSUFFICIENT_EVIDENCE"])
        elif ds == "ATTRACTOR_LOOP":
            add("ATTRACTOR_LOOP_RISK", gap_meta["ATTRACTOR_LOOP_RISK"]["severity"],
                "episode circling a fixed set of claims without progress", "episode",
                ["PAUSE_AND_CHECKPOINT", "ESCALATE_TO_GPT_OWNER"])

    # 12. Human judgment (value / high-stakes / external review).
    if (ep.get("high_stakes") or ep.get("requires_external_review")) and ep.get("state") != "ESCALATED_TO_GPT_OWNER":
        add("HUMAN_JUDGMENT_REQUIRED", gap_meta["HUMAN_JUDGMENT_REQUIRED"]["severity"],
            "high-stakes or external review required before claim", "episode", ["ESCALATE_TO_GPT_OWNER"])

    # 13. Adversarial review missing for assertive claims.
    has_adv = any(
        (o.get("type") == "adversarial_review") for o in ep.get("observations", []) or []
    )
    if not has_adv:
        for c in ep.get("candidate_claims", []):
            if c["claim_ceiling"] in ("QUALIFIED", "BOUNDED_STRONG"):
                add("ADVERSARIAL_REVIEW_MISSING", gap_meta["ADVERSARIAL_REVIEW_MISSING"]["severity"],
                    f"claim {c['claim_id']} at {c['claim_ceiling']} without adversarial review observation",
                    f"claim:{c['claim_id']}", ["RUN_ADVERSARIAL_REVIEW", "SEEK_METHODOLOGICAL_CRITIQUE"])
                break

    return {
        "episode_id": ep.get("episode_id"),
        "engine_version": ENGINE_VERSION,
        "findings": findings,
    }


def highest_severity(diagnosis: dict) -> str:
    sev = [R.GAP_BY_CODE[f["gap_code"]]["severity"] for f in diagnosis["findings"]]
    if not sev:
        return "NONE"
    return max(sev, key=lambda s: R.SEVERITY_RANK[s])
