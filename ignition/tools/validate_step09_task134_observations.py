#!/usr/bin/env python3
"""Close every Task134 long-run observation with a targeted, typed receipt.

This is a bounded closure runner, not a replacement test framework.  It
replays the exact affected test or validator for each inventory row, uses the
canonical isolated dependency environment for dependency-sensitive rows, and
records a terminal state for every observation.  A sealed historical residual
is considered closed only when its exact-residual assertion passes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve()
APP_ROOT = HERE.parents[1]
REPO_ROOT = APP_ROOT.parent
RECEIPT_PATH = APP_ROOT / "data/operations/iterations/135/step09-task134-observation-closure.json"
SCHEMA_PATH = APP_ROOT / "schemas/operations/step09-task134-observation-closure-r1.schema.json"
INVENTORY_PATH = APP_ROOT / "data/operations/iterations/135/step00-failure-inventory.json"

sys.path.insert(0, str(APP_ROOT / "tools"))
import run_full_regression as runner  # noqa: E402


TERMINAL_STATES = {
    "FIXED_CURRENT_DEFECT",
    "FIXED_STALE_TEST",
    "SEALED_RESIDUAL_ASSERTED",
    "ENVIRONMENT_CONTRACT_FIXED",
    "RUNNER_BOUNDARY_FIXED",
    "BLOCKED_WITH_EVIDENCE",
}


TARGETS = (
    {
        "id": "E01",
        "terminal_state": "RUNNER_BOUNDARY_FIXED",
        "kind": "unittest",
        "test_id": "tests.test_change_propagation.ChangePropagationTests.test_a_method_version_change_reaches_front_doors_and_map",
    },
    {
        "id": "E02",
        "terminal_state": "RUNNER_BOUNDARY_FIXED",
        "kind": "unittest",
        "test_id": "tests.test_state_changelog.StateChangelogTests.test_broken_repository_link_is_rejected",
    },
    {
        "id": "E03",
        "terminal_state": "RUNNER_BOUNDARY_FIXED",
        "kind": "unittest",
        "test_id": "tests.test_state_changelog.StateChangelogTests.test_missing_required_field_is_rejected",
    },
    {
        "id": "F01",
        "terminal_state": "ENVIRONMENT_CONTRACT_FIXED",
        "kind": "unittest",
        "test_id": "foundation.test_foundation.FoundationTests.test_core_claims",
    },
    {
        "id": "F02",
        "terminal_state": "ENVIRONMENT_CONTRACT_FIXED",
        "kind": "unittest",
        "test_id": "foundation.test_foundation.FoundationTests.test_integrity_validator",
    },
    {
        "id": "F03",
        "terminal_state": "FIXED_CURRENT_DEFECT",
        "kind": "unittest",
        "test_id": "foundation.test_function_asset_closure.FunctionAssetClosureTests.test_closure_validator",
    },
    {
        "id": "F04",
        "terminal_state": "FIXED_CURRENT_DEFECT",
        "kind": "unittest",
        "test_id": "foundation.test_function_asset_closure.FunctionAssetClosureTests.test_generators_are_deterministic",
    },
    {
        "id": "F05",
        "terminal_state": "SEALED_RESIDUAL_ASSERTED",
        "kind": "unittest",
        "test_id": "foundation.test_generator_reconciliation_staleness.Task106ReconciliationStalenessTest.test_propagation_reconciliation_check",
    },
    {
        "id": "F06",
        "terminal_state": "SEALED_RESIDUAL_ASSERTED",
        "kind": "unittest",
        "test_id": "foundation.test_generator_reconciliation_staleness.Task106ReconciliationStalenessTest.test_propagation_reconciliation_unit",
    },
    {
        "id": "F07",
        "terminal_state": "FIXED_CURRENT_DEFECT",
        "kind": "unittest",
        "test_id": "foundation.test_repository_path_classification.PositiveTreeTest.test_current_tree_passes",
    },
    {
        "id": "F08",
        "terminal_state": "FIXED_CURRENT_DEFECT",
        "kind": "unittest",
        "test_id": "tests.test_durability_projection_hygiene.DurabilityProjectionHygieneTests.test_step17_projection_and_residual_gates_pass",
    },
    {
        "id": "F09",
        "terminal_state": "FIXED_STALE_TEST",
        "kind": "unittest",
        "test_id": "tests.test_overall_architecture.OverallArchitectureTest.test_conceptual_map_is_transparent_clickable_and_bounded",
    },
    {
        "id": "F10",
        "terminal_state": "ENVIRONMENT_CONTRACT_FIXED",
        "kind": "unittest",
        "test_id": "tests.test_production_execution_authority.ProductionProfileProbe.test_production_capability_contract_and_all_local_validators_run",
    },
    {
        "id": "F11",
        "terminal_state": "SEALED_RESIDUAL_ASSERTED",
        "kind": "unittest",
        "test_id": "tests.test_propagation_reconciliation.TestRemediatedRepository.test_run_check_clean",
    },
    {
        "id": "F12",
        "terminal_state": "FIXED_STALE_TEST",
        "kind": "unittest",
        "test_id": "tests.test_state_changelog.StateChangelogTests.test_current_log_is_valid",
    },
)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _status(root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=all"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in completed.stdout.splitlines() if line]


def _unittest_result(stdout: str, stderr: str, returncode: int) -> dict[str, Any]:
    parsed = runner.parse_unittest_result(stdout, stderr, returncode)
    return {
        "tests_run": parsed["tests_run"],
        "failures": parsed["failures"],
        "errors": parsed["errors"],
        "skipped": parsed["skipped"],
        "summary": parsed["summary"],
        "semantic_pass": (
            returncode == 0
            and parsed["status"] == "PASS"
            and parsed["tests_run"] is not None
            and parsed["failures"] == 0
            and parsed["errors"] == 0
            and parsed["skipped"] == 0
        ),
    }


def _run_target(target: dict[str, Any], python_executable: Path, env: dict[str, str]) -> dict[str, Any]:
    command = [str(python_executable), "-m", "unittest", target["test_id"], "-v"]
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=APP_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    elapsed = time.monotonic() - started
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    parsed = _unittest_result(stdout, stderr, completed.returncode)
    return {
        "id": target["id"],
        "test_id": target["test_id"],
        "terminal_state": target["terminal_state"],
        "command": command,
        "working_directory": "formal-repository/ignition",
        "returncode": completed.returncode,
        "runtime_seconds": round(elapsed, 3),
        "status": "PASS" if parsed["semantic_pass"] else "FAIL",
        "tests_run": parsed["tests_run"],
        "failures": parsed["failures"],
        "errors": parsed["errors"],
        "skipped": parsed["skipped"],
        "summary": parsed["summary"],
        "stdout_sha256": _sha256(stdout),
        "stderr_sha256": _sha256(stderr),
        "stdout_bytes": len(stdout.encode("utf-8", errors="replace")),
        "stderr_bytes": len(stderr.encode("utf-8", errors="replace")),
    }


def _inventory_ids() -> list[str]:
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    return [str(item["id"]) for item in inventory["entries"]]


def build_receipt() -> dict[str, Any]:
    before = _status(REPO_ROOT)
    execution_python, holder, environment_metadata = runner.provision_isolated_environment(
        requirements_path=APP_ROOT / "requirements-foundation.txt"
    )
    execution_identity = runner.interpreter_identity(execution_python)
    try:
        dependency_preflight = runner.dependency_preflight(
            requirements_path=APP_ROOT / "requirements-foundation.txt",
            python_executable=execution_python,
        )
        env = runner.canonical_environment(APP_ROOT, execution_python)
        results = []
        if dependency_preflight["status"] == "PASS":
            for target in TARGETS:
                results.append(_run_target(target, execution_python, env))
        else:
            results = [
                {
                    "id": target["id"],
                    "test_id": target["test_id"],
                    "terminal_state": "BLOCKED_WITH_EVIDENCE",
                    "command": [],
                    "working_directory": "formal-repository/ignition",
                    "returncode": 2,
                    "runtime_seconds": 0,
                    "status": "FAIL",
                    "tests_run": 0,
                    "failures": 0,
                    "errors": 0,
                    "skipped": 0,
                    "summary": "canonical dependency preflight failed",
                    "stdout_sha256": _sha256(""),
                    "stderr_sha256": _sha256(""),
                    "stdout_bytes": 0,
                    "stderr_bytes": 0,
                }
                for target in TARGETS
            ]
        after = _status(REPO_ROOT)
    finally:
        holder.cleanup()

    all_pass = (
        dependency_preflight["status"] == "PASS"
        and len(results) == len(TARGETS)
        and all(row["status"] == "PASS" for row in results)
        and before == after
    )
    return {
        "schema_version": "ignition-135-step09-task134-observation-closure-r1",
        "task_id": "IGNITION-20260822-135",
        "step": "09",
        "status": "PASS" if all_pass else "FAIL",
        "inventory_source": "ignition/data/operations/iterations/135/step00-failure-inventory.json",
        "inventory_ids": _inventory_ids(),
        "terminal_state_enum": sorted(TERMINAL_STATES),
        "forbidden_ambiguous_states": ["CLASSIFIED_AND_MOVE_ON"],
        "dependency_environment": {
            "metadata": environment_metadata,
            "interpreter": execution_identity,
            "preflight": dependency_preflight,
            "path_prepend_contract": "execution interpreter directory precedes inherited PATH so profile python3 validators reuse the canonical isolated environment",
        },
        "results": results,
        "closure": {
            "inventory_count": len(TARGETS),
            "closed_count": sum(row["status"] == "PASS" for row in results),
            "blocked_count": sum(row["terminal_state"] == "BLOCKED_WITH_EVIDENCE" for row in results),
            "current_failure_semantics_closed": all(row["status"] == "PASS" for row in results),
            "worktree_unchanged_by_targeted_runs": before == after,
        },
        "claim_ceiling": "Repository-local targeted closure of the exact Task134 long-run inventory; sealed residual passing means exact historical residual assertion, not historical repair or external truth. No full-suite PASS, production readiness, Owner acceptance or epistemic acceptance is inferred.",
    }


def _validate(receipt: dict[str, Any]) -> list[str]:
    errors = [error.message for error in Draft202012Validator(json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))).iter_errors(receipt)]
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()

    receipt = build_receipt()
    errors = _validate(receipt)
    if errors:
        receipt["schema_errors"] = errors
        print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True), file=sys.stderr)
        return 1
    if receipt["status"] != "PASS":
        print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True), file=sys.stderr)
        return 1
    if args.write:
        RECEIPT_PATH.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"STEP09_TASK134_OBSERVATIONS_WRITTEN entries={len(receipt['results'])} closed={receipt['closure']['closed_count']} path={RECEIPT_PATH.relative_to(REPO_ROOT)}")
    else:
        print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
