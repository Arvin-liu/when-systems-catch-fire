#!/usr/bin/env python3
"""Validate the canonical current task-lineage/status record."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

try:
    from tools import advance_current_task
except ImportError:  # direct script / tools-on-PYTHONPATH execution
    import advance_current_task


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
STATUS_PATH = ROOT / "data/operations/current-task-lineage-status.json"
SCHEMA_PATH = ROOT / "schemas/operations/current-task-lineage-status-r1.schema.json"
IDENTITY_PATH = ROOT / "data/architecture/current-system-identity.json"
FIXTURE_PATH = ROOT / "data/operations/iterations/129/fixtures/current-task-lineage-status-fixtures-r1.json"
CURRENT_SURFACE_IDS = {"project-current-state", "ai-cold-start", "ai-agents-handoff", "machine-entry"}
CURRENT_SNAPSHOT_BLOCK_RE = re.compile(
    r"<!-- CURRENT-SNAPSHOT:BEGIN profile=(?:human|ai|machine) schema=current-snapshot-r1 -->\n.*?<!-- CURRENT-SNAPSHOT:END -->\n?",
    re.DOTALL,
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_repo_path(relative_path: str) -> Path:
    candidate = (REPO_ROOT / relative_path).resolve()
    try:
        candidate.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes repository: {relative_path}") from exc
    return candidate


def current_surface_paths() -> list[str]:
    identity = load_json(IDENTITY_PATH)
    paths = [row["path"] for row in identity["required_sync_surfaces"] if row["surface_id"] in CURRENT_SURFACE_IDS]
    paths.extend(["ignition/data/architecture/current-facts.json", "ignition/docs/architecture/current-facts.md"])
    return paths


def validate_surface_text(source: dict[str, Any], text: str, label: str) -> list[str]:
    requirements = source["current_surface_status_requirements"]
    errors: list[str] = []
    forbidden = [token for token in requirements["forbidden_status_tokens"] if token in text]
    if forbidden:
        errors.append(f"TASK_LINEAGE_STALE_DEFERRED:{label}:{','.join(forbidden)}")
    missing = [token for token in requirements["required_status_tokens"] if token not in text]
    if missing:
        if "HISTORICAL_UNEXECUTED" not in text and ("COMPLETED" in text or "TASK125_FILE_STATUS" in text):
            errors.append(f"TASK_LINEAGE_OLD_TASK_COMPLETED:{label}")
        elif "REBASED_INTO_127" not in text:
            errors.append(f"TASK_LINEAGE_SUCCESSOR_LINEAGE_MISSING:{label}")
        else:
            errors.append(f"TASK_LINEAGE_CURRENT_STATUS_INCOMPLETE:{label}:{','.join(missing)}")
    return errors


def validate_publication_projection(text: str, label: str) -> list[str]:
    """Keep task-lineage Current surfaces on ref-derived publication semantics."""

    match = CURRENT_SNAPSHOT_BLOCK_RE.search(text)
    if not match:
        return [f"TASK_LINEAGE_PUBLICATION_BLOCK_MISSING:{label}"]
    block = match.group(0)
    errors: list[str] = []
    if "REMOTE_REF_OBSERVATION" not in block:
        errors.append(f"TASK_LINEAGE_PUBLICATION_AUTHORITY_MISSING:{label}")
    if "refs/heads/main" not in block:
        errors.append(f"TASK_LINEAGE_PUBLICATION_REF_MISSING:{label}")
    if "NOT_PUBLISHED" in block or "release_publication_state" in block or "release_task_branch_projection" in block:
        errors.append(f"TASK_LINEAGE_STATIC_PUBLICATION_STATE:{label}")
    if label in {"ignition/AI-START-HERE.md", "ignition/AI-HANDOFF.md"} and "ref-derived verification" not in block:
        errors.append(f"TASK_LINEAGE_AI_PUBLICATION_INSTRUCTION_MISSING:{label}")
    return errors


def validate_history_classification(source: dict[str, Any], path: str, classification: str) -> list[str]:
    if path in set(source["protected_historical_paths"]) and classification == "CURRENT_SURFACE":
        return [f"TASK_LINEAGE_HISTORICAL_MISCLASSIFIED_CURRENT:{path}"]
    return []


def validate_current_surfaces(source: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for relative_path in current_surface_paths():
        try:
            path = resolve_repo_path(relative_path)
            if not path.is_file():
                errors.append(f"TASK_LINEAGE_CURRENT_SURFACE_MISSING:{relative_path}")
                continue
            text = path.read_text(encoding="utf-8")
            errors.extend(validate_surface_text(source, text, relative_path))
            if "current-facts" not in relative_path:
                errors.extend(validate_publication_projection(text, relative_path))
        except (OSError, ValueError) as exc:
            errors.append(f"TASK_LINEAGE_CURRENT_SURFACE_UNREADABLE:{relative_path}:{exc}")

    append_only_path = source["current_surface_status_requirements"]["append_only_current_path"]
    try:
        changelog = resolve_repo_path(append_only_path).read_text(encoding="utf-8")
        task_marker = source["current_task"]["task_id"]
        markers = [line for line in changelog.splitlines() if line.startswith("## ") and task_marker in line]
        if not markers:
            errors.append(f"TASK_LINEAGE_CURRENT_APPEND_MISSING:{append_only_path}")
        else:
            marker = markers[-1]
            latest_section = changelog.rsplit(marker, 1)[-1]
            errors.extend(validate_surface_text(source, latest_section, append_only_path + "#latest-current-task"))
    except (OSError, ValueError) as exc:
        errors.append(f"TASK_LINEAGE_CURRENT_APPEND_UNREADABLE:{append_only_path}:{exc}")

    for protected_path in source["protected_historical_paths"]:
        errors.extend(validate_history_classification(source, protected_path, "HISTORICAL_RECORD"))
    return errors


def validate_fixture_manifest() -> list[str]:
    if not FIXTURE_PATH.is_file():
        return [f"TASK_LINEAGE_FIXTURES_MISSING:{FIXTURE_PATH.relative_to(REPO_ROOT)}"]
    fixture = load_json(FIXTURE_PATH)
    errors: list[str] = []
    if fixture.get("schema_version") != "current-task-lineage-status-fixtures-r1":
        errors.append("TASK_LINEAGE_FIXTURES_SCHEMA_INVALID")
    required = {
        "stale-deferred-current-surface": "TASK_LINEAGE_STALE_DEFERRED",
        "old-task-marked-completed": "TASK_LINEAGE_OLD_TASK_COMPLETED",
        "successor-lineage-missing": "TASK_LINEAGE_SUCCESSOR_LINEAGE_MISSING",
        "historical-record-misclassified-current": "TASK_LINEAGE_HISTORICAL_MISCLASSIFIED_CURRENT",
    }
    rows = {row.get("id"): row for row in fixture.get("fixtures", [])}
    for fixture_id, expected_code in required.items():
        row = rows.get(fixture_id)
        if not row or row.get("kind") != "negative" or row.get("expected_status") != "FAIL" or row.get("expected_code") != expected_code:
            errors.append(f"TASK_LINEAGE_FIXTURE_INCOMPLETE:{fixture_id}")
    return errors


def validate(document: dict[str, Any] | None = None) -> list[str]:
    if not STATUS_PATH.is_file():
        return [f"missing canonical task-lineage source: {STATUS_PATH.relative_to(REPO_ROOT)}"]
    if not SCHEMA_PATH.is_file():
        return [f"missing task-lineage schema: {SCHEMA_PATH.relative_to(REPO_ROOT)}"]
    source = document if document is not None else load_json(STATUS_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(source)]
    if errors:
        return errors

    current_task = source["current_task"]
    if "task_identity" in source:
        errors.extend(advance_current_task.validate_state(source))
    if current_task["execution_status"] == "IN_PROGRESS" and current_task["terminal"]:
        errors.append("IN_PROGRESS current task cannot be terminal")
    if current_task["execution_status"] in {"COMPLETED_WITH_CLASSIFIED_RESIDUALS", "COMPLETED_WITH_OPEN_OBLIGATIONS"} and not current_task["terminal"]:
        errors.append("completed current task must be terminal")
    if source["current_state"]["current_state_status"] != "CURRENT_WITH_OPEN_OBLIGATIONS":
        errors.append("current state status must remain CURRENT_WITH_OPEN_OBLIGATIONS")
    if source["current_state"]["epistemically_accepted"] != 0:
        errors.append("epistemically_accepted must remain exactly 0")

    lineage_ids = [lineage["lineage_id"] for lineage in source["lineages"]]
    if len(lineage_ids) != len(set(lineage_ids)):
        errors.append("duplicate task lineage id")
    for lineage in source["lineages"]:
        predecessor = lineage["predecessor"]
        successor = lineage["successor"]
        if predecessor["task_file_status"] == "HISTORICAL_UNEXECUTED" and predecessor["requirement_lineage_status"] != "REBASED_INTO_127":
            errors.append("unexecuted 125 file must explicitly carry REBASED_INTO_127 requirement lineage")
        if successor["execution_status"] == "COMPLETED_WITH_CLASSIFIED_RESIDUALS" and successor["new_regressions"] != 0:
            errors.append("127 classified-completion lineage must record new_regressions=0")
        for token in lineage["current_surface_rule"]["forbidden_status_tokens"]:
            if token not in {"DEFERRED_PENDING_REBASE", "DEFERRED"}:
                errors.append(f"unexpected forbidden current-status token: {token}")
        for provenance in lineage["provenance"]:
            if provenance["repository"] == "Arvin-liu/when-systems-catch-fire":
                try:
                    if not resolve_repo_path(provenance["path"]).is_file():
                        errors.append(f"missing local lineage provenance: {provenance['path']}")
                except ValueError as exc:
                    errors.append(str(exc))
    for path in source["protected_historical_paths"]:
        try:
            if not resolve_repo_path(path).is_file():
                errors.append(f"missing protected historical path: {path}")
        except ValueError as exc:
            errors.append(str(exc))
    errors.extend(validate_current_surfaces(source))
    errors.extend(validate_fixture_manifest())
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("CURRENT_TASK_LINEAGE_STATUS_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("CURRENT_TASK_LINEAGE_STATUS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
