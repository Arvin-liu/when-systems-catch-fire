#!/usr/bin/env python3
"""Validate the committed R2 offline multi-Run repository-maintenance receipt."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.memory import OperationalMemoryStore  # noqa: E402
from agent_runtime.pilots.r2_repository_maintenance import validate_receipts  # noqa: E402


PILOT_DIR = ROOT / "data/agent-runtime/pilots/r2-offline-repository-maintenance"
PRIVATE_MARKERS = ("/Users/", "/private/var/", "/var/folders/", "file://", "ssh://")


def main() -> int:
    result = validate_receipts(PILOT_DIR)
    receipt_text = (PILOT_DIR / "pilot-receipt.json").read_text(encoding="utf-8")
    adversarial = json.loads((PILOT_DIR / "adversarial-receipt.json").read_text(encoding="utf-8"))
    receipt = json.loads(receipt_text)
    if any(marker in receipt_text for marker in PRIVATE_MARKERS):
        raise AssertionError("committed pilot receipt contains a private path or URL")
    if receipt["fresh_clone"]["network_allowed"] or receipt["fresh_clone"]["remote_mutation"] or receipt["fresh_clone"]["git_push_invoked"]:
        raise AssertionError("offline pilot receipt widened network or remote mutation")
    if receipt["fresh_clone"]["private_paths_in_receipt"] is not False:
        raise AssertionError("pilot receipt did not assert private-path sanitization")
    if receipt["claim_ceiling"] != "OFFLINE_REPOSITORY_PILOT_OBSERVED_ONLY_NOT_GENERAL_INTELLIGENCE":
        raise AssertionError("pilot claim ceiling changed")
    if adversarial["terminal_state"] != "EPISODE_COMPLETED_WITH_INDEPENDENT_FAILURES":
        raise AssertionError("adversarial episode did not preserve independent failures")
    memory = OperationalMemoryStore(PILOT_DIR / "durable-memory.jsonl")
    if memory.audit()["status"] != "PASS" or not memory.query(memory_type="FAILURE") or not memory.query(memory_type="EPISODIC"):
        raise AssertionError("durable operational memory does not contain the failure and episode records")
    capsule = json.loads((PILOT_DIR / "memory-capsule.json").read_text(encoding="utf-8"))
    if not capsule.get("bounded") or "not knowledge truth" not in capsule.get("claim_ceiling", ""):
        raise AssertionError("operational memory capsule is not bounded")
    print(json.dumps({
        **result,
        "checkpoint_count": receipt["episode"]["checkpoint_count"],
        "handoffs": len(receipt["episode"]["handoffs"]),
        "memory_audit": memory.audit()["status"],
        "network_allowed": receipt["fresh_clone"]["network_allowed"],
        "remote_mutation": receipt["fresh_clone"]["remote_mutation"],
        "private_paths_in_receipt": receipt["fresh_clone"]["private_paths_in_receipt"],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
