#!/usr/bin/env python3
"""Task 110 — generic candidate completion-state reconciliation engine.

The task-109 planner ranked candidates purely by a frozen priority model over the
candidate portfolio's `selection_decision` field, with NO lifecycle-state awareness.
That let already-completed work (C-01 by task 103; C-04 by task 105) be recommended
again. This module supplies the missing, GENERIC reconciliation layer.

Design (contract §5):
  * Linkage relies on governed identifiers (candidate_id, claim_id, run/task id,
    supersession, owner alias) — never on prose/text similarity.
  * Authoritative completion inputs are evidence-program runs, function-os
    benchmarks, and task FINAL_STATE records. Generated planner rankings/dossiers
    are NEVER authoritative.
  * The reconciliation is DATA-DRIVEN from a ledger
    (data/operations/iterations/110/completion-reconciliation.json) that is itself
    derived from those authoritative sources, with full provenance.
  * Every ledger entry is VALIDATED against the live authoritative artifact; on any
    mismatch the engine FAILS CLOSED to UNKNOWN_COMPLETION_STATE_REVIEW_REQUIRED.
  * The planner logic contains NO per-candidate hard-coded exclusion.

Determinism: no randomness, no network, no git. Output is a pure function of the
ledger + working-tree authoritative artifacts.
"""
import hashlib
import json
import os
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# ---- §5.2 fifteen-state lifecycle model ----
LIFECYCLE_STATES = {
    "UNASSESSED", "ELIGIBLE", "BLOCKED", "DEFERRED", "IN_PROGRESS",
    "COMPLETED_SUPPORTED", "COMPLETED_PARTIAL", "COMPLETED_CONTRADICTED",
    "COMPLETED_NULL_OR_INCONCLUSIVE", "COMPLETED_TEST_INVALID", "SUPERSEDED",
    "WITHDRAWN", "DO_NOT_SCHEDULE", "REOPENED_BY_OWNER",
    "UNKNOWN_COMPLETION_STATE_REVIEW_REQUIRED",
}

# Terminal states excluded from the active ranked queue (contract §5.4)
LIFECYCLE_TERMINAL = {
    "COMPLETED_SUPPORTED", "COMPLETED_PARTIAL", "COMPLETED_CONTRADICTED",
    "COMPLETED_NULL_OR_INCONCLUSIVE", "COMPLETED_TEST_INVALID",
    "SUPERSEDED", "WITHDRAWN", "DO_NOT_SCHEDULE",
}

UNKNOWN_STATE = "UNKNOWN_COMPLETION_STATE_REVIEW_REQUIRED"

# Authoritative outcome vocabulary -> lifecycle state
OUTCOME_TO_STATE = {
    "SUPPORTED_WITHIN_SCOPE": "COMPLETED_SUPPORTED",
    "SUPPORTED_WITHIN_BOUNDED_DOMAIN": "COMPLETED_SUPPORTED",
    "PARTIALLY_SUPPORTED_WITH_IDENTIFIED_MISMATCHES": "COMPLETED_PARTIAL",
    "PARTIALLY_SUPPORTED_WITH_IDENTIFIED_FAILURES": "COMPLETED_PARTIAL",
    "CONTRADICTED_WITHIN_SCOPE": "COMPLETED_CONTRADICTED",
    "CONTRADICTED_WITHIN_BOUNDED_DOMAIN": "COMPLETED_CONTRADICTED",
    "NULL_OR_INCONCLUSIVE": "COMPLETED_NULL_OR_INCONCLUSIVE",
    "TEST_INVALID_OR_ABORTED": "COMPLETED_TEST_INVALID",
}

LEDGER_PATH = REPO / "data/operations/iterations/110/completion-reconciliation.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_ledger():
    if not LEDGER_PATH.exists():
        return []
    return json.loads(LEDGER_PATH.read_text())


