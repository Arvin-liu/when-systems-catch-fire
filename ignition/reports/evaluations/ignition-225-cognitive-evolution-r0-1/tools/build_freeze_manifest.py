#!/usr/bin/env python3
"""Deterministically build the Task225 R0.1 science-freeze manifest and sidecar."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[5]
SUBTREE = REPO / "ignition/reports/evaluations/ignition-225-cognitive-evolution-r0-1"
MANIFEST = SUBTREE / "freeze-manifest.json"
SIDECAR = SUBTREE / "freeze.sha256"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def main() -> None:
    files = []
    for path in sorted(SUBTREE.rglob("*")):
        if not path.is_file() or path in (MANIFEST, SIDECAR):
            continue
        files.append({"path": rel(path), "sha256": digest(path)})

    source_paths = []
    source_root = REPO / "ignition/reports/evaluations/ignition-220-cognitive-evolution-r0"
    for family in ("FAMILY01", "FAMILY02", "FAMILY03"):
        for name in ("m0.md", "revision-evidence-e1.md"):
            source_paths.append(source_root / "families" / family / name)

    payload = {
        "freeze_version": "R0.1",
        "study_class": "POST_RESULT_EXPLORATORY_COGNITIVE_EVOLUTION_R0_1",
        "command": {
            "path": "agent-commands/IGNITION-20260927-225-R1-ANTIBYPASS-REPAIR-AND-RESUME-OVERNIGHT.md",
            "blob_sha": "4bea72e6c766683e1452f885e0ef823b952a0e9a"
        },
        "starting_anchor": {
            "formal_pr": 235,
            "head": "8989a7c58e602f1e02c5de95af1cde418ad827a9",
            "base": "1f7286515768347a2a3a131dd0f6de87f631676c",
            "initial_pr_state": "OPEN_DRAFT_UNMERGED",
            "initial_required_workflows": "SUCCESS"
        },
        "design_gate": {
            "family01": "4/4",
            "family02": "4/4",
            "family03": "4/4",
            "full_a_case_validity_gate": "3/3",
            "m0_only_two_way_ambiguity_proven": "3/3",
            "repair_round": 3
        },
        "outputs_at_scientific_freeze": {
            "revision": 0,
            "transfer": 0,
            "evaluator": 0
        },
        "external_evidence": [
            {"path": rel(path), "sha256": digest(path)} for path in source_paths
        ],
        "frozen_files": files
    }
    MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    sidecar_hash = digest(MANIFEST)
    SIDECAR.write_text(f"{sidecar_hash}  freeze-manifest.json\n", encoding="utf-8")


if __name__ == "__main__":
    main()
