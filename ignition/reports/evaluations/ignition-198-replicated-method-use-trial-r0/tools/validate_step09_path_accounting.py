#!/usr/bin/env python3
"""Validate the Task198 path-accounting fixed point."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[5]
ROOT_REL = Path("ignition/reports/evaluations/ignition-198-replicated-method-use-trial-r0")
ROOT = REPO / ROOT_REL
ACCOUNTING = ROOT / "path-accounting.json"
SIDECAR = ROOT / "path-accounting.sha256"
SOURCE = "76bb9b566bffc8fd92e6a84026a336bd96d8a534"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def fail(message: str) -> None:
    raise SystemExit(f"TASK198_STEP09_INVALID: {message}")


def command_lines(args: list[str]) -> list[str]:
    return subprocess.run(
        args,
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()


def main() -> None:
    data = json.loads(ACCOUNTING.read_text())
    if data["source_commit"] != SOURCE:
        fail("wrong source commit")
    scope = data["accounting_scope"]
    prefix = scope["required_prefix"]
    declared = sorted(scope["declared_step09_paths"])
    if len(declared) != 4 or len(set(declared)) != 4:
        fail("Step09 declaration does not contain exactly four unique paths")
    if any(not path.startswith(prefix) for path in declared):
        fail("declared Step09 path is outside task prefix")

    diff_paths = command_lines(["git", "diff", "--name-only", f"{SOURCE}..HEAD"])
    untracked = command_lines(["git", "ls-files", "--others", "--exclude-standard", "--", str(ROOT_REL)])
    actual = sorted(set(diff_paths + untracked))
    if len(actual) != scope["expected_path_count"]:
        fail(f"path count {len(actual)} != {scope['expected_path_count']}")
    if any(not path.startswith(prefix) for path in actual):
        fail("path outside task-local prefix")
    inventory = ("\n".join(actual) + "\n").encode()
    if sha256_bytes(inventory) != scope["sorted_newline_path_inventory_sha256"]:
        fail("sorted path inventory digest mismatch")
    if not set(declared).issubset(set(actual)):
        fail("declared Step09 path is absent from actual inventory")

    forbidden_sets = [
        "canonical_claim_ids",
        "canonical_promotion_artifacts",
        "foundation_mutations",
        "current_state_mutations",
        "fire_seeds_mutations",
        "model_rsi_or_metarsi_artifacts",
        "weight_training_artifacts",
    ]
    if any(scope[key] for key in forbidden_sets):
        fail("forbidden canonical or training artifact is declared")

    if not SIDECAR.is_file():
        fail("accounting sidecar is missing")
    expected_sidecar = f"{sha256_bytes(ACCOUNTING.read_bytes())}  path-accounting.json\n"
    if SIDECAR.read_text() != expected_sidecar:
        fail("accounting sidecar does not bind final accounting bytes")

    porcelain = command_lines(["git", "status", "--porcelain"])
    unexpected = [line for line in porcelain if not any(path in line for path in declared)]
    if unexpected:
        fail(f"unexpected working-tree residual: {unexpected}")

    if data["terminal_stop"] != "READY_FOR_REPLICATED_METHOD_USE_SUCCESSOR_TRIALS":
        fail("wrong terminal stop")
    print("TASK198_STEP09_PATH_ACCOUNTING_FIXED_POINT_VALID")


if __name__ == "__main__":
    main()
