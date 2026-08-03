"""Executor Adapter Contract (Checkpoint B).

Tool-agnostic dispatch/return contract so Codex, WorkBuddy, other agents or
scripts can act as executors. The OS sends an exact, bounded spec; the executor
returns observations with explicit provenance and NO self-approval. The OS then
diagnoses the returned state; an executor cannot mark its episode complete merely
by returning success.
"""

from __future__ import annotations

from typing import Any

from . import registries as R

RETURN_SCHEMA = "research-os/executor-return/0.1"
RETURN_REQUIRED_FIELDS = [
    "observations",
    "source_identities",
    "access_level",
    "calculation_result",
    "errors",
    "provenance",
    "timestamps",
]


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


def validate_return(ret: dict) -> dict:
    if not isinstance(ret, dict):
        raise ValueError("executor return must be a JSON object")
    missing = [k for k in RETURN_REQUIRED_FIELDS if k not in ret]
    if missing:
        raise ValueError(f"executor return missing required fields: {missing}")
    if ret.get("self_approved") or ret.get("mark_episode_complete"):
        raise ValueError(
            "executor return contains self-approval (self_approved / "
            "mark_episode_complete); rejected by Research OS"
        )
    return ret
