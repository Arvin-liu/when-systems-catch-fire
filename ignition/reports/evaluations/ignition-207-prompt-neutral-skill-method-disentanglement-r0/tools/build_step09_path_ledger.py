#!/usr/bin/env python3
"""Inventory Task207 preparation paths and bind hashes for Step09 accounting."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
TASK_DIR = REPO_ROOT / "ignition/reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0"
TASK_PREFIX = TASK_DIR.relative_to(REPO_ROOT).as_posix() + "/"
BASE_COMMIT = "8e70ba196739cf1a79600e02ace36f90ad2c130c"
LEDGER_PATH = TASK_DIR / "provenance/path-accounting-r0.json"
LEDGER_MD = TASK_DIR / "provenance/path-accounting-r0.md"
SELF_PATHS = {LEDGER_PATH, LEDGER_MD}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify(path: Path) -> tuple[str, str]:
    rel = path.relative_to(TASK_DIR).as_posix()
    if path.name.endswith(".sha256"):
        return "HASH_SIDECAR", "EVALUATION_EVIDENCE"
    if rel.startswith("packets/") or rel.startswith("common/"):
        return "SUCCESSOR_VISIBLE_PACKET_INPUT", "EVALUATION_EVIDENCE"
    if rel.startswith("evaluator/sealed-r0/"):
        return "EVALUATOR_SEALED_PROTOCOL", "EVALUATION_EVIDENCE"
    if rel.startswith("evaluator/"):
        return "EVALUATOR_PROTOCOL", "EVALUATION_EVIDENCE"
    if rel.startswith("future-tasks/"):
        return "FUTURE_TASK_PLAN_NOT_LAUNCHED", "EVALUATION_EVIDENCE"
    if rel.startswith("cases/") or rel.startswith("payload/"):
        return "SYNTHETIC_TASK_INPUT", "EVALUATION_EVIDENCE"
    if rel.startswith("tools/"):
        return "BUILDER_OR_VALIDATOR", "EVALUATION_EVIDENCE"
    if rel.startswith("schema/"):
        return "TASK_LOCAL_SCHEMA", "EVALUATION_EVIDENCE"
    if rel.startswith("design/"):
        return "EXPERIMENTAL_DESIGN_GATE", "EVALUATION_EVIDENCE"
    if rel.startswith("provenance/"):
        return "PROVENANCE_OR_PACKET_PLAN", "EVALUATION_EVIDENCE"
    if path.name == "owner-gpt-adjudication-input.json":
        return "FROZEN_OWNER_GPT_ADJUDICATION", "EVALUATION_EVIDENCE"
    if path.name.startswith("representation-sufficiency"):
        return "REPRESENTATION_AUDIT", "EVALUATION_EVIDENCE"
    return "TASK207_PREPARATION_ARTIFACT", "EVALUATION_EVIDENCE"


def repo_rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def main() -> int:
    rows = []
    for root, dirs, files in os.walk(TASK_DIR, followlinks=False):
        dirs[:] = sorted(name for name in dirs if not (Path(root) / name).is_symlink())
        for filename in sorted(files):
            path = Path(root) / filename
            if path in SELF_PATHS or path.name in {"path-accounting-r0.json.sha256", "path-accounting-r0.md.sha256"}:
                continue
            if path.is_symlink() or not path.is_file():
                raise SystemExit(f"unexpected non-regular Task207 path: {path}")
            category, artifact_type = classify(path)
            rel = repo_rel(path)
            rows.append(
                {
                    "path": rel,
                    "sha256": sha256(path),
                    "size_bytes": path.stat().st_size,
                    "path_class": category,
                    "artifact_type": artifact_type,
                    "canonical_claim_ids": [],
                    "canonical_promotion": "NONE",
                    "successor_or_evaluator_execution": "NOT_RUN",
                    "sha256_sidecar": f"{rel}.sha256" if path.with_name(path.name + ".sha256").is_file() else None,
                }
            )
    rows.sort(key=lambda row: row["path"])

    path_diff = subprocess.run(
        ["git", "diff", "--name-only", f"{BASE_COMMIT}...HEAD"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if path_diff.returncode != 0:
        raise SystemExit(path_diff.stderr.strip() or "git diff path accounting failed")
    changed_paths = [line for line in path_diff.stdout.splitlines() if line]
    outside_task = [path for path in changed_paths if not path.startswith(TASK_PREFIX)]
    if outside_task:
        raise SystemExit("changed paths outside the Task207 evaluation directory: " + ", ".join(outside_task[:10]))

    data = {
        "artifact_type": "EVALUATION_EVIDENCE",
        "task_id": "IGNITION-20260923-207",
        "step": "Step09",
        "schema_version": "task207-path-accounting-r0",
        "base_commit": BASE_COMMIT,
        "pre_step08_head": "0ca97b283f0955a708f6bfe8f24762b3672c0896",
        "scope": "ALL_TASK207_PREPARATION_FILES; NO_REPOSITORY_WIDE_RECLASSIFICATION",
        "task_root": TASK_PREFIX.rstrip("/"),
        "path_count_excluding_this_ledger_and_sidecars": len(rows),
        "paths": rows,
        "self_accounting": {
            "ledger_path": repo_rel(LEDGER_PATH),
            "ledger_sha256": "PROTECTED_BY_DETACHED_SHA256_SIDECAR",
            "ledger_sidecar_path": repo_rel(LEDGER_PATH.with_name(LEDGER_PATH.name + ".sha256")),
            "summary_path": repo_rel(LEDGER_MD),
            "summary_sha256": "PROTECTED_BY_DETACHED_SHA256_SIDECAR",
            "summary_sidecar_path": repo_rel(LEDGER_MD.with_name(LEDGER_MD.name + ".sha256")),
        },
        "downstream_projections": [
            {
                "target": "human-results",
                "required": False,
                "disposition": "NO_PROPAGATION_REQUIRED",
                "proof": "This branch adds design/preparation artifacts only; it contains no Successor output, evaluator result, accepted empirical outcome, or canonical claim ID, and no changed path is outside this Task207 evaluation directory.",
            },
            {
                "target": "Foundation / Current / knowledge / Fire Seeds / self-correction",
                "required": False,
                "disposition": "UNCHANGED",
                "proof": "The exact-base branch diff is scoped entirely under the Task207 evaluation directory; no source projection or canonical path is changed.",
            },
        ],
        "projection_generators_run": [],
        "canonical_claim_ids": [],
        "canonical_promotion": "NONE",
        "successor": "NOT_RUN",
        "evaluator": "NOT_RUN",
        "cross_model_execution": "NOT_AUTHORIZED",
        "r1": "NOT_AUTHORIZED",
    }
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    summary = [
        "# Task207 Path Accounting R0",
        "",
        "All inventoried paths are task-local `EVALUATION_EVIDENCE` preparation artifacts. No canonical claim IDs were added.",
        "",
        f"- Exact base: `{BASE_COMMIT}`",
        f"- Inventory count (excluding this ledger and its sidecars): **{len(rows)}**",
        f"- Changed paths outside this task root: **0**",
        "- Human-results projection: not required; no successor output, evaluator result, accepted empirical outcome, or canonical claim exists.",
        "- Foundation, Current, knowledge, Fire Seeds, and self-correction projections: unchanged; no generator was run.",
        "- Successor/Evaluator: not run. R1 and cross-model execution: not authorized.",
        "",
        "The machine-readable ledger lists each path, SHA-256, byte count, path class, artifact type, canonical status, and available sidecar.",
        "",
    ]
    LEDGER_MD.write_text("\n".join(summary), encoding="utf-8")
    print("TASK207_STEP09_PATH_LEDGER_BUILT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
