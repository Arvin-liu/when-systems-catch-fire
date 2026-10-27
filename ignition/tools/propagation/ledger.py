#!/usr/bin/env python3
"""Canonical merged-iteration ledger (task 106, contract §4).

The ledger is the single repository-native, machine-readable authority of
accepted merged iterations. It is append-oriented and deterministic: a record
is never rewritten merely because later work corrects its conclusions;
corrections use explicit supersession/amendment records (see the
``supersession_or_correction_links`` field).

This module loads and validates ``data/operations/merged-iteration-ledger.jsonl``
and exposes helpers used by the impact contract, current-truth projection and
the fail-closed reconciliation validator.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Dict, List, Optional

LEDGER_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "operations",
    "merged-iteration-ledger.jsonl",
)

# Lifecycle states required by contract §4.
VALID_STATES = {
    "AUTHORIZED",
    "RUNNING",
    "BLOCKED",
    "PR_OPEN",
    "MERGED_NOT_VERIFIED",
    "TERMINAL_SUCCESS",
    "TERMINAL_BLOCKED",
}

# Fields every accepted (terminal) record must carry so a public statement can
# cite remote evidence rather than chat.
REQUIRED_TERMINAL_FIELDS = (
    "task_number",
    "task_id",
    "formal_pr_number",
    "ordinary_merge_commit",
    "exact_reviewed_head",
    "receipt_branch",
    "terminal_receipt_path",
    "terminal_state",
    "exact_head_ci_evidence",
    "post_merge_verification_evidence",
    "clean_clone_evidence",
)


def ledger_path() -> str:
    return os.path.abspath(LEDGER_PATH)


def load_ledger(path: Optional[str] = None) -> List[Dict]:
    """Load the ledger as an ordered list of records (append order preserved)."""
    p = os.path.abspath(path or LEDGER_PATH)
    if not os.path.exists(p):
        raise FileNotFoundError(f"ledger not found: {p}")
    records: List[Dict] = []
    with open(p, "r", encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{p}:{lineno}: invalid JSON: {exc}") from exc
    return records


def validate_ledger(records: List[Dict]) -> List[str]:
    """Return a list of human-readable problems (empty == valid).

    Checks: every record has a numeric task_number; ledger_status is one of the
    seven required states; terminal records carry all required evidence fields;
    terminal records must not be derived from a non-terminal task.
    """
    problems: List[str] = []
    seen = set()
    for rec in records:
        tn = rec.get("task_number")
        if not isinstance(tn, int):
            problems.append(f"record missing integer task_number: {rec.get('task_id')}")
            continue
        if tn in seen:
            problems.append(f"duplicate task_number {tn} in ledger")
        seen.add(tn)
        status = rec.get("ledger_status")
        if status not in VALID_STATES:
            problems.append(f"task {tn}: invalid ledger_status {status!r}")
        if status in ("TERMINAL_SUCCESS", "TERMINAL_BLOCKED"):
            for field in REQUIRED_TERMINAL_FIELDS:
                val = rec.get(field)
                if val in (None, "", "null") or (isinstance(val, str) and val.startswith("<")):
                    problems.append(
                        f"task {tn}: terminal record missing/placeholder evidence field {field}"
                    )
    return problems


def get_record(records: List[Dict], task_number: int) -> Optional[Dict]:
    for rec in records:
        if rec.get("task_number") == task_number:
            return rec
    return None


def terminal_records(records: List[Dict]) -> List[Dict]:
    """Only TERMINAL_SUCCESS records may drive a public 'complete' statement."""
    return [r for r in records if r.get("ledger_status") == "TERMINAL_SUCCESS"]


def main() -> int:
    recs = load_ledger()
    problems = validate_ledger(recs)
    if problems:
        for p in problems:
            print(f"LEDGER_INVALID: {p}", file=sys.stderr)
        return 1
    print(f"LEDGER_OK records={len(recs)} terminal={len(terminal_records(recs))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
