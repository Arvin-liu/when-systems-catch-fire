#!/usr/bin/env python3
"""Fail-closed validation for Task150 Step04 viewport residual evidence."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
ARTIFACT_PATH = ROOT / "data/operations/iterations/150/step04-viewport-residual-repair.json"
SCHEMA_PATH = ROOT / "schemas/operations/task150-step04-viewport-residual-repair-r1.schema.json"
CANONICAL_PATH = ROOT / "data/architecture/overall-architecture.json"
ADAPTER_PATH = ROOT / "tools/run_task150_bounded_visualization_adapter.py"
IR_PATH = ROOT / "data/operations/iterations/150/task150-archify-typed-ir-r1.json"

EXPECTED_PREVIOUS_COMMIT = "658e8aeffa37a4286ad62a0debb49f7bd52b1ba7"
# Step04 is a historical blocker receipt.  The typed IR was subsequently
# refreshed by Step21, so validate this receipt against the exact Step04
# publication tree instead of the later working-tree bytes.
STEP04_PUBLISHED_COMMIT = "e6d29c57ea54817bdebc39f0d83e5c362e6caf46"
EXPECTED_SOURCE_SHA = "251df5de786c53374e3bf0488d90a95983a47e452860f15922d9432ed6f17f13"
EXPECTED_SOURCE_REVISION = "d7372c27abe456b5b8c058675630d8038f91b448"
EXPECTED_ADAPTER_SHA = "20f45aafe13ac43328f02627ecf3f49f74fe60cf24f0c907c1b315025760603e"
EXPECTED_IR_SHA = "02ee0e727af237b778fd0b88fbdb2a42eca0395b8eaed8d731636b3e4bb7b3c3"
EXPECTED_INVARIANTS = (
    "EXTERNAL_PROVIDER ≠ IGNITION_AUTHORITY",
    "PROVIDER_CAPABILITY ≠ PERMISSION",
    "PROVIDER_OUTPUT ≠ EXTERNAL_TRUTH",
    "PROVIDER_LOCAL_POLICY ≠ IGNITION_GLOBAL_POLICY",
    "ADAPTER_SPIKE_PASS ≠ CURRENT_CAPABILITY",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_bytes(commit: str, relative_path: str) -> bytes:
    return subprocess.check_output(
        ["git", "show", f"{commit}:{relative_path}"],
        cwd=REPO_ROOT,
        stderr=subprocess.DEVNULL,
    )


def git_json(commit: str, relative_path: str) -> Any:
    return json.loads(git_bytes(commit, relative_path).decode("utf-8"))


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [
        error.json_path + ": " + error.message
        for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)
    ]
    if errors:
        return errors

    if document["formal_previous_commit"] != EXPECTED_PREVIOUS_COMMIT:
        errors.append("Step04 must bind the published Step03 formal commit")
    canonical_relative = "ignition/data/architecture/overall-architecture.json"
    adapter_relative = "ignition/tools/run_task150_bounded_visualization_adapter.py"
    ir_relative = "ignition/data/operations/iterations/150/task150-archify-typed-ir-r1.json"
    if hashlib.sha256(git_bytes(STEP04_PUBLISHED_COMMIT, canonical_relative)).hexdigest() != EXPECTED_SOURCE_SHA:
        errors.append("canonical architecture source hash drifted")
    if hashlib.sha256(git_bytes(STEP04_PUBLISHED_COMMIT, adapter_relative)).hexdigest() != EXPECTED_ADAPTER_SHA:
        errors.append("Task150 bounded adapter hash drifted")
    if hashlib.sha256(git_bytes(STEP04_PUBLISHED_COMMIT, ir_relative)).hexdigest() != EXPECTED_IR_SHA:
        errors.append("Task150 typed IR hash drifted")

    source = document["canonical_source"]
    if source["sha256"] != EXPECTED_SOURCE_SHA or source["source_revision"] != EXPECTED_SOURCE_REVISION:
        errors.append("canonical source identity or revision drifted")
    if source["node_count"] != 24 or source["edge_count"] != 24:
        errors.append("canonical topology cardinality drifted")

    candidate = git_json(STEP04_PUBLISHED_COMMIT, ir_relative)
    if candidate["meta"]["repository"]["revision"] != EXPECTED_SOURCE_REVISION:
        errors.append("derived IR is not bound to the current formal source revision")
    if candidate["meta"]["viewBox"] != [1650, 420]:
        errors.append("derived IR viewBox is not the recorded bounded geometry")
    if any(component["size"] != [190, 28] for component in candidate["components"]):
        errors.append("derived IR component geometry drifted")
    architecture = git_json(STEP04_PUBLISHED_COMMIT, canonical_relative)
    expected_nodes = [node["id"] for node in architecture["nodes"]]
    expected_edges = [f"canonical-edge-{index:02d}" for index, _ in enumerate(architecture["edges"], start=1)]
    if [component["id"] for component in candidate["components"]] != expected_nodes:
        errors.append("derived node identity/order changed")
    if [connection["id"] for connection in candidate["connections"]] != expected_edges:
        errors.append("derived edge identity/order changed")
    actual_endpoints = [(connection["from"], connection["to"]) for connection in candidate["connections"]]
    source_endpoints = [(edge["source"], edge["target"]) for edge in architecture["edges"]]
    if actual_endpoints != source_endpoints or len(actual_endpoints) != 24:
        errors.append("derived edge endpoint relations changed")

    baseline = document["baseline_reproduction"]["visual_check"]["residuals"]
    if len(baseline) != 6 or document["baseline_reproduction"]["visual_check"]["diagnostics"] != 6:
        errors.append("baseline must retain all six Task149 viewport residuals")
    repaired = document["repair_validation"]["delta_visual_check"]["observations"]
    if len(repaired) != 6:
        errors.append("Step04 must report all six required light/dark viewport observations")
    if document["repair_validation"]["delta_visual_check"]["status"] != "FAIL_UPSTREAM_WRAPPER":
        errors.append("Delta wrapper residual must remain fail-closed")
    if document["repair_validation"]["standalone_visual_check"]["status"] != "PASS":
        errors.append("standalone authored-geometry validation must pass")
    if document["repair_validation"]["delta_compare"]["semantic_checks"] != {"total": 28, "passed": 28}:
        errors.append("Delta semantic comparison must remain 28/28")
    if document["upstream_blocker"]["confirmed"] is not True:
        errors.append("the fixed upstream Delta-shell blocker must be confirmed")
    if document["scope_freeze"]["current_admission"] != "NOT_ADMITTED":
        errors.append("Step04 cannot admit a Current capability")
    if document["scope_freeze"]["authenticated_channels"] != "NO_AUTHENTICATED_ADMISSION":
        errors.append("authenticated admission changed")
    if document["scope_freeze"]["live_external_invocation"] != "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN":
        errors.append("live external invocation changed")
    if document["scope_freeze"]["agent_reach"] != "NO_CHANGE":
        errors.append("Agent Reach scope changed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate()
    if errors:
        print("TASK150_STEP04_VIEWPORT_RESIDUAL_REPAIR_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    document = load_json(ARTIFACT_PATH)
    observation = document["repair_validation"]["delta_visual_check"]
    print(
        "TASK150_STEP04_VIEWPORT_RESIDUAL_REPAIR_UPSTREAM_BLOCKER_RECORDED "
        f"standalone=PASS delta_semantic=28/28 delta_visual={observation['status']} "
        f"diagnostics={observation['diagnostics']} current={document['scope_freeze']['current_admission']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
