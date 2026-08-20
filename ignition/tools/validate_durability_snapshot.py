#!/usr/bin/env python3
"""Validate a canonical durability snapshot against an optional ledger."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent_runtime.durability import CanonicalSnapshotStore, SnapshotIntegrityError
from agent_runtime.event_ledger import EventLedger


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "schemas/operations/durability-snapshot-r1.schema.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--namespace")
    args = parser.parse_args()
    try:
        snapshot = CanonicalSnapshotStore(args.snapshot).read()
        if args.ledger:
            audit = CanonicalSnapshotStore(args.snapshot).audit(EventLedger(args.ledger), snapshot, namespace_scope=args.namespace)
            print(f"DURABILITY_SNAPSHOT_OK captured={audit['captured_events']} tail={audit['tail_events']} equivalent={audit['replay_equivalent']}")
        else:
            print(f"DURABILITY_SNAPSHOT_SCHEMA_OK id={snapshot.snapshot_id} epoch={snapshot.schema_epoch}")
        return 0
    except (SnapshotIntegrityError, OSError, json.JSONDecodeError) as exc:
        print(f"DURABILITY_SNAPSHOT_FAIL_CLOSED: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
