#!/usr/bin/env python3
"""Run the declared negative-fixture audit without laundering rejection as error.

Every target below is an ordinary unittest target.  The fixture itself is
expected to be rejected by a validator, diagnostic list, typed exception, or
non-zero CLI result; the unittest process must still terminate with zero
failures, zero errors, and zero skips.  The target tests contain the exact
assertions for their declared rejection mode.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve()
APP_ROOT = HERE.parents[1]
REPO_ROOT = APP_ROOT.parent
RECEIPT_PATH = APP_ROOT / "data/operations/iterations/135/step08-negative-fixture-semantics.json"

RAN_RE = re.compile(r"Ran\s+(\d+)\s+tests?\s+in\s+([0-9.]+)s")
FAILURE_RE = re.compile(r"failures=(\d+)")
ERROR_RE = re.compile(r"errors=(\d+)")
SKIP_RE = re.compile(r"skipped=(\d+)")


TARGETS: tuple[dict[str, Any], ...] = (
    {
        "case_id": "state-changelog",
        "semantic_kind": "validator_diagnostics",
        "tests": ("tests.test_state_changelog.StateChangelogTests",),
        "assertion_contract": "mutated source is passed to validate(path) and expected diagnostics are asserted; sealed legacy PASS remains explicit",
    },
    {
        "case_id": "sealed-propagation-residual",
        "semantic_kind": "validator_diagnostics",
        "tests": ("tests.test_propagation_reconciliation.TestSealedResidualContract",),
        "assertion_contract": "exact residual PASS and added/removed/mutated fixture cases fail closed inside unittest",
    },
    {
        "case_id": "current-surface-semantic",
        "semantic_kind": "validator_diagnostics",
        "tests": ("tests.test_current_surface_semantics.CurrentSurfaceSemanticGateTests.test_ten_negative_fixtures_fail_closed",),
        "assertion_contract": "each fixture must produce a non-empty validator issue list",
    },
    {
        "case_id": "derived-architecture-projection",
        "semantic_kind": "caught_typed_rejection",
        "tests": ("tests.test_overall_architecture.OverallArchitectureTest.test_unsynchronized_projection_fixture_fails_closed",),
        "assertion_contract": "stale projection rejection is caught by assertRaises and does not escape the test method",
    },
    {
        "case_id": "projection-preflight-gate",
        "semantic_kind": "structured_gate_result",
        "tests": ("tests.test_projection_preflight.ProjectionPreflightTests.test_stale_fixture_cannot_enter_release_gate",),
        "assertion_contract": "stale fixture produces structured gate failure and release_admission=false",
    },
    {
        "case_id": "stage-snapshot-contract",
        "semantic_kind": "caught_typed_rejection_and_schema_diagnostics",
        "tests": ("tests.test_stage_snapshot_publication.StageSnapshotPublicationTests",),
        "assertion_contract": "negative registry/request fixtures assert schema diagnostics or caught ContractError",
    },
    {
        "case_id": "generated-output-authority",
        "semantic_kind": "nonzero_cli_result",
        "tests": ("tests.test_generated_output_authority_negative.GeneratedOutputAuthorityNegativeTests",),
        "assertion_contract": "validator subprocess uses check=False and asserts non-zero return plus stable rejection text",
    },
    {
        "case_id": "incremental-execution-validator",
        "semantic_kind": "structured_validator_result_and_nonzero_cli_result",
        "tests": ("tests.test_incremental_execution_validator.UnifiedIncrementalValidatorAcceptance",),
        "assertion_contract": "mutated plans assert structured error codes; CLI rejection uses check=False and parses JSON",
    },
    {
        "case_id": "path-classification",
        "semantic_kind": "validator_return_code_and_diagnostics",
        "tests": ("foundation.test_repository_path_classification.NegativeClassificationTest",),
        "assertion_contract": "injected path violations assert validator return code 1 and expected diagnostic text",
    },
    {
        "case_id": "publication-gate",
        "semantic_kind": "structured_gate_result",
        "tests": ("tests.test_publication_gate_fail_closed.PublicationGateFailClosedTests",),
        "assertion_contract": "forged decisions assert success=false and the intended error dimension",
    },
    {
        "case_id": "phase-d-cli-rejection",
        "semantic_kind": "nonzero_cli_result",
        "tests": ("tests.test_phase_d_closeout.PhaseD4CloseoutValidation.test_d4_20_cli_check_success_and_stable_failure",),
        "assertion_contract": "forged report is run with check=False and its structured error code is asserted",
    },
)


def _environment() -> dict[str, str]:
    environment = os.environ.copy()
    inherited = environment.get("PYTHONPATH")
    # The ordinary discovery command adds ``tests/`` as a top-level import
    # root, so the foundation namespace must be available for explicit class
    # targets too. Keep the application root first for the formal packages.
    entries = [str(APP_ROOT), str(APP_ROOT / "tests")]
    if inherited:
        entries.extend(item for item in inherited.split(os.pathsep) if item)
    environment["PYTHONPATH"] = os.pathsep.join(entries)
    return environment


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def _parse_result(stdout: str, stderr: str, returncode: int) -> dict[str, Any]:
    combined = "\n".join(part for part in (stdout, stderr) if part)
    matches = list(RAN_RE.finditer(combined))
    ran = matches[-1] if matches else None
    summary_lines = [line.strip() for line in combined.splitlines() if line.strip()]
    summary = summary_lines[-1] if summary_lines else ""
    failures_match = FAILURE_RE.search(summary)
    errors_match = ERROR_RE.search(summary)
    skips_match = SKIP_RE.search(summary)
    failures = int(failures_match.group(1)) if failures_match else 0
    errors = int(errors_match.group(1)) if errors_match else 0
    skipped = int(skips_match.group(1)) if skips_match else 0
    tests_run = int(ran.group(1)) if ran else None
    runtime = float(ran.group(2)) if ran else None
    passed = returncode == 0 and tests_run is not None and failures == errors == skipped == 0 and "OK" in summary
    return {
        "returncode": returncode,
        "tests_run": tests_run,
        "runtime_seconds": runtime,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
        "summary": summary,
        "status": "PASS" if passed else "FAIL",
        "stdout_sha256": _sha256(stdout),
        "stderr_sha256": _sha256(stderr),
        "stdout_bytes": len(stdout.encode("utf-8", errors="replace")),
        "stderr_bytes": len(stderr.encode("utf-8", errors="replace")),
    }


def run_audit() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for target in TARGETS:
        completed = subprocess.run(
            [sys.executable, "-m", "unittest", *target["tests"]],
            cwd=APP_ROOT,
            env=_environment(),
            check=False,
            capture_output=True,
            text=True,
        )
        row = {
            "case_id": target["case_id"],
            "semantic_kind": target["semantic_kind"],
            "tests": list(target["tests"]),
            "assertion_contract": target["assertion_contract"],
            **_parse_result(completed.stdout, completed.stderr, completed.returncode),
        }
        rows.append(row)
    failed = [row["case_id"] for row in rows if row["status"] != "PASS"]
    return {
        "schema_version": "ignition-135-step08-negative-fixture-semantics-r1",
        "task_id": "IGNITION-20260822-135",
        "step": "08",
        "status": "PASS" if not failed else "FAIL",
        "contract": {
            "fixture_rejection_is_asserted_inside_test": True,
            "uncaught_fixture_exception_is_not_an_expected_result": True,
            "negative_fixture_unittest_failures_allowed": 0,
            "negative_fixture_unittest_errors_allowed": 0,
            "negative_fixture_unittest_skips_allowed": 0,
            "subprocess_negative_cli_policy": "check=False plus explicit returncode and structured output assertions",
        },
        "targets": rows,
        "target_count": len(rows),
        "tests_run": sum(row["tests_run"] or 0 for row in rows),
        "failed_targets": failed,
        "claim_ceiling": "Repository-local targeted negative-fixture semantics only; no whole-project full-suite PASS, external truth, production readiness, Owner acceptance or epistemic acceptance is inferred.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    report = run_audit()
    if args.write:
        RECEIPT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"NEGATIVE_FIXTURE_SEMANTICS_WRITTEN targets={report['target_count']} tests={report['tests_run']} status={report['status']}")
    else:
        print(f"NEGATIVE_FIXTURE_SEMANTICS_{report['status']} targets={report['target_count']} tests={report['tests_run']}")
    if report["status"] != "PASS":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), file=sys.stderr)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
