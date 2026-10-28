#!/usr/bin/env python3
"""Offline executor capability/health lease gate."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.executor_health import ExecutorCapabilityLease, ExecutorHealthStore


def main() -> int:
    clock = [100.0]
    with tempfile.TemporaryDirectory(prefix="executor-health-gate-") as temp:
        store = ExecutorHealthStore(Path(temp) / "health.json", clock=lambda: clock[0])
        value = ExecutorCapabilityLease(
            executor_id="reference-gate", family="reference", adapter_version="r2-fixture", observed_version="fixture-1",
            capability_tokens=("repo.read",), permission_ceiling=("repo.read",), workspace_modes=("isolated",),
            supports_progress=True, supports_cancel=True, supports_resume=False, supports_handoff=False,
            max_concurrency=1, status="HEALTHY", observed_at=100.0, expires_at=105.0, probe_kind="OFFLINE_FIXTURE",
            evidence_refs=("validator-fixture",),
        )
        store.observe(value)
        healthy = store.usable("reference-gate", required_capabilities=("repo.read",))
        clock[0] = 106.0
        stale = not store.usable("reference-gate", required_capabilities=("repo.read",)) and store.get("reference-gate").status == "STALE"
        print(f"EXECUTOR_HEALTH_LEASE_R1={'PASS' if healthy and stale else 'FAIL'}")
        print(f"HEALTHY_ROUTE={'PASS' if healthy else 'FAIL'}")
        print(f"EXPIRED_LEASE={'STALE' if stale else 'NOT_STALE'}")
        print(f"STORE_AUDIT={store.audit()['status']}")
        return 0 if healthy and stale else 1


if __name__ == "__main__":
    raise SystemExit(main())
