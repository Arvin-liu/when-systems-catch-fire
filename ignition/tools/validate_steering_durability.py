#!/usr/bin/env python3
"""Validate steering event append, snapshot/replay, recovery, and migration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/operations/iterations/129/fixtures/steering-durability-r1.json"
SCHEMA = ROOT / "schemas/operations/steering-durability-r1.schema.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.event_ledger import EventLedger  # noqa: E402
from agent_runtime.steering import SteeringDurabilityAdapter, SteeringState  # noqa: E402


def validate() -> list[str]:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    errors = [error.message for error in Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).iter_errors(document)]
    state = SteeringState.from_dict({"schema": "os-steering-intent-obligation-r1.durable-state", **document["state"], "claim_ceiling": "fixture"})
    with tempfile.TemporaryDirectory(prefix="ignition-129-durability-") as temp:
        root = Path(temp)
        ledger = EventLedger(root / "steering-events.jsonl")
        adapter = SteeringDurabilityAdapter()
        first = adapter.append_state(ledger, state, occurred_at="2026-08-21T12:00:00+08:00")
        snapshot = adapter.snapshot(ledger, str(root / "steering-snapshot.json"), snapshot_id="snapshot-steering-1", provenance_refs=("intent-durable-1",))
        second_state = SteeringState.from_dict({**state.to_dict(), "goals": list(state.goals) + [{"goal_id": "goal-durable-2", "status": "BLOCKED"}]})
        adapter.append_state(ledger, second_state, expected_version=1, occurred_at="2026-08-21T12:01:00+08:00")
        replayed = adapter.replay(ledger)
        restored = adapter.restore(ledger, snapshot=snapshot)
        migration = adapter.migrate(replayed, migration_id="migration-steering-1", from_epoch="steering-r1", to_epoch="steering-r2", event_lineage=tuple(event.event_id for event in ledger.events()))
        if first.event_type != "STEERING_STATE_RECORDED" or len(ledger.events()) != 2:
            errors.append("steering events were not appended through the canonical ledger")
        if replayed.digest() != second_state.digest() or restored.digest() != second_state.digest():
            errors.append("snapshot plus tail replay did not recover the final steering state")
        if snapshot.namespace_scope != "steering" or migration.receipt.events_rewritten:
            errors.append("snapshot namespace or migration lineage boundary failed")
        if migration.receipt.status != "DRY_RUN" or migration.receipt.event_lineage_digest == "0" * 64:
            errors.append("migration receipt did not preserve dry-run lineage evidence")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    errors = validate()
    if errors:
        print("STEERING_DURABILITY_INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("STEERING_DURABILITY_OK events=2 snapshot_tail_replay=PASS recovery=PASS migration=DRY_RUN lineage_preserved=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
