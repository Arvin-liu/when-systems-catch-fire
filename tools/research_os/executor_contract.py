"""Executor Adapter Contract (Checkpoint B).

Tool-agnostic dispatch/return contract so Codex, WorkBuddy, other agents or
scripts can act as executors. The OS sends an exact, bounded spec; the executor
returns observations with explicit provenance and NO self-approval. The OS then
diagnoses the returned state; an executor cannot mark its episode complete merely
by returning success.
"""

from __future__ import annotations

import json
import os
from typing import Any

from . import registries as R

RETURN_SCHEMA = "research-os/executor-return/0.1"
RETURN_SCHEMA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "schemas",
    "research-os",
    "executor-return.schema.json",
)

# Keys an executor is strictly forbidden from setting. Presence of any of these
# is rejected by the OS regardless of value; raising a claim ceiling,
# self-approving, or marking the episode complete are OS/gate decisions only.
PROHIBITED_RETURN_KEYS = (
    "self_approved",
    "mark_episode_complete",
    "claim_ceiling",
)

RETURN_REQUIRED_FIELDS = [
    "observations",
    "source_identities",
    "access_level",
    "calculation_result",
    "errors",
    "provenance",
    "timestamps",
]


def load_executor_return_schema() -> dict:
    """Load the formal JSON Schema for the executor return contract."""
    with open(RETURN_SCHEMA_FILE, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _validate_with_jsonschema(ret: dict, schema: dict) -> list[str]:
    """Full structural validation when the jsonschema package is available."""
    try:
        import jsonschema  # type: ignore
    except Exception:
        return []
    validator = jsonschema.Draft202012Validator(schema)
    return [f"{e.path}: {e.message}" for e in validator.iter_errors(ret)]


def build_dispatch_spec(ep: dict, action_code: str, actor: str = "kernel") -> dict:
    R.assert_action(action_code)
    meta = R.ACTION_BY_CODE[action_code]
    return {
        "action_type": action_code,
        "bounded_objective": meta["description"],
        "required_inputs": {
            "episode_id": ep.get("episode_id"),
            "strategy_pack": ep.get("strategy_pack"),
            "question_version": ep.get("question_version"),
        },
        "expected_output_schema": RETURN_SCHEMA,
        "success_failure_evidence": (
            "executor must return explicit success/failure with exact source "
            "identities and calculation results; absence of evidence is failure."
        ),
        "prohibited_claims": [
            "executor must not raise any claim ceiling",
            "executor must not assert a positive finding",
            "executor must not mark the episode complete",
        ],
        "budget": ep.get("budgets", {}),
        "stop_condition": (
            "return when the bounded objective is met or a budget/blocker is "
            "reached; never self-approve."
        ),
        "dispatched_by": actor,
    }


def validate_return(ret: dict, strict_schema: bool = False) -> dict:
    """Validate an executor return against the contract.

    Always enforces the required fields and the prohibited keys. When
    ``strict_schema`` is True (or jsonschema is available and the caller
    requests it), also runs full JSON-Schema structural validation against the
    formal schema document.
    """
    if not isinstance(ret, dict):
        raise ValueError("executor return must be a JSON object")
    missing = [k for k in RETURN_REQUIRED_FIELDS if k not in ret]
    if missing:
        raise ValueError(f"executor return missing required fields: {missing}")
    for key in PROHIBITED_RETURN_KEYS:
        if key in ret:
            raise ValueError(
                f"executor return contains prohibited key '{key}'; "
                "an executor may never self-approve, mark complete, or raise a "
                "claim ceiling. Rejected by Research OS."
            )
    if strict_schema:
        errors = _validate_with_jsonschema(ret, load_executor_return_schema())
        if errors:
            raise ValueError(
                "executor return failed schema validation: " + "; ".join(errors)
            )
    return ret
