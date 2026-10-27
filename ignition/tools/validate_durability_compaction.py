#!/usr/bin/env python3
"""Validate immutable snapshot-chain fallback and compaction receipts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent_runtime.durability import SnapshotChainStore, SnapshotIntegrityError
from agent_runtime.event_ledger import EventLedger


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("chain", type=Path)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--namespace")
    args = parser.parse_args()
    try:
        state, snapshot, path = SnapshotChainStore(args.chain).restore_with_fallback(EventLedger(args.ledger), namespace_scope=args.namespace)
        print(f"DURABILITY_COMPACTION_OK snapshot={snapshot.snapshot_id} path={path.name} events={state['event_count']} fallback_chain=PASS")
        return 0
    except (SnapshotIntegrityError, OSError, json.JSONDecodeError) as exc:
        print(f"DURABILITY_COMPACTION_FAIL_CLOSED: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
