#!/usr/bin/env python3
"""Validate the content-owned, repository-local Current release lifecycle record."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
LIFECYCLE_PATH = ROOT / "data/operations/current-release-lifecycle-r1.json"
SCHEMA_PATH = ROOT / "schemas/operations/current-release-lifecycle-r1.schema.json"
LINEAGE_PATH = ROOT / "data/operations/current-task-lineage-status.json"
IDENTITY_PATH = ROOT / "data/architecture/current-system-identity.json"
AUDIT_PATH = ROOT / "data/operations/iterations/131/step02-lifecycle-migration-audit.json"

PHASES = ["RUNNING", "TERMINAL_CANDIDATE", "RELEASE_READY"]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def validate(document: dict[str, Any] | None = None) -> list[str]:
    lifecycle = document if document is not None else load_json(LIFECYCLE_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(lifecycle)]
    if errors:
        return errors
    lineage = load_json(LINEAGE_PATH)
    identity = load_json(IDENTITY_PATH)
    current_task = lineage["current_task"]
    if lifecycle["task_id"] != current_task["task_id"]:
        errors.append("lifecycle task_id differs from canonical current task")
    if lifecycle["identity_epoch"] != identity["identity_epoch"]:
        errors.append("lifecycle identity_epoch differs from current identity epoch")
    if lifecycle["current_iteration_boundary"] != identity["current_iteration_boundary"]:
        errors.append("lifecycle boundary differs from current identity boundary")
    if lifecycle["latest_architecture_changing_task"] == lifecycle["task_id"]:
        errors.append("presentation-only Current task cannot also be latest architecture-changing task")
    if current_task["identity_impact"] != "PRESENTATION_ONLY":
        errors.append("release lifecycle requires PRESENTATION_ONLY identity impact")
    if lifecycle["phase_order"] != PHASES:
        errors.append("phase_order must preserve the content-owned lifecycle order")
    if lifecycle["required_publication_ref"] != "refs/heads/main":
        errors.append("required_publication_ref must be refs/heads/main")
    if lifecycle["publication_authority"] != "REMOTE_REF_OBSERVATION":
        errors.append("publication_authority must be REMOTE_REF_OBSERVATION")
    if lifecycle["embedded_publication_assertion"] != "NONE":
        errors.append("embedded_publication_assertion must remain NONE")
    phase = lifecycle["content_phase"]
    if phase == "RUNNING":
        if lifecycle["current_task_terminal"]:
            errors.append("RUNNING lifecycle cannot be terminal")
    if phase in {"TERMINAL_CANDIDATE", "RELEASE_READY"} and not lifecycle["current_task_terminal"]:
        errors.append(f"{phase} lifecycle must be terminal")
    if "sha" in json.dumps(lifecycle, ensure_ascii=False).casefold() or "commit" in lifecycle:
        errors.append("lifecycle record must not carry a release self-SHA")
    return errors


def audit() -> dict[str, Any]:
    errors = validate()
    lifecycle = load_json(LIFECYCLE_PATH)
    return {
        "schema_version": "current-release-lifecycle-audit-r1",
        "task_id": lifecycle["task_id"],
        "result": "PASS" if not errors else "FAIL",
        "content_phase": lifecycle["content_phase"],
        "publication_authority": lifecycle["publication_authority"],
        "embedded_publication_assertion": lifecycle["embedded_publication_assertion"],
        "lifecycle_sha256": hashlib.sha256(LIFECYCLE_PATH.read_bytes()).hexdigest(),
        "errors": errors,
        "claim_ceiling": "Lifecycle validation is repository-local content-readiness evidence only; it is not remote publication, external truth, Owner acceptance or epistemic acceptance."
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = audit()
    if args.write:
        AUDIT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"CURRENT_RELEASE_LIFECYCLE_AUDIT_WRITTEN path={relative(AUDIT_PATH)} result={result['result']}")
        return 0 if result["result"] == "PASS" else 1
    if result["result"] != "PASS":
        print("CURRENT_RELEASE_LIFECYCLE_INVALID", file=sys.stderr)
        for error in result["errors"]:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"CURRENT_RELEASE_LIFECYCLE_OK content_phase={result['content_phase']} publication_authority={result['publication_authority']} embedded_publication_assertion={result['embedded_publication_assertion']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
