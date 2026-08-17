#!/usr/bin/env python3
"""Offline resource conflict, atomicity and lease-expiry gate."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.resource_arbitration import ResourceArbiter, ResourceConflict, ResourceIntent


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="resource-arbiter-gate-") as temp:
        arbiter = ResourceArbiter(Path(temp) / "resources.json", clock=lambda: 100.0)
        arbiter.acquire_many((
            ResourceIntent("gate-read-a", "gate-a", "workspace:shared", "READ_SHARED", created_at="2026-08-17T00:00:00Z"),
            ResourceIntent("gate-read-b", "gate-b", "workspace:shared", "READ_SHARED", created_at="2026-08-17T00:00:00Z"),
        ), now=100.0)
        try:
            arbiter.acquire(ResourceIntent("gate-write", "gate-c", "workspace:shared/file", "WRITE_EXCLUSIVE", created_at="2026-08-17T00:00:00Z"), now=100.0)
        except ResourceConflict:
            conflict = True
        else:
            conflict = False
        result = arbiter.audit()
        ok = conflict and result["active_count"] == 2 and result["unknown_side_effect_policy"] == "NO_OVERLAP_NO_AUTOMATIC_FAILOVER"
        print(f"RESOURCE_ARBITRATION_R1={'PASS' if ok else 'FAIL'}")
        print(f"ATOMIC_CONFLICT={'FAIL_CLOSED' if conflict else 'ACCEPTED'}")
        print(f"ACTIVE_LEASES={result['active_count']}")
        print(f"UNKNOWN_SIDE_EFFECT_POLICY={result['unknown_side_effect_policy']}")
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
