#!/usr/bin/env python3
"""Validate Ignition iteration manifests and front-door synchronization."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/operations/iteration-manifest.schema.json"
MANIFEST_DIR = ROOT / "data/operations/iterations"

FRONT_DOOR_SURFACES = {
    "README.md",
    "docs/project-current-state.md",
    "AI-HANDOFF.md",
    "AI-START-HERE.md",
    "llms.txt",
    "SUMMARY.md",
    "CHANGELOG.md",
}


def load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _has_decision(manifest: dict, surface: str) -> bool:
    return any(item["surface"] == surface for item in manifest["impact_matrix"])


def validate_custom(manifest: dict, path: Path) -> None:
    task = manifest["task_id"]
    status = manifest["status"]
    classifications = set(manifest["change_classification"])

    require(manifest["claim_ceiling"].strip(), f"{path}: claim ceiling is blank")
    require(not status["current"] or status["merged"], f"{path}: current cannot be true unless merged is true")
    require(not status["merged"] or status["accepted"], f"{path}: merged cannot be true unless accepted is true")
    require(not status["accepted"] or status["ready_for_gpt_verification"], f"{path}: accepted cannot be true unless ready_for_gpt_verification is true")
    require(status["candidate"] or status["ready_for_gpt_verification"] or status["accepted"] or status["merged"] or status["current"], f"{path}: all states are false")
    require(not (status["current"] and manifest["branch_pr"]["draft"]), f"{path}: Draft PR cannot be current")
    require(not (status["merged"] and manifest["branch_pr"]["draft"]), f"{path}: Draft PR cannot be merged")
    require(not (manifest["branch_pr"]["merged"] and manifest["branch_pr"]["draft"]), f"{path}: branch_pr cannot be both merged and draft")

    decisions = {item["surface"]: item for item in manifest["impact_matrix"]}
    for surface, item in decisions.items():
        if item["decision"] == "NO_CHANGE_WITH_REASON":
            require(item["reason"].strip(), f"{path}: {surface} has NO_CHANGE without reason")

    if classifications & {"CAPABILITY_ADDITION", "INTERFACE_CHANGE", "GOVERNANCE_CHANGE", "RELEASE_OR_CURRENT_STATE_SYNC", "OPERATIONS_METHOD"}:
        for surface in FRONT_DOOR_SURFACES:
            require(_has_decision(manifest, surface), f"{path}: missing front-door/current-state impact decision for {surface}")

    changed = set(manifest["changed_surfaces"])
    if "OPERATIONS_METHOD" in classifications:
        require("ITERATION.md" in changed, f"{path}: operations method change must include ITERATION.md")
        require("tools/validate_iteration_sync.py" in changed, f"{path}: operations method change must include validator")

    sync_decisions = manifest.get("required_synchronization_decisions", [])
    require(sync_decisions, f"{path}: synchronization decisions missing")
    for item in sync_decisions:
        require("NO_CHANGE" not in item or "reason" in item.lower(), f"{path}: unexplained NO_CHANGE synchronization decision: {item}")

    forbidden_current_claim = "Open Draft"
    for limitation in manifest["remaining_limitations"]:
        require(forbidden_current_claim not in limitation, f"{path}: ambiguous Draft/current limitation in {task}")


def validate_all() -> dict:
    schema = load_json(SCHEMA_PATH)
    validator = Draft202012Validator(schema)
    paths = sorted(MANIFEST_DIR.glob("*.json"))
    require(paths, "no iteration manifests found")
    checked = 0
    for path in paths:
        manifest = load_json(path)
        errors = sorted(validator.iter_errors(manifest), key=lambda error: list(error.path))
        if errors:
            first = errors[0]
            loc = ".".join(str(part) for part in first.path) or "<root>"
            raise AssertionError(f"{path}: schema error at {loc}: {first.message}")
        validate_custom(manifest, path)
        checked += 1

    for surface in FRONT_DOOR_SURFACES | {"ITERATION.md"}:
        require((ROOT / surface).exists(), f"required synchronized surface missing: {surface}")

    return {"status": "PASS", "checked": checked}


def main() -> int:
    try:
        result = validate_all()
    except AssertionError as exc:
        print(f"iteration sync validation failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
