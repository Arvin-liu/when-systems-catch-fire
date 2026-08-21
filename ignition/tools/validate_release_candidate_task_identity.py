#!/usr/bin/env python3
"""Fail-closed release-candidate task identity and ordinal gate for IGNITION-133."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from tools import build_current_snapshot
    from tools import current_surface_compiler
    from tools import validate_execution_contract_133 as validate_execution_contract
    from tools import validate_iteration_ordinal_binding as ordinal_binding
    from tools import task_identity
except ImportError:  # direct script / tools-on-PYTHONPATH execution
    import build_current_snapshot
    import current_surface_compiler
    import validate_execution_contract_133 as validate_execution_contract
    import validate_iteration_ordinal_binding as ordinal_binding
    import task_identity


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
CONTRACT_PATH = ROOT / "data/operations/iterations/133/execution-contract-r1.json"
LINEAGE_PATH = ROOT / "data/operations/current-task-lineage-status.json"
LIFECYCLE_PATH = ROOT / "data/operations/current-release-lifecycle-r1.json"
SNAPSHOT_PATH = ROOT / "data/operations/current-snapshot-r1.json"
PROGRESS_PATH = ROOT / "data/operations/iterations/133/progress.jsonl"
RESULT_PATH = ROOT / "agent-results/IGNITION-20260822-133-result.md"
MACHINE_RECEIPT_PATH = ROOT / "agent-results/IGNITION-20260822-133-machine-receipt.json"
EXPECTED_TASK_ID = "IGNITION-20260822-133"
EXPECTED_ARCHITECTURE_TASK = "IGNITION-20260821-129"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_progress() -> list[dict[str, Any]]:
    if not PROGRESS_PATH.is_file():
        return []
    return [json.loads(line) for line in PROGRESS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_result_task(path: Path) -> str | None:
    if not path.is_file():
        return None
    if path.suffix == ".json":
        return load_json(path).get("task_id") or load_json(path).get("formal_task_id")
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("Task ID:"):
            return line.split(":", 1)[1].strip().strip("`")
        if "IGNITION-20260822-133" in line and "#" not in line:
            return EXPECTED_TASK_ID
    return None


def validate_documents(
    *,
    contract: dict[str, Any],
    lineage: dict[str, Any],
    lifecycle: dict[str, Any],
    snapshot: dict[str, Any],
    progress: list[dict[str, Any]],
    observed_branch: str | None,
    surface_documents: dict[str, str] | None = None,
    result_task_id: str | None = None,
    machine_receipt_task_id: str | None = None,
    require_result: bool = False,
    require_release_ready: bool = False,
) -> list[str]:
    errors: list[str] = []

    def equal(label: str, observed: Any, expected: str = EXPECTED_TASK_ID) -> None:
        if observed != expected:
            errors.append(f"TASK_IDENTITY_MISMATCH:{label}:expected={expected}:observed={observed}")

    contract_errors = validate_execution_contract.validate(contract)
    errors.extend(f"EXECUTION_CONTRACT_INVALID:{error}" for error in contract_errors)
    equal("execution_contract.task_id", contract.get("task_id"))
    equal("execution_contract.identity_expectations.current_formal_task", contract.get("identity_expectations", {}).get("current_formal_task"))
    equal("execution_contract.identity_expectations.release_candidate_task", contract.get("identity_expectations", {}).get("release_candidate_task"))
    if contract.get("identity_expectations", {}).get("latest_architecture_changing_task") != EXPECTED_ARCHITECTURE_TASK:
        errors.append("TASK_IDENTITY_MISMATCH:execution_contract.latest_architecture_changing_task")

    equal("lineage.current_task.task_id", lineage.get("current_task", {}).get("task_id"))
    state = lineage.get("task_identity", {})
    equal("lineage.task_identity.current_formal_task", state.get("current_formal_task"))
    equal("lineage.task_identity.release_candidate_task", state.get("release_candidate_task"))
    equal("lineage.task_identity.publication_witness_task", state.get("publication_witness_task"))
    if state.get("latest_architecture_changing_task") != EXPECTED_ARCHITECTURE_TASK:
        errors.append("TASK_IDENTITY_MISMATCH:lineage.task_identity.latest_architecture_changing_task")

    equal("lifecycle.task_id", lifecycle.get("task_id"))
    if lifecycle.get("latest_architecture_changing_task") != EXPECTED_ARCHITECTURE_TASK:
        errors.append("TASK_IDENTITY_MISMATCH:lifecycle.latest_architecture_changing_task")
    if lifecycle.get("task_identity_source", {}).get("binding") != "MUST_MATCH_CURRENT_FORMAL_EXECUTION_CONTRACT_AND_ORDINAL_DERIVATION":
        errors.append("TASK_IDENTITY_BINDING_MISSING:lifecycle")

    equal("snapshot.current_task.task_id", snapshot.get("current_task", {}).get("task_id"))
    identity = snapshot.get("task_identity", {})
    equal("snapshot.task_identity.current_formal_task", identity.get("current_formal_task"))
    equal("snapshot.task_identity.release_candidate_task", identity.get("release_candidate_task"))
    equal("snapshot.task_identity.publication_witness_task", identity.get("publication_witness_task"))
    equal("snapshot.release_lifecycle.task_id", snapshot.get("release_lifecycle", {}).get("task_id"))
    if snapshot.get("latest_architecture_changing_task") != EXPECTED_ARCHITECTURE_TASK:
        errors.append("TASK_IDENTITY_MISMATCH:snapshot.latest_architecture_changing_task")

    if observed_branch is not None and observed_branch != contract.get("expected_task_branch"):
        errors.append(f"TASK_BRANCH_METADATA_MISMATCH:expected={contract.get('expected_task_branch')}:observed={observed_branch}")

    if not progress:
        errors.append("PROGRESS_CURRENT_ITERATION_MISSING")
    else:
        last = progress[-1]
        if last.get("task_id") != EXPECTED_TASK_ID:
            errors.append("PROGRESS_TASK_ID_MISMATCH")
        if last.get("current_iteration_id") != 133:
            errors.append("PROGRESS_CURRENT_ITERATION_ID_MISMATCH")

    if require_result:
        if result_task_id is None:
            errors.append("FORMAL_RESULT_TASK_ID_MISSING")
        else:
            equal("formal_result.task_id", result_task_id)
        if machine_receipt_task_id is None:
            errors.append("FORMAL_MACHINE_RECEIPT_TASK_ID_MISSING")
        else:
            equal("formal_machine_receipt.task_id", machine_receipt_task_id)
    else:
        for label, task_id in (("formal_result.task_id", result_task_id), ("formal_machine_receipt.task_id", machine_receipt_task_id)):
            if task_id is not None:
                equal(label, task_id)

    if require_release_ready and lifecycle.get("content_phase") != "RELEASE_READY":
        errors.append(f"RELEASE_CANDIDATE_NOT_READY:phase={lifecycle.get('content_phase')}")

    if surface_documents is None:
        surface_documents = {
            surface["path"]: (REPO_ROOT / surface["path"]).read_text(encoding="utf-8")
            for surface in current_surface_compiler.load_json(current_surface_compiler.CONTRACT_PATH)["surfaces"]
        }
    surface_contract = current_surface_compiler.load_json(current_surface_compiler.CONTRACT_PATH)
    for surface in surface_contract["surfaces"]:
        text = surface_documents.get(surface["path"])
        if text is None:
            errors.append(f"COMPILER_SURFACE_MISSING:{surface['surface_id']}")
            continue
        try:
            expected = current_surface_compiler.compile_surface(text, surface, snapshot=snapshot)
        except Exception as exc:
            errors.append(f"COMPILER_SURFACE_UNREADABLE:{surface['surface_id']}:{type(exc).__name__}")
            continue
        if text != expected:
            errors.append(f"COMPILER_SURFACE_STALE:{surface['surface_id']}")
        if EXPECTED_TASK_ID not in text:
            errors.append(f"COMPILER_TASK_ID_MISSING:{surface['surface_id']}")
        if EXPECTED_ARCHITECTURE_TASK not in text:
            errors.append(f"COMPILER_ARCHITECTURE_TASK_MISSING:{surface['surface_id']}")
    formal_result = None
    if result_task_id is not None:
        try:
            formal_result = {"task_id": result_task_id, "current_formal_task_ordinal": task_identity.parse_task_id(result_task_id)["ordinal"]}
        except task_identity.TaskIdentityError:
            formal_result = {"task_id": result_task_id}
    publication_witness = None
    if machine_receipt_task_id is not None:
        try:
            publication_witness = {"task_id": machine_receipt_task_id, "task_binding": {"current_formal_task_ordinal": task_identity.parse_task_id(machine_receipt_task_id)["ordinal"]}}
        except task_identity.TaskIdentityError:
            publication_witness = {"task_id": machine_receipt_task_id}
    ordinal_errors, _records = ordinal_binding.validate_documents(
        contract=contract,
        lineage=lineage,
        lifecycle=lifecycle,
        snapshot=snapshot,
        facts=load_json(ROOT / "data/architecture/current-facts.json"),
        formal_result=formal_result,
        publication_witness=publication_witness,
        require_terminal_evidence=require_result,
    )
    errors.extend(f"ORDINAL_BINDING:{error}" for error in ordinal_errors)
    return errors


def validate(*, require_result: bool = False, require_release_ready: bool = False) -> list[str]:
    observed_branch = subprocess.run(
        ["git", "branch", "--show-current"], cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    ).stdout.strip()
    result_task_id = load_result_task(RESULT_PATH)
    machine_task_id = load_result_task(MACHINE_RECEIPT_PATH)
    return validate_documents(
        contract=load_json(CONTRACT_PATH),
        lineage=load_json(LINEAGE_PATH),
        lifecycle=load_json(LIFECYCLE_PATH),
        snapshot=load_json(SNAPSHOT_PATH),
        progress=load_progress(),
        observed_branch=observed_branch,
        result_task_id=result_task_id,
        machine_receipt_task_id=machine_task_id,
        require_result=require_result,
        require_release_ready=require_release_ready,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--require-result", action="store_true")
    parser.add_argument("--require-release-ready", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate(require_result=args.require_result, require_release_ready=args.require_release_ready)
    if errors:
        print("RELEASE_CANDIDATE_TASK_IDENTITY_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"RELEASE_CANDIDATE_TASK_IDENTITY_OK task_id={EXPECTED_TASK_ID}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
