#!/usr/bin/env python3
"""Prepare eight non-launched, single-packet Successor task manifests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
TASK_DIR = REPO_ROOT / "ignition/reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0"
PACKET_SET = TASK_DIR / "provenance/packet-set-r0.json"
TASKS_DIR = TASK_DIR / "future-tasks/tasks"
INDEX_PATH = TASK_DIR / "future-tasks/task-index-r0.json"
TASK_ASSIGNMENTS = (
    ("TASK-31A7", "PKT-40BC81"),
    ("TASK-6C2F", "PKT-7C4A9D"),
    ("TASK-4E90", "PKT-E3157A"),
    ("TASK-B2A5", "PKT-05E8B2"),
    ("TASK-993D", "PKT-92DE30"),
    ("TASK-0F68", "PKT-D18F63"),
    ("TASK-712C", "PKT-B6092E"),
    ("TASK-E43B", "PKT-A7C145"),
)
TASK_REL = "ignition/reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0/future-tasks"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_sidecar(path: Path, repo_rel: str) -> str:
    digest = sha256(path)
    path.with_name(path.name + ".sha256").write_text(f"{digest}  {repo_rel}\n", encoding="utf-8")
    return digest


def main() -> int:
    if TASKS_DIR.exists() or INDEX_PATH.exists():
        raise SystemExit("refusing to replace existing future task manifests")
    packet_set = json.loads(PACKET_SET.read_text(encoding="utf-8"))
    packets = {row["packet_id"]: row for row in packet_set["packets"]}
    task_rows = []
    task_ids = set()
    packet_ids = set()
    for task_id, packet_id in TASK_ASSIGNMENTS:
        if task_id in task_ids or packet_id in packet_ids or packet_id not in packets:
            raise SystemExit("future task assignments must be unique and reference known packets")
        task_ids.add(task_id)
        packet_ids.add(packet_id)
        packet_manifest_path = TASK_DIR / "packets" / packet_id / "packet-manifest.json"
        packet_manifest = json.loads(packet_manifest_path.read_text(encoding="utf-8"))
        task = {
            "artifact_type": "EVALUATION_EVIDENCE",
            "task_id": task_id,
            "parent_experiment_id": "IGNITION-20260923-207",
            "schema_version": "task207-future-successor-task-r0",
            "role": "SUCCESSOR",
            "packet": {
                "opaque_packet_id": packet_id,
                "packet_manifest_path": f"packets/{packet_id}/packet-manifest.json",
                "packet_manifest_sha256": packets[packet_id]["packet_manifest_sha256"],
                "prompt_sha256": packet_manifest["prompt"]["sha256"],
                "read_manifest_sha256": packet_manifest["read_manifest"]["sha256"],
                "freeze_contract_sha256": packet_manifest["freeze_contract"]["sha256"],
                "output_schema_sha256": packet_manifest["output_schema"]["sha256"],
                "case_order": packet_manifest["case_order"],
            },
            "launch": {
                "launch_authorization": "NOT_GRANTED_BY_PREPARATION; EXPLICIT_OWNER_AUTHORIZATION_REQUIRED",
                "prepared_branch": "work/IGNITION-20260923-207-prompt-neutral-skill-method-disentanglement-r0",
                "prepared_commit": "EXACT_TASK207_PR_HEAD_SHA_MUST_BE_RECORDED_AND_PINNED_BEFORE_LAUNCH",
                "starting_worktree_must_be_clean": True,
                "conversation_must_be_fresh_and_independent": True,
                "shared_history_or_context_between_tasks": False,
                "prompt_bytes_must_be_unchanged": True,
                "read_only_scope": "THIS_PACKET_ONLY_AND_ITS_READ_MANIFEST",
                "output_path": f"trial-output/{packet_id}/successor-output.jsonl",
            },
            "runtime_policy": {
                "model_assignment": "UNASSIGNED_PENDING_FUTURE_OWNER_AUTHORIZATION",
                "same_runtime_configuration_across_all_eight": True,
                "runtime_receipt_required_per_conversation": "evaluator/runtime-attestation/receipt-r0.schema.json",
                "configuration_status_must_not_be_overstated": True,
                "cross_model_execution": "NOT_AUTHORIZED",
                "r1": "NOT_AUTHORIZED",
            },
            "output_contract": {
                "records": 3,
                "encoding": "UTF-8 JSON Lines; one schema-valid object per case; no wrapper",
                "case_ids_and_order_from_packet_manifest": True,
                "claim_ceiling": "SYNTHETIC_CASE_FIXTURES_ONLY; NO EXPERIMENTAL_OUTCOME",
            },
            "status": {
                "successor": "NOT_RUN",
                "evaluator": "NOT_RUN",
                "cross_model_execution": "NOT_AUTHORIZED",
                "r1": "NOT_AUTHORIZED",
                "canonical_claim_ids": [],
                "canonical_promotion": "NONE",
            },
        }
        manifest_path = TASKS_DIR / f"{task_id}.json"
        write_json(manifest_path, task)
        manifest_rel = manifest_path.relative_to(REPO_ROOT).as_posix()
        task_hash = write_sidecar(manifest_path, manifest_rel)
        task_rows.append({"opaque_future_task_id": task_id, "manifest_path": manifest_rel, "manifest_sha256": task_hash, "opaque_packet_id": packet_id})

    if len(task_rows) != 8 or packet_ids != set(packets):
        raise SystemExit("future task plan must cover the eight packets exactly once")
    index = {
        "artifact_type": "EVALUATION_EVIDENCE",
        "task_id": "IGNITION-20260923-207",
        "step": "Step07",
        "schema_version": "task207-future-task-index-r0",
        "base_commit": "8e70ba196739cf1a79600e02ace36f90ad2c130c",
        "future_task_count": 8,
        "future_successors": task_rows,
        "condition_mapping": "WITHHELD_IN_EVALUATOR_SEALED_PACKAGE",
        "launch_authorization": "NOT_GRANTED_BY_PREPARATION; EXPLICIT_OWNER_AUTHORIZATION_REQUIRED",
        "same_runtime_configuration_across_all_eight": True,
        "successor": "NOT_RUN",
        "evaluator": "NOT_RUN",
        "cross_model_execution": "NOT_AUTHORIZED",
        "r1": "NOT_AUTHORIZED",
        "canonical_claim_ids": [],
        "canonical_promotion": "NONE",
    }
    write_json(INDEX_PATH, index)
    write_sidecar(INDEX_PATH, INDEX_PATH.relative_to(REPO_ROOT).as_posix())
    print("TASK207_STEP07_FUTURE_TASKS_BUILT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
