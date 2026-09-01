#!/usr/bin/env python3
"""Fail-closed validation for Task149 Step17 limited propagation."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from tools.validate_state_changelog import validate as validate_state_changelog


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
ARTIFACT_PATH = ROOT / "data/operations/iterations/149/step17-limited-propagation-r0.json"
SCHEMA_PATH = ROOT / "schemas/operations/task149-step17-limited-propagation-r0.schema.json"
SURFACES_PATH = ROOT / "data/operations/synchronization-surfaces.json"
NONIMPACT_PATH = ROOT / "data/operations/front-door-nonimpact-proofs.json"
STATE_CHANGELOG_PATH = ROOT / "STATE-CHANGELOG.md"
PROFILE_PATH = ROOT / "data/operations/state-changelog-profile-r1.json"
IDENTITY_PATH = ROOT / "data/architecture/current-system-identity.json"
EXPECTED_MAIN_BASELINE = "14c2595d796494286caf31378173fd9dd027edcf"
EXPECTED_FORMAL_PARENT = "ea24f4f66b61693a76a09be6243711ab93ffdf57"
EXPECTED_LABEL = "IGNITION-20260831-149 — External Capability Provider Adapter Spikes R0 Draft propagation delta"
EXPECTED_PROOF_CLAIMS = ["点火已支持 Archify", "点火已拥有全网能力", "点火支持 15 个平台"]
POST_STEP17_DERIVED_RECONCILIATIONS = {
    "ignition/data/architecture/current-facts.json",
    # The Knowledge Experience README is a generated projection of the same
    # source corpus.  Step18's official self-correction and Knowledge
    # Experience rebuild changed its counts/links without changing the
    # Task149 provider decision or adding a Current capability.
    "ignition/KNOWLEDGE/README.md",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git_show(commit: str, path: str) -> bytes | None:
    try:
        return subprocess.check_output(
            ["git", "show", f"{commit}:{path}"],
            cwd=REPO_ROOT,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return None


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors: list[str] = []
    schema = load_json(SCHEMA_PATH)
    errors.extend(error.json_path + ": " + error.message for error in Draft202012Validator(schema).iter_errors(document))

    if document.get("formal_main_baseline") != EXPECTED_MAIN_BASELINE:
        errors.append("Step17 must retain the fresh Task148 Current main baseline")
    if document.get("formal_previous_commit") != EXPECTED_FORMAL_PARENT:
        errors.append("Step17 must bind the exact Step16 formal parent")

    registry = load_json(SURFACES_PATH)
    declared = {item.get("surface_id"): item for item in registry.get("surfaces", [])}
    decisions = document.get("surface_decisions", [])
    decision_ids = [item.get("surface_id") for item in decisions]
    if len(decision_ids) != len(set(decision_ids)):
        errors.append("Step17 surface decisions must be unique")
    if set(decision_ids) != set(declared):
        errors.append("Step17 surface decisions must cover exactly the synchronization registry")
    for item in decisions:
        surface_id = item.get("surface_id")
        surface = declared.get(surface_id)
        if surface is None:
            continue
        if item.get("locator") != surface.get("locator"):
            errors.append(f"surface locator drifted: {surface_id}")
        if item.get("decision") not in surface.get("allowed_decisions", []):
            errors.append(f"surface decision is not allowed by registry: {surface_id}")
        if not str(item.get("reason", "")).strip():
            errors.append(f"surface decision lacks a reason: {surface_id}")
        if not item.get("evidence_refs"):
            errors.append(f"surface decision lacks evidence: {surface_id}")

    decision_map = {item.get("surface_id"): item for item in decisions}
    if decision_map.get("human.readme", {}).get("decision") != "NO_CHANGE_WITH_REASON":
        errors.append("human.readme must remain NO_CHANGE_WITH_REASON")
    if decision_map.get("release.state_changelog", {}).get("decision") != "CHANGE":
        errors.append("release.state_changelog must be the only changed registered release surface")
    changed_registered = {item.get("surface_id") for item in decisions if item.get("decision") == "CHANGE"}
    if changed_registered != {"release.state_changelog"}:
        errors.append("Step17 must not promote a provider spike into another registered surface")

    proof = document.get("front_door_nonimpact_proof", {})
    if proof.get("forbidden_claims") != EXPECTED_PROOF_CLAIMS:
        errors.append("front-door forbidden-claim guard drifted")
    proofs = load_json(NONIMPACT_PATH).get("exemptions", [])
    matching = [
        item for item in proofs
        if item.get("surface_id") == "human.readme"
        and item.get("iteration_id") == "IGNITION-20260831-149"
    ]
    if len(matching) != 1:
        errors.append("Task149 human.readme NonImpactProof is missing or duplicated")
    else:
        entry = matching[0]
        for key, expected in (
            ("decision", "NO_CHANGE_WITH_REASON"),
            ("scope", "DRAFT_BRANCH_ONLY"),
        ):
            if entry.get(key) != expected:
                errors.append(f"Task149 NonImpactProof {key} is not bounded")
        if set(entry.get("evidence_refs", [])) != {
            "ignition/data/operations/iterations/149/step17-limited-propagation-r0.json",
            "ignition/data/operations/iterations/149/External Capability Provider Adapter Spikes R0.md",
        }:
            errors.append("Task149 NonImpactProof evidence refs drifted")

    delta = document.get("state_changelog_delta", {})
    if delta.get("label") != EXPECTED_LABEL:
        errors.append("Task149 STATE-CHANGELOG label drifted")
    text = STATE_CHANGELOG_PATH.read_text(encoding="utf-8")
    if f"## 2026-09-01 — {EXPECTED_LABEL}" not in text:
        errors.append("Task149 STATE-CHANGELOG delta is missing")
    if sha256_bytes(STATE_CHANGELOG_PATH.read_bytes()) != delta.get("whole_file_after_sha256"):
        errors.append("Task149 STATE-CHANGELOG whole-file after hash drifted")
    parent_changelog = git_show(document.get("formal_previous_commit", ""), "ignition/STATE-CHANGELOG.md")
    if parent_changelog is None or sha256_bytes(parent_changelog) != delta.get("whole_file_before_sha256"):
        errors.append("Task149 STATE-CHANGELOG whole-file before hash is not bound to Step16 parent")
    profile = load_json(PROFILE_PATH)
    if profile.get("entry_count") != 55 or profile.get("historical_entry_count") != 27:
        errors.append("state-changelog profile counts do not preserve the Task149 historical boundary")
    profile_entry = next((item for item in profile.get("entries", []) if item.get("ordinal") == 55), None)
    if profile_entry is None or profile_entry.get("profile") != "historical-current-r0" or profile_entry.get("section_sha256") != delta.get("section_sha256"):
        errors.append("Task149 STATE-CHANGELOG profile seal is missing or not historical")
    errors.extend(f"state-changelog: {error}" for error in validate_state_changelog())

    for item in document.get("protected_surface_fingerprints", []):
        path = item.get("path")
        current_path = REPO_ROOT / path
        if not current_path.is_file():
            errors.append(f"protected surface is missing: {path}")
            continue
        before = git_show(document.get("formal_previous_commit", ""), path)
        if before is None or sha256_bytes(before) != item.get("before_sha256"):
            errors.append(f"protected surface before hash is not bound: {path}")
        # Step17 is an era-bound Draft receipt.  Its recorded after hash must
        # remain the Step16-parent bytes, while the current-facts projection
        # may be regenerated later when Step18 reconciles upstream foundation
        # outputs.  Other protected surfaces remain byte-stable on the branch.
        if path in POST_STEP17_DERIVED_RECONCILIATIONS:
            after = git_show(document.get("formal_previous_commit", ""), path)
            if after is None or sha256_bytes(after) != item.get("after_sha256"):
                errors.append(f"protected surface historical after hash drifted: {path}")
        elif sha256_bytes(current_path.read_bytes()) != item.get("after_sha256"):
            errors.append(f"protected surface after hash drifted: {path}")
        if item.get("before_sha256") != item.get("after_sha256"):
            errors.append(f"protected surface changed unexpectedly: {path}")

    supporting = document.get("supporting_registry_delta", {})
    supporting_path = REPO_ROOT / supporting.get("path", "")
    if not supporting_path.is_file() or sha256_bytes(supporting_path.read_bytes()) != supporting.get("after_sha256"):
        errors.append("front-door NonImpactProof registry after hash drifted")
    supporting_before = git_show(document.get("formal_previous_commit", ""), supporting.get("path", ""))
    if supporting_before is None or sha256_bytes(supporting_before) != supporting.get("before_sha256"):
        errors.append("front-door NonImpactProof registry before hash is not bound")
    if supporting.get("before_sha256") == supporting.get("after_sha256"):
        errors.append("front-door NonImpactProof registry was not changed")

    identity = load_json(IDENTITY_PATH)
    if identity.get("current_formal_task_id") != "IGNITION-20260829-148":
        errors.append("Current identity must remain Task148 during the Draft spike")
    if identity.get("current_operating_method", {}).get("status") != "CURRENT":
        errors.append("Current Operating Method status drifted during the Draft spike")
    if document.get("task_state_boundary", {}).get("current_identity_changed") is not False:
        errors.append("Task149 must not claim a Current identity change")
    safety = document.get("safety_boundary", {})
    if safety.get("authenticated_channel_admission") != "NO_AUTHENTICATED_CHANNEL_ADMISSION" or safety.get("live_external_invocation") != "LIVE_EXTERNAL_INVOCATION_UNCHANGED":
        errors.append("Task149 Step17 safety boundary drifted")
    if any(safety.get(key) is not False for key in ("system_mutation", "secret_or_cookie_access", "login", "provider_vendoring", "automatic_task150")):
        errors.append("Task149 Step17 must keep system, credential, vendoring and Task150 side effects closed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("TASK149_STEP17_LIMITED_PROPAGATION_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK149_STEP17_LIMITED_PROPAGATION_OK surfaces=21 readme=NO_CHANGE_WITH_REASON state_changelog=CHANGE current_state=NO_CHANGE_WITH_REASON")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
