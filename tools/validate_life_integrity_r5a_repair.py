#!/usr/bin/env python3
# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Machine acceptance gate for the R5-A narrow repair.

The gate executes the explicit attack registry, validates the aggregate
contract, compares committed generated artifacts, and checks the formal diff
does not enter prohibited R5-B/R5-C/R6 or production-runtime paths.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from life_integrity_r5a import attack_gate, registries, validators  # noqa: E402
import tools.generate_life_integrity_r5a as generator  # noqa: E402


def _git_changed_paths() -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", registries.CANDIDATE_FROZEN_HEAD],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return sorted(
        set(line for line in completed.stdout.splitlines() if line)
        | set(line for line in untracked.stdout.splitlines() if line)
    )


def _artifact_errors() -> list[str]:
    errors: list[str] = []
    for name, builder in generator._ARTIFACTS:
        path = Path(generator.OUT_DIR) / name
        if not path.is_file():
            errors.append(f"missing generated artifact: {path.relative_to(REPO_ROOT)}")
            continue
        actual = json.loads(path.read_text(encoding="utf-8"))
        expected = builder()
        if actual != expected:
            errors.append(f"stale generated artifact: {path.relative_to(REPO_ROOT)}")
    return errors


def _scope_errors(changed_paths: list[str]) -> list[str]:
    errors: list[str] = []
    prohibited_prefixes = (
        "domain-packs/",
        "tools/ignition_runtime/",
        "schemas/ignition_runtime/",
        "tests/ignition_runtime/",
        "tools/adaptive_relational_runtime/",
    )
    for path in changed_paths:
        if path.startswith(prohibited_prefixes):
            errors.append(f"prohibited implementation path changed: {path}")
    return errors


def main() -> int:
    attack_receipt = attack_gate.run_attack_gate()
    aggregate_ok, aggregate_failures = validators.validate_all()
    changed_paths = _git_changed_paths()
    errors = []
    if attack_receipt["status"] != "PASS":
        errors.extend(attack_receipt["identity_errors"])
        errors.extend(
            f"failed attack instance: {case_id}"
            for case_id in attack_receipt["failed_case_ids"]
        )
    if not aggregate_ok:
        errors.extend(aggregate_failures)
    errors.extend(_artifact_errors())
    errors.extend(_scope_errors(changed_paths))

    receipt = {
        "schema": "r5a/narrow-repair-machine-gate/v1",
        "candidate_frozen_head": registries.CANDIDATE_FROZEN_HEAD,
        "adjudication": "NIGHT_QUEUE_R1_PARTIAL_SALVAGE_NOT_ACCEPTED",
        "attack_gate_status": attack_receipt["status"],
        "executed_case_ids": [item["case_id"] for item in attack_receipt["results"]],
        "aggregate_validator": "PASS" if aggregate_ok else "BLOCKED",
        "changed_paths": changed_paths,
        "r5b_started": False,
        "r5c_started": False,
        "r6_started": False,
        "errors": errors,
        "status": "PASS" if not errors else "BLOCKED",
        "claim_ceiling": "repository_contract_observed",
        "count_is_not_acceptance": True,
    }
    print(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
