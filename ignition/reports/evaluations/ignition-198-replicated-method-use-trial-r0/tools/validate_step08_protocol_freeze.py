#!/usr/bin/env python3
"""Validate Task198's no-new-protocol/no-second-schema freeze."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[5]
ROOT = REPO / "ignition/reports/evaluations/ignition-198-replicated-method-use-trial-r0"
FREEZE = ROOT / "protocol-complexity-freeze.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str) -> None:
    raise SystemExit(f"TASK198_STEP08_INVALID: {message}")


def main() -> None:
    data = json.loads(FREEZE.read_text())
    if data["source_commit"] != "76bb9b566bffc8fd92e6a84026a336bd96d8a534":
        fail("wrong source commit")
    protocol = data["protocol_freeze"]
    if protocol["new_r0_5_protocol"] != "NONE":
        fail("R0.5 protocol is present")
    if protocol["new_method_use_schema"] != "NONE":
        fail("new method-use schema is present")
    if protocol["second_method_use_schema"] != "PROHIBITED":
        fail("second method-use schema is not prohibited")
    if protocol["new_case_schema"] != "NONE" or protocol["new_condition_schema"] != "NONE":
        fail("new case or condition schema is present")

    trace = protocol["method_trace_schema"]
    trace_path = REPO / trace["path"]
    if not trace_path.is_file() or digest(trace_path) != trace["sha256"]:
        fail("Method-Use Trace R0 schema hash mismatch")
    validator = protocol["method_trace_validator"]
    validator_path = REPO / validator["path"]
    if not validator_path.is_file() or digest(validator_path) != validator["sha256"]:
        fail("Method-Use Trace R0 validator hash mismatch")

    for pin in data["r0_4_baseline_pins"]:
        path = REPO / pin["path"]
        if not path.is_file() or digest(path) != pin["sha256"]:
            fail(f"R0.4 baseline hash mismatch: {pin['path']}")

    changed = subprocess.run(
        ["git", "diff", "--name-only", "76bb9b566bffc8fd92e6a84026a336bd96d8a534..HEAD", "--", "ignition/evaluation/r0.4"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    if changed:
        fail(f"R0.4 baseline paths changed: {changed}")

    forbidden_names = ["r0.5", "R0.5", "second-method-use", "method-use-trace-r0.5"]
    task_paths = subprocess.run(
        ["git", "ls-files", "ignition/reports/evaluations/ignition-198-replicated-method-use-trial-r0"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    for path in task_paths:
        if any(token in path for token in forbidden_names):
            fail(f"forbidden protocol/schema name in task path: {path}")

    if data["terminal_stop"] != "READY_FOR_REPLICATED_METHOD_USE_SUCCESSOR_TRIALS":
        fail("wrong terminal stop")
    print("TASK198_STEP08_PROTOCOL_COMPLEXITY_FREEZE_VALID")


if __name__ == "__main__":
    main()
