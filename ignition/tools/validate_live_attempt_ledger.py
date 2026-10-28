#!/usr/bin/env python3
"""Validate the append-only LiveAttemptLedger and its negative contract fixtures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

try:
    from agent_federation.live_attempt_ledger import LiveAttemptLedger, LiveAttemptLedgerError
except ImportError:  # direct invocation from the ignition directory
    from live_attempt_ledger import LiveAttemptLedger, LiveAttemptLedgerError


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
DEFAULT_PATH = ROOT / "data/operations/iterations/139/live-attempt-ledger.jsonl"
FIXTURE_PATH = ROOT / "data/operations/iterations/139/fixtures/live-attempt-ledger-fixtures-r1.json"


def validate_fixtures() -> list[str]:
    if not FIXTURE_PATH.is_file():
        return [f"missing fixture file: {FIXTURE_PATH.relative_to(ROOT.parent)}"]
    try:
        document = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"fixture file unreadable: {exc}"]
    if document.get("schema_version") != "live-attempt-ledger-fixtures-r1":
        return ["fixture schema version mismatch"]
    required = {"duplicate-dispatch", "duplicate-attempt", "wrong-task-binding", "unknown-state", "incomplete-success"}
    observed = {row.get("id") for row in document.get("fixtures", []) if isinstance(row, dict)}
    return [f"missing negative fixture: {fixture_id}" for fixture_id in sorted(required - observed)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default=str(DEFAULT_PATH))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate_fixtures()
    try:
        audit = LiveAttemptLedger(args.path).audit()
    except LiveAttemptLedgerError as exc:
        errors.append(f"ledger invalid: {exc}")
        audit = None
    if errors:
        print("LIVE_ATTEMPT_LEDGER_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    assert audit is not None
    print(
        f"LIVE_ATTEMPT_LEDGER_OK records={audit['record_count']} "
        f"dispatches={audit['dispatch_count']} attempts={audit['attempt_count']} head={audit['head_hash']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
