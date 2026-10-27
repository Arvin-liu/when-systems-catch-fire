#!/usr/bin/env python3
"""Derive named Current task ordinals from canonical identity sources."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    from tools import task_identity
except ImportError:
    import task_identity


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
MODEL_PATH = ROOT / "data/operations/iteration-boundary-semantics-r1.json"
LINEAGE_PATH = ROOT / "data/operations/current-task-lineage-status.json"
LIFECYCLE_PATH = ROOT / "data/operations/current-release-lifecycle-r1.json"
METHOD_PATH = ROOT / "ITERATION.md"


class IterationBoundaryError(ValueError):
    """Raised when a Current task/ordinal derivation cannot be trusted."""


def load_json(path: Path) -> Any:
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def _current_method_version() -> str:
    match = re.search(r"^Current:\s*`([^`]+)`", METHOD_PATH.read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        raise IterationBoundaryError("current method marker is missing from ignition/ITERATION.md")
    return match.group(1)


def derive() -> dict[str, Any]:
    """Return the complete named iteration identity projection.

    The only numeric values returned here are parsed from canonical task IDs;
    no JSON field containing a manually authored ordinal is consulted.
    """

    model = load_json(MODEL_PATH)
    if model.get("contract_id") != "ITERATION_BOUNDARY_SEMANTICS_INVARIANT":
        raise IterationBoundaryError("iteration semantics contract id is invalid")
    lineage = load_json(LINEAGE_PATH)
    lifecycle = load_json(LIFECYCLE_PATH)
    task_identity_state = lineage.get("task_identity") or {}
    formal_id = task_identity_state.get("current_formal_task")
    architecture_id = task_identity_state.get("latest_architecture_changing_task")
    current_task_id = lineage.get("current_task", {}).get("task_id")
    if not formal_id or not architecture_id:
        raise IterationBoundaryError("canonical task identity is missing formal or architecture task id")
    if current_task_id != formal_id:
        raise IterationBoundaryError("current_task.task_id differs from task_identity.current_formal_task")
    if lifecycle.get("task_id") != formal_id:
        raise IterationBoundaryError("current release lifecycle task_id differs from canonical formal task id")
    try:
        formal = task_identity.parse_task_id(formal_id)
        architecture = task_identity.parse_task_id(architecture_id)
    except task_identity.TaskIdentityError as exc:
        raise IterationBoundaryError(str(exc)) from exc

    alias = model["compatibility_policy"]["current_iteration_boundary"]
    if alias.get("alias_of") != "current_formal_task_ordinal" or alias.get("status") != "DEPRECATED_COMPATIBILITY_ALIAS":
        raise IterationBoundaryError("current_iteration_boundary compatibility policy is not the formal ordinal alias")
    return {
        "current_formal_task_id": formal["canonical"],
        "current_formal_task_ordinal": formal["ordinal"],
        "latest_architecture_changing_task_id": architecture["canonical"],
        "latest_architecture_task_ordinal": architecture["ordinal"],
        "current_method_version": _current_method_version(),
        "current_iteration_boundary": formal["ordinal"],
        "current_iteration_boundary_semantics": "DEPRECATED_COMPATIBILITY_ALIAS_OF_CURRENT_FORMAL_TASK_ORDINAL",
    }


def validate_projection(document: dict[str, Any], *, label: str) -> list[str]:
    """Compare a materialized projection with the canonical derivation."""

    expected = derive()
    errors: list[str] = []
    for key, value in expected.items():
        if document.get(key) != value:
            errors.append(f"{label}.{key} differs from canonical derivation: expected {value!r}, got {document.get(key)!r}")
    return errors
