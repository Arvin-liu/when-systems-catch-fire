#!/usr/bin/env python3
"""Fail-closed validation for Task150 Step06 Current architecture smoke."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
ARTIFACT_PATH = ROOT / "data/operations/iterations/150/step06-current-architecture-smoke.json"
SCHEMA_PATH = ROOT / "schemas/operations/task150-step06-current-architecture-smoke-r1.schema.json"
CANONICAL_PATH = ROOT / "data/architecture/overall-architecture.json"
ADAPTER_PATH = ROOT / "tools/run_task150_bounded_visualization_adapter.py"
IR_PATH = ROOT / "data/operations/iterations/150/task150-archify-typed-ir-r1.json"
HTML_PATH = ROOT / "data/operations/iterations/150/derived-artifacts/task150-current-architecture.html"
SVG_PATH = ROOT / "data/operations/iterations/150/derived-artifacts/task150-current-architecture.svg"

EXPECTED_CANONICAL_SHA = "251df5de786c53374e3bf0488d90a95983a47e452860f15922d9432ed6f17f13"
EXPECTED_ADAPTER_SHA = "20f45aafe13ac43328f02627ecf3f49f74fe60cf24f0c907c1b315025760603e"
EXPECTED_IR_SHA = "02ee0e727af237b778fd0b88fbdb2a42eca0395b8eaed8d731636b3e4bb7b3c3"
EXPECTED_HTML_SHA = "42b268b31c78aa5d7c8b85a8babec8f36ee16e89878c3e07ade396208a61b6f4"
EXPECTED_SVG_SHA = "34d1da4c0ed795502f1eeef3af3d82e8872953422f9ea7ce5b48549424e57952"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [
        error.json_path + ": " + error.message
        for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)
    ]
    if errors:
        return errors
    expected_files = {
        CANONICAL_PATH: EXPECTED_CANONICAL_SHA,
        ADAPTER_PATH: EXPECTED_ADAPTER_SHA,
        IR_PATH: EXPECTED_IR_SHA,
        HTML_PATH: EXPECTED_HTML_SHA,
        SVG_PATH: EXPECTED_SVG_SHA,
    }
    for path, expected in expected_files.items():
        if not path.is_file():
            errors.append(f"missing bound smoke output: {path.relative_to(REPO_ROOT)}")
        elif sha256(path) != expected:
            errors.append(f"bound smoke output hash drifted: {path.relative_to(REPO_ROOT)}")
    source = document["fresh_source"]
    if source["revision"] != "d7372c27abe456b5b8c058675630d8038f91b448":
        errors.append("fresh source revision drifted")
    if source["worktree"] != "CLEAN" or source["non_shallow"] is not True:
        errors.append("fresh source cleanliness or depth boundary drifted")
    if document["adapter"]["topology"] != {"nodes": 24, "edges": 24, "semantic_relationships_unchanged": True}:
        errors.append("smoke topology boundary drifted")
    if len(document["runs"]) != 2:
        errors.append("Step06 must record exactly two runs")
    if document["stability"] != {
        "ir_equal": True,
        "html_equal": True,
        "svg_equal": True,
        "observed_scope": "TWO_RUNS_SAME_INPUT_SAME_PROVIDER_REVISION",
        "future_nondeterminism_claim": "NOT_CLAIMED",
    }:
        errors.append("stability claim exceeded the two-run observation")
    if document["scope_freeze"]["current_admission"] != "NOT_ADMITTED":
        errors.append("Step06 cannot admit a Current capability")
    if document["scope_freeze"]["delta_blocker"] != "INHERITED_STEP04_UPSTREAM_WRAPPER_BLOCKER":
        errors.append("Step04 Delta blocker was not carried forward")
    if document["scope_freeze"]["agent_reach"] != "NO_CHANGE":
        errors.append("Agent Reach changed")
    if document["scope_freeze"]["authenticated_channels"] != "NO_AUTHENTICATED_ADMISSION":
        errors.append("authenticated admission changed")
    if document["scope_freeze"]["live_external_invocation"] != "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN":
        errors.append("live external invocation changed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate()
    if errors:
        print("TASK150_STEP06_CURRENT_ARCHITECTURE_SMOKE_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        "TASK150_STEP06_CURRENT_ARCHITECTURE_SMOKE_OK "
        "fresh_source=EXACT_D7372C27 two_runs=STABLE standalone=PASS "
        "visualReview=pending current=NOT_ADMITTED"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
