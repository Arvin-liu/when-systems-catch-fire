#!/usr/bin/env python3
"""Validate Task141 R3 projection materialization and deterministic receipt."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agent_federation.live_current_projection import validate_projection


ROOT = Path(__file__).resolve().parents[1]
PROJECTION = ROOT / "data/operations/iterations/141/live-current-projection-r3.json"
RECEIPT = ROOT / "data/operations/iterations/141/step12-deterministic-current-projection.json"


class Task141CurrentProjectionError(RuntimeError):
    """Raised when Task141 R3 Current projection is stale or semantically collapsed."""


def run_validation() -> dict[str, Any]:
    projection = validate_projection(json.loads(PROJECTION.read_text(encoding="utf-8")))
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    if receipt.get("status") != "PASS" or receipt.get("task_id") != "IGNITION-20260826-141" or receipt.get("step") != "12":
        raise Task141CurrentProjectionError("Step12 receipt binding/status is invalid")
    if projection["schema_version"] != "live-current-projection-r3" or projection["projection_digest"] != receipt["projection_digest"]:
        raise Task141CurrentProjectionError("R3 projection schema or digest diverged")
    if projection["counts"] != receipt["counts"]:
        raise Task141CurrentProjectionError("R3 counts diverged from receipt")
    dimensions = projection["live_state_dimensions"]
    expected = receipt["canonical_dimensions"]
    if any(dimensions[key] != value for key, value in expected.items()):
        raise Task141CurrentProjectionError("canonical live dimensions diverged")
    if projection["current_live_ceiling"] != "LIVE_EXTERNAL_PROCESS_OBSERVED_NO_VALIDATED_COMPLETION":
        raise Task141CurrentProjectionError("process observation was collapsed into invocation-not-observed")
    if projection["compatibility_projection"]["status"] != "DEPRECATED_COMPATIBILITY_ALIAS":
        raise Task141CurrentProjectionError("compatibility alias is not marked deprecated")
    return {"status": "PASS", "projection_digest": projection["projection_digest"], "counts": projection["counts"], "dimensions": dimensions, "claim_ceiling": receipt["claim_ceiling"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    print(json.dumps(run_validation(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
