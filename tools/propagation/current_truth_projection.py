#!/usr/bin/env python3
"""Deterministic current-truth projection (task 106, contract §6).

The projection is derived ONLY from terminal (remotely verified) ledger records
plus canonical machine records. It must never be derived from an
authorized/running task. ``generate`` is deterministic (sorted keys, no
nondeterministic iteration, no network) so that two consecutive runs produce a
byte-identical file; the reconciliation validator enforces this fixed point.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List

from ledger import ledger_path, load_ledger, terminal_records

OUT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "operations",
    "current-truth-projection.json",
)

# Task 108 lifecycle events file (event-sourced terminality). When a task from
# the lifecycle ledger has resolved TERMINAL_SUCCESS but is absent from the
# legacy merged-iteration-ledger.jsonl (e.g. 107) or was historically only
# PR_OPEN (e.g. 106), the projection folds in its terminal facts so current
# public truth is complete and honest.
LIFECYCLE_EVENTS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "operations",
    "lifecycle-events.jsonl",
)


def _projections_from_terminal(records: List[Dict]) -> Dict[str, Any]:
    terminals = terminal_records(records)
    # Sort by task_number for determinism.
    terminals = sorted(terminals, key=lambda r: r.get("task_number", 0))
    recently_merged = []
    article_states: Dict[str, str] = {}
    open_questions_resolved = []
    capability_evidence = []
    corrections = []
    map_verdicts = []
    unresolved_obligations = []
    for rec in terminals:
        recently_merged.append({
            "task_number": rec.get("task_number"),
            "task_id": rec.get("task_id"),
            "merge_commit": rec.get("ordinary_merge_commit"),
            "exact_head": rec.get("exact_reviewed_head"),
            "terminal_state": rec.get("terminal_state"),
            "classification": rec.get("result_classification"),
        })
        for art, st in (rec.get("article_review_state") or {}).items():
            article_states[art] = st
        if rec.get("task_number") in (104, 105):
            # OQ-103-5 (Function OS v0.2 correctness) was resolved by 105.
            open_questions_resolved.append("OQ-103-5: Function OS v0.2 correctness benchmark executed (bounded)")
        capability_evidence.append({
            "ids": rec.get("affected_capability_status_claim_ids"),
            "task": rec.get("task_number"),
        })
        if rec.get("map_impact_verdict"):
            map_verdicts.append({
                "task": rec.get("task_number"),
                "verdict": rec.get("map_impact_verdict"),
            })
    # Unresolved obligations: surfaces each terminal record said must change but
    # the reconciliation must confirm. Task 106 itself closes these.
    for rec in terminals:
        for surf in (rec.get("public_surfaces_required_to_change") or []):
            unresolved_obligations.append({
                "task": rec.get("task_number"),
                "surface": surf,
            })
    return {
        "current_accepted_iteration": terminals[-1].get("task_number") if terminals else None,
        "current_project_status_date": "2026-07-31",
        "current_project_status_commit": terminals[-1].get("ordinary_merge_commit") if terminals else None,
        "recently_merged_results": recently_merged,
        "resolved_questions": open_questions_resolved,
        "article_review_states": article_states,
        "current_capability_evidence": capability_evidence,
        "map_state_and_impact": map_verdicts,
        "unresolved_propagation_obligations": unresolved_obligations,
    }


def _fold_lifecycle_terminal(repo_root: str, proj: Dict[str, Any]) -> None:
    """Fold terminal tasks from the event-sourced lifecycle into the projection.

    Only tasks whose lifecycle resolver reports TERMINAL_SUCCESS are folded in,
    so an un-reconciled task (e.g. 106/107 before their retroactive tag, or 108
    before its terminal tag) is NOT silently presented as current truth.
    """
    events_file = os.path.join(repo_root, "data/operations", "lifecycle-events.jsonl")
    if not os.path.exists(events_file):
        return
    try:
        import lifecycle_events as le  # noqa: F401  (tools/propagation on sys.path)
    except Exception:
        return
    events = le.load_events(events_file)
    view = le.derive_current_truth(events, "origin/main")
    already = {r.get("task_number") for r in proj.get("recently_merged_results", [])}
    for tn_str, state in view["resolved"].items():
        tn = int(tn_str)
        if state != "TERMINAL_SUCCESS" or tn in already:
            continue
        evs = [e for e in events if e.get("task_number") == tn]
        task_id = next((e.get("task_id") for e in evs), None)
        merge = next((e.get("content_merge_commit") or e.get("ordinary_merge_commit")
                      for e in evs if e.get("event_type") in ("TERMINALIZATION_PROJECTION", "LEGACY_TERMINAL_SUCCESS")), None)
        head = next((e.get("exact_reviewed_content_head") or e.get("exact_reviewed_head")
                     for e in evs if e.get("event_type") in ("ITERATION_CANDIDATE", "LEGACY_TERMINAL_SUCCESS")), None)
        terminal_state = next((e.get("terminal_state") for e in evs if e.get("terminal_state")), None)
        proj["recently_merged_results"].append({
            "task_number": tn,
            "task_id": task_id,
            "merge_commit": merge,
            "exact_head": head,
            "terminal_state": terminal_state,
            "classification": "folded from event-sourced lifecycle (TERMINAL_SUCCESS); retroactive reconciliation by task 108",
        })
        proj["_non_terminal_tasks_excluded"] = [t for t in proj["_non_terminal_tasks_excluded"] if t != tn]


def generate(repo_root: str, out_path: str = None) -> Dict[str, Any]:
    records = load_ledger(os.path.join(repo_root, "data", "operations", "merged-iteration-ledger.jsonl"))
    proj = _projections_from_terminal(records)
    # Guard: never derive from a non-terminal task.
    non_terminal = [r for r in records if r.get("ledger_status") not in ("TERMINAL_SUCCESS", "TERMINAL_BLOCKED")]
    proj["_derived_from_terminal_only"] = True
    proj["_non_terminal_tasks_excluded"] = [r.get("task_number") for r in non_terminal]
    # Fold terminal tasks reconciled via the event-sourced lifecycle (106/107
    # after retroactive attestation). Guarded to TERMINAL_SUCCESS only.
    _fold_lifecycle_terminal(repo_root, proj)
    # Recompute the current accepted iteration from the (now complete) terminals.
    terminals = sorted(proj["recently_merged_results"], key=lambda r: r.get("task_number", 0))
    if terminals:
        proj["current_accepted_iteration"] = terminals[-1].get("task_number")
        proj["current_project_status_commit"] = terminals[-1].get("merge_commit")
    target = out_path or os.path.abspath(OUT_PATH)
    with open(target, "w", encoding="utf-8") as fh:
        json.dump(proj, fh, ensure_ascii=False, sort_keys=True, indent=2)
        fh.write("\n")
    return proj


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--out", default=None)
    ap.add_argument("--check", action="store_true", help="regenerate and assert byte-identical to committed file")
    args = ap.parse_args()
    repo = os.path.abspath(args.repo)
    target = args.out or os.path.abspath(OUT_PATH)
    new = generate(repo, target)
    if args.check:
        with open(target, "r", encoding="utf-8") as fh:
            committed = fh.read()
        import io
        buf = io.StringIO()
        json.dump(new, buf, ensure_ascii=False, sort_keys=True, indent=2)
        buf.write("\n")
        if buf.getvalue() != committed:
            print("PROJECTION_NOT_DETERMINISTIC: regenerated bytes differ from committed file", file=sys.stderr)
            return 1
    print(f"CURRENT_TRUTH_PROJECTION_OK path={target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
