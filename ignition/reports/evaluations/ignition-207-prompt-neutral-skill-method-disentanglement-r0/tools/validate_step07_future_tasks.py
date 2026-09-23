#!/usr/bin/env python3
"""Validate eight distinct, unlaunched future Successor task manifests."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
TASK_DIR = REPO_ROOT / "ignition/reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0"
FUTURE_DIR = TASK_DIR / "future-tasks"
TASKS_DIR = FUTURE_DIR / "tasks"
INDEX_PATH = FUTURE_DIR / "task-index-r0.json"
SEALED_MARKERS = ("condition-map-r0", "evaluator/sealed-r0", "condition_label")
FORBIDDEN_LABELS = ("FACTS_ONLY", "SKILL_ONLY", "METHOD_ARTIFACT", "BROKEN_METHOD", "BROKEN_METHOD_TRACE")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL_TASK207_STEP07: {message}")


def check_sidecar(path: Path, rel: str, expected_hash=None) -> None:
    digest = sha256(path)
    if expected_hash is not None:
        require(digest == expected_hash, f"hash mismatch: {rel}")
    sidecar = path.with_name(path.name + ".sha256")
    require(sidecar.is_file() and sidecar.read_text(encoding="utf-8") == f"{digest}  {rel}\n", f"sidecar mismatch: {rel}")


def main() -> int:
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    require(index.get("artifact_type") == "EVALUATION_EVIDENCE" and index.get("step") == "Step07", "wrong artifact type or step")
    require(index.get("base_commit") == "8e70ba196739cf1a79600e02ace36f90ad2c130c", "wrong exact base")
    require(index.get("future_task_count") == 8 and len(index.get("future_successors", [])) == 8, "must prepare eight future tasks")
    require(index.get("condition_mapping") == "WITHHELD_IN_EVALUATOR_SEALED_PACKAGE", "condition mapping was exposed")
    require(index.get("launch_authorization", "").startswith("NOT_GRANTED_BY_PREPARATION"), "preparation granted launch authority")
    require(index.get("same_runtime_configuration_across_all_eight") is True, "same-runtime control missing")
    for key, expected in (("successor", "NOT_RUN"), ("evaluator", "NOT_RUN"), ("cross_model_execution", "NOT_AUTHORIZED"), ("r1", "NOT_AUTHORIZED"), ("canonical_claim_ids", []), ("canonical_promotion", "NONE")):
        require(index.get(key) == expected, f"status boundary changed: {key}")

    packet_set = json.loads((TASK_DIR / "provenance/packet-set-r0.json").read_text(encoding="utf-8"))
    packet_ids = {row["packet_id"] for row in packet_set["packets"]}
    task_ids = set()
    assigned_packet_ids = set()
    for row in index["future_successors"]:
        task_id = row.get("opaque_future_task_id", "")
        packet_id = row.get("opaque_packet_id", "")
        require(re.fullmatch(r"TASK-[0-9A-F]{4}", task_id) is not None, f"future task id is not opaque: {task_id}")
        require(task_id not in task_ids and packet_id not in assigned_packet_ids, "task or packet assigned more than once")
        require(packet_id in packet_ids, f"unknown packet: {packet_id}")
        task_ids.add(task_id)
        assigned_packet_ids.add(packet_id)
        rel = row["manifest_path"]
        path = REPO_ROOT / rel
        check_sidecar(path, rel, row.get("manifest_sha256"))
        manifest = json.loads(path.read_text(encoding="utf-8"))
        encoded = json.dumps(manifest, ensure_ascii=False).upper()
        require(manifest.get("task_id") == task_id and manifest.get("packet", {}).get("opaque_packet_id") == packet_id, f"task assignment mismatch: {task_id}")
        require(not any(marker.upper() in encoded for marker in SEALED_MARKERS), f"sealed/evaluator material referenced by {task_id}")
        require(not any(label in encoded for label in FORBIDDEN_LABELS), f"condition label exposed in {task_id}")
        require("condition" not in manifest and "experimental_condition" not in manifest, f"condition field exposed in {task_id}")
        launch = manifest.get("launch", {})
        require(launch.get("launch_authorization", "").startswith("NOT_GRANTED_BY_PREPARATION"), f"launch gate absent: {task_id}")
        require(launch.get("prepared_commit") == "EXACT_TASK207_PR_HEAD_SHA_MUST_BE_RECORDED_AND_PINNED_BEFORE_LAUNCH", f"launch commit pin missing: {task_id}")
        require(launch.get("starting_worktree_must_be_clean") is True and launch.get("conversation_must_be_fresh_and_independent") is True, f"clean/fresh task contract missing: {task_id}")
        require(launch.get("shared_history_or_context_between_tasks") is False, f"conversation isolation missing: {task_id}")
        require(launch.get("read_only_scope") == "THIS_PACKET_ONLY_AND_ITS_READ_MANIFEST", f"packet allowlist missing: {task_id}")
        require(launch.get("output_path") == f"trial-output/{packet_id}/successor-output.jsonl", f"output path mismatch: {task_id}")
        require(manifest.get("runtime_policy", {}).get("same_runtime_configuration_across_all_eight") is True, f"same-runtime policy missing: {task_id}")
        require(manifest.get("runtime_policy", {}).get("cross_model_execution") == "NOT_AUTHORIZED", f"cross-model authorization leaked: {task_id}")
        require(manifest.get("runtime_policy", {}).get("r1") == "NOT_AUTHORIZED", f"R1 authorization leaked: {task_id}")
        require(manifest.get("status", {}).get("successor") == "NOT_RUN" and manifest.get("status", {}).get("evaluator") == "NOT_RUN", f"future task marked run: {task_id}")
        packet_manifest = json.loads((TASK_DIR / "packets" / packet_id / "packet-manifest.json").read_text(encoding="utf-8"))
        require(manifest.get("packet", {}).get("packet_manifest_sha256") == sha256(TASK_DIR / "packets" / packet_id / "packet-manifest.json"), f"packet hash mismatch: {task_id}")
        require(manifest.get("packet", {}).get("case_order") == packet_manifest.get("case_order"), f"case order mismatch: {task_id}")
        require(manifest.get("packet", {}).get("prompt_sha256") == packet_manifest.get("prompt", {}).get("sha256"), f"prompt hash mismatch: {task_id}")
    require(assigned_packet_ids == packet_ids, "future task plan does not assign every packet exactly once")
    require(len(list(TASKS_DIR.glob("TASK-*.json"))) == 8, "unexpected future task manifest count")
    check_sidecar(INDEX_PATH, INDEX_PATH.relative_to(REPO_ROOT).as_posix())
    print("TASK207_STEP07_FUTURE_TASKS_VALID: 8 isolated task manifests; none launched; one opaque packet per task")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
