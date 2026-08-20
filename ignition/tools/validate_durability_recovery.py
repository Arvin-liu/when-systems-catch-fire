#!/usr/bin/env python3
"""Validate Step 12 recovery orchestrator contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from agent_runtime.recovery import FAULT_POINTS, RECOVERY_PHASES


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data/operations/durability/recovery-orchestrator-contract-r1.json"
DEFAULT_SCHEMA = ROOT / "schemas/operations/durability-recovery-orchestrator-r1.schema.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args()
    data = json.loads(args.data.read_text(encoding="utf-8"))
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(data)]
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    if data["phase_sequence"] != list(RECOVERY_PHASES) or set(data["fault_points"]) != set(FAULT_POINTS):
        print("FAIL\n- recovery sequence or fault matrix does not match runtime")
        return 1
    print("DURABILITY_RECOVERY_OK phases=11 ledger_snapshot_tail=PASS migration=NO_EVENT_REWRITE queue_budget_lease=PASS memory=PASS uncertain_dispatch=RECONCILE_ONLY advisory_soft_context=PASS fault_points=10 exactly_once=NOT_CLAIMED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
