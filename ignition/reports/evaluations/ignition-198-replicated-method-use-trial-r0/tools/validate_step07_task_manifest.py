#!/usr/bin/env python3
"""Validate Task198's future-only six-slot Successor task manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "future-task-manifest.json"
OUTPUT_SCHEMA_PATH = "ignition/evaluation/heldout/r0.1/successor-visible/successor-output-r0.1.schema.json"
OUTPUT_SCHEMA_SHA256 = "fdf46bbe7f92dbc5a8340ad95381a0932b5b55f49f3c88f48f33c502a52c0133"


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

    control = data["shared_contracts"]["packet_manifest_control_metadata"]
    if control["read_class"] != "CONTROL_METADATA":
        fail("packet manifest control metadata is not separated from cognitive input")
    if control["purpose"] != [
        "VERIFY_PACKET_MANIFEST_FINAL_BYTES_AND_SHA256",
        "PARSE_EXACT_PACKET_READ_ALLOWLIST",
    ]:
        fail("packet manifest control purpose drifted")
    if control["self_listing"] != "PACKET_MANIFEST_IS_NOT_REQUIRED_TO_SELF_LIST_IN_ITS_OWN_CONTENT_HASH_ALLOWLIST":
        fail("packet self-listing rule drifted")
    if control["verification_exposure"] != "MANIFEST_VERIFICATION_DOES_NOT_EXPOSE_OTHER_CONDITION_OR_EVALUATOR_MATERIAL":
        fail("manifest verification exposure boundary drifted")
    if control["cognitive_input_reads"] != "ONLY_FROM_VERIFIED_PACKET_READ_ALLOWLIST":
        fail("cognitive input read boundary drifted")
    if control["command_level_extra_input"] != "PROHIBITED_AND_NOT_A_SUBSTITUTE_FOR_MISSING_PACKET_INPUT":
        fail("command-level extra input is not prohibited")
    if control["experimental_content_outside_packet"] != "PROHIBITED":
        fail("experimental content outside packet is not prohibited")
    schema_contract = control["actual_output_schema"]
    if schema_contract != {
        "path": OUTPUT_SCHEMA_PATH,
        "sha256": OUTPUT_SCHEMA_SHA256,
        "role": "output_schema",
        "future_successor_read": "ALLOWED_FROM_PACKET_ALLOWLIST",
    }:
        fail("actual output schema control contract drifted")

    expected = {
        "FACTS-A": ("FACTS_ONLY", "A", "facts-a", "c6d3c0a4c67c0c1ab28ea5b56da69526a3aef2b21ee53a3b4587e388a252ca1a"),
        "FACTS-B": ("FACTS_ONLY", "B", "facts-b", "3926b9b2085cd7930e26532f9b1f59e75437b8e8c684349922b5ed372d876891"),
        "METHOD-A": ("METHOD_TRACE", "A", "method-a", "65822249c3b008426f69ec12f61a4d5c703d436ed64abf2c199c661f5a57251a"),
        "METHOD-B": ("METHOD_TRACE", "B", "method-b", "3f1b6a4fc0eb39393c775210da83de4b5a39a02b572ae171ce028772b8a98ca0"),
        "BROKEN-A": ("BROKEN_METHOD_TRACE_CONTROL", "A", "broken-a", "44b001c0da14f2c5fcb9f237a381dc17aa402b7fe76cee864a61782fbbd9d2af"),
        "BROKEN-B": ("BROKEN_METHOD_TRACE_CONTROL", "B", "broken-b", "e3384e79faabe03b44a274775c9ca3a42c3e59badc44a441eaf932600f78fe05"),
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
        schema_rows = [row for row in packet_data["read_allowlist"] if row["role"] == "output_schema"]
        if schema_rows != [{"path": OUTPUT_SCHEMA_PATH, "sha256": OUTPUT_SCHEMA_SHA256, "role": "output_schema"}]:
            fail(f"actual output schema allowlist row mismatch for {suffix}")
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
