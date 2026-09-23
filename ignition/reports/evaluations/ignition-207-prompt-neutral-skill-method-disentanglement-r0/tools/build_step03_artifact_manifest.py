#!/usr/bin/env python3
"""Bind Task207 procedural artifacts to their final source bytes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
TASK_DIR = REPO_ROOT / "ignition/reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0"
PAYLOAD_DIR = TASK_DIR / "payload"
SCHEMA_PATH = TASK_DIR / "schema/skill-procedure-r0.schema.json"
MANIFEST_PATH = TASK_DIR / "provenance/artifact-manifest.json"
SOURCE_HISTORY = PAYLOAD_DIR / "item-b-history.md"
PARTIAL_SOURCE = PAYLOAD_DIR / "item-c-source.md"
METHOD_TRACE = PAYLOAD_DIR / "item-b.json"
PARTIAL_TRACE = PAYLOAD_DIR / "item-c.json"

REUSED_CONTRACTS = (
    (
        "ignition/reports/evaluations/ignition-190-method-use-trace-r0/schema/method-use-trace-r0.schema.json",
        "e53532c8338c76d83b72c79edbb3780800d190ce9338c194c7ba2f03eec69e8b",
    ),
    (
        "ignition/reports/evaluations/ignition-190-method-use-trace-r0/tools/validate_method_use_trace_r0.py",
        "7adcd2c56acb520b26e2f9e126f0ac258ec5f794582e08c0e2c993fcb4f527a5",
    ),
    (
        "ignition/evaluation/heldout/r0.1/successor-visible/successor-output-r0.1.schema.json",
        "fdf46bbe7f92dbc5a8340ad95381a0932b5b55f49f3c88f48f33c502a52c0133",
    ),
)
PAYLOADS = (
    ("item-a", "REUSABLE_PROCEDURAL_SKILL", "payload/item-a.json", "synthetic://ignition-207/skill/paired-readout-comparison-r0", None),
    ("item-b-history", "METHOD_SOURCE_HISTORY", "payload/item-b-history.md", "synthetic://ignition-207/calibration/gated-local-measurement-r0", None),
    ("item-b", "COMPLETE_METHOD_USE_TRACE_R0", "payload/item-b.json", "synthetic://ignition-207/calibration/gated-local-measurement-r0", "payload/item-b-history.md"),
    ("item-c-source", "PARTIAL_LINEAGE_SOURCE", "payload/item-c-source.md", "synthetic://ignition-207/calibration/fragment-r7", None),
    ("item-c", "LINEAGE_FRAGMENT", "payload/item-c.json", "synthetic://ignition-207/calibration/fragment-r7", "payload/item-c-source.md"),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repo_relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_sidecar(path: Path) -> str:
    digest = sha256(path)
    sidecar = path.with_name(path.name + ".sha256")
    sidecar.write_text(f"{digest}  {repo_relative(path)}\n", encoding="utf-8")
    return digest


def main() -> int:
    history_hash = sha256(SOURCE_HISTORY)
    partial_hash = sha256(PARTIAL_SOURCE)

    method = json.loads(METHOD_TRACE.read_text(encoding="utf-8"))
    for segment in method["segments"]:
        segment["source_sha256"] = history_hash
    write_json(METHOD_TRACE, method)

    partial = json.loads(PARTIAL_TRACE.read_text(encoding="utf-8"))
    for segment in partial["segments"]:
        segment["source_sha256"] = partial_hash
    write_json(PARTIAL_TRACE, partial)

    artifact_entries = []
    for opaque_id, role, rel, source_ref, source_rel in PAYLOADS:
        path = TASK_DIR / rel
        source_path = TASK_DIR / source_rel if source_rel is not None else None
        artifact_entries.append(
            {
                "opaque_artifact_id": opaque_id,
                "representation_role": role,
                "path": repo_relative(path),
                "sha256": sha256(path),
                "sha256_sidecar": repo_relative(path.with_name(path.name + ".sha256")),
                "source_kind": "BUILDER_AUTHORED_SYNTHETIC",
                "source_ref": source_ref,
                "source_path": repo_relative(source_path) if source_path is not None else None,
                "source_sha256": sha256(source_path) if source_path is not None else None,
            }
        )
    artifact_entries.append(
        {
            "opaque_artifact_id": "skill-procedure-r0",
            "representation_role": "TASK_LOCAL_SKILL_SCHEMA",
            "path": repo_relative(SCHEMA_PATH),
            "sha256": sha256(SCHEMA_PATH),
            "sha256_sidecar": repo_relative(SCHEMA_PATH.with_name(SCHEMA_PATH.name + ".sha256")),
            "source_kind": "TASK_LOCAL_SCHEMA_AUTHORED_FOR_THIS_PREPARATION",
            "source_ref": "synthetic://ignition-207/schema/skill-procedure-r0",
            "source_path": None,
            "source_sha256": None,
        }
    )

    reused = []
    for rel, expected in REUSED_CONTRACTS:
        path = REPO_ROOT / rel
        actual = sha256(path)
        if actual != expected:
            raise SystemExit(f"pinned reusable contract changed: {rel}")
        reused.append({"path": rel, "sha256": actual})

    manifest = {
        "artifact_type": "EVALUATION_EVIDENCE",
        "task_id": "IGNITION-20260923-207",
        "step": "Step03",
        "base_commit": "8e70ba196739cf1a79600e02ace36f90ad2c130c",
        "scope": "TASK_LOCAL_SYNTHETIC_INPUT_ARTIFACTS_ONLY",
        "artifacts": artifact_entries,
        "reused_contracts": reused,
        "method_trace_lineage": {
            "complete_trace_segment_count": 6,
            "complete_trace_source_path": repo_relative(SOURCE_HISTORY),
            "complete_trace_source_sha256": history_hash,
            "excerpt_segment_kinds": [
                "METHOD_CANDIDATE",
                "CONTEXT",
                "OBSERVED_OUTCOME_OR_FAILURE",
            ],
            "excerpt_source_path": repo_relative(PARTIAL_SOURCE),
            "excerpt_source_sha256": partial_hash,
            "missing_lineage_kinds": [
                "SELECTION_RATIONALE",
                "METHOD_USE_EVENT",
                "REVISION_OR_DISPOSITION",
            ],
        },
        "skill_boundary": {
            "method_lineage": "NOT_PRESENT",
            "case_answers_included": False,
        },
        "status": {
            "successor": "NOT_RUN",
            "evaluator": "NOT_RUN",
            "canonical_claim_ids": [],
            "canonical_promotion": "NONE",
        },
    }
    write_json(MANIFEST_PATH, manifest)

    for _, _, rel, _, _ in PAYLOADS:
        write_sidecar(TASK_DIR / rel)
    write_sidecar(SCHEMA_PATH)
    write_sidecar(MANIFEST_PATH)
    print("TASK207_STEP03_ARTIFACT_MANIFEST_BUILT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
