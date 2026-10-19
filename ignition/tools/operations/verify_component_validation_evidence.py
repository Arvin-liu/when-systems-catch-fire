#!/usr/bin/env python3
"""Verify that a selected-test receipt is complete and bound to its plan."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.operations.route_component_validation import (  # noqa: E402
    MAP_PATH,
    RoutingBlocked,
    digest_json,
    load_json,
)

SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")


def _fail(message: str) -> None:
    raise RoutingBlocked(message)


def verify_evidence(
    plan: dict[str, Any], receipt: dict[str, Any], *, expected_validation_sha: str,
    expected_mode: str, validation_map: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fail closed unless every declared target has complete successful evidence."""
    if not SHA40.fullmatch(expected_validation_sha):
        _fail("expected validation SHA must be an exact lowercase commit SHA")
    if expected_mode not in {"TARGETED", "FULL"}:
        _fail(f"unexpected validation mode: {expected_mode!r}")
    if plan.get("schema_version") != "1.0.0" or plan.get("mode") != expected_mode:
        _fail("plan schema version or mode does not match the workflow result")

    plan_hash = plan.get("plan_sha256")
    plan_body = dict(plan)
    plan_body.pop("plan_sha256", None)
    if not isinstance(plan_hash, str) or not SHA64.fullmatch(plan_hash) or digest_json(plan_body) != plan_hash:
        _fail("plan digest is missing or invalid")

    source = plan.get("source")
    if not isinstance(source, dict):
        _fail("plan has no exact Git source binding")
    base_sha, head_sha = source.get("base_sha"), source.get("head_sha")
    if not all(isinstance(value, str) and SHA40.fullmatch(value) for value in (base_sha, head_sha)):
        _fail("plan base/head SHA is malformed")
    if source.get("validation_sha") != expected_validation_sha:
        _fail("plan validation SHA does not match the exact workflow commit")

    validation_map = validation_map or load_json(MAP_PATH)
    targets = {item["target_id"]: item for item in validation_map["targets"]}
    expected_map_hash = digest_json(validation_map)
    if plan.get("validation_map_sha256") != expected_map_hash:
        _fail("plan validation-map digest does not match the checked-out map")
    selected = plan.get("selected_target_ids")
    if not isinstance(selected, list) or not selected or any(not isinstance(item, str) for item in selected):
        _fail("plan selected-target list is empty or malformed")
    if len(selected) != len(set(selected)) or any(item not in targets for item in selected):
        _fail("plan selected-target list contains duplicate or undeclared target IDs")

    receipt_hash = receipt.get("receipt_sha256")
    receipt_body = dict(receipt)
    receipt_body.pop("receipt_sha256", None)
    if not isinstance(receipt_hash, str) or not SHA64.fullmatch(receipt_hash) or digest_json(receipt_body) != receipt_hash:
        _fail("receipt digest is missing or invalid")
    if receipt.get("schema_version") != "1.0.0":
        _fail("unsupported receipt schema version")
    for key, expected in (
        ("base_sha", base_sha),
        ("head_sha", head_sha),
        ("validation_sha", expected_validation_sha),
        ("plan_sha256", plan_hash),
        ("validation_map_sha256", expected_map_hash),
    ):
        if receipt.get(key) != expected:
            _fail(f"receipt {key} does not match its plan or exact validation commit")

    result_docs = receipt.get("target_results")
    if not isinstance(result_docs, list):
        _fail("receipt has no target result list")
    result_ids = [item.get("target_id") if isinstance(item, dict) else None for item in result_docs]
    if result_ids != selected:
        _fail("receipt target IDs do not exactly match the plan target IDs")

    for result, target_id in zip(result_docs, selected):
        target = targets[target_id]
        if result.get("domain") != target["domain"] or result.get("successful") is not True:
            _fail(f"target {target_id} is failed or has a mismatched domain")
        tests = result.get("tests")
        if not isinstance(tests, dict):
            _fail(f"target {target_id} has no test evidence")
        test_count = tests.get("tests_run")
        outcomes = tests.get("test_outcomes")
        modules = target["modules"]
        report = tests.get("test_report")
        if not isinstance(report, str):
            _fail(f"target {target_id} has no auditable test report")
        report_bytes = report.encode("utf-8")
        report_lines = report.rstrip().splitlines()
        if (
            not isinstance(test_count, int) or isinstance(test_count, bool) or test_count <= 0
            or tests.get("modules") != modules
            or tests.get("tests_executed") != test_count
            or tests.get("skipped") != 0
            or tests.get("failures") != 0
            or tests.get("errors") != 0
            or tests.get("expected_failures") != []
            or tests.get("unexpected_successes") != []
            or tests.get("successful") is not True
            or tests.get("status") != "PASSED"
            or not isinstance(outcomes, list)
            or len(outcomes) != test_count
            or any(not isinstance(item, dict) or item.get("status") != "passed" for item in outcomes)
            or any(
                not isinstance(item.get("test"), str)
                or not any(item["test"].startswith(module + ".") for module in modules)
                for item in outcomes
            )
            or any(item["test"] not in report for item in outcomes)
            or not any(line.startswith(f"Ran {test_count} test") for line in report_lines)
            or not report_lines
            or report_lines[-1] != "OK"
            or len({item["test"] for item in outcomes if isinstance(item, dict) and isinstance(item.get("test"), str)}) != len(outcomes)
            or tests.get("test_report_sha256") != hashlib.sha256(report_bytes).hexdigest()
            or tests.get("test_report_bytes") != len(report_bytes)
            or not isinstance(tests.get("test_report_sha256"), str)
            or not SHA64.fullmatch(tests["test_report_sha256"])
            or not isinstance(tests.get("test_report_bytes"), int)
            or isinstance(tests.get("test_report_bytes"), bool)
            or tests["test_report_bytes"] <= 0
        ):
            _fail(f"target {target_id} test results are incomplete, skipped, or unsuccessful")

        expected_commands = target.get("command_ids", [])
        command_docs = result.get("commands")
        if not isinstance(command_docs, list) or [item.get("command_id") for item in command_docs] != expected_commands:
            _fail(f"target {target_id} command results do not match the registered commands")
        for command in command_docs:
            if (
                command.get("exit_code") != 0
                or not isinstance(command.get("stdout_sha256"), str)
                or not SHA64.fullmatch(command["stdout_sha256"])
                or not isinstance(command.get("stderr_sha256"), str)
                or not SHA64.fullmatch(command["stderr_sha256"])
                or not isinstance(command.get("stdout_bytes"), int)
                or isinstance(command.get("stdout_bytes"), bool)
                or command["stdout_bytes"] < 0
                or not isinstance(command.get("stderr_bytes"), int)
                or isinstance(command.get("stderr_bytes"), bool)
                or command["stderr_bytes"] < 0
            ):
                _fail(f"target {target_id} has a failed or incomplete command result")

    return {
        "validation_sha": expected_validation_sha,
        "mode": expected_mode,
        "plan_sha256": plan_hash,
        "receipt_sha256": receipt_hash,
        "validation_map_sha256": expected_map_hash,
        "selected_target_ids": selected,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--expected-validation-sha", required=True)
    parser.add_argument("--expected-mode", required=True)
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
        summary = verify_evidence(
            plan, receipt,
            expected_validation_sha=args.expected_validation_sha,
            expected_mode=args.expected_mode,
        )
    except (OSError, json.JSONDecodeError, KeyError, TypeError, RoutingBlocked, ValueError) as exc:
        print(f"component validation evidence rejected: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
