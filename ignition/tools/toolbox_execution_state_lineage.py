#!/usr/bin/env python3
"""Audit caller-declared checkpoint branches, active-path accounting and resume bindings."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
IGNITION_ROOT = HERE.parents[1]
INPUT_SCHEMA = IGNITION_ROOT / "schemas/operations/toolbox-execution-state-lineage-input-r0.schema.json"
MAX_INPUT_BYTES = 262_144
MAX_FINDINGS = 128
TOOL_ID = "maintenance.audit_execution_state_lineage"
TOOL_VERSION = "0.1.0"
CLAIM_CEILING = (
    "Checks only the structure of caller-declared checkpoint parent links, active and inactive leaf accounting, "
    "resume-capsule identity bindings, and rollback ancestor references. It does not authenticate callers, records, "
    "digests, state bytes, branch isolation, compression quality, execution, or external effects; it reads no checkpoint "
    "state and grants no permission."
)


class DuplicateJSONKey(ValueError):
    """Raised when a JSON object repeats a key."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJSONKey(key)
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _finding(code: str, path: str) -> dict[str, str]:
    return {"code": code, "path": path}


def _sorted_findings(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    unique = {(row["code"], row["path"]) for row in rows}
    return [
        {"code": code, "path": path}
        for code, path in sorted(unique)[:MAX_FINDINGS]
    ]


def _safe_document(raw: bytes) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    if len(raw) > MAX_INPUT_BYTES:
        return None, [_finding("INPUT_TOO_LARGE", "$")]
    try:
        document = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except DuplicateJSONKey:
        return None, [_finding("INPUT_DUPLICATE_JSON_KEY", "$")]
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return None, [_finding("INPUT_INVALID_JSON", "$")]
    if not isinstance(document, dict):
        return None, [_finding("INPUT_SCHEMA_INVALID", "$")]
    try:
        schema = json.loads(INPUT_SCHEMA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, [_finding("LOCAL_INPUT_SCHEMA_UNAVAILABLE", "$")]
    problems = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: (list(map(str, error.absolute_path)), error.validator or ""),
    )
    findings = [
        _finding(
            "INPUT_SCHEMA_INVALID",
            "$" + ("/" + "/".join(str(part) for part in error.absolute_path) if error.absolute_path else ""),
        )
        for error in problems[:MAX_FINDINGS]
    ]
    if findings:
        return document, findings
    return document, []


def _is_ancestor(ancestor_id: str, descendant_id: str, parents: dict[str, str | None]) -> bool:
    cursor: str | None = descendant_id
    visited: set[str] = set()
    while cursor is not None and cursor not in visited:
        if cursor == ancestor_id:
            return True
        visited.add(cursor)
        cursor = parents.get(cursor)
    return False


def _analyze_graph(document: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    findings: list[dict[str, str]] = []
    checkpoints = document.get("checkpoints", [])
    if not isinstance(checkpoints, list):
        checkpoints = []

    by_id: dict[str, dict[str, Any]] = {}
    for index, checkpoint in enumerate(checkpoints):
        if not isinstance(checkpoint, dict):
            continue
        checkpoint_id = checkpoint.get("checkpoint_id")
        if not isinstance(checkpoint_id, str):
            continue
        if checkpoint_id in by_id:
            findings.append(_finding("DUPLICATE_CHECKPOINT_ID", f"$/checkpoints/{index}/checkpoint_id"))
        else:
            by_id[checkpoint_id] = checkpoint

    parents: dict[str, str | None] = {}
    children: dict[str, list[str]] = {checkpoint_id: [] for checkpoint_id in by_id}
    # Build links from the first record for each ID so duplicate IDs cannot silently replace a parent.
    first_indexes: dict[str, int] = {}
    for index, checkpoint in enumerate(checkpoints):
        if isinstance(checkpoint, dict) and isinstance(checkpoint.get("checkpoint_id"), str):
            first_indexes.setdefault(checkpoint["checkpoint_id"], index)
    for checkpoint_id, checkpoint in by_id.items():
        parent_id = checkpoint.get("parent_checkpoint_id")
        parents[checkpoint_id] = parent_id if isinstance(parent_id, str) else None
        if parent_id is None:
            continue
        if parent_id not in by_id:
            findings.append(_finding("PARENT_CHECKPOINT_UNKNOWN", f"$/checkpoints/{first_indexes[checkpoint_id]}/parent_checkpoint_id"))
            continue
        children[parent_id].append(checkpoint_id)
        if parent_id == checkpoint_id:
            findings.append(_finding("CHECKPOINT_SELF_PARENT", f"$/checkpoints/{first_indexes[checkpoint_id]}/parent_checkpoint_id"))
        if checkpoint.get("run_id") != by_id[parent_id].get("run_id"):
            findings.append(_finding("PARENT_RUN_ID_MISMATCH", f"$/checkpoints/{first_indexes[checkpoint_id]}/run_id"))

    colors: dict[str, int] = {}
    cycle_nodes: set[str] = set()

    def visit(checkpoint_id: str) -> None:
        color = colors.get(checkpoint_id, 0)
        if color == 1:
            cycle_nodes.add(checkpoint_id)
            return
        if color == 2:
            return
        colors[checkpoint_id] = 1
        parent_id = parents.get(checkpoint_id)
        if parent_id in by_id:
            if colors.get(parent_id, 0) == 1:
                cycle_nodes.update({checkpoint_id, parent_id})
            else:
                visit(parent_id)
        colors[checkpoint_id] = 2

    for checkpoint_id in sorted(by_id):
        visit(checkpoint_id)
    for checkpoint_id in sorted(cycle_nodes):
        findings.append(_finding("CHECKPOINT_PARENT_CYCLE", f"$/checkpoints/{first_indexes[checkpoint_id]}/parent_checkpoint_id"))

    leaf_ids = sorted(checkpoint_id for checkpoint_id, child_ids in children.items() if not child_ids)
    active_id = document.get("active_checkpoint_id")
    active_path: list[str] = []
    if not isinstance(active_id, str) or active_id not in by_id:
        findings.append(_finding("ACTIVE_CHECKPOINT_UNKNOWN", "$/active_checkpoint_id"))
    else:
        if children.get(active_id):
            findings.append(_finding("ACTIVE_CHECKPOINT_NOT_LEAF", "$/active_checkpoint_id"))
        cursor: str | None = active_id
        visited_path: set[str] = set()
        while cursor is not None and cursor in by_id and cursor not in visited_path:
            visited_path.add(cursor)
            active_path.append(cursor)
            cursor = parents.get(cursor)
        active_path.reverse()

    expected_inactive = sorted(set(leaf_ids) - ({active_id} if isinstance(active_id, str) else set()))
    declared_inactive = document.get("declared_inactive_tip_checkpoint_ids", [])
    if not isinstance(declared_inactive, list):
        declared_inactive = []
    declared_inactive_sorted = sorted(value for value in declared_inactive if isinstance(value, str))
    if set(declared_inactive_sorted) != set(expected_inactive):
        findings.append(_finding("INACTIVE_TIP_ACCOUNTING_MISMATCH", "$/declared_inactive_tip_checkpoint_ids"))

    declared_path = document.get("declared_active_path_checkpoint_ids")
    if isinstance(declared_path, list) and declared_path != active_path:
        findings.append(_finding("DECLARED_ACTIVE_PATH_MISMATCH", "$/declared_active_path_checkpoint_ids"))

    branch_points = [
        {
            "parent_checkpoint_id": checkpoint_id,
            "child_checkpoint_ids": sorted(child_ids),
        }
        for checkpoint_id, child_ids in sorted(children.items())
        if len(child_ids) > 1
    ]

    seen_capsules: set[str] = set()
    resume_capsules = document.get("resume_capsules", [])
    if not isinstance(resume_capsules, list):
        resume_capsules = []
    for index, capsule in enumerate(resume_capsules):
        if not isinstance(capsule, dict):
            continue
        capsule_id = capsule.get("capsule_id")
        path = f"$/resume_capsules/{index}"
        if isinstance(capsule_id, str):
            if capsule_id in seen_capsules:
                findings.append(_finding("DUPLICATE_RESUME_CAPSULE_ID", f"{path}/capsule_id"))
            seen_capsules.add(capsule_id)
        checkpoint_id = capsule.get("checkpoint_id")
        checkpoint = by_id.get(checkpoint_id) if isinstance(checkpoint_id, str) else None
        if checkpoint is None:
            findings.append(_finding("RESUME_CHECKPOINT_UNKNOWN", f"{path}/checkpoint_id"))
            continue
        if capsule.get("run_id") != checkpoint.get("run_id"):
            findings.append(_finding("RESUME_RUN_ID_MISMATCH", f"{path}/run_id"))
        if capsule.get("state_ref") != checkpoint.get("state_ref"):
            findings.append(_finding("RESUME_STATE_REF_MISMATCH", f"{path}/state_ref"))
        if capsule.get("state_sha256") != checkpoint.get("state_sha256"):
            findings.append(_finding("RESUME_STATE_DIGEST_MISMATCH", f"{path}/state_sha256"))
        if capsule.get("from_executor_id") == capsule.get("to_executor_id"):
            findings.append(_finding("RESUME_EXECUTOR_NOT_CHANGED", f"{path}/to_executor_id"))

    rollback_records = document.get("rollback_records", [])
    if not isinstance(rollback_records, list):
        rollback_records = []
    seen_rollbacks: set[str] = set()
    for index, rollback in enumerate(rollback_records):
        if not isinstance(rollback, dict):
            continue
        rollback_id = rollback.get("rollback_id")
        path = f"$/rollback_records/{index}"
        if isinstance(rollback_id, str):
            if rollback_id in seen_rollbacks:
                findings.append(_finding("DUPLICATE_ROLLBACK_ID", f"{path}/rollback_id"))
            seen_rollbacks.add(rollback_id)
        from_id = rollback.get("from_checkpoint_id")
        to_id = rollback.get("to_checkpoint_id")
        if from_id not in by_id:
            findings.append(_finding("ROLLBACK_SOURCE_UNKNOWN", f"{path}/from_checkpoint_id"))
            continue
        if to_id not in by_id:
            findings.append(_finding("ROLLBACK_TARGET_UNKNOWN", f"{path}/to_checkpoint_id"))
            continue
        if from_id == to_id or not _is_ancestor(to_id, from_id, parents):
            findings.append(_finding("ROLLBACK_TARGET_NOT_ANCESTOR", f"{path}/to_checkpoint_id"))

    summary = {
        "active_path_checkpoint_ids": active_path,
        "leaf_checkpoint_ids": leaf_ids,
        "expected_inactive_tip_checkpoint_ids": expected_inactive,
        "declared_inactive_tip_checkpoint_ids": declared_inactive_sorted,
        "branch_points": branch_points,
    }
    return summary, _sorted_findings(findings)


def analyze(raw: bytes) -> dict[str, Any]:
    document, schema_findings = _safe_document(raw)
    if document is None:
        document = {}
    if schema_findings:
        graph = {
            "active_path_checkpoint_ids": [],
            "leaf_checkpoint_ids": [],
            "expected_inactive_tip_checkpoint_ids": [],
            "declared_inactive_tip_checkpoint_ids": [],
            "branch_points": [],
        }
        findings = schema_findings
    else:
        graph, findings = _analyze_graph(document)

    active_id = document.get("active_checkpoint_id")
    if not isinstance(active_id, str):
        active_id = None
    task_ref = document.get("task_ref")
    if not isinstance(task_ref, str) or not task_ref.strip():
        task_ref = "UNKNOWN"
    checkpoint_rows = document.get("checkpoints", [])
    capsule_rows = document.get("resume_capsules", [])
    rollback_rows = document.get("rollback_records", [])
    status = "PASS" if not findings else "FAIL"
    report = {
        "schema_version": "toolbox-execution-state-lineage-output-r0",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "task_ref": task_ref,
        "status": status,
        "result_code": "CHECKPOINT_LINEAGE_VALID" if status == "PASS" else "CHECKPOINT_LINEAGE_INVALID",
        "active_checkpoint_id": active_id,
        **graph,
        "checkpoint_count": len(checkpoint_rows) if isinstance(checkpoint_rows, list) else 0,
        "resume_capsule_count": len(capsule_rows) if isinstance(capsule_rows, list) else 0,
        "rollback_record_count": len(rollback_rows) if isinstance(rollback_rows, list) else 0,
        "findings": findings,
        "source_authentication": "NOT_PERFORMED",
        "caller_declarations_authenticated": False,
        "checkpoint_state_bytes_read": False,
        "network_calls": 0,
        "write_effects": False,
        "execution_authorized": False,
        "claim_ceiling": CLAIM_CEILING,
        "input_sha256": _sha256(raw),
        "tool_source_sha256": _sha256(HERE.read_bytes()),
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded JSON object from stdin")
    parser.parse_args(argv)
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    report = analyze(raw)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
