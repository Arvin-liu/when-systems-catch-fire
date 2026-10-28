#!/usr/bin/env python3
"""Deterministic derived lifecycle view (task 108, contract §5).

Produces ``data/operations/derived-lifecycle-view.json`` -- the resolved,
machine-readable current truth of the iteration lifecycle, derived from the
append-only event ledger plus annotated terminal tags. It is deterministic
(sorted keys, no entropy) so two runs produce byte-identical output; the CI
fixed-point check enforces this.

This view replaces the role of reading a single mutable ledger row: it resolves
each task's status from valid events, never from a record that had to know its
own future merge commit.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Dict, List

import lifecycle_events as le

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT_PATH = os.path.join(REPO, "data", "operations", "derived-lifecycle-view.json")


def generate(repo_root: str = REPO, out_path: str = None, main_ref: str = "origin/main") -> Dict:
    root = os.path.abspath(repo_root)
    events_file = os.path.join(root, "data", "operations", "lifecycle-events.jsonl")
    events = le.load_events(events_file)
    view = le.derive_current_truth(events, main_ref)
    # Add a per-task summary with receipts for human/CI consumption.
    summary: List[Dict] = []
    for ev in sorted(events, key=lambda e: e.get("task_number", 0)):
        tn = ev.get("task_number")
        if any(s.get("task_number") == tn for s in summary):
            continue
        r = view["resolved"].get(str(tn))
        summary.append({
            "task_number": tn,
            "task_id": ev.get("task_id"),
            "resolved_state": r,
        })
    view["task_summary"] = summary
    out = out_path or os.path.join(root, "data", "operations", "derived-lifecycle-view.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(view, fh, ensure_ascii=False, sort_keys=True, indent=2)
        fh.write("\n")
    return view


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--out", default=None)
    ap.add_argument("--main-ref", default="origin/main")
    args = ap.parse_args()
    generate(args.repo, args.out, args.main_ref)
    print(f"GENERATED derived-lifecycle-view.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
