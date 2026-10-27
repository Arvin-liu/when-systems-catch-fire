#!/usr/bin/env python3
"""Run the disposable five-child Control Plane R2 pilot and persist its receipt."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.control import _atomic_json
from agent_runtime.pilots.control_plane_r2 import run_pilot


DEFAULT_OUTPUT = ROOT / "data" / "agent-runtime" / "pilots" / "r2-control-plane" / "pilot-result.json"


def main() -> int:
    parser = argparse.ArgumentParser(prog="run-control-plane-r2-pilot")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run_pilot()
    _atomic_json(args.output, result)
    print(f"CONTROL_PLANE_R2_PILOT={result['status']}")
    print(f"OUTPUT={args.output}")
    print(f"MAX_CONCURRENT_OBSERVED={result['scheduler']['max_concurrent_observed']}")
    print(f"CHILD_COUNT={len(result['children'])}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
