#!/usr/bin/env python3
"""Validate caller-declared version and handoff relations in a research episode manifest."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import re
import sys
from typing import Any

from jsonschema import Draft202012Validator


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve()
IGNITION_ROOT = HERE.parents[1]
SCHEMA_PATH = IGNITION_ROOT / "schemas/operations/toolbox-portable-research-episode-r0.schema.json"
MAX_INPUT_BYTES = 262_144
MAX_FINDINGS = 64
TOOL_ID = "collaboration.validate_portable_research_episode"
TOOL_VERSION = "0.1.0"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
RFC3339_DATE_TIME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)

CLAIM_CEILING = (
    "Checks only schema and caller-declared episode, artifact-version, execution, review, omission, and fork-map relations. "
    "It does not authenticate any source, actor, digest, execution, review, or permission; read package bytes; import or fork files; "
    "execute code; validate scientific meaning; or authorize research, publication, or external action."
)


class DuplicateJSONKey(ValueError):
    """Raised when any JSON object repeats a key."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJSONKey
        result[key] = value
    return result


def _pointer(path: Any) -> str:
    parts = [str(item).replace("~", "~0").replace("/", "~1") for item in path]
    return "$" + ("/" + "/".join(parts) if parts else "")


def _finding(code: str, path: str) -> dict[str, str]:
    return {"code": code, "path": path}


def _ref_key(ref: dict[str, Any]) -> tuple[str, str, str]:
    return (ref["artifact_id"], ref["version_id"], ref["sha256"])


def _schema_findings(episode: Any) -> list[dict[str, str]]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    problems = sorted(
        validator.iter_errors(episode),
        key=lambda error: (list(map(str, error.absolute_path)), error.validator or ""),
    )
    findings = [_finding("INPUT_SCHEMA_INVALID", _pointer(problem.absolute_path)) for problem in problems[:MAX_FINDINGS]]
    # The jsonschema package may omit its optional RFC 3339 format dependency.
    # Enforce the declared review timestamp contract with the Python stdlib.
    if isinstance(episode, dict) and isinstance(episode.get("reviews"), list):
        for index, review in enumerate(episode["reviews"]):
            if not isinstance(review, dict):
                continue
            value = review.get("reviewed_at_utc")
            if not isinstance(value, str) or not RFC3339_DATE_TIME_RE.fullmatch(value):
                findings.append(_finding("INPUT_SCHEMA_INVALID", f"$/reviews/{index}/reviewed_at_utc"))
                continue
            normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
            try:
                parsed = datetime.fromisoformat(normalized)
            except ValueError:
                findings.append(_finding("INPUT_SCHEMA_INVALID", f"$/reviews/{index}/reviewed_at_utc"))
                continue
            if parsed.tzinfo is None:
                findings.append(_finding("INPUT_SCHEMA_INVALID", f"$/reviews/{index}/reviewed_at_utc"))
    return findings[:MAX_FINDINGS]


