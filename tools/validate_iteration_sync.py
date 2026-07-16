#!/usr/bin/env python3
"""Validate iteration lifecycle, task-specific seals, and propagation closure."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/operations/iteration-manifest.schema.json"
REGISTRY_PATH = ROOT / "data/operations/synchronization-surfaces.json"
REGISTRY_SCHEMA_PATH = ROOT / "schemas/operations/synchronization-surfaces.schema.json"
MANIFEST_DIR = ROOT / "data/operations/iterations"
SEAL_DIR = ROOT / "reports/operations"

LEGACY_FRONT_DOORS = {
    "README.md",
    "docs/project-current-state.md",
    "AI-HANDOFF.md",
    "AI-START-HERE.md",
    "llms.txt",
    "SUMMARY.md",
    "CHANGELOG.md",
}
LEGACY_Q24_METHOD_PATHS = {
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
TRIGGERING_CLASSIFICATIONS = {
    "CAPABILITY_ADDITION",
    "INTERFACE_CHANGE",
    "GOVERNANCE_CHANGE",
    "RELEASE_OR_CURRENT_STATE_SYNC",
    "OPERATIONS_METHOD",
}
UNRESOLVED_STATUSES = {"PENDING", "TODO", "UNKNOWN", "", "TBD", "N/A"}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _validate_schema(instance: object, schema_path: Path, source: Path) -> None:
    schema = load_json(schema_path)
    errors = sorted(Draft202012Validator(schema).iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.path) or "<root>"
        raise AssertionError(f"{source}: schema error at {location}: {first.message}")


def validate_manifest_schema(manifest: dict, source: Path) -> None:
    _validate_schema(manifest, SCHEMA_PATH, source)


def validate_registry(registry: dict, source: Path = REGISTRY_PATH) -> dict[str, dict]:
    _validate_schema(registry, REGISTRY_SCHEMA_PATH, source)
    surfaces = registry["surfaces"]
    ids = [item["surface_id"] for item in surfaces]
    require(len(ids) == len(set(ids)), f"{source}: duplicate surface_id")
    by_id = {item["surface_id"]: item for item in surfaces}
    for item in surfaces:
        for dependency in item["derived_from"]:
            require(dependency in by_id, f"{source}: unknown derived_from surface {dependency}")
        is_external = item["surface_type"] == "external_rendered_deployed_surface"
        require((item["authority"] == "external") == is_external, f"{source}: external authority/type mismatch for {item['surface_id']}")
        if not is_external:
            require((ROOT / item["locator"]).exists(), f"{source}: repository surface does not exist: {item['locator']}")
    return by_id


def _unique(items: list[str], label: str, source: Path) -> None:
    require(len(items) == len(set(items)), f"{source}: duplicate {label}: {items}")


def _impact_decisions(manifest: dict, source: Path) -> dict[str, dict]:
    surfaces = [item["surface"] for item in manifest["impact_matrix"]]
    _unique(surfaces, "impact_matrix.surface", source)
    return {item["surface"]: item for item in manifest["impact_matrix"]}


def _validation_names(items: list[dict], label: str, source: Path) -> None:
    names = [item["name"] for item in items]
    _unique(names, f"{label} validation name", source)
    run_ids = [item.get("run_id") for item in items if item.get("run_id") is not None]
    require(len(run_ids) == len(set(run_ids)), f"{source}: duplicate {label} workflow run id")


def infer_seal_path(manifest: dict) -> Path:
    declared = manifest.get("completion_seal_path")
    if declared:
        return ROOT / declared
    return SEAL_DIR / f"{manifest['task_id']}-completion-seal.json"


def required_registry_surfaces(manifest: dict, registry: dict[str, dict]) -> set[str]:
    classifications = set(manifest["change_classification"])
    dimensions = set(manifest["state_transition"]["changed_dimensions"])
    required = {
        surface_id
        for surface_id, item in registry.items()
        if classifications.intersection(item["trigger_classifications"])
        or dimensions.intersection(item["trigger_dimensions"])
    }
    changed = True
    while changed:
        changed = False
        for surface_id, item in registry.items():
            if surface_id in required:
                before = len(required)
                required.update(item["derived_from"])
                changed |= len(required) != before
            elif required.intersection(item["derived_from"]):
                required.add(surface_id)
                changed = True
    return required


def _validate_lifecycle(manifest: dict, source: Path) -> None:
    status = manifest["status"]
    branch_pr = manifest["branch_pr"]
    require(not status["current"] or status["merged"], f"{source}: current cannot be true unless merged is true")
    require(not status["merged"] or status["accepted"], f"{source}: merged cannot be true unless accepted is true")
    require(not status["accepted"] or status["ready_for_gpt_verification"], f"{source}: accepted cannot be true unless ready_for_gpt_verification is true")
    require(any(status.values()), f"{source}: all lifecycle states are false")
    require(branch_pr["merged"] == status["merged"], f"{source}: branch_pr.merged and status.merged disagree")
    require(not (branch_pr["draft"] and (status["accepted"] or status["merged"] or status["current"])), f"{source}: Draft cannot be accepted, merged, or current")
    require(not (branch_pr["merged"] and branch_pr["draft"]), f"{source}: branch_pr cannot be both merged and draft")
    if status["merged"] or status["current"]:
        merge_commit = branch_pr.get("merge_commit")
        require(branch_pr["pr_number"] and branch_pr["pr_number"] > 0, f"{source}: merged/current task requires PR number")
        require(isinstance(merge_commit, str) and SHA_RE.match(merge_commit), f"{source}: merged/current task requires valid merge commit")
        require("candidate_only" not in manifest["claim_ceiling"], f"{source}: merged/current task cannot keep candidate-only claim ceiling")


def _validate_ready_evidence(manifest: dict, source: Path) -> None:
    status = manifest["status"]
    if not status["ready_for_gpt_verification"]:
        return
    branch_pr = manifest["branch_pr"]
    head_binding = manifest["head_binding"]
    external_policy = manifest["validation"]["external_exact_head_policy"]
    require(branch_pr["pr_number"] and branch_pr["pr_number"] > 0, f"{source}: ready candidate requires PR number")
    if not (status["accepted"] or status["merged"] or status["current"]):
        require(branch_pr["draft"], f"{source}: unaccepted ready candidate must remain Draft until independently accepted")
    else:
        require(not branch_pr["draft"], f"{source}: accepted, merged, or current ready record must not remain Draft")
    require(head_binding["mode"] == "external_exact_head_attestation", f"{source}: ready candidate requires external exact-head attestation mode")
    require(head_binding["authority"] == "pull_request_body_and_1111_receipt", f"{source}: ready candidate requires externally resolvable attestation authority")
    require(head_binding["pr_number"] == branch_pr["pr_number"], f"{source}: head-binding PR mismatch")
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


def _validate_seal(manifest: dict, seal: dict, source: Path) -> None:
    require(seal.get("task_id") == manifest["task_id"], f"{source}: seal task mismatch")
    require(seal.get("method_version") == manifest["method_version"], f"{source}: seal method_version mismatch")
    phase_b = seal.get("phase_b", {})
    lifecycle = seal.get("lifecycle", {})
    require(phase_b.get("draft_pr") == manifest["branch_pr"]["pr_number"], f"{source}: seal PR mismatch")
    require(phase_b.get("branch") == manifest["branch_pr"]["branch"], f"{source}: seal branch mismatch")
    require(phase_b.get("base_head") == manifest["branch_pr"]["base_head"], f"{source}: seal base_head mismatch")
    require(phase_b.get("base", manifest["branch_pr"]["base"]) == manifest["branch_pr"]["base"], f"{source}: seal base mismatch")
    if manifest["status"]["merged"] or manifest["status"]["current"]:
        require(phase_b.get("merge_commit") == manifest["branch_pr"].get("merge_commit"), f"{source}: seal merge commit mismatch")
        require(seal.get("status") != "READY_FOR_GPT_VERIFICATION_CANDIDATE_ONLY", f"{source}: seal remains candidate-only after merge")
    seal_binding = phase_b.get("head_binding", {})
    binding_labels = {
        "mode": "seal head-binding mode mismatch",
        "authority": "seal attestation authority mismatch",
        "receipt_path": "seal attestation receipt mismatch",
        "embedded_exact_current_head": "seal embedded-head policy mismatch",
        "live_refetch_required": "seal live-refetch policy mismatch",
    }
    for key, label in binding_labels.items():
        require(seal_binding.get(key) == manifest["head_binding"][key], f"{source}: {label}")
    require(phase_b.get("claim_ceiling") == manifest["claim_ceiling"], f"{source}: seal claim ceiling mismatch")
    for key in ("candidate", "ready_for_gpt_verification", "accepted", "merged", "current"):
        require(lifecycle.get(key) == manifest["status"][key], f"{source}: seal lifecycle mismatch for {key}")
    if manifest["method_version"] == "1.1.0":
        require(seal.get("completion_state") == manifest["completion_state"], f"{source}: seal completion_state mismatch")
        require(seal.get("synchronization_registry", {}).get("path") == manifest["synchronization_closure"]["registry_path"], f"{source}: seal synchronization registry mismatch")


def _validate_v11_closure(manifest: dict, source: Path, registry: dict[str, dict]) -> None:
    closure = manifest["synchronization_closure"]
    completion = manifest["completion_state"]
    require(closure["registry_version"] == load_json(REGISTRY_PATH)["registry_version"], f"{source}: registry version mismatch")
    decisions = closure["surface_decisions"]
    ids = [item["surface_id"] for item in decisions]
    _unique(ids, "synchronization surface decision", source)
    decision_map = {item["surface_id"]: item for item in decisions}
    required_ids = required_registry_surfaces(manifest, registry)
    missing = sorted(required_ids - set(decision_map))
    require(not missing, f"{source}: missing registry-derived surface decisions: {missing}")
    unknown = sorted(set(decision_map) - set(registry))
    require(not unknown, f"{source}: unknown synchronization surface decisions: {unknown}")

    repository_complete = True
    external_required = False
    for surface_id in required_ids:
        spec = registry[surface_id]
        decision = decision_map[surface_id]
        require(decision["decision"] in spec["allowed_decisions"], f"{source}: disallowed decision for {surface_id}")
        require(decision["reason"].strip(), f"{source}: blank synchronization reason for {surface_id}")
        require(decision["evidence_refs"] and all(ref.strip() for ref in decision["evidence_refs"]), f"{source}: {surface_id} decision lacks evidence references")
        require(decision["validation_mode"] == spec["validation_mode"], f"{source}: validation mode mismatch for {surface_id}")
        require(decision.get("derived_from", []) == spec["derived_from"], f"{source}: derived_from mismatch for {surface_id}")
        is_external = spec["surface_type"] == "external_rendered_deployed_surface"
        if is_external:
            external_required = True
            require(spec["locator"] not in manifest["changed_surfaces"], f"{source}: external surface incorrectly listed as repository changed path")
        elif decision["decision"] == "CHANGE":
            require(spec["locator"] in manifest["changed_surfaces"], f"{source}: changed registry surface absent from changed_surfaces: {spec['locator']}")
            require((ROOT / spec["locator"]).exists(), f"{source}: changed registry path missing: {spec['locator']}")

    require(closure["live_external_surfaces_verified"] is False, f"{source}: local validator cannot claim live rendered verification")
    require(completion["external_synchronization_required"] == external_required, f"{source}: external synchronization requirement mismatch")
    require(completion["repository_synchronization_complete"] == (repository_complete and not closure["unresolved_residue"]), f"{source}: repository synchronization completion inconsistent with residue")
    expected_project = completion["repository_synchronization_complete"] and (not external_required or completion["external_synchronization_attested"])
    require(completion["project_synchronization_complete"] == expected_project, f"{source}: project synchronization completion is inflated or inconsistent")
    if manifest["status"]["ready_for_gpt_verification"]:
        require(completion["implementation_complete"], f"{source}: implementation incomplete candidate cannot be ready")
        require(completion["repository_synchronization_complete"], f"{source}: repository synchronization incomplete candidate cannot be ready")
    if manifest["status"]["accepted"] or manifest["status"]["current"]:
        require(completion["project_synchronization_complete"], f"{source}: accepted/current lifecycle requires project synchronization complete")
    if manifest["status"]["current"]:
        require(manifest["status"]["merged"], f"{source}: current requires merged lifecycle")


def validate_custom(manifest: dict, source: Path, seal: dict, registry: dict[str, dict] | None = None) -> None:
    _validate_lifecycle(manifest, source)
    _validate_ready_evidence(manifest, source)
    classifications = set(manifest["change_classification"])
    changed = set(manifest["changed_surfaces"])
    decisions = _impact_decisions(manifest, source)
    _unique(manifest["changed_surfaces"], "changed_surfaces", source)
    _validation_names(manifest["validation"]["local"], "local", source)
    _validation_names(manifest["validation"]["remote"], "remote", source)

    if manifest["method_version"] == "1.0.0" and classifications & TRIGGERING_CLASSIFICATIONS:
        for surface in LEGACY_FRONT_DOORS:
            require(surface in decisions, f"{source}: missing front-door/current-state impact decision for {surface}")

    for surface, item in decisions.items():
        if item["decision"] == "CHANGE":
            require(surface in changed, f"{source}: CHANGE decision not present in changed_surfaces: {surface}")
        elif item["decision"] == "NO_CHANGE_WITH_REASON":
            require(item["reason"].strip(), f"{source}: {surface} has NO_CHANGE without reason")
            require(surface not in changed, f"{source}: NO_CHANGE surface falsely declared changed: {surface}")
    for path in changed:
        if "://" not in path:
            require((ROOT / path).exists(), f"{source}: declared changed path does not exist: {path}")

    if manifest["method_version"] == "1.0.0" and manifest["task_id"] == "121Q24" and "OPERATIONS_METHOD" in classifications:
        missing = sorted(LEGACY_Q24_METHOD_PATHS - changed)
        require(not missing, f"{source}: legacy Q24 operations method missing changed paths: {missing}")
    if manifest["method_version"] == "1.1.0":
        require(registry is not None, f"{source}: method 1.1.0 requires synchronization registry")
        _validate_v11_closure(manifest, source, registry)
    _validate_seal(manifest, seal, source)


def validate_manifest_bindings(documents: list[tuple[Path, dict]]) -> list[tuple[Path, dict, Path]]:
    seen_tasks: set[str] = set()
    seen_seals: set[Path] = set()
    bound: list[tuple[Path, dict, Path]] = []
    for path, manifest in documents:
        task_id = manifest["task_id"]
        require(task_id not in seen_tasks, f"{path}: duplicate task binding: {task_id}")
        seen_tasks.add(task_id)
        seal_path = infer_seal_path(manifest)
        require(seal_path not in seen_seals, f"{path}: duplicate completion seal binding: {seal_path}")
        seen_seals.add(seal_path)
        require(seal_path.is_file(), f"{path}: missing completion seal: {seal_path.relative_to(ROOT)}")
        bound.append((path, manifest, seal_path))
    return bound


def validate_all() -> dict:
    paths = sorted(MANIFEST_DIR.glob("*.json"))
    require(paths, "no iteration manifests found")
    registry = validate_registry(load_json(REGISTRY_PATH))
    documents = [(path, load_json(path)) for path in paths]
    for path, manifest in documents:
        validate_manifest_schema(manifest, path)
    bound = validate_manifest_bindings(documents)
    checked = 0
    for path, manifest, seal_path in bound:
        seal = load_json(seal_path)
        validate_custom(manifest, path, seal, registry)
        checked += 1

    return {
        "status": "PASS",
        "checked": checked,
        "implementation_consistency": "PASS",
        "repository_synchronization_closure": "PASS",
        "external_synchronization_required": any(load_json(path).get("completion_state", {}).get("external_synchronization_required", False) for path in paths),
        "live_external_surfaces_verified": False,
        "scope": "repository_local_consistency_and_synchronization_only",
    }


def main() -> int:
    try:
        result = validate_all()
    except (AssertionError, KeyError, TypeError, ValueError) as exc:
        print(f"iteration sync validation failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
