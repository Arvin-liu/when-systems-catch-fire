#!/usr/bin/env python3
"""Fail-closed release admission gate for canonical full regression evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
PROTOCOL_PATH = ROOT / "data/operations/release-transaction-protocol-r2.json"
PROTOCOL_SCHEMA_PATH = ROOT / "schemas/operations/release-transaction-protocol-r2.schema.json"
R2_PATH = ROOT / "data/operations/iterations/135/step13-residual-ledger-r2.json"
CANDIDATE_RECEIPT_PATH = ROOT / "data/operations/iterations/135/step10-candidate-full-regression-2.json"
INVENTORY_RECEIPT_PATH = ROOT / "data/operations/iterations/135/step11-full-suite-determinism-side-effect-audit.json"
FRESH_RECEIPT_PATH = ROOT / "data/operations/iterations/135/step12-fresh-clone-full-regression.json"

EXPECTED_HARD_GATES = [
    "deterministic_projection_preflight",
    "current_path_manifest_exact",
    "residual_non_growth",
    "current_semantic_gates",
    "canonical_full_suite",
    "exact_candidate_sha_binding",
    "no_post_suite_tracked_mutation",
    "task_ordinal_binding",
]
EXPECTED_TEST_ID_SHA256 = "28fbc92c4a3c93b1add49e46286b97569e170c9c1cad24278d4a14f60407b3a8"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()


def is_ancestor(ancestor: str, descendant: str) -> bool:
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=REPO_ROOT,
        check=False,
    ).returncode == 0


def validate() -> list[str]:
    errors: list[str] = []
    protocol = load(PROTOCOL_PATH)
    schema_errors = sorted(
        Draft202012Validator(load(PROTOCOL_SCHEMA_PATH)).iter_errors(protocol),
        key=lambda error: list(error.path),
    )
    errors.extend(error.json_path + ": " + error.message for error in schema_errors)
    hard_gates = protocol.get("pre_publication_hard_gates", {})
    if hard_gates.get("required_gate_ids") != EXPECTED_HARD_GATES:
        errors.append("HARD_GATE_SET_MISMATCH")
    if hard_gates.get("fail_closed") is not True:
        errors.append("HARD_GATE_NOT_FAIL_CLOSED")

    candidate = load(CANDIDATE_RECEIPT_PATH)
    inventory_receipt = load(INVENTORY_RECEIPT_PATH)
    fresh = load(FRESH_RECEIPT_PATH)
    r2 = load(R2_PATH)
    for label, receipt in (("candidate", candidate), ("fresh_clone", fresh)):
        if receipt.get("status") != "PASS":
            errors.append(f"{label}:FULL_SUITE_NOT_PASS")
        suite = receipt.get("result") or receipt.get("full_suite") or {}
        if suite.get("failures") != 0 or suite.get("errors") != 0 or suite.get("skipped") != 0:
            errors.append(f"{label}:FAILURES_ERRORS_OR_SKIPS_PRESENT")
        natural = receipt.get("long_window") or receipt.get("full_suite", {}).get("natural_window", {})
        if natural.get("natural_terminal_state") is False or natural.get("process_completed_naturally") is False:
            errors.append(f"{label}:NON_NATURAL_TERMINAL_STATE")
        if natural.get("process_killed") is True or natural.get("watchdog_used") is True:
            errors.append(f"{label}:WATCHDOG_OR_KILL_USED")
        minimum = natural.get("minimum_window_seconds") or natural.get("minimum_supported_seconds")
        if minimum != 14400:
            errors.append(f"{label}:NATURAL_WINDOW_CONTRACT_MISMATCH")
        side_effect = receipt.get("side_effect_observation", {})
        if side_effect.get("clean_before") is not True or side_effect.get("clean_after") is not True:
            errors.append(f"{label}:WORKTREE_NOT_CLEAN_BEFORE_AFTER")
        if side_effect.get("generated_output_drift") != [] or side_effect.get("tracked_mutations") != []:
            errors.append(f"{label}:POST_SUITE_MUTATION_OR_DRIFT")
        laundering = receipt.get("prohibited_green_laundering", {})
        if any(laundering.get(key) is not False for key in ("skip_added", "xfail_added", "expected_failure_added", "ignore_added", "residual_expanded")):
            errors.append(f"{label}:GREEN_LAUNDERING_MARKER")

    candidate_sha = candidate.get("candidate_head_sha")
    fresh_sha = fresh.get("candidate_head_sha")
    if not candidate_sha or not fresh_sha:
        errors.append("EXACT_CANDIDATE_SHA_MISSING")
    else:
        if fresh.get("fresh_clone", {}).get("head_sha") != fresh_sha:
            errors.append("FRESH_CLONE_HEAD_SHA_MISMATCH")
        if fresh.get("fresh_clone", {}).get("source_remote_sha") != fresh_sha:
            errors.append("FRESH_CLONE_SOURCE_REMOTE_SHA_MISMATCH")
        if not is_ancestor(candidate_sha, fresh_sha):
            errors.append("CANDIDATE_SUITE_SHA_NOT_ANCESTOR_OF_FRESH_SUITE_SHA")
        current_head = git("rev-parse", "HEAD")
        if not is_ancestor(fresh_sha, current_head):
            errors.append("TESTED_CANDIDATE_NOT_IN_CURRENT_LINEAGE")

    candidate_inventory = inventory_receipt.get("discovery_inventory", {})
    fresh_inventory = fresh.get("discovery_inventory", {})
    if candidate_inventory.get("test_case_count") != 1082 or fresh_inventory.get("test_case_count") != 1082:
        errors.append("TEST_INVENTORY_COUNT_MISMATCH")
    if candidate_inventory.get("test_id_sha256") != EXPECTED_TEST_ID_SHA256:
        errors.append("CANDIDATE_TEST_ID_INVENTORY_MISMATCH")
    if fresh_inventory.get("test_id_sha256") != EXPECTED_TEST_ID_SHA256:
        errors.append("FRESH_TEST_ID_INVENTORY_MISMATCH")
    if r2.get("summary", {}).get("current_failure_count") != 0:
        errors.append("R2_CURRENT_FAILURE_PRESENT")
    if r2.get("summary", {}).get("environment_blocker_count") != 0:
        errors.append("R2_ENVIRONMENT_BLOCKER_PRESENT")
    if r2.get("summary", {}).get("residual_non_growth") != "PASS":
        errors.append("R2_RESIDUAL_NON_GROWTH_NOT_PASS")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("FULL_REGRESSION_RELEASE_GATE_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("FULL_REGRESSION_RELEASE_GATE_OK candidate_suite=PASS fresh_clone_suite=PASS tests=1082 failures=0 errors=0 skips=0 residual_current_failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