def _semantic_findings(episode: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]], bool]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    incomplete = False

    artifacts: dict[tuple[str, str, str], dict[str, Any]] = {}
    versions: dict[tuple[str, str], dict[str, Any]] = {}
    current_by_artifact: dict[str, list[str]] = {}
    for index, artifact in enumerate(episode["artifacts"]):
        path = f"$/artifacts/{index}"
        version_key = (artifact["artifact_id"], artifact["version_id"])
        if version_key in versions:
            errors.append(_finding("DUPLICATE_ARTIFACT_VERSION", path))
            continue
        versions[version_key] = artifact
        if not SHA256_RE.fullmatch(artifact["sha256"]):
            errors.append(_finding("ARTIFACT_DIGEST_INVALID", f"{path}/sha256"))
        artifacts[(artifact["artifact_id"], artifact["version_id"], artifact["sha256"])] = artifact
        if artifact["is_current"]:
            current_by_artifact.setdefault(artifact["artifact_id"], []).append(artifact["version_id"])
        if artifact["availability"] == "INCLUDED" and artifact["omission_reason"] is not None:
            errors.append(_finding("INCLUDED_ARTIFACT_HAS_OMISSION_REASON", f"{path}/omission_reason"))
        if artifact["availability"] == "OMITTED" and artifact["omission_reason"] is None:
            errors.append(_finding("OMITTED_ARTIFACT_NO_REASON", f"{path}/omission_reason"))
        if artifact["availability"] == "OMITTED":
            if artifact["required"]:
                incomplete = True
                warnings.append(_finding("REQUIRED_ARTIFACT_BYTES_OMITTED", path))
            else:
                warnings.append(_finding("OPTIONAL_ARTIFACT_BYTES_OMITTED", path))

    for artifact_id, current_versions in current_by_artifact.items():
        if len(current_versions) > 1:
            errors.append(_finding("MULTIPLE_CURRENT_VERSIONS", f"$/artifacts/{artifact_id}"))

    omissions: dict[tuple[str, str | None], dict[str, Any]] = {}
    for index, omission in enumerate(episode["omissions"]):
        path = f"$/omissions/{index}"
        key = (omission["artifact_id"], omission["version_id"])
        if key in omissions:
            errors.append(_finding("DUPLICATE_OMISSION_RECORD", path))
        omissions[key] = omission
        if omission["required"]:
            incomplete = True
            warnings.append(_finding("REQUIRED_CONTENT_EXPLICITLY_OMITTED", path))
        else:
            warnings.append(_finding("OPTIONAL_CONTENT_EXPLICITLY_OMITTED", path))
        if omission["rationale"].strip() == "":
            errors.append(_finding("OMISSION_RATIONALE_EMPTY", f"{path}/rationale"))

    for index, artifact in enumerate(episode["artifacts"]):
        if (artifact["artifact_id"], artifact["version_id"]) in omissions:
            errors.append(_finding("ARTIFACT_VERSION_BOTH_PRESENT_AND_OMITTED", f"$/artifacts/{index}"))

    for index, artifact_id in enumerate(episode["required_artifact_ids"]):
        known = any(key[0] == artifact_id for key in versions)
        omitted = any(key[0] == artifact_id and record["required"] for key, record in omissions.items())
        if not known and not omitted:
            incomplete = True
            warnings.append(_finding("REQUIRED_ARTIFACT_UNACCOUNTED", f"$/required_artifact_ids/{index}"))
        if known and not any(row["required"] and row["availability"] == "INCLUDED" for key, row in versions.items() if key[0] == artifact_id):
            incomplete = True
            warnings.append(_finding("REQUIRED_ARTIFACT_NOT_INCLUDED", f"$/required_artifact_ids/{index}"))

    dependency_graph: dict[tuple[str, str, str], list[tuple[str, str, str]]] = {}
    for index, artifact in enumerate(episode["artifacts"]):
        path = f"$/artifacts/{index}"
        key = (artifact["artifact_id"], artifact["version_id"], artifact["sha256"])
        dependencies = list(artifact["dependency_refs"])
        parent = artifact["parent_ref"]
        if parent is not None:
            if parent["artifact_id"] != artifact["artifact_id"]:
                errors.append(_finding("PARENT_REF_CHANGES_LOGICAL_ARTIFACT_ID", f"{path}/parent_ref/artifact_id"))
            dependencies.append(parent)
        resolved: list[tuple[str, str, str]] = []
        for ref_index, ref in enumerate(dependencies):
            ref_key = _ref_key(ref)
            if ref_key not in artifacts:
                errors.append(_finding("ARTIFACT_VERSION_REF_UNKNOWN", f"{path}/dependency_refs/{ref_index}"))
            else:
                resolved.append(ref_key)
        dependency_graph[key] = resolved

    visiting: set[tuple[str, str, str]] = set()
    visited: set[tuple[str, str, str]] = set()

    def visit(node: tuple[str, str, str]) -> None:
        if node in visiting:
            errors.append(_finding("ARTIFACT_DEPENDENCY_CYCLE", "$/artifacts"))
            return
        if node in visited:
            return
        visiting.add(node)
        for child in dependency_graph.get(node, []):
            visit(child)
        visiting.remove(node)
        visited.add(node)

    for node in dependency_graph:
        visit(node)

    execution_ids: set[str] = set()
    execution_statuses: Counter[str] = Counter()
    for index, execution in enumerate(episode["executions"]):
        path = f"$/executions/{index}"
        execution_id = execution["execution_id"]
        if execution_id in execution_ids:
            errors.append(_finding("DUPLICATE_EXECUTION_ID", f"{path}/execution_id"))
        execution_ids.add(execution_id)
        status = execution["status"]
        execution_statuses[status] += 1
        run_ref = execution["run_ref"]
        if status in {"ATTEMPTED", "EXECUTED"} and run_ref is None:
            errors.append(_finding("EXECUTION_STATUS_REQUIRES_RUN_REF", f"{path}/run_ref"))
        if status in {"PLANNED", "NOT_EXECUTED", "UNKNOWN"} and run_ref is not None:
            errors.append(_finding("NONRUN_STATUS_HAS_RUN_REF", f"{path}/run_ref"))
        if status in {"PLANNED", "NOT_EXECUTED", "UNKNOWN"} and execution["used_artifact_refs"]:
            errors.append(_finding("NONRUN_STATUS_CLAIMS_USED_INPUT", f"{path}/used_artifact_refs"))
        if status in {"PLANNED", "NOT_EXECUTED", "UNKNOWN"} and execution["produced_artifact_refs"]:
            errors.append(_finding("NONRUN_STATUS_CLAIMS_PRODUCED_OUTPUT", f"{path}/produced_artifact_refs"))
        if status == "NOT_EXECUTED" and not execution["not_executed_reason"].strip():
            errors.append(_finding("NOT_EXECUTED_REASON_MISSING", f"{path}/not_executed_reason"))
        if status != "NOT_EXECUTED" and execution["not_executed_reason"] is not None:
            errors.append(_finding("NOT_EXECUTED_REASON_ON_OTHER_STATUS", f"{path}/not_executed_reason"))
        for relation in ("used_artifact_refs", "attached_artifact_refs", "produced_artifact_refs"):
            for ref_index, ref in enumerate(execution[relation]):
                if _ref_key(ref) not in artifacts:
                    errors.append(_finding("EXECUTION_ARTIFACT_REF_UNKNOWN", f"{path}/{relation}/{ref_index}"))

    review_ids: set[str] = set()
    for index, review in enumerate(episode["reviews"]):
        path = f"$/reviews/{index}"
        review_id = review["review_id"]
        if review_id in review_ids:
            errors.append(_finding("DUPLICATE_REVIEW_ID", f"{path}/review_id"))
        review_ids.add(review_id)
        target = _ref_key(review["target_ref"])
        artifact = artifacts.get(target)
        if artifact is None:
            errors.append(_finding("REVIEW_TARGET_VERSION_UNKNOWN", f"{path}/target_ref"))
        elif artifact["version_id"] != current_by_artifact.get(artifact["artifact_id"], [None])[0]:
            warnings.append(_finding("REVIEW_TARGET_IS_NOT_CURRENT_VERSION", f"{path}/target_ref"))

    mapping_ids: set[tuple[str, str]] = set()
    fork_destinations: set[tuple[str, str]] = set()
    mapped_pairs: set[tuple[str, str]] = set()
    for index, mapping in enumerate(episode["fork_id_mappings"]):
        path = f"$/fork_id_mappings/{index}"
        source_key = (mapping["entity_type"], mapping["source_id"])
        dest_key = (mapping["entity_type"], mapping["fork_id"])
        if source_key in mapping_ids:
            errors.append(_finding("DUPLICATE_FORK_ID_MAPPING_SOURCE", path))
        if dest_key in fork_destinations:
            errors.append(_finding("DUPLICATE_FORK_ID_MAPPING_DESTINATION", path))
        if mapping["source_id"] == mapping["fork_id"]:
            errors.append(_finding("FORK_ID_MAPPING_DOES_NOT_REMAP", path))
        mapping_ids.add(source_key)
        fork_destinations.add(dest_key)
        mapped_pairs.add(source_key)

    if episode["import_mode"] == "SOURCE_PACKAGE" and episode["fork_id_mappings"]:
        errors.append(_finding("SOURCE_PACKAGE_HAS_FORK_ID_MAPPINGS", "$/fork_id_mappings"))
    if episode["import_mode"] == "READ_ONLY_FORK_PREVIEW":
        required_mappings = {("EPISODE", episode["episode_id"])}
        required_mappings.update(("ARTIFACT", artifact["artifact_id"]) for artifact in episode["artifacts"])
        required_mappings.update(("ARTIFACT", item["artifact_id"]) for item in episode["omissions"])
        required_mappings.update(("EXECUTION", row["execution_id"]) for row in episode["executions"])
        required_mappings.update(("REVIEW", row["review_id"]) for row in episode["reviews"])
        missing = sorted(required_mappings - mapped_pairs)
        if missing:
            errors.append(_finding("FORK_ID_MAPPING_INCOMPLETE", "$/fork_id_mappings"))

    return errors[:MAX_FINDINGS], warnings[:MAX_FINDINGS], incomplete


