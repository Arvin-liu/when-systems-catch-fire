#!/usr/bin/env python3
"""Validate the five-child offline Control Plane R2 pilot receipt."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.pilots.control_plane_r2 import run_pilot


def main() -> int:
    result = run_pilot()
    child_ids = sorted(result.get("children", {}))
    passed = result.get("status") == "PASS" and child_ids == ["pilot-a", "pilot-b", "pilot-c", "pilot-d", "pilot-e"] and all(result.get("adversarial", {}).values())
    print(json.dumps({"status": "PASS" if passed else "FAIL", "child_ids": child_ids, "max_concurrent_observed": result.get("scheduler", {}).get("max_concurrent_observed"), "adversarial": result.get("adversarial", {}), "claim_ceiling": result.get("claim_ceiling")}, ensure_ascii=False, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
