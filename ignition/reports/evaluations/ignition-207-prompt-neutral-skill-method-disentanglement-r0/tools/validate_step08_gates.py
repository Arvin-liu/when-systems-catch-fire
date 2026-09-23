#!/usr/bin/env python3
"""Validate R0 complexity, invalidation, retirement, and authorization gates."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
TASK_DIR = REPO_ROOT / "ignition/reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0"
GATES_JSON = TASK_DIR / "design/complexity-and-gates-r0.json"
GATES_MD = TASK_DIR / "design/complexity-and-gates-r0.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL_TASK207_STEP08: {message}")


def check_sidecar(path: Path, rel: str) -> None:
    expected = f"{sha256(path)}  {rel}\n"
    sidecar = path.with_name(path.name + ".sha256")
    require(sidecar.is_file() and sidecar.read_text(encoding="utf-8") == expected, f"sidecar mismatch: {rel}")


def main() -> int:
    data = json.loads(GATES_JSON.read_text(encoding="utf-8"))
    require(data.get("artifact_type") == "EVALUATION_EVIDENCE" and data.get("step") == "Step08", "wrong artifact type or step")
    require(data.get("base_commit") == "8e70ba196739cf1a79600e02ace36f90ad2c130c", "wrong exact base")
    counts = data.get("design_counts", {})
    require(counts == {
        "conditions": 4,
        "independent_conversations_per_condition": 2,
        "future_conversations": 8,
        "cases_per_conversation": 3,
        "nested_case_records": 24,
        "independent_replication_unit": "CONVERSATION",
    }, "complexity counts changed")
    require(data.get("analysis_ceiling", {}).get("summary_mode") == "DESCRIPTIVE_ONLY", "analysis ceiling raised")
    require(data["analysis_ceiling"].get("inferential_significance") == "NOT_AUTHORIZED", "inferential analysis authorized")
    require(data["analysis_ceiling"].get("general_cognitive_inheritance") == "NOT_ESTABLISHED", "general inheritance established")
    require(data["analysis_ceiling"].get("r1") == "NOT_AUTHORIZED" and data["analysis_ceiling"].get("cross_model_transfer") == "NOT_AUTHORIZED", "R1/cross-model authorization changed")
    require(data.get("condition_separation", {}).get("direct_condition_labels_in_successor_packets") is False, "condition labels exposed")
    require(data.get("condition_separation", {}).get("input_content_nature_may_be_inferable") is True, "content distinction hidden by overclaim")
    require("TRIAL_WORKTREE_MUTATION_INVALID" in data.get("retirement_triggers", []), "mutation invalidation absent")
    require(data.get("invalid_trial_disposition") == "STOP_RUN_FAMILY; DO_NOT_REPLACE_OR_RERUN_WITHIN_R0", "invalid trial disposition changed")
    require(len(data.get("next_gate", [])) == 6, "next gate sequence incomplete")
    for key, expected in (("successor", "NOT_RUN"), ("evaluator", "NOT_RUN"), ("cross_model_execution", "NOT_AUTHORIZED"), ("r1", "NOT_AUTHORIZED"), ("canonical_claim_ids", []), ("canonical_promotion", "NONE")):
        require(data.get("status", {}).get(key) == expected, f"status boundary changed: {key}")
    md = GATES_MD.read_text(encoding="utf-8")
    for required in ("TRIAL_WORKTREE_MUTATION_INVALID", "randomized task execution order", "not authorization to start them", "two independent score sheets"):
        require(required in md, f"gate narrative missing: {required}")
    check_sidecar(GATES_JSON, GATES_JSON.relative_to(REPO_ROOT).as_posix())
    check_sidecar(GATES_MD, GATES_MD.relative_to(REPO_ROOT).as_posix())
    print("TASK207_STEP08_GATES_VALID: nested unit, hard stop conditions, and authorization limits preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