def validate_episode(episode: Any) -> dict[str, Any]:
    """Validate one declared episode manifest; do not read or import its package."""
    if not isinstance(episode, dict):
        return {
            "tool_id": TOOL_ID,
            "tool_version": TOOL_VERSION,
            "episode_id": None,
            "status": "EPISODE_MANIFEST_INVALID",
            "checks": {"input_schema": "FAIL", "cross_reference_consistency": "NOT_RUN"},
            "findings": [_finding("INPUT_MUST_BE_OBJECT", "$")],
            "warnings": [],
            "summary": {},
            "execution_authorized": False,
            "import_performed": False,
            "artifact_bytes_verified": False,
            "claim_ceiling": CLAIM_CEILING,
        }

    schema_findings = _schema_findings(episode)
    if schema_findings:
        return {
            "tool_id": TOOL_ID,
            "tool_version": TOOL_VERSION,
            "episode_id": episode.get("episode_id") if isinstance(episode.get("episode_id"), str) else None,
            "status": "EPISODE_MANIFEST_INVALID",
            "checks": {"input_schema": "FAIL", "cross_reference_consistency": "NOT_RUN"},
            "findings": schema_findings,
            "warnings": [],
            "summary": {},
            "execution_authorized": False,
            "import_performed": False,
            "artifact_bytes_verified": False,
            "claim_ceiling": CLAIM_CEILING,
        }

    errors, warnings, incomplete = _semantic_findings(episode)
    if errors:
        status = "EPISODE_MANIFEST_INVALID"
    elif incomplete:
        status = "EPISODE_MANIFEST_INCOMPLETE"
    else:
        status = "EPISODE_MANIFEST_CONSISTENT"
    execution_statuses = Counter(row["status"] for row in episode["executions"])
    summary = {
        "artifact_version_count": len(episode["artifacts"]),
        "included_artifact_version_count": sum(row["availability"] == "INCLUDED" for row in episode["artifacts"]),
        "omitted_artifact_version_count": sum(row["availability"] == "OMITTED" for row in episode["artifacts"]),
        "explicit_omission_count": len(episode["omissions"]),
        "execution_status_counts": dict(sorted(execution_statuses.items())),
        "used_reference_count": sum(len(row["used_artifact_refs"]) for row in episode["executions"]),
        "attached_reference_count": sum(len(row["attached_artifact_refs"]) for row in episode["executions"]),
        "review_count": len(episode["reviews"]),
        "fork_id_mapping_count": len(episode["fork_id_mappings"]),
        "import_mode": episode["import_mode"],
        "execution_relations": [
            {
                "execution_id": row["execution_id"],
                "declared_status": row["status"],
                "run_ref_present": row["run_ref"] is not None,
                "used_artifact_ref_count": len(row["used_artifact_refs"]),
                "attached_artifact_ref_count": len(row["attached_artifact_refs"]),
                "produced_artifact_ref_count": len(row["produced_artifact_refs"]),
            }
            for row in episode["executions"]
        ],
    }
    return {
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "episode_id": episode["episode_id"],
        "status": status,
        "checks": {"input_schema": "PASS", "cross_reference_consistency": "FAIL" if errors else "PASS"},
        "findings": errors,
        "warnings": warnings,
        "summary": summary,
        "execution_authorized": False,
        "import_performed": False,
        "artifact_bytes_verified": False,
        "claim_ceiling": CLAIM_CEILING,
    }


