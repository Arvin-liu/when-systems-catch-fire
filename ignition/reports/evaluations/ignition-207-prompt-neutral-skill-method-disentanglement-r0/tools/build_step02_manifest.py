#!/usr/bin/env python3
"""Build Task207 case provenance hash sidecars and deterministic manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
TASK_DIR = REPO_ROOT / "ignition/reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0"
CASES_DIR = TASK_DIR / "cases"
CASE_DESCRIPTORS = (
    ("DISENTANGLE-CASE-01", "PARALLEL_RESETTABLE_CHANNELS"),
    ("DISENTANGLE-CASE-02", "SINGLE_PATH_NON_RESETTABLE_STATE"),
    ("DISENTANGLE-CASE-03", "SERIAL_BRIDGE_MISSING_BASELINE"),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repo_relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def write_sidecar(target: Path, sidecar: Path) -> str:
    digest = sha256(target)
    sidecar.write_text(f"{digest}  {repo_relative(target)}\n", encoding="utf-8")
    return digest


def main() -> int:
    entries = []
    for case_id, structure_signature in CASE_DESCRIPTORS:
        case_dir = CASES_DIR / case_id
        facts = case_dir / "facts.md"
        provenance = case_dir / "provenance.json"
        provenance_data = json.loads(provenance.read_text(encoding="utf-8"))
        facts_hash = sha256(facts)
        if provenance_data.get("source_sha256") != facts_hash:
            raise SystemExit(f"source hash mismatch in {repo_relative(provenance)}")
        if provenance_data.get("source_path") != repo_relative(facts):
            raise SystemExit(f"source path mismatch in {repo_relative(provenance)}")
        if provenance_data.get("case_id") != case_id:
            raise SystemExit(f"case id mismatch in {repo_relative(provenance)}")
        facts_sidecar = case_dir / "facts.md.sha256"
        provenance_sidecar = case_dir / "provenance.json.sha256"
        write_sidecar(facts, facts_sidecar)
        provenance_hash = write_sidecar(provenance, provenance_sidecar)
        entries.append(
            {
                "case_id": case_id,
                "structure_signature": structure_signature,
                "candidate_count": 2,
                "facts_path": repo_relative(facts),
                "facts_sha256": facts_hash,
                "facts_sha256_sidecar": repo_relative(facts_sidecar),
                "provenance_path": repo_relative(provenance),
                "provenance_sha256": provenance_hash,
                "provenance_sha256_sidecar": repo_relative(provenance_sidecar),
            }
        )

    manifest = {
        "artifact_type": "EVALUATION_EVIDENCE",
        "task_id": "IGNITION-20260923-207",
        "step": "Step02",
        "schema_version": "task207-case-manifest-r0",
        "base_commit": "8e70ba196739cf1a79600e02ace36f90ad2c130c",
        "synthetic": True,
        "personal_data": False,
        "external_sources_used": False,
        "cases": entries,
        "case_count": 3,
        "claim_ceiling": "SYNTHETIC_CASE_FIXTURES_ONLY; NO_EXPERIMENTAL_OUTCOME",
        "canonical_claim_ids": [],
        "canonical_promotion": "NONE",
    }
    manifest_path = CASES_DIR / "case-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest_sidecar = CASES_DIR / "case-manifest.sha256"
    write_sidecar(manifest_path, manifest_sidecar)
    print("TASK207_STEP02_CASE_MANIFEST_BUILT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
