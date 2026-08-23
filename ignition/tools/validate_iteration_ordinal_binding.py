#!/usr/bin/env python3
"""Fail-closed ordinal binding for the Task135 release transaction.

Task identity is read from canonical records and ordinals are always derived
with ``task_identity.parse_task_id``.  The gate deliberately keeps the latest
architecture-changing task as a separate role: it may differ from the formal
task without causing a failure.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from tools import task_identity
except ImportError:  # direct script / tools-on-PYTHONPATH execution
    import task_identity


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
CONTRACT_PATH = ROOT / "data/operations/iterations/135/execution-contract-r1.json"
LINEAGE_PATH = ROOT / "data/operations/current-task-lineage-status.json"
LIFECYCLE_PATH = ROOT / "data/operations/current-release-lifecycle-r1.json"
SNAPSHOT_PATH = ROOT / "data/operations/current-snapshot-r1.json"
FACTS_PATH = ROOT / "data/architecture/current-facts.json"
SEMANTICS_PATH = ROOT / "data/operations/iteration-boundary-semantics-r1.json"
FORMAL_RESULT_PATH = ROOT / "agent-results/IGNITION-20260822-135-result.md"
MACHINE_RECEIPT_PATH = ROOT / "agent-results/IGNITION-20260822-135-machine-receipt.json"
REPORT_PATH = ROOT / "data/operations/iterations/135/step15-ordinal-binding-gate-r1.json"
SCHEMA_PATH = ROOT / "schemas/operations/ordinal-binding-gate-135-step15-r1.schema.json"

EXPECTED_TASK_ID = "IGNITION-20260822-135"
EXPECTED_ARCHITECTURE_TASK = "IGNITION-20260821-129"
ALIAS_SEMANTICS = "DEPRECATED_COMPATIBILITY_ALIAS_OF_CURRENT_FORMAL_TASK_ORDINAL"
FORMAL_ROLES = (
    "execution_contract_task",
    "current_formal_task",
    "lifecycle_task",
    "snapshot_task",
    "formal_result_task",
    "release_candidate_task",
    "publication_witness_task",
)
REQUIRED_ROLES = FORMAL_ROLES + ("architecture_task",)
PENDING_TERMINAL_ROLES = {"formal_result_task", "publication_witness_task"}
TASK_LINE_RE = re.compile(r"^Task ID:\s*`?([^`\s]+)`?\s*$")
ORDINAL_LINE_RE = re.compile(r"(?:formal task ordinal|current_formal_task_ordinal)\s*[:=`]\s*`?(\d+)", re.I)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _nested(record: dict[str, Any], *keys: str) -> Any:
    current: Any = record
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _first(record: dict[str, Any], *paths: tuple[str, ...]) -> Any:
    for path in paths:
        value = _nested(record, *path)
        if value is not None:
            return value
    return None


def _task_record(
    role_id: str,
    task_id: Any,
    *,
    declared_ordinal: Any = None,
    architecture_task_id: Any = None,
    architecture_ordinal: Any = None,
    boundary: Any = None,
    alias_semantics: Any = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {"role_id": role_id, "task_id": task_id}
    if declared_ordinal is not None:
        record["declared_ordinal"] = declared_ordinal
    if architecture_task_id is not None:
        record["architecture_task_id"] = architecture_task_id
    if architecture_ordinal is not None:
        record["architecture_ordinal"] = architecture_ordinal
    if boundary is not None:
        record["current_iteration_boundary"] = boundary
    if alias_semantics is not None:
        record["current_iteration_boundary_semantics"] = alias_semantics
    return record


def _parse_result_file(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    if path.suffix == ".json":
        return load_json(path)
    task_id: str | None = None
    ordinal: int | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        match = TASK_LINE_RE.match(line.strip())
        if match:
            task_id = match.group(1)
        match = ORDINAL_LINE_RE.search(line)
        if match:
            ordinal = int(match.group(1))
    return {"task_id": task_id, "current_formal_task_ordinal": ordinal}


def _record_from_terminal(role_id: str, record: dict[str, Any]) -> dict[str, Any]:
    binding = record.get("task_binding") if isinstance(record.get("task_binding"), dict) else {}
    identity = record.get("identity_binding") if isinstance(record.get("identity_binding"), dict) else {}
    ordinal_binding = record.get("ordinal_binding") if isinstance(record.get("ordinal_binding"), dict) else {}
    state = record.get("current_state") if isinstance(record.get("current_state"), dict) else {}
    task_id = _first(record, ("task_id",), ("formal_task_id",), ("formal_result_task_id",))
    if role_id == "publication_witness_task":
        task_id = task_id or _first(binding, ("canonical_current_formal_task_id",), ("release_candidate_task_id",))
    ordinal_paths = [
        ("current_formal_task_ordinal",),
        ("formal_task_ordinal",),
        ("identity_binding", "current_formal_task_ordinal"),
        ("task_binding", "current_formal_task_ordinal"),
        ("ordinal_binding", "current_formal_task_ordinal"),
    ]
    if role_id != "publication_witness_task":
        ordinal_paths[2], ordinal_paths[4] = ordinal_paths[4], ordinal_paths[2]
    ordinal = _first(record, *ordinal_paths)
    ordinal = ordinal if ordinal is not None else _first(ordinal_binding, ("current_formal_task_ordinal",))
    architecture_id = _first(
        record,
        ("latest_architecture_changing_task",),
        ("latest_architecture_changing_task_id",),
        ("ordinal_binding", "latest_architecture_changing_task_id"),
        ("identity_binding", "latest_architecture_changing_task"),
        ("task_binding", "latest_architecture_changing_task"),
        ("current_state", "latest_architecture_changing_task"),
    )
    architecture_paths = [
        ("latest_architecture_task_ordinal",),
        ("identity_binding", "latest_architecture_task_ordinal"),
        ("task_binding", "latest_architecture_task_ordinal"),
        ("ordinal_binding", "latest_architecture_task_ordinal"),
        ("current_state", "latest_architecture_task_ordinal"),
    ]
    if role_id == "publication_witness_task":
        architecture_paths[2], architecture_paths[3] = architecture_paths[3], architecture_paths[2]
    architecture_ordinal = _first(record, *architecture_paths)
    boundary_paths = [
        ("current_iteration_boundary",),
        ("identity_binding", "current_iteration_boundary"),
        ("task_binding", "current_iteration_boundary"),
        ("ordinal_binding", "current_iteration_boundary"),
        ("current_state", "current_iteration_boundary"),
    ]
    if role_id == "publication_witness_task":
        boundary_paths[2], boundary_paths[3] = boundary_paths[3], boundary_paths[2]
    boundary = _first(record, *boundary_paths)
    semantics_paths = [
        ("current_iteration_boundary_semantics",),
        ("identity_binding", "current_iteration_boundary_semantics"),
        ("task_binding", "current_iteration_boundary_semantics"),
        ("ordinal_binding", "current_iteration_boundary_semantics"),
    ]
    if role_id == "publication_witness_task":
        semantics_paths[2], semantics_paths[3] = semantics_paths[3], semantics_paths[2]
    semantics = _first(record, *semantics_paths)
    return _task_record(
        role_id,
        task_id,
        declared_ordinal=ordinal,
        architecture_task_id=architecture_id,
        architecture_ordinal=architecture_ordinal,
        boundary=boundary,
        alias_semantics=semantics,
    )


def pending_roles(records: list[dict[str, Any]]) -> list[str]:
    present = {row.get("role_id") for row in records}
    return [role for role in FORMAL_ROLES if role in PENDING_TERMINAL_ROLES and role not in present]


def validate_binding_chain(
    records: list[dict[str, Any]],
    *,
    expected_task_id: str = EXPECTED_TASK_ID,
    expected_architecture_task: str = EXPECTED_ARCHITECTURE_TASK,
    require_terminal_evidence: bool = False,
) -> list[str]:
    """Validate normalized role records; used by the CLI and adversarial tests."""

    errors: list[str] = []
    role_ids = [row.get("role_id") for row in records]
    if len(role_ids) != len(set(role_ids)):
        duplicates = sorted({role for role in role_ids if role_ids.count(role) > 1 and role})
        errors.extend(f"DUPLICATE_BINDING_ROLE:{role}" for role in duplicates)
    present = set(role_ids)
    for role in REQUIRED_ROLES:
        if role not in present and (require_terminal_evidence or role not in PENDING_TERMINAL_ROLES):
            errors.append(f"MISSING_BINDING_ROLE:{role}")

    parser_records = [
        {key: row[key] for key in ("role_id", "task_id", "declared_ordinal") if key in row}
        for row in records
        if row.get("role_id") in present
    ]
    errors.extend(task_identity.validate_binding_records(parser_records))
    try:
        expected_formal = task_identity.parse_task_id(expected_task_id)
    except task_identity.TaskIdentityError as exc:
        errors.append(f"EXPECTED_FORMAL_TASK_INVALID:{exc}")
        expected_formal = None
    try:
        expected_architecture = task_identity.parse_task_id(expected_architecture_task)
    except task_identity.TaskIdentityError as exc:
        errors.append(f"EXPECTED_ARCHITECTURE_TASK_INVALID:{exc}")
        expected_architecture = None

    for row in records:
        role = row.get("role_id")
        if not role:
            continue
        task_id = row.get("task_id")
        try:
            parsed = task_identity.parse_task_id(task_id)
        except task_identity.TaskIdentityError as exc:
            errors.append(f"{role}:TASK_ID_INVALID:{exc}")
            continue
        if role in FORMAL_ROLES and expected_formal and parsed["canonical"] != expected_formal["canonical"]:
            errors.append(f"FORMAL_TASK_ID_MISMATCH:{role}:expected={expected_formal['canonical']}:observed={parsed['canonical']}")
        if role == "architecture_task" and expected_architecture and parsed["canonical"] != expected_architecture["canonical"]:
            errors.append(f"ARCHITECTURE_TASK_ID_MISMATCH:expected={expected_architecture['canonical']}:observed={parsed['canonical']}")
        declared = row.get("declared_ordinal")
        if declared is None and role in {"formal_result_task", "publication_witness_task"}:
            errors.append(f"ORDINAL_ASSERTION_MISSING:{role}")
        if declared is not None and declared != parsed["ordinal"]:
            errors.append(f"ORDINAL_MISMATCH:{role}:expected={parsed['ordinal']}:observed={declared}")
        architecture_id = row.get("architecture_task_id")
        architecture_ordinal = row.get("architecture_ordinal")
        if architecture_id is not None:
            try:
                parsed_architecture = task_identity.parse_task_id(architecture_id)
            except task_identity.TaskIdentityError as exc:
                errors.append(f"{role}:ARCHITECTURE_TASK_ID_INVALID:{exc}")
            else:
                if expected_architecture and parsed_architecture["canonical"] != expected_architecture["canonical"]:
                    errors.append(f"ARCHITECTURE_TASK_MISMATCH:{role}:expected={expected_architecture['canonical']}:observed={parsed_architecture['canonical']}")
                if parsed_architecture["canonical"] == expected_task_id:
                    errors.append(f"ARCHITECTURE_TASK_PROMOTED_TO_FORMAL:{role}")
                if architecture_ordinal is not None and architecture_ordinal != parsed_architecture["ordinal"]:
                    errors.append(f"ARCHITECTURE_ORDINAL_MISMATCH:{role}:expected={parsed_architecture['ordinal']}:observed={architecture_ordinal}")
        elif architecture_ordinal is not None:
            errors.append(f"ARCHITECTURE_TASK_ID_MISSING_FOR_ORDINAL:{role}")
        boundary = row.get("current_iteration_boundary")
        if boundary is not None and boundary != parsed["ordinal"]:
            errors.append(f"COMPATIBILITY_ALIAS_MISMATCH:{role}:expected={parsed['ordinal']}:observed={boundary}")
        semantics = row.get("current_iteration_boundary_semantics")
        if semantics is not None and semantics != ALIAS_SEMANTICS:
            errors.append(f"COMPATIBILITY_ALIAS_SEMANTICS_INVALID:{role}")
    return sorted(set(errors))


def _current_records(
    *,
    contract: dict[str, Any],
    lineage: dict[str, Any],
    lifecycle: dict[str, Any],
    snapshot: dict[str, Any],
    formal_result: dict[str, Any] | None,
    release_candidate: dict[str, Any] | None,
    publication_witness: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    expectations = contract.get("identity_expectations", {})
    lineage_identity = lineage.get("task_identity", {})
    iteration = snapshot.get("iteration_identity", {})
    records = [
        _task_record(
            "execution_contract_task",
            contract.get("task_id"),
            architecture_task_id=expectations.get("latest_architecture_changing_task"),
        ),
        _task_record(
            "current_formal_task",
            lineage.get("current_task", {}).get("task_id"),
            architecture_task_id=lineage_identity.get("latest_architecture_changing_task"),
        ),
        _task_record(
            "lifecycle_task",
            lifecycle.get("task_id"),
            declared_ordinal=lifecycle.get("current_formal_task_ordinal"),
            architecture_task_id=lifecycle.get("latest_architecture_changing_task"),
            architecture_ordinal=lifecycle.get("latest_architecture_task_ordinal"),
            boundary=lifecycle.get("current_iteration_boundary"),
            alias_semantics=lifecycle.get("current_iteration_boundary_semantics"),
        ),
        _task_record(
            "snapshot_task",
            snapshot.get("current_task", {}).get("task_id"),
            declared_ordinal=iteration.get("current_formal_task_ordinal"),
            architecture_task_id=iteration.get("latest_architecture_changing_task_id"),
            architecture_ordinal=iteration.get("latest_architecture_task_ordinal"),
            boundary=iteration.get("current_iteration_boundary"),
            alias_semantics=iteration.get("current_iteration_boundary_semantics"),
        ),
        _task_record(
            "architecture_task",
            expectations.get("latest_architecture_changing_task"),
            declared_ordinal=iteration.get("latest_architecture_task_ordinal"),
        ),
    ]
    formal_result_record = _record_from_terminal("formal_result_task", formal_result) if formal_result is not None else None
    if formal_result_record is not None:
        records.append(formal_result_record)
    candidate_record = (
        _record_from_terminal("release_candidate_task", release_candidate)
        if release_candidate is not None
        else _task_record("release_candidate_task", expectations.get("release_candidate_task"))
    )
    records.append(candidate_record)
    witness_record = _record_from_terminal("publication_witness_task", publication_witness) if publication_witness is not None else None
    if witness_record is not None:
        records.append(witness_record)
    return records


def _validate_facts(facts: dict[str, Any], expected_task_id: str, expected_architecture_task: str) -> list[str]:
    errors: list[str] = []
    iteration = facts.get("facts", {}).get("iteration", {})
    projections = (facts, iteration)
    try:
        formal_ordinal = task_identity.parse_task_id(expected_task_id)["ordinal"]
        architecture_ordinal = task_identity.parse_task_id(expected_architecture_task)["ordinal"]
    except task_identity.TaskIdentityError:
        return ["FACTS_EXPECTED_TASK_INVALID"]
    expected = {
        "current_formal_task_id": expected_task_id,
        "current_formal_task_ordinal": formal_ordinal,
        "latest_architecture_changing_task_id": expected_architecture_task,
        "latest_architecture_task_ordinal": architecture_ordinal,
        "current_iteration_boundary": formal_ordinal,
        "current_iteration_boundary_semantics": ALIAS_SEMANTICS,
    }
    for projection in projections:
        for key, value in expected.items():
            if projection.get(key) != value:
                errors.append(f"CURRENT_FACTS_PROJECTION_MISMATCH:{key}:expected={value}:observed={projection.get(key)}")
    return errors


def validate_documents(
    *,
    contract: dict[str, Any],
    lineage: dict[str, Any],
    lifecycle: dict[str, Any],
    snapshot: dict[str, Any],
    facts: dict[str, Any] | None = None,
    formal_result: dict[str, Any] | None = None,
    release_candidate: dict[str, Any] | None = None,
    publication_witness: dict[str, Any] | None = None,
    require_terminal_evidence: bool = False,
) -> tuple[list[str], list[dict[str, Any]]]:
    lineage_identity = lineage.get("task_identity") if isinstance(lineage.get("task_identity"), dict) else {}
    if not lineage_identity.get("current_formal_task"):
        source_errors = ["CANONICAL_FORMAL_SOURCE_MISSING"]
    else:
        source_errors = []
    if lineage.get("current_task", {}).get("task_id") != lineage_identity.get("current_formal_task"):
        source_errors.append("CANONICAL_FORMAL_SOURCE_MISMATCH")
    records = _current_records(
        contract=contract,
        lineage=lineage,
        lifecycle=lifecycle,
        snapshot=snapshot,
        formal_result=formal_result,
        release_candidate=release_candidate,
        publication_witness=publication_witness,
    )
    errors = source_errors + validate_binding_chain(
        records,
        expected_task_id=contract.get("identity_expectations", {}).get("current_formal_task", EXPECTED_TASK_ID),
        expected_architecture_task=contract.get("identity_expectations", {}).get("latest_architecture_changing_task", EXPECTED_ARCHITECTURE_TASK),
        require_terminal_evidence=require_terminal_evidence,
    )
    if facts is not None:
        expected_task_id = contract.get("identity_expectations", {}).get("current_formal_task", EXPECTED_TASK_ID)
        expected_architecture_task = contract.get("identity_expectations", {}).get(
            "latest_architecture_changing_task", EXPECTED_ARCHITECTURE_TASK
        )
        errors.extend(_validate_facts(facts, expected_task_id, expected_architecture_task))
    return sorted(set(errors)), records


def validate(*, require_terminal_evidence: bool = False) -> tuple[list[str], list[dict[str, Any]]]:
    formal_result = _parse_result_file(FORMAL_RESULT_PATH)
    witness = load_json(MACHINE_RECEIPT_PATH) if MACHINE_RECEIPT_PATH.is_file() else None
    return validate_documents(
        contract=load_json(CONTRACT_PATH),
        lineage=load_json(LINEAGE_PATH),
        lifecycle=load_json(LIFECYCLE_PATH),
        snapshot=load_json(SNAPSHOT_PATH),
        facts=load_json(FACTS_PATH),
        formal_result=formal_result,
        publication_witness=witness,
        require_terminal_evidence=require_terminal_evidence,
    )


def report(*, require_terminal_evidence: bool = False) -> dict[str, Any]:
    errors, records = validate(require_terminal_evidence=require_terminal_evidence)
    pending = pending_roles(records)
    status = "FAIL" if errors else ("PASS" if not pending else "PASS_WITH_PENDING_TERMINAL_EVIDENCE")
    return {
        "schema_version": "ignition-135-step15-ordinal-binding-gate-r1",
        "task_id": EXPECTED_TASK_ID,
        "step": "15",
        "result": status,
        "binding_chain": records,
        "pending_terminal_roles": pending,
        "formal_task_ordinal": task_identity.parse_task_id(EXPECTED_TASK_ID)["ordinal"],
        "latest_architecture_task_ordinal": task_identity.parse_task_id(EXPECTED_ARCHITECTURE_TASK)["ordinal"],
        "current_iteration_boundary": task_identity.parse_task_id(EXPECTED_TASK_ID)["ordinal"],
        "current_iteration_boundary_semantics": ALIAS_SEMANTICS,
        "errors": errors,
        "claim_ceiling": "Repository-local ordinal binding evidence only; no external truth, production readiness, Owner acceptance or epistemic acceptance is inferred.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    parser.add_argument("--require-terminal-evidence", action="store_true")
    args = parser.parse_args()
    result = report(require_terminal_evidence=args.require_terminal_evidence)
    if args.write:
        REPORT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"ITERATION_ORDINAL_BINDING_WRITTEN path={REPORT_PATH.relative_to(REPO_ROOT)} result={result['result']}")
        return 0 if result["result"] != "FAIL" else 1
    if result["result"] == "FAIL":
        print("ITERATION_ORDINAL_BINDING_INVALID", file=sys.stderr)
        for error in result["errors"]:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"ITERATION_ORDINAL_BINDING_OK result={result['result']} pending={','.join(result['pending_terminal_roles']) or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
