#!/usr/bin/env python3
"""Deterministic terminalization generator (task 108, contract §3.2/§7/§17).

Given the exact content merge commit, this module generates the immutable
TERMINALIZATION_PROJECTION event that is appended to the lifecycle ledger. It is
deterministic: same inputs => same bytes. It appends only a second event for the
task; it does not modify the candidate event and it does not invent a merge.

The terminal tag name is fixed as ``ignition/iterations/<n>/terminal-r1``. The
generator does not create the tag (that is done after the terminalization PR
merges and the core receipt is written); it only declares the expected name.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from typing import Dict, Optional

import lifecycle_events as le

DEFAULT_EVENTS_PATH = le.DEFAULT_EVENTS_PATH


def expected_terminal_tag_name(task_number: int) -> str:
    return f"ignition/iterations/{task_number}/terminal-r1"


def build_projection_event(
    task_number: int,
    task_id: str,
    control_commit: str,
    content_pr_number: int,
    content_merge_commit: str,
    terminal_state: str,
    receipt_branch: str,
    receipt_root: str,
    predecessor_terminal_state: Optional[str] = None,
) -> Dict:
    """Build the deterministic TERMINALIZATION_PROJECTION event.

    Contains only facts knowable AFTER the content merge. Does NOT include the
    tag object sha, tag target or core receipt digest yet (those are filled by
    the post-merge terminalization step). Determinism: sorted keys, no entropy.
    """
    event = {
        "schema_version": "1.0.0",
        "event_type": "TERMINALIZATION_PROJECTION",
        "record_type": "TERMINALIZATION_PROJECTION",
        "task_number": task_number,
        "task_id": task_id,
        "control_commit": control_commit,
        "predecessor_terminal_state": predecessor_terminal_state,
        "lifecycle_state": "AWAITING_TERMINAL_TAG",
        "content_pr_number": content_pr_number,
        "content_merge_commit": content_merge_commit,
        "terminalization_pr_number": None,  # filled after terminalization PR opens
        "terminalization_merge_commit": None,  # filled after terminalization PR merges
        "terminal_tag_name": expected_terminal_tag_name(task_number),
        "terminal_tag_object_sha": None,
        "terminal_tag_target": None,
        "core_receipt_sha256": None,
        "attestation_mode": "ORIGINAL_TERMINATION",
        "terminal_state": terminal_state,
        "note": "Generated deterministically from exact content merge; no future merge invented.",
    }
    return event


def append_projection(
    task_number: int,
    task_id: str,
    control_commit: str,
    content_pr_number: int,
    content_merge_commit: str,
    terminal_state: str,
    receipt_branch: str,
    receipt_root: str,
    events_path: Optional[str] = None,
) -> str:
    """Append the projection event to the ledger and return its canonical JSON line."""
    p = os.path.abspath(events_path or DEFAULT_EVENTS_PATH)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    event = build_projection_event(
        task_number, task_id, control_commit, content_pr_number,
        content_merge_commit, terminal_state, receipt_branch, receipt_root,
    )
    line = json.dumps(event, ensure_ascii=False, sort_keys=True)
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    return line


def core_receipt_sha256(core: Dict) -> str:
    """Content-address the immutable TERMINAL_EVIDENCE_CORE.json."""
    canonical = json.dumps(core, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-number", type=int, required=True)
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--control-commit", required=True)
    ap.add_argument("--content-pr", type=int, required=True)
    ap.add_argument("--content-merge", required=True)
    ap.add_argument("--terminal-state", required=True)
    ap.add_argument("--receipt-branch", required=True)
    ap.add_argument("--receipt-root", required=True)
    ap.add_argument("--events", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.dry_run:
        line = build_projection_event(
            args.task_number, args.task_id, args.control_commit,
            args.content_pr, args.content_merge, args.terminal_state,
            args.receipt_branch, args.receipt_root,
        )
        print(json.dumps(line, ensure_ascii=False, indent=2))
        return 0
    append_projection(
        args.task_number, args.task_id, args.control_commit,
        args.content_pr, args.content_merge, args.terminal_state,
        args.receipt_branch, args.receipt_root, args.events,
    )
    print(f"APPENDED TERMINALIZATION_PROJECTION for task {args.task_number}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
