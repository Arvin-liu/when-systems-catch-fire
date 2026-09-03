#!/usr/bin/env python3
"""Fail-closed, era-bound validation for Task150 Step26 front-door synchronization."""

from __future__ import annotations

import argparse
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
ARTIFACT_PATH = ROOT / "data/operations/iterations/150/step26-front-door-and-sync-surface-restraint.json"
SCHEMA_PATH = ROOT / "schemas/operations/task150-step26-front-door-and-sync-surface-restraint-r1.schema.json"
SYNC_REGISTRY_PATH = ROOT / "data/operations/synchronization-surfaces.json"
README_PATH = REPO_ROOT / ".github/README.md"
CAPABILITY_REGISTRY_PATH = ROOT / "data/operations/ignition-operation-capability-registry-r1.json"

EXPECTED_PREVIOUS_COMMIT = "11cbbf7bc7519730b16af9b5ee074b5b6b355ada"
TASK150_STEP26_PUBLISHED_COMMIT = "672a7a1a757a3741cd1c2643a29e5fc4470ab06a"
EXPECTED_SYNC_SHA = "c67508eba1b6ad37cfd723f06cb731877ca14a76bfa55e17bf17afc8d252eec9"
EXPECTED_README_BEFORE_SHA = "1720c242aa9329ab5cfb4d79d62253fd4d9eed6b8bae23ea9e0e08116e4cd4a0"
EXPECTED_README_AFTER_SHA = "f24f0039ae2fede1b06abc2fa37690e39786568a340a44d0c4c39fdadd1d82b7"
EXPECTED_ALLOWED_STATEMENT = "在受支持环境中，点火也可以按 Capability Registry 生成受约束的派生系统视图；这是 provider-neutral 的 bounded 结构阅读能力，不替代 canonical source、架构权威或真值判断。"
FORBIDDEN_HOMEPAGE_CLAIMS = (
    "Archify 是点火官方 renderer",
    "点火架构由 Archify 驱动",
    "Archify验证了点火架构",
    "Archify is Ignition's official renderer",
    "Ignition architecture is driven by Archify",
    "Archify validated Ignition architecture",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def previous_file_sha(commit: str, path: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "show", f"{commit}:{path}"],
            cwd=REPO_ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError:
        return None
    return sha256_bytes(result.stdout)


def historical_file_bytes(commit: str, path: str) -> bytes | None:
    """Read the exact Step26-era file, keeping successor front-door changes independent."""
    try:
        result = subprocess.run(
            ["git", "show", f"{commit}:{path}"],
            cwd=REPO_ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError:
        return None
    return result.stdout


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [
        error.json_path + ": " + error.message
        for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)
    ]
    if errors:
        return errors

    if document["formal_previous_commit"] != EXPECTED_PREVIOUS_COMMIT:
        errors.append("Step26 must start from the pushed Step25 formal head")
    sync_registry = load_json(SYNC_REGISTRY_PATH)
    if sha256(SYNC_REGISTRY_PATH) != EXPECTED_SYNC_SHA:
        errors.append("synchronization registry digest drifted")
    if sync_registry.get("registry_version") != "1.7.0" or len(sync_registry.get("surfaces", [])) != 21:
        errors.append("synchronization registry version or surface count drifted")
    if document["synchronization_registry"]["sha256"] != EXPECTED_SYNC_SHA:
        errors.append("recorded synchronization registry digest drifted")

    expected_surfaces = [(row["surface_id"], row["locator"]) for row in sync_registry["surfaces"]]
    actual_surfaces = [(row["surface_id"], row["locator"]) for row in document["surface_decisions"]]
    if actual_surfaces != expected_surfaces:
        errors.append("surface decisions do not exactly follow the synchronization registry")
    changed = [row for row in document["surface_decisions"] if row["decision"] == "CHANGE"]
    if len(changed) != 1 or changed[0]["surface_id"] != "human.readme":
        errors.append("only human.readme may be changed by this Step26 public wording sync")
    if any(row["decision"] != "NO_CHANGE_WITH_REASON" for row in document["surface_decisions"] if row["surface_id"] != "human.readme"):
        errors.append("non-homepage surfaces require explicit NO_CHANGE_WITH_REASON decisions")

    homepage = document["homepage"]
    historical_readme = historical_file_bytes(TASK150_STEP26_PUBLISHED_COMMIT, ".github/README.md")
    if historical_readme is None or sha256_bytes(historical_readme) != EXPECTED_README_AFTER_SHA or homepage["after_sha256"] != EXPECTED_README_AFTER_SHA:
        errors.append("Task150 Step26 homepage after digest drifted")
    if previous_file_sha(EXPECTED_PREVIOUS_COMMIT, ".github/README.md") != EXPECTED_README_BEFORE_SHA or homepage["before_sha256"] != EXPECTED_README_BEFORE_SHA:
        errors.append("homepage before digest is not the Step25 formal baseline")
    if historical_readme is None:
        normalized_readme = ""
    else:
        normalized_readme = " ".join(historical_readme.decode("utf-8").split())
    normalized_statement = " ".join(EXPECTED_ALLOWED_STATEMENT.split())
    if normalized_statement not in normalized_readme:
        errors.append("homepage lacks the exact provider-neutral bounded usage statement")
    if any(claim.casefold() in normalized_readme.casefold() for claim in FORBIDDEN_HOMEPAGE_CLAIMS):
        errors.append("homepage contains a forbidden Archify authority or renderer claim")
    if homepage["allowed_statement"] != EXPECTED_ALLOWED_STATEMENT:
        errors.append("recorded homepage statement drifted")

    try:
        from tools.validate_human_front_door import validate_all

        validate_all()
    except Exception as exc:
        errors.append(f"human front-door validator failed: {exc}")

    registry = load_json(CAPABILITY_REGISTRY_PATH)
    operation_ids = [row["operation_id"] for row in registry.get("operations", [])]
    if any("delta" in operation_id.casefold() or "archify" in operation_id.casefold() for operation_id in operation_ids):
        errors.append("Capability Registry contains a Delta or provider-specific Archify operation ID")
    if document["public_expression"]["forbidden_claim_matches"]:
        errors.append("forbidden homepage claim matches were recorded")
    public = document["public_expression"]
    if public["homepage_default"] != "NO_ARCHIFY_BRAND_PROMOTION" or public["architecture_authority"] or public["external_truth"] or public["production_readiness"]:
        errors.append("public expression authority boundary widened")
    if public["owner_aesthetic_endorsement"] != "NOT_GRANTED_NOT_CLAIMED":
        errors.append("aesthetic endorsement boundary widened")
    scope = document["scope_freeze"]
    if scope["architecture_delta"] != "EXPERIMENTAL_EXTENSION_DEFERRED" or scope["agent_reach"] != "NO_CHANGE" or scope["authenticated_channel_admission"] != "NO_CHANGE":
        errors.append("Delta, Agent Reach or authentication boundary changed")
    if scope["live_external_invocation"] != "OPEN_OWNER_DEFERRED_NOT_RUN" or scope["task151"] != "FORBIDDEN":
        errors.append("live invocation or Task151 boundary changed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate()
    if errors:
        print("TASK150_STEP26_FRONT_DOOR_AND_SYNC_SURFACE_RESTRAINT_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK150_STEP26_FRONT_DOOR_AND_SYNC_SURFACE_RESTRAINT_OK homepage=CHANGE_PROVIDER_NEUTRAL_USAGE_ENTRY unchanged_surfaces=20 forbidden_claims=0 brand_promotion=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