def validate_entry(entry):
    """Validate one ledger entry against the live authoritative artifact.

    Returns (ok: bool, derived_state: str|None, detail: str).
    Fails closed on any mismatch.
    """
    auth = entry.get("authority", {})
    src = REPO / auth.get("source", "")
    if not src.exists():
        return False, None, f"authority source missing: {auth.get('source')}"
    try:
        obj = json.loads(src.read_text())
    except Exception as e:  # noqa: BLE001
        return False, None, f"cannot parse {src}: {e}"
    live_outcome = obj.get("overall_verdict") or obj.get("outcome")
    observed = auth.get("observed_outcome")
    if observed is not None and live_outcome is not None and live_outcome != observed:
        return False, None, f"outcome drift: ledger={observed} live={live_outcome}"
    derived = OUTCOME_TO_STATE.get(live_outcome or observed)
    if derived is None:
        return False, None, f"unmapped outcome: {live_outcome or observed}"
    if entry.get("lifecycle_state") != derived:
        return False, None, f"state mismatch: ledger={entry.get('lifecycle_state')} derived={derived}"
    sha = auth.get("source_sha256")
    if sha and _sha256(src) != sha:
        return False, None, f"sha256 mismatch for {src}"
    return True, derived, "ok"


def build_index(ledger):
    """Build candidate_id -> state and claim_id -> state maps.

    Returns (candidate_map, claim_map, validation_report).
    On validation failure the entry degrades to UNKNOWN (fail closed).
    """
    cand = {}
    claim = {}
    report = []
    for e in ledger:
        ok, state, detail = validate_entry(e)
        cid = e.get("candidate_id")
        clid = e.get("claim_id")
        eff = state if ok else UNKNOWN_STATE
        report.append({
            "candidate_id": cid, "claim_id": clid, "ok": ok,
            "state": eff, "detail": detail,
        })
        if cid:
            cand[cid] = eff
        if clid:
            claim[clid] = eff
    return cand, claim, report


def _prior_recommendation_invalidated(cand_map, claim_map):
    """Read task-109 recommended_next and report whether reconciliation invalidates it."""
    rq = REPO / "data/operations/iterations/109/ranked_queue.json"
    if not rq.exists():
        return None
    try:
        obj = json.loads(rq.read_text())
    except Exception:  # noqa: BLE001
        return None
    prev = obj.get("recommended_next")
    if not prev:
        return None
    state = cand_map.get(prev)
    if state is None:
        # fall back to claim map via 109 inventory provenance not needed; report as unaudited
        return {"recommended_next": prev, "state": "UNASSESSED",
                "invalidated": False, "note": "no ledger entry for prior recommendation"}
    return {"recommended_next": prev, "state": state,
            "invalidated": state in LIFECYCLE_TERMINAL}


def reconcile(candidates, ledger=None):
    """Augment candidates with lifecycle_state + reconciliation_evidence.

    Returns (candidates, historical_register, validation_report, prev_invalidated).
    The function is pure/deterministic. It never mutates scores or blocked_reasons.
    """
    if ledger is None:
        ledger = load_ledger()
    cand_map, claim_map, report = build_index(ledger)
    historical = []
    for c in candidates:
        cid = c.get("canonical_id")
        clid = (c.get("provenance") or {}).get("claim_id")
        state = cand_map.get(cid)
        if state is None and clid:
            state = claim_map.get(clid)
        if state is None:
            state = "UNASSESSED"
        c["lifecycle_state"] = state
        c["reconciliation_evidence"] = None
        if state in LIFECYCLE_TERMINAL or state == UNKNOWN_STATE:
            ev = next((e for e in ledger
                       if e.get("candidate_id") == cid or e.get("claim_id") == clid), None)
            c["reconciliation_evidence"] = ev
            if state in LIFECYCLE_TERMINAL:
                historical.append({
                    "canonical_id": cid, "class": c.get("class"),
                    "lifecycle_state": state, "title": c.get("title"),
                    "evidence": ev,
                })
    prev_invalidated = _prior_recommendation_invalidated(cand_map, claim_map)
    return candidates, historical, report, prev_invalidated


if __name__ == "__main__":
    led = load_ledger()
    c, h, rep, prev = reconcile([], ledger=led)
    print(f"ledger entries={len(led)}")
    for r in rep:
        print(f"  {'OK ' if r['ok'] else 'BAD'} {r['candidate_id']:6s} {r['state']:42s} {r['detail']}")
    print(f"prior recommendation invalidated: {prev}")
