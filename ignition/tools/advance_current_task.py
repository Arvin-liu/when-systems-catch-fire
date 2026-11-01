#!/usr/bin/env python3
"""Advance canonical Current task identity from the current task contract.

The operation is deliberately source-local: it changes the canonical lineage
record and never edits generated surfaces or claims remote publication.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
STATUS_PATH = ROOT / "data/operations/current-task-lineage-status.json"
IDENTITY_MODEL_PATH = ROOT / "data/operations/task-identity-model-r1.json"
TASK_ID_RE = re.compile(r"^IGNITION-(?:(?P<date>\d{8})-)?(?P<number>\d+)$")
EXECUTION_CONTRACT_PATH_RE = re.compile(
    r"^ignition/data/operations/iterations/(?P<ordinal>[0-9]+)/execution-contract-r1\.json$"
)
CLAIM_CEILING = "Canonical repository-local task advancement only; this record does not grant authority, prove external truth, establish production readiness or set epistemic acceptance."


class AdvancementError(ValueError):
    """The requested task transition is not an authorized monotonic transition."""


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def render(document: dict[str, Any]) -> bytes:
    return (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def task_order(task_id: str) -> tuple[int, int]:
    match = TASK_ID_RE.fullmatch(task_id)
    if not match:
        raise AdvancementError(f"invalid task id: {task_id}")
    return (int(match.group("date") or 0), int(match.group("number")))


def _contract_target(contract: dict[str, Any]) -> str:
    target = contract["identity_expectations"]["current_formal_task"]
    if contract.get("task_id") != target:
        raise AdvancementError("execution contract task_id must equal its current_formal_task expectation")
    task_order(target)
    for key in (
        "latest_architecture_changing_task",
        "previous_canonical_current_task",
        "previous_formal_task",
        "release_candidate_task",
        "publication_witness_task",
    ):
        if not isinstance(contract["identity_expectations"].get(key), str):
            raise AdvancementError(f"execution contract identity expectation is missing: {key}")
    return target


def _formal_edges() -> list[dict[str, str]]:
    return [
        {
            "predecessor_task_id": "IGNITION-20260821-129",
            "successor_task_id": "IGNITION-20260821-130",
            "relation": "FORMAL_TASK_SUCCESSOR",
            "status": "COMPLETED_HISTORICAL",
        },
        {
            "predecessor_task_id": "IGNITION-20260821-130",
            "successor_task_id": "IGNITION-20260821-131",
            "relation": "FORMAL_TASK_SUCCESSOR",
            "status": "COMPLETED_HISTORICAL",
        },
        {
            "predecessor_task_id": "IGNITION-20260821-131",
            "successor_task_id": "IGNITION-20260822-132",
            "relation": "FORMAL_TASK_SUCCESSOR",
            "status": "COMPLETED_HISTORICAL",
        },
        {
            "predecessor_task_id": "IGNITION-20260822-132",
            "successor_task_id": "IGNITION-20260822-133",
            "relation": "CANONICAL_SOURCE_ADVANCEMENT",
            "status": "COMPLETED_HISTORICAL",
        },
        {
            "predecessor_task_id": "IGNITION-20260822-132",
            "successor_task_id": "IGNITION-20260822-133",
            "relation": "FORMAL_TASK_SUCCESSOR",
            "status": "COMPLETED_HISTORICAL",
        },
        {
            "predecessor_task_id": "IGNITION-20260822-133",
            "successor_task_id": "IGNITION-20260822-134",
            "relation": "CANONICAL_SOURCE_ADVANCEMENT",
            "status": "COMPLETED_HISTORICAL",
        },
        {
            "predecessor_task_id": "IGNITION-20260822-133",
            "successor_task_id": "IGNITION-20260822-134",
            "relation": "FORMAL_TASK_SUCCESSOR",
            "status": "COMPLETED_HISTORICAL",
        },
        {
            "predecessor_task_id": "IGNITION-20260822-134",
            "successor_task_id": "IGNITION-20260822-135",
            "relation": "FORMAL_TASK_SUCCESSOR",
            "status": "COMPLETED_HISTORICAL",
        },
        {
            "predecessor_task_id": "IGNITION-20260822-135",
            "successor_task_id": "IGNITION-20260823-136",
            "relation": "FORMAL_TASK_SUCCESSOR",
            "status": "COMPLETED_HISTORICAL",
        },
    ]


def advance_document(document: dict[str, Any], contract: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    target = _contract_target(contract)
    current = document["current_task"]["task_id"]
    expectations = contract["identity_expectations"]
    if current == target:
        state = document.get("task_identity", {})
        expected = {
            "current_formal_task": target,
            "release_candidate_task": expectations["release_candidate_task"],
            "publication_witness_task": expectations["publication_witness_task"],
            "latest_architecture_changing_task": expectations["latest_architecture_changing_task"],
        }
        if all(state.get(key) == value for key, value in expected.items()):
            return copy.deepcopy(document), False
        raise AdvancementError("current task is already the contract target but task identity state is incomplete")
    if task_order(current) >= task_order(target):
        raise AdvancementError(f"task advancement cannot move backward or stay at {current} -> {target}")
    if current != contract["identity_expectations"]["previous_canonical_current_task"]:
        raise AdvancementError(
            f"expected previous canonical Current task {contract['identity_expectations']['previous_canonical_current_task']}, observed {current}"
        )

    updated = copy.deepcopy(document)
    prior_digest = hashlib.sha256(render(document)).hexdigest()
    impact = contract.get("identity_impact", "PRESENTATION_ONLY")
    updated["current_task"] = {
        "task_id": target,
        "scope": f"Formal task {target} Current advancement",
        "execution_status": "IN_PROGRESS",
        "terminal": False,
        "identity_impact": impact,
    }
    previous_edges = list(document.get("task_identity", {}).get("historical_lineage", [])) or _formal_edges()
    new_edges = previous_edges + [{
        "predecessor_task_id": current,
        "successor_task_id": target,
        "relation": "CANONICAL_SOURCE_ADVANCEMENT",
        "status": "CURRENT_ADVANCEMENT",
    }, {
        "predecessor_task_id": expectations["previous_formal_task"],
        "successor_task_id": target,
        "relation": "FORMAL_TASK_SUCCESSOR",
        "status": "CURRENT_ADVANCEMENT",
    }]
    updated["task_identity"] = {
        "schema_version": "task-identity-state-r1",
        "current_formal_task": target,
        "latest_architecture_changing_task": expectations["latest_architecture_changing_task"],
        "release_candidate_task": expectations["release_candidate_task"],
        "publication_witness_task": expectations["publication_witness_task"],
        "previous_canonical_current_task": current,
        "previous_formal_task": expectations["previous_formal_task"],
        "historical_lineage": new_edges,
        "advancement": {
            "from_task_id": current,
            "to_task_id": target,
            "transition_reason": (
                f"{target} advances canonical Current from recorded predecessor {current} with "
                f"execution_status={document['current_task']['execution_status']} and "
                f"terminal={str(document['current_task']['terminal']).lower()}; prior task completion "
                "is not inferred, its exact source is retained by prior_source_sha256, and the formal "
                "task remains separate from the latest architecture-changing task."
            ),
            "prior_source_sha256": prior_digest,
            "execution_contract_path": f"ignition/data/operations/iterations/{task_order(target)[1]:03d}/execution-contract-r1.json",
            "idempotency_key": target,
        },
        "claim_ceiling": CLAIM_CEILING,
    }
    return updated, True


def validate_state(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    state = document.get("task_identity")
    if not state:
        return ["canonical task identity state is missing"]
    if state["current_formal_task"] != document["current_task"]["task_id"]:
        errors.append("task identity current_formal_task differs from current_task")
    if state["current_formal_task"] != document["current_task"]["task_id"]:
        errors.append("canonical task identity does not match current task")
    if (
        state["latest_architecture_changing_task"] == state["current_formal_task"]
        and document["current_task"].get("identity_impact") != "ARCHITECTURE_CHANGED"
    ):
        errors.append("presentation-only architecture task must remain distinct from current formal task")
    edge = state["advancement"]
    if edge["from_task_id"] != state["previous_canonical_current_task"] or edge["to_task_id"] != state["current_formal_task"]:
        errors.append("advancement provenance does not match previous/current task ids")
    if state.get("release_candidate_task") != state.get("current_formal_task"):
        errors.append("release candidate task must follow current formal task")
    if state.get("publication_witness_task") != state.get("current_formal_task"):
        errors.append("publication witness task must follow current formal task")
    return errors


def resolve_contract_path(identity_model: dict[str, Any], repo_root: Path = REPO_ROOT) -> Path:
    """Resolve the release candidate contract from its canonical role binding.

    The numeric suffix in a task ID is not a reliable "next task" selector:
    formal ordinals can be explicitly registered and need not be current + 1.
    The identity model's release-candidate source is the sole selection source.
    """
    binding = identity_model.get("role_bindings", {}).get("release_candidate_task", {})
    source_path = binding.get("source_path")
    match = EXECUTION_CONTRACT_PATH_RE.fullmatch(source_path) if isinstance(source_path, str) else None
    if not match:
        raise AdvancementError("release_candidate_task must bind an exact iterations/<ordinal>/execution-contract-r1.json source")
    candidate = (repo_root / source_path).resolve()
    try:
        candidate.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise AdvancementError("release-candidate execution contract escapes the repository root") from exc
    if not candidate.is_file():
        raise AdvancementError(f"registered release-candidate execution contract is missing: {source_path}")
    contract = load_json(candidate)
    task_id = contract.get("task_id")
    if task_id != contract.get("identity_expectations", {}).get("release_candidate_task"):
        raise AdvancementError("registered execution contract task_id differs from its release-candidate identity")
    if task_order(task_id)[1] != int(match.group("ordinal")):
        raise AdvancementError("registered execution-contract path ordinal differs from its task identity")
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    document = load_json(STATUS_PATH)
    identity_model = load_json(IDENTITY_MODEL_PATH)
    try:
        contract_path = resolve_contract_path(identity_model)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"CANONICAL_CURRENT_ADVANCEMENT_INVALID: {exc}", file=sys.stderr)
        return 1
    contract = load_json(contract_path)
    try:
        updated, changed = advance_document(document, contract)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"CANONICAL_CURRENT_ADVANCEMENT_INVALID: {exc}", file=sys.stderr)
        return 1
    if args.check:
        errors = validate_state(updated)
        if errors and changed:
            print("CANONICAL_CURRENT_ADVANCEMENT_NOT_APPLIED", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1
        print(f"CANONICAL_CURRENT_ADVANCEMENT_OK target={updated['current_task']['task_id']} idempotent={str(not changed).lower()}")
        return 0
    STATUS_PATH.write_bytes(render(updated))
    print(f"CANONICAL_CURRENT_ADVANCEMENT_WRITTEN target={updated['current_task']['task_id']} changed={str(changed).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