def _read_stdin() -> Any:
    data = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    if len(data) > MAX_INPUT_BYTES:
        raise ValueError("input exceeds the 262144-byte limit")
    return json.loads(data.decode("utf-8"), object_pairs_hook=_unique_object)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded episode manifest from stdin")
    parser.parse_args(argv)
    try:
        episode = _read_stdin()
        result = validate_episode(episode)
    except DuplicateJSONKey:
        result = {
            "tool_id": TOOL_ID,
            "tool_version": TOOL_VERSION,
            "episode_id": None,
            "status": "EPISODE_MANIFEST_INVALID",
            "checks": {"input_schema": "FAIL", "cross_reference_consistency": "NOT_RUN"},
            "findings": [_finding("DUPLICATE_JSON_KEY", "$")],
            "warnings": [],
            "summary": {},
            "execution_authorized": False,
            "import_performed": False,
            "artifact_bytes_verified": False,
            "claim_ceiling": CLAIM_CEILING,
        }
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError):
        result = {
            "tool_id": TOOL_ID,
            "tool_version": TOOL_VERSION,
            "episode_id": None,
            "status": "EPISODE_MANIFEST_INVALID",
            "checks": {"input_schema": "FAIL", "cross_reference_consistency": "NOT_RUN"},
            "findings": [_finding("INPUT_UNAVAILABLE_OR_INVALID", "$")],
            "warnings": [],
            "summary": {},
            "execution_authorized": False,
            "import_performed": False,
            "artifact_bytes_verified": False,
            "claim_ceiling": CLAIM_CEILING,
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "EPISODE_MANIFEST_CONSISTENT" else 2


if __name__ == "__main__":
    raise SystemExit(main())
