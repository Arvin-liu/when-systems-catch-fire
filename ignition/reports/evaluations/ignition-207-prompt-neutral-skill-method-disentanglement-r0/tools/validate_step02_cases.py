#!/usr/bin/env python3
"""Validate Task207's synthetic case sources, provenance, and leakage boundary."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
TASK_DIR = REPO_ROOT / "ignition/reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0"
CASES_DIR = TASK_DIR / "cases"
MANIFEST_PATH = CASES_DIR / "case-manifest.json"
EXPECTED = {
    "DISENTANGLE-CASE-01": (
        "PARALLEL_RESETTABLE_CHANNELS",
        ("two independent lanes", "same input token `T-4`", "Candidate A:", "Candidate B:"),
    ),
    "DISENTANGLE-CASE-02": (
        "SINGLE_PATH_NON_RESETTABLE_STATE",
        ("one active path", "one shared state register", "no reset control", "Candidate A:", "Candidate B:"),
    ),
    "DISENTANGLE-CASE-03": (
        "SERIAL_BRIDGE_MISSING_BASELINE",
        ("downstream bridge counter", "`A0`", "`NOT_RECORDED`", "Candidate A:", "Candidate B:"),
    ),
}
FORBIDDEN_LEAKAGE = (
    "FACTS_ONLY",
    "SKILL_ONLY",
    "METHOD_ARTIFACT",
    "BROKEN_METHOD",
    "BROKEN_METHOD_TRACE",
    "EVALUATOR CRITERIA",
    "ANSWER KEY",
    "EXPECTED CONDITION",
    "SKILL ARTIFACT",
    "METHOD ARTIFACT",
    "APPLY THE METHOD",
    "APPLY THE SKILL",
    "SELECTION RULE",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL_TASK207_STEP02: {message}")


def checked_repo_path(value: str) -> Path:
    path = (REPO_ROOT / value).resolve()
    require(path.is_relative_to(REPO_ROOT), f"path escapes repository: {value}")
    require(path.is_file() and not path.is_symlink(), f"missing or non-regular file: {value}")
    return path


def require_sidecar(sidecar_rel: str, target: Path, expected_hash: str) -> None:
    sidecar = checked_repo_path(sidecar_rel)
    expected = f"{expected_hash}  {target.relative_to(REPO_ROOT).as_posix()}\n"
    require(sidecar.read_text(encoding="utf-8") == expected, f"sidecar mismatch: {sidecar_rel}")
    require(sha256(target) == expected_hash, f"source hash mismatch: {target.relative_to(REPO_ROOT)}")


def main() -> int:
    require(MANIFEST_PATH.is_file(), "case-manifest.json missing")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    require(manifest.get("artifact_type") == "EVALUATION_EVIDENCE", "wrong artifact type")
    require(manifest.get("task_id") == "IGNITION-20260923-207", "wrong task id")
    require(manifest.get("schema_version") == "task207-case-manifest-r0", "wrong manifest version")
    require(manifest.get("base_commit") == "8e70ba196739cf1a79600e02ace36f90ad2c130c", "wrong exact base")
    require(manifest.get("synthetic") is True, "cases are not declared synthetic")
    require(manifest.get("personal_data") is False, "personal data must be absent")
    require(manifest.get("external_sources_used") is False, "external sources are out of scope")
    require(manifest.get("canonical_claim_ids") == [], "canonical claim IDs must be empty")
    require(manifest.get("canonical_promotion") == "NONE", "canonical promotion must be NONE")

    manifest_rel = MANIFEST_PATH.relative_to(REPO_ROOT).as_posix()
    manifest_sidecar_rel = (CASES_DIR / "case-manifest.sha256").relative_to(REPO_ROOT).as_posix()
    require_sidecar(manifest_sidecar_rel, MANIFEST_PATH, sha256(MANIFEST_PATH))
    entries = manifest.get("cases")
    require(isinstance(entries, list) and len(entries) == 3, "manifest must contain exactly three cases")
    require(manifest.get("case_count") == 3, "case_count must be three")
    require([row.get("case_id") for row in entries] == list(EXPECTED), "case identity/order mismatch")

    signatures: set[str] = set()
    for row in entries:
        case_id = row["case_id"]
        expected_signature, required_markers = EXPECTED[case_id]
        require(row.get("structure_signature") == expected_signature, f"wrong structure signature: {case_id}")
        signatures.add(row["structure_signature"])
        require(row.get("candidate_count", 0) >= 2, f"fewer than two candidates: {case_id}")
        facts = checked_repo_path(row.get("facts_path", ""))
        provenance = checked_repo_path(row.get("provenance_path", ""))
        facts_hash = row.get("facts_sha256")
        provenance_hash = row.get("provenance_sha256")
        require(isinstance(facts_hash, str) and re.fullmatch(r"[0-9a-f]{64}", facts_hash) is not None, f"bad facts hash: {case_id}")
        require(isinstance(provenance_hash, str) and re.fullmatch(r"[0-9a-f]{64}", provenance_hash) is not None, f"bad provenance hash: {case_id}")
        require_sidecar(row.get("facts_sha256_sidecar", ""), facts, facts_hash)
        require_sidecar(row.get("provenance_sha256_sidecar", ""), provenance, provenance_hash)

        facts_text = facts.read_text(encoding="utf-8")
        require(facts_text.count("- Candidate A:") == 1, f"Candidate A missing/duplicated: {case_id}")
        require(facts_text.count("- Candidate B:") == 1, f"Candidate B missing/duplicated: {case_id}")
        for marker in required_markers:
            require(marker in facts_text, f"structural fact absent ({marker}): {case_id}")
        upper_facts = facts_text.upper()
        for banned in FORBIDDEN_LEAKAGE:
            require(banned not in upper_facts, f"condition/evaluator/answer leakage ({banned}): {case_id}")

        provenance_data = json.loads(provenance.read_text(encoding="utf-8"))
        require(provenance_data.get("artifact_type") == "EVALUATION_EVIDENCE", f"wrong provenance artifact type: {case_id}")
        require(provenance_data.get("task_id") == "IGNITION-20260923-207", f"wrong provenance task id: {case_id}")
        require(provenance_data.get("case_id") == case_id, f"provenance case id mismatch: {case_id}")
        require(provenance_data.get("source_path") == row["facts_path"], f"provenance path mismatch: {case_id}")
        require(provenance_data.get("source_sha256") == facts_hash, f"provenance source hash mismatch: {case_id}")
        require(provenance_data.get("synthetic") is True, f"provenance not synthetic: {case_id}")
        require(provenance_data.get("personal_data") is False, f"personal data not excluded: {case_id}")
        require(provenance_data.get("external_sources_used") is False, f"external source recorded: {case_id}")
        require(provenance_data.get("reused_case_families") == [], f"prior case family reused: {case_id}")
    require(len(signatures) == 3, "case structures are not distinct")
    print(f"TASK207_STEP02_CASES_VALID: {manifest_rel}; {len(entries)} distinct synthetic cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
