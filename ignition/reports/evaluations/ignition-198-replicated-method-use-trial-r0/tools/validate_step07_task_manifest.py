#!/usr/bin/env python3
"""Validate Task198's future-only six-slot Successor task manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "future-task-manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str) -> None:
    raise SystemExit(f"TASK198_STEP07_INVALID: {message}")


def main() -> None:
    data = json.loads(MANIFEST.read_text())
    if data["artifact_type"] != "FUTURE_SUCCESSOR_TASK_MANIFEST":
        fail("wrong artifact type")
    if data["source_commit"] != "76bb9b566bffc8fd92e6a84026a336bd96d8a534":
        fail("wrong Task197 source commit")
    if data["status"] != "FROZEN_NOT_RUN":
        fail("manifest is not frozen")

    policy = data["future_execution_policy"]
    forbidden_true = [
        "write_to_1111",
        "run_successor_now",
        "run_evaluator_now",
        "cross_model_trial",
        "canonical_promotion",
        "metarsi_or_model_rsi",
        "weight_training",
        "future_successor_commit_or_push",
        "future_successor_external_search",
    ]
    if any(policy[key] for key in forbidden_true):
        fail("forbidden future execution policy is enabled")
    if not policy["owner_gpt_authorization_required"]:
        fail("Owner/GPT authorization is not required")
    if not policy["future_task_manifest_is_not_execution_authority"]:
        fail("manifest incorrectly grants execution authority")

    expected = {
        "FACTS-A": ("FACTS_ONLY", "A", "facts-a", "b98cf2b4b321235a887865a5697fc8e5e402d4764b620550f50ddec223caa164"),
        "FACTS-B": ("FACTS_ONLY", "B", "facts-b", "a7f7dfe5a8702fa7c2f5e0ade04d7306735379d5a4fa37cecf8fdaf05fbf9e93"),
        "METHOD-A": ("METHOD_TRACE", "A", "method-a", "cd9596898e526a27bf0ef7779036e017baaf25f25c821a43a75e7c3cb23f3ac1"),
        "METHOD-B": ("METHOD_TRACE", "B", "method-b", "2b417095f663101070fd1da1dd1f9f6b54ed002a221490c914bc513956d6b11a"),
        "BROKEN-A": ("BROKEN_METHOD_TRACE_CONTROL", "A", "broken-a", "e1a89ae7d9f9da26a377ae0691e622ed3509c408e2d52f4284318f12f53d9b23"),
        "BROKEN-B": ("BROKEN_METHOD_TRACE_CONTROL", "B", "broken-b", "24b6680f360fe0112fda3c9ffc1fd6204aa3244cef002e548db4c52363d506cf"),
    }
    tasks = data["tasks"]
    if len(tasks) != 6:
        fail("task count is not six")
    seen = set()
    for task in tasks:
        suffix = task["task_id"].removeprefix("IGNITION-20260921-198-")
        if suffix not in expected:
            fail(f"unexpected task id {task['task_id']}")
        if suffix in seen:
            fail(f"duplicate task id {suffix}")
        seen.add(suffix)
        condition, replicate, packet_dir, packet_sha = expected[suffix]
        if task["condition"] != condition or task["replicate"] != replicate:
            fail(f"condition/replicate mismatch for {suffix}")
        if task["status"] != "NOT_RUN":
            fail(f"task {suffix} is not NOT_RUN")
        if task["allowed_reads"] != "EXACT_PACKET_MANIFEST_READ_ALLOWLIST":
            fail(f"task {suffix} does not use exact packet allowlist")
        packet = task["packet_manifest"]
        expected_path = f"ignition/reports/evaluations/ignition-198-replicated-method-use-trial-r0/packets/{packet_dir}/packet-manifest.json"
        if packet["path"] != expected_path or packet["sha256"] != packet_sha:
            fail(f"packet manifest reference mismatch for {suffix}")
        packet_path = Path(__file__).resolve().parents[5] / packet["path"]
        if not packet_path.is_file() or sha256(packet_path) != packet["sha256"]:
            fail(f"packet manifest final-byte hash mismatch for {suffix}")
        packet_data = json.loads(packet_path.read_text())
        if packet_data["condition"] != condition or packet_data["replicate"] != replicate:
            fail(f"packet condition/replicate mismatch for {suffix}")
        if packet_data["case_order"] != task["case_order"]:
            fail(f"case order mismatch for {suffix}")
        if task["normal_terminal_state"] != "SUCCESSOR_TRIAL_LOCAL_ONLY_COMPLETE":
            fail(f"wrong future terminal state for {suffix}")
        if "criteria" in task["output_directory"].lower():
            fail(f"criteria path used as output for {suffix}")

    if seen != set(expected):
        fail("not all six task slots are present")
    orders = {tuple(task["case_order"]) for task in tasks}
    if len(orders) != 2:
        fail("A/B case orders are not exactly two distinct orders")
    a_orders = {tuple(task["case_order"]) for task in tasks if task["replicate"] == "A"}
    b_orders = {tuple(task["case_order"]) for task in tasks if task["replicate"] == "B"}
    if a_orders == b_orders:
        fail("A/B order distinction is not frozen")

    print("TASK198_STEP07_FUTURE_TASK_MANIFEST_VALID")


if __name__ == "__main__":
    main()
