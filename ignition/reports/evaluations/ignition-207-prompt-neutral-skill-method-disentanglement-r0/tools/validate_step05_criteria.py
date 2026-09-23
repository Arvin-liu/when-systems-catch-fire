#!/usr/bin/env python3
"""Validate the sealed, pre-outcome evaluator rubric for Task207."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
TASK_DIR = REPO_ROOT / "ignition/reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0"
CRITERIA_JSON = TASK_DIR / "evaluator/criteria-r0.json"
CRITERIA_MD = TASK_DIR / "evaluator/criteria-r0.md"
PACKET_DIR = TASK_DIR / "packets"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL_TASK207_STEP05: {message}")


def check_sidecar(path: Path, rel: str) -> None:
    sidecar = path.with_name(path.name + ".sha256")
    expected = f"{sha256(path)}  {rel}\n"
    require(sidecar.is_file() and sidecar.read_text(encoding="utf-8") == expected, f"sidecar mismatch: {rel}")


def main() -> int:
    criteria = json.loads(CRITERIA_JSON.read_text(encoding="utf-8"))
    require(criteria.get("artifact_type") == "EVALUATION_EVIDENCE", "wrong artifact type")
    require(criteria.get("task_id") == "IGNITION-20260923-207" and criteria.get("step") == "Step05", "wrong task or step")
    require(criteria.get("status") == "PREPARATION_ONLY", "criteria are not preparation-only")
    require(criteria.get("replication_unit") == "INDEPENDENT_CONVERSATION", "replication unit must be conversation")
    require(criteria.get("case_records_per_conversation") == 3, "expected three nested case records")
    require(criteria.get("future_conversations") == 8 and criteria.get("future_conversations_per_condition") == 2, "future sample plan changed")
    require(criteria.get("independent_evaluators") == 2, "two independent evaluator sheets are required")
    require(criteria.get("condition_mapping_release") == "AFTER_BOTH_SCORE_SHEETS_ARE_LOCKED", "condition map release rule changed")
    require(set(criteria.get("domains", {})) == {"FACTUAL_FIDELITY", "EVIDENCE_BOUNDARY", "DECISION_QUALITY", "REFERENCE_INTEGRATION"}, "scoring domains differ from plan")
    for domain, rule in criteria["domains"].items():
        require(rule.get("scale") == [0, 1, 2], f"invalid scale: {domain}")
    require(criteria.get("successor") == "NOT_RUN" and criteria.get("evaluator") == "NOT_RUN", "future trial/evaluation already ran")
    require(criteria.get("canonical_claim_ids") == [] and criteria.get("canonical_promotion") == "NONE", "canonical promotion present")

    md = CRITERIA_MD.read_text(encoding="utf-8")
    for required in (
        "CASE-01",
        "CASE-02",
        "CASE-03",
        "INCOMPLETE_LINKS_RECOGNIZED",
        "TRIAL_WORKTREE_MUTATION_INVALID",
        "nested observations",
        "Do not calculate inferential significance",
    ):
        require(required in md, f"criteria anchor missing: {required}")
    require(CRITERIA_JSON.parent != PACKET_DIR and not CRITERIA_JSON.is_relative_to(PACKET_DIR), "evaluator criteria are inside successor-visible packets")
    for packet_manifest in PACKET_DIR.glob("*/packet-manifest.json"):
        data = json.loads(packet_manifest.read_text(encoding="utf-8"))
        encoded = json.dumps(data, ensure_ascii=False)
        require("criteria-r0" not in encoded and "evaluator/" not in encoded, "successor-visible packet points at evaluator criteria")

    json_rel = "ignition/reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0/evaluator/criteria-r0.json"
    md_rel = "ignition/reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0/evaluator/criteria-r0.md"
    check_sidecar(CRITERIA_JSON, json_rel)
    check_sidecar(CRITERIA_MD, md_rel)
    print("TASK207_STEP05_CRITERIA_VALID: pre-outcome rubric locked; evaluator criteria excluded from successor packets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
