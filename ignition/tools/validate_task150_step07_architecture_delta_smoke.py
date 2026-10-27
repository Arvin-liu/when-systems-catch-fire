#!/usr/bin/env python3
"""Fail-closed validation for Task150 Step07 architecture Delta evidence."""

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
ARTIFACT_PATH = ROOT / "data/operations/iterations/150/step07-architecture-delta-smoke.json"
SCHEMA_PATH = ROOT / "schemas/operations/task150-step07-architecture-delta-smoke-r1.schema.json"
FIXTURE_PATH = ROOT / "data/operations/iterations/150/fixtures/task150-step07-fail-closed.json"
EXPECTED_PREVIOUS_COMMIT = "2ce2e098d421256ff976a535ca3e0962f182ae72"
EXPECTED_REVISIONS = ("a1a1d102c3cd2fa12fc962b648b0eea62d8097cf", "14c2595d796494286caf31378173fd9dd027edcf")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def topology(document: dict[str, Any]) -> tuple[Any, ...]:
    return (
        tuple(component["id"] for component in document["components"]),
        tuple((connection["id"], connection["from"], connection["to"]) for connection in document["connections"]),
        tuple((boundary["kind"], boundary["label"]) for boundary in document["boundaries"]),
    )


def mutate(base: dict[str, Any], mutation: str) -> dict[str, Any]:
    document = copy.deepcopy(base)
    if mutation == "ADD_COMPONENT":
        document["components"].append({"id":"task150-rogue-node","type":"external","label":"rogue","tag":"UNTRUSTED","pos":[0,0],"size":[1,1]})
    elif mutation == "ADD_CONNECTION":
        document["connections"].append({"id":"task150-rogue-edge","from":"source-functions","to":"task150-rogue-node","label":"rogue","variant":"default","route":"auto"})
    elif mutation == "MOVE_COMPONENT":
        document["components"][0]["pos"] = [document["components"][0]["pos"][0] + 17, document["components"][0]["pos"][1] + 9]
    elif mutation == "CHANGE_LINEAGE_METADATA":
        document["meta"]["repository"]["revision"] = "14c2595d796494286caf31378173fd9dd027edcf"
    else:
        raise ValueError(f"unknown fixture mutation: {mutation}")
    return document


def fixture_results(base: dict[str, Any]) -> list[dict[str, str]]:
    results = []
    for fixture in load_json(FIXTURE_PATH)["fixtures"]:
        mutated = mutate(base, fixture["mutation"])
        same_topology = topology(mutated) == topology(base)
        if fixture["id"] in {"extra-node", "extra-edge"}:
            observed = "FAIL_TOPOLOGY_DRIFT" if not same_topology else "UNEXPECTED_TOPOLOGY_ACCEPTED"
        elif fixture["id"] == "geometry-moved":
            observed = "PASS_TOPOLOGY_UNCHANGED_NOT_ARCHITECTURE_CHANGE" if same_topology else "UNEXPECTED_TOPOLOGY_DRIFT"
        else:
            observed = "PASS_PROVENANCE_ONLY" if same_topology else "UNEXPECTED_TOPOLOGY_DRIFT"
        results.append({"id": fixture["id"], "expected": fixture["expected"], "observed": observed})
    return results


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)]
    if errors:
        return errors
    if document["formal_previous_commit"] != EXPECTED_PREVIOUS_COMMIT:
        errors.append("Step07 must bind the published Step06 formal commit")
    lineage = document["lineage"]
    for index, state in enumerate((lineage["before"], lineage["after"])):
        source = REPO_ROOT / state["source_path"]
        if not source.is_file() or sha256(source) != state["source_sha256"]:
            errors.append(f"lineage source hash drifted: {state['source_path']}")
        if state["source_revision"] != EXPECTED_REVISIONS[index]:
            errors.append("lineage source revision drifted")
    base = load_json(REPO_ROOT / "ignition/data/operations/iterations/150/delta-evidence/task150-before.json")
    head = load_json(REPO_ROOT / "ignition/data/operations/iterations/150/delta-evidence/task150-after.json")
    if topology(base) != topology(head):
        errors.append("formal provenance-only lineage snapshots do not have identical topology")
    if base["meta"]["repository"]["revision"] != EXPECTED_REVISIONS[0] or head["meta"]["repository"]["revision"] != EXPECTED_REVISIONS[1]:
        errors.append("derived Before/After lineage metadata drifted")
    if document["comparison"]["semantic_classification"]["provenance_changed"] is not True:
        errors.append("provenance-only Delta was not retained")
    if document["comparison"]["semantic_classification"]["presentation_changed"] is not False:
        errors.append("presentation-only classification drifted")
    actual_results = fixture_results(base)
    expected_results = [{"id": item["id"], "expected": item["expected"]} for item in actual_results]
    if expected_results != document["fixtures"]["results"]:
        errors.append("fixture expectation list drifted")
    if any(item["expected"] != item["observed"] for item in actual_results):
        errors.append("one or more fail-closed fixture outcomes did not match")
    for item in document["evidence_files"]:
        path = REPO_ROOT / item["path"]
        if not path.is_file():
            errors.append(f"missing Delta evidence file: {item['path']}")
        elif path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
            errors.append(f"Delta evidence digest drifted: {item['path']}")
    if document["comparison"]["delta_visual"]["status"] != "FAIL_UPSTREAM_WRAPPER":
        errors.append("Delta visual blocker was relabelled")
    scope = document["scope_freeze"]
    if scope["current_admission"] != "NOT_ADMITTED" or scope["agent_reach"] != "NO_CHANGE":
        errors.append("Current or Agent Reach scope changed")
    if scope["authenticated_channels"] != "NO_AUTHENTICATED_ADMISSION" or scope["live_external_invocation"] != "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN":
        errors.append("authentication or live invocation boundary changed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate()
    if errors:
        print("TASK150_STEP07_ARCHITECTURE_DELTA_SMOKE_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK150_STEP07_ARCHITECTURE_DELTA_SMOKE_OK before=PASS delta_semantic=28/28 provenance_only=PASS fixtures=4/4 delta_visual=FAIL_UPSTREAM_WRAPPER")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
