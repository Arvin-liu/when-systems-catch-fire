#!/usr/bin/env python3
"""Validate Ignition iteration manifests and artifact synchronization."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/operations/iteration-manifest.schema.json"
MANIFEST_DIR = ROOT / "data/operations/iterations"
SEAL_PATH = ROOT / "reports/operations/121Q24-completion-seal.json"

FRONT_DOOR_SURFACES = {
    "README.md",
    "docs/project-current-state.md",
    "AI-HANDOFF.md",
    "AI-START-HERE.md",
    "llms.txt",
    "SUMMARY.md",
    "CHANGELOG.md",
}

OPERATIONS_METHOD_REQUIRED_CHANGED = {
    "ITERATION.md",
    "schemas/operations/iteration-manifest.schema.json",
    "data/operations/iterations/121Q24.json",
    "tools/validate_iteration_sync.py",
    "tests/test_iteration_sync.py",
    ".github/workflows/foundation-validation.yml",
    "reports/operations/121Q24-current-state-reconciliation.md",
    "reports/operations/121Q24-completion-seal.json",
    "templates/operations/task-command-template.md",
    "templates/operations/execution-result-template.md",
    "templates/operations/independent-review-template.md",
}

UNRESOLVED_STATUSES = {"PENDING", "TODO", "UNKNOWN", "", "TBD", "N/A"}


def load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _unique(items: list[str], label: str, source: Path) -> None:
    require(len(items) == len(set(items)), f"{source}: duplicate {label}: {items}")


def _decision_map(manifest: dict, source: Path) -> dict[str, dict]:
    surfaces = [item["surface"] for item in manifest["impact_matrix"]]
    _unique(surfaces, "impact_matrix.surface", source)
    return {item["surface"]: item for item in manifest["impact_matrix"]}


def _validation_names(items: list[dict], label: str, source: Path) -> None:
    names = [item["name"] for item in items]
    _unique(names, f"{label} validation name", source)
    run_ids = [item.get("run_id") for item in items if item.get("run_id") is not None]
    require(len(run_ids) == len(set(run_ids)), f"{source}: duplicate {label} workflow run id")


def validate_manifest_schema(manifest: dict, source: Path) -> None:
    schema = load_json(SCHEMA_PATH)
    errors = sorted(Draft202012Validator(schema).iter_errors(manifest), key=lambda error: list(error.path))
    if errors:
        first = errors[0]
        loc = ".".join(str(part) for part in first.path) or "<root>"
        raise AssertionError(f"{source}: schema error at {loc}: {first.message}")


def validate_custom(manifest: dict, source: Path, seal: dict | None = None) -> None:
    status = manifest["status"]
    classifications = set(manifest["change_classification"])
    changed = set(manifest["changed_surfaces"])
    decisions = _decision_map(manifest, source)
    head_binding = manifest["head_binding"]
    external_policy = manifest["validation"]["external_exact_head_policy"]

    _unique(manifest["changed_surfaces"], "changed_surfaces", source)
    _validation_names(manifest["validation"]["local"], "local", source)
    _validation_names(manifest["validation"]["remote"], "remote", source)

    require(not status["current"] or status["merged"], f"{source}: current cannot be true unless merged is true")
    require(not status["merged"] or status["accepted"], f"{source}: merged cannot be true unless accepted is true")
    require(not status["accepted"] or status["ready_for_gpt_verification"], f"{source}: accepted cannot be true unless ready_for_gpt_verification is true")
    require(status["candidate"] or status["ready_for_gpt_verification"] or status["accepted"] or status["merged"] or status["current"], f"{source}: all states are false")
    require(manifest["branch_pr"]["merged"] == status["merged"], f"{source}: branch_pr.merged and status.merged disagree")
    require(not (manifest["branch_pr"]["draft"] and (status["accepted"] or status["merged"] or status["current"])), f"{source}: Draft cannot be accepted, merged, or current")
    require(not (manifest["branch_pr"]["merged"] and manifest["branch_pr"]["draft"]), f"{source}: branch_pr cannot be both merged and draft")

    if status["ready_for_gpt_verification"]:
        require(manifest["branch_pr"]["pr_number"] is not None and manifest["branch_pr"]["pr_number"] > 0, f"{source}: ready candidate requires PR number")
        require(manifest["branch_pr"]["draft"], f"{source}: ready candidate must remain Draft until independently accepted")
        require(head_binding["mode"] == "external_exact_head_attestation", f"{source}: ready candidate requires external exact-head attestation mode")
        require(head_binding["authority"] == "pull_request_body_and_1111_receipt", f"{source}: ready candidate requires externally resolvable attestation authority")
        require(head_binding["pr_number"] == manifest["branch_pr"]["pr_number"], f"{source}: head-binding PR mismatch")
        require(head_binding["receipt_path"] == manifest["receipt_location"], f"{source}: head-binding receipt mismatch")
        require(head_binding["embedded_exact_current_head"] is False, f"{source}: repository artifact cannot claim embedded exact current self HEAD")
        require(head_binding["live_refetch_required"] is True, f"{source}: exact-head attestation must require live re-fetch")
        require(external_policy["required"] is True, f"{source}: ready candidate requires external exact-head attestation policy")
        require(external_policy["authority"] == head_binding["authority"], f"{source}: attestation authority mismatch")
        require(external_policy["live_refetch_before_acceptance_or_merge"] is True, f"{source}: acceptance/merge must require live PR/CI re-fetch")
        require(set(external_policy["required_workflows"]) == {"foundation-validation", "function-os-ci"}, f"{source}: exact-head policy must require both remote workflows")
        require(manifest["validation"]["local"], f"{source}: ready candidate requires local validation")
        for item in manifest["validation"]["local"] + manifest["validation"]["remote"]:
            require(item["status"].upper() not in UNRESOLVED_STATUSES, f"{source}: unresolved validation status for {item['name']}")
            require(item["status"].upper() in {"PASS", "SUCCESS"}, f"{source}: validation status must be PASS/SUCCESS for {item['name']}")
        for item in manifest["validation"]["remote"]:
            require(item.get("run_id"), f"{source}: remote validation {item['name']} missing run_id")
            require(item.get("evidence_scope") == "historical_subject_head_only", f"{source}: stale CI evidence mislabeled as current-final evidence")
            require(item.get("subject_head"), f"{source}: historical validation {item['name']} missing subject_head")
            require(item.get("conclusion", "").lower() == "success", f"{source}: remote validation {item['name']} conclusion not success")

    if classifications & {"CAPABILITY_ADDITION", "INTERFACE_CHANGE", "GOVERNANCE_CHANGE", "RELEASE_OR_CURRENT_STATE_SYNC", "OPERATIONS_METHOD"}:
        for surface in FRONT_DOOR_SURFACES:
            require(surface in decisions, f"{source}: missing front-door/current-state impact decision for {surface}")

    for surface, item in decisions.items():
        if item["decision"] == "CHANGE":
            require(surface in changed, f"{source}: CHANGE decision not present in changed_surfaces: {surface}")
        if item["decision"] == "NO_CHANGE_WITH_REASON":
            require(item["reason"].strip(), f"{source}: {surface} has NO_CHANGE without reason")
            require(surface not in changed, f"{source}: NO_CHANGE surface falsely declared changed: {surface}")

    for path in changed:
        require((ROOT / path).exists(), f"{source}: declared changed path does not exist: {path}")

    if "OPERATIONS_METHOD" in classifications:
        missing = sorted(OPERATIONS_METHOD_REQUIRED_CHANGED - changed)
        require(not missing, f"{source}: operations method missing changed paths: {missing}")

    if seal is not None and manifest["task_id"] == seal.get("task_id"):
        phase_b = seal["phase_b"]
        lifecycle = seal["lifecycle"]
        require(seal["method_version"] == manifest["method_version"], f"{source}: seal method_version mismatch")
        require(phase_b["draft_pr"] == manifest["branch_pr"]["pr_number"], f"{source}: seal PR mismatch")
        require(phase_b["branch"] == manifest["branch_pr"]["branch"], f"{source}: seal branch mismatch")
        require(phase_b["base_head"] == manifest["branch_pr"]["base_head"], f"{source}: seal base_head mismatch")
        require(phase_b["head_binding"]["mode"] == head_binding["mode"], f"{source}: seal head-binding mode mismatch")
        require(phase_b["head_binding"]["authority"] == head_binding["authority"], f"{source}: seal attestation authority mismatch")
        require(phase_b["head_binding"]["receipt_path"] == head_binding["receipt_path"], f"{source}: seal attestation receipt mismatch")
        require(phase_b["head_binding"]["embedded_exact_current_head"] == head_binding["embedded_exact_current_head"], f"{source}: seal embedded-head policy mismatch")
        require(phase_b["head_binding"]["live_refetch_required"] == head_binding["live_refetch_required"], f"{source}: seal live-refetch policy mismatch")
        require(phase_b["claim_ceiling"] == manifest["claim_ceiling"], f"{source}: seal claim ceiling mismatch")
        for key in ("candidate", "ready_for_gpt_verification", "accepted", "merged", "current"):
            require(lifecycle[key] == manifest["status"][key], f"{source}: seal lifecycle mismatch for {key}")


def validate_all() -> dict:
    paths = sorted(MANIFEST_DIR.glob("*.json"))
    require(paths, "no iteration manifests found")
    seal = load_json(SEAL_PATH) if SEAL_PATH.exists() else None
    checked = 0
    for path in paths:
        manifest = load_json(path)
        validate_manifest_schema(manifest, path)
        validate_custom(manifest, path, seal)
        checked += 1

    for surface in FRONT_DOOR_SURFACES | {"ITERATION.md"}:
        require((ROOT / surface).exists(), f"required synchronized surface missing: {surface}")

    return {
        "status": "PASS",
        "checked": checked,
        "scope": "repository_local_consistency_only",
        "live_github_truth_verified": False,
    }


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
