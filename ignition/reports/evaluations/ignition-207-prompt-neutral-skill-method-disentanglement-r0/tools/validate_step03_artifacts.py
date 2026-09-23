#!/usr/bin/env python3
"""Validate Task207 skill/method/partial-lineage artifacts and provenance."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[5]
TASK_DIR = REPO_ROOT / "ignition/reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0"
MANIFEST_PATH = TASK_DIR / "provenance/artifact-manifest.json"
SKILL_SCHEMA_PATH = TASK_DIR / "schema/skill-procedure-r0.schema.json"
SKILL_PATH = TASK_DIR / "payload/item-a.json"
METHOD_PATH = TASK_DIR / "payload/item-b.json"
PARTIAL_PATH = TASK_DIR / "payload/item-c.json"
METHOD_VALIDATOR = REPO_ROOT / "ignition/reports/evaluations/ignition-190-method-use-trace-r0/tools/validate_method_use_trace_r0.py"
EXPECTED_ROLES = {
    "item-a": "REUSABLE_PROCEDURAL_SKILL",
    "item-b-history": "METHOD_SOURCE_HISTORY",
    "item-b": "COMPLETE_METHOD_USE_TRACE_R0",
    "item-c-source": "PARTIAL_LINEAGE_SOURCE",
    "item-c": "LINEAGE_FRAGMENT",
    "skill-procedure-r0": "TASK_LOCAL_SKILL_SCHEMA",
}
EXPECTED_PROVENANCE = {
    "item-a": ("BUILDER_AUTHORED_SYNTHETIC", "synthetic://ignition-207/skill/paired-readout-comparison-r0", None, None),
    "item-b-history": ("BUILDER_AUTHORED_SYNTHETIC", "synthetic://ignition-207/calibration/gated-local-measurement-r0", None, None),
    "item-b": (
        "BUILDER_AUTHORED_SYNTHETIC",
        "synthetic://ignition-207/calibration/gated-local-measurement-r0",
        "ignition/reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0/payload/item-b-history.md",
        None,
    ),
    "item-c-source": ("BUILDER_AUTHORED_SYNTHETIC", "synthetic://ignition-207/calibration/fragment-r7", None, None),
    "item-c": (
        "BUILDER_AUTHORED_SYNTHETIC",
        "synthetic://ignition-207/calibration/fragment-r7",
        "ignition/reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0/payload/item-c-source.md",
        None,
    ),
    "skill-procedure-r0": ("TASK_LOCAL_SCHEMA_AUTHORED_FOR_THIS_PREPARATION", "synthetic://ignition-207/schema/skill-procedure-r0", None, None),
}
FORBIDDEN_CUES = (
    "FACTS_ONLY",
    "SKILL_ONLY",
    "METHOD_ARTIFACT",
    "BROKEN_METHOD",
    "DISENTANGLE-CASE-01",
    "DISENTANGLE-CASE-02",
    "DISENTANGLE-CASE-03",
    "EXPECTED_CONDITION",
    "ANSWER_KEY",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL_TASK207_STEP03: {message}")


def repo_path(rel: str) -> Path:
    path = REPO_ROOT / rel
    require(path.is_file(), f"file missing: {rel}")
    require(path.resolve().is_relative_to(REPO_ROOT.resolve()), f"path escapes repository: {rel}")
    return path


def check_hash_and_sidecar(path: Path, expected_hash: str, sidecar_rel: str) -> None:
    require(re.fullmatch(r"[0-9a-f]{64}", expected_hash) is not None, f"invalid SHA256: {path}")
    require(sha256(path) == expected_hash, f"hash mismatch: {path.relative_to(REPO_ROOT)}")
    sidecar = repo_path(sidecar_rel)
    expected_sidecar = f"{expected_hash}  {path.relative_to(REPO_ROOT).as_posix()}\n"
    require(sidecar.read_text(encoding="utf-8") == expected_sidecar, f"sidecar mismatch: {sidecar_rel}")


def run_method_validator(path: Path, *, expect_invalid: bool) -> str:
    command = [sys.executable, str(METHOD_VALIDATOR), str(path)]
    if expect_invalid:
        command.append("--expect-invalid")
    result = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    require(result.returncode == 0, f"Method-Use Trace R0 validator failed: {result.stdout}{result.stderr}")
    return result.stdout.strip()


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    require(manifest.get("artifact_type") == "EVALUATION_EVIDENCE", "wrong manifest artifact type")
    require(manifest.get("task_id") == "IGNITION-20260923-207", "wrong manifest task id")
    require(manifest.get("step") == "Step03", "wrong manifest step")
    require(manifest.get("base_commit") == "8e70ba196739cf1a79600e02ace36f90ad2c130c", "wrong exact base")
    require(manifest.get("scope") == "TASK_LOCAL_SYNTHETIC_INPUT_ARTIFACTS_ONLY", "wrong artifact scope")

    artifacts = manifest.get("artifacts")
    require(isinstance(artifacts, list) and len(artifacts) == len(EXPECTED_ROLES), "artifact manifest is incomplete")
    seen_ids = set()
    indexed = {}
    for row in artifacts:
        opaque_id = row.get("opaque_artifact_id")
        require(opaque_id in EXPECTED_ROLES, f"unexpected artifact id: {opaque_id}")
        require(opaque_id not in seen_ids, f"duplicate artifact id: {opaque_id}")
        seen_ids.add(opaque_id)
        require(row.get("representation_role") == EXPECTED_ROLES[opaque_id], f"artifact role mismatch: {opaque_id}")
        expected_source_kind, expected_source_ref, expected_source_path, _ = EXPECTED_PROVENANCE[opaque_id]
        require(row.get("source_kind") == expected_source_kind, f"source kind mismatch: {opaque_id}")
        require(row.get("source_ref") == expected_source_ref, f"source reference mismatch: {opaque_id}")
        require(row.get("source_path") == expected_source_path, f"source path mismatch: {opaque_id}")
        path = repo_path(row.get("path", ""))
        check_hash_and_sidecar(path, row.get("sha256", ""), row.get("sha256_sidecar", ""))
        source_path = row.get("source_path")
        if source_path is None:
            require(row.get("source_sha256") is None, f"unexpected source hash without a source path: {opaque_id}")
        else:
            source = repo_path(source_path)
            source_hash = sha256(source)
            require(row.get("source_sha256") == source_hash, f"source hash mismatch: {opaque_id}")
        indexed[opaque_id] = path
    require(seen_ids == set(EXPECTED_ROLES), "artifact IDs differ from frozen plan")
    check_hash_and_sidecar(
        MANIFEST_PATH,
        sha256(MANIFEST_PATH),
        "ignition/reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0/provenance/artifact-manifest.json.sha256",
    )

    for entry in manifest.get("reused_contracts", []):
        path = repo_path(entry["path"])
        require(sha256(path) == entry["sha256"], f"reused contract hash mismatch: {entry['path']}")
    require(len(manifest.get("reused_contracts", [])) == 3, "expected Method-Use Trace R0 schema, validator, and R0.1 output schema pins")

    schema = json.loads(SKILL_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    skill = json.loads(SKILL_PATH.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(skill), key=lambda error: list(error.path))
    require(not errors, "skill artifact violates its narrow schema: " + (errors[0].message if errors else ""))
    skill_boundary = manifest.get("skill_boundary", {})
    require(skill_boundary.get("method_lineage") == "NOT_PRESENT", "skill representation includes method lineage")
    require(skill_boundary.get("case_answers_included") is False, "skill representation includes case answers")
    forbidden_skill_fields = {
        "candidate_set",
        "selection_rationale",
        "method_use_history",
        "validation_outcome",
        "revision_history",
        "case_answers",
        "condition_id",
    }
    require(not forbidden_skill_fields.intersection(skill), "skill payload contains method-lineage or answer fields")

    method = json.loads(METHOD_PATH.read_text(encoding="utf-8"))
    method_history_hash = sha256(indexed["item-b-history"])
    require(len(method.get("segments", [])) == 6, "complete method trace must contain six segments")
    require(all(segment.get("source_sha256") == method_history_hash for segment in method["segments"]), "method trace source hash mismatch")
    require(manifest.get("method_trace_lineage", {}).get("complete_trace_source_sha256") == method_history_hash, "method history manifest pin mismatch")
    require(run_method_validator(METHOD_PATH, expect_invalid=False).startswith("VALID:"), "complete Method-Use Trace R0 did not validate")

    excerpt = json.loads(PARTIAL_PATH.read_text(encoding="utf-8"))
    excerpt_kinds = [segment.get("segment_kind") for segment in excerpt.get("segments", [])]
    require(excerpt_kinds == ["METHOD_CANDIDATE", "CONTEXT", "OBSERVED_OUTCOME_OR_FAILURE"], "lineage fragment shape changed")
    require(len(excerpt.get("segments", [])) == 3, "lineage fragment must remain partial")
    forbidden_links = {"selected_candidate_ref", "used_candidate_ref", "input_ref", "use_segment_ref", "revision_type", "disposition"}
    require(not any(forbidden_links.intersection(segment) for segment in excerpt["segments"]), "lineage fragment contains a completion link")
    partial_hash = sha256(indexed["item-c-source"])
    require(all(segment.get("source_sha256") == partial_hash for segment in excerpt["segments"]), "lineage fragment source hash mismatch")
    require(manifest.get("method_trace_lineage", {}).get("excerpt_source_sha256") == partial_hash, "fragment source manifest pin mismatch")
    require(run_method_validator(PARTIAL_PATH, expect_invalid=True).startswith("EXPECTED_INVALID:"), "incomplete fragment was accepted as a complete trace")

    check_paths = [indexed[key] for key in ("item-a", "item-b-history", "item-b", "item-c-source", "item-c")]
    for path in check_paths:
        text = path.read_text(encoding="utf-8")
        upper = text.upper()
        for cue in FORBIDDEN_CUES:
            require(cue not in upper, f"condition/case answer cue {cue} in {path.relative_to(REPO_ROOT)}")
    fixed = manifest.get("status", {})
    require(fixed.get("successor") == "NOT_RUN", "Successor must remain unrun")
    require(fixed.get("evaluator") == "NOT_RUN", "Evaluator must remain unrun")
    require(fixed.get("canonical_claim_ids") == [], "canonical IDs must be empty")
    require(fixed.get("canonical_promotion") == "NONE", "canonical promotion must remain NONE")
    print("TASK207_STEP03_ARTIFACTS_VALID: skill schema valid; Method-Use Trace R0 valid; incomplete lineage rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
