#!/usr/bin/env python3
"""Assemble the evaluator-only packet map and runtime-attestation package index."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
TASK_DIR = REPO_ROOT / "ignition/reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0"
PACKET_SET = TASK_DIR / "provenance/packet-set-r0.json"
SEALED_DIR = TASK_DIR / "evaluator/sealed-r0"
CRITERIA_FILES = (
    "evaluator/criteria-r0.md",
    "evaluator/criteria-r0.json",
)
RUNTIME_FILES = (
    "evaluator/runtime-attestation/receipt-r0.schema.json",
    "evaluator/runtime-attestation/interpretation-r0.md",
    "tools/validate_runtime_attestation_r0.py",
)
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
    SEALED_DIR.mkdir(parents=True, exist_ok=True)
    packet_set = json.loads(PACKET_SET.read_text(encoding="utf-8"))
    map_path = SEALED_DIR / "condition-map-r0.json"
    if not map_path.is_file():
        raise SystemExit(f"evaluator-only condition map is required: {map_path}")
    mapping = json.loads(map_path.read_text(encoding="utf-8"))
    if mapping.get("condition_count") != 4 or len(mapping.get("mappings", [])) != 8:
        raise SystemExit("evaluator-only condition map has invalid cardinality")
    map_rel = map_path.relative_to(REPO_ROOT).as_posix()
    map_hash = sha256(map_path)
    map_sidecar = map_path.with_name(map_path.name + ".sha256")
    if not map_sidecar.is_file() or map_sidecar.read_text(encoding="utf-8") != f"{map_hash}  {map_rel}\n":
        raise SystemExit("evaluator-only condition map sidecar is absent or mismatched")

    protected_files = []
    for rel in (*CRITERIA_FILES, *RUNTIME_FILES):
        path = TASK_DIR / rel
        protected_files.append({"path": path.relative_to(REPO_ROOT).as_posix(), "sha256": sha256(path)})
    package = {
        "artifact_type": "EVALUATION_EVIDENCE",
        "task_id": "IGNITION-20260923-207",
        "step": "Step06",
        "schema_version": "task207-evaluator-sealed-package-r0",
        "base_commit": "8e70ba196739cf1a79600e02ace36f90ad2c130c",
        "input_packet_set_sha256": sha256(PACKET_SET),
        "condition_map": {"path": map_rel, "sha256": map_hash, "sha256_sidecar": f"{map_rel}.sha256"},
        "evaluator_and_runtime_contract_files": protected_files,
        "protection_boundary": {
            "successor_visible": False,
            "release_gate": "AFTER_BOTH_INDEPENDENT_EVALUATOR_SCORE_SHEETS_ARE_LOCKED",
            "enforcement": "TASK_READ_ALLOWLIST_AND_EVALUATOR_PATH_SEPARATION",
            "cryptographic_encryption_or_repository_acl": False,
            "limitation": "This repository package is protocol-separated, not cryptographically secret from repository readers. Successor tasks must receive only allowlisted packet paths; do not claim repository-level secrecy.",
        },
        "runtime_receipts_included": 0,
        "status": {
            "successor": "NOT_RUN",
            "evaluator": "NOT_RUN",
            "cross_model_execution": "NOT_AUTHORIZED",
            "r1": "NOT_AUTHORIZED",
            "canonical_claim_ids": [],
            "canonical_promotion": "NONE",
        },
    }
    package_path = SEALED_DIR / "package-manifest-r0.json"
    write_json(package_path, package)
    write_sidecar(package_path, package_path.relative_to(REPO_ROOT).as_posix())
    print("TASK207_STEP06_EVALUATOR_PACKAGE_BUILT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
