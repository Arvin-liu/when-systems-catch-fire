#!/usr/bin/env python3
"""Build or check the R0.2 packet's separated cognitive and operational surfaces."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
PACKET = Path(__file__).resolve().parent
VISIBLE = PACKET / "successor-visible"
MANIFEST = VISIBLE / "packet-manifest.json"
MANIFEST_REL = MANIFEST.relative_to(REPO_ROOT).as_posix()

COGNITIVE_FILES = (
    "ignition/evaluation/heldout/r0.2/successor-visible/README.md",
    "ignition/evaluation/heldout/r0.2/successor-visible/bootstrap.md",
    "ignition/evaluation/heldout/r0.2/successor-visible/task-contract.md",
    "ignition/evaluation/heldout/r0.2/successor-visible/method-contract.md",
    "ignition/evaluation/heldout/r0.2/successor-visible/provider-neutral-capability-interface.json",
    "ignition/evaluation/heldout/r0.2/successor-visible/successor-output-r0.2.schema.json",
    "ignition/evaluation/heldout/r0.2/successor-visible/successor-read-ledger-r0.2.schema.json",
    "ignition/evaluation/heldout/r0.2/successor-visible/packet-manifest-r0.2.schema.json",
    "ignition/evaluation/heldout/r0.2/successor-visible/cases/coastal-meter-study-r02-01/provenance.json",
    "ignition/evaluation/heldout/r0.2/successor-visible/cases/coastal-meter-study-r02-01/raw-source.md",
    "ignition/evaluation/heldout/r0.2/successor-visible/cases/harbor-export-policy-r02-01/provenance.json",
    "ignition/evaluation/heldout/r0.2/successor-visible/cases/harbor-export-policy-r02-01/raw-contract.json",
)
CASE_SOURCE_FILES = {
    "coastal-meter-study-r02-01": "ignition/evaluation/heldout/r0.2/successor-visible/cases/coastal-meter-study-r02-01/raw-source.md",
    "harbor-export-policy-r02-01": "ignition/evaluation/heldout/r0.2/successor-visible/cases/harbor-export-policy-r02-01/raw-contract.json",
}
GUARD_STATUS_CODES = [
    "PASS_BRANCH_AUTHORIZED",
    "FAIL_TASK_BRANCH_MISMATCH",
    "FAIL_WRONG_REPOSITORY",
    "FAIL_WRONG_REMOTE",
    "FAIL_BRANCH_UNAUTHORIZED",
    "FAIL_BASE_ANCESTRY",
    "FAIL_AUTHOR_IDENTITY",
    "FAIL_PUSH_DESTINATION",
    "FAIL_FORCE_PUSH",
    "FAIL_HOOK_CONFIGURATION",
    "FAIL_UNEXPLAINED_WORKTREE",
    "FAIL_AUTHORIZATION_RECEIPT",
]
LEDGER_STATUS_CODES = [
    "PASS_READ_LEDGER_CLEAN",
    "FAIL_READ_LEDGER_CONTAMINATED",
    "FAIL_READ_LEDGER_INVALID",
]
OPERATIONAL_COMPONENTS = (
    {
        "component_id": "git-pre-commit-hook",
        "component_type": "HOOK_ENTRYPOINT",
        "path": "ignition/evaluation/hooks/pre-commit",
        "successor_access": "EXECUTE_STATUS_ONLY",
        "permitted_actions": ["EXECUTE", "OBSERVE_STATUS"],
        "allowed_status_codes": GUARD_STATUS_CODES,
    },
    {
        "component_id": "git-pre-push-hook",
        "component_type": "HOOK_ENTRYPOINT",
        "path": "ignition/evaluation/hooks/pre-push",
        "successor_access": "EXECUTE_STATUS_ONLY",
        "permitted_actions": ["EXECUTE", "OBSERVE_STATUS"],
        "allowed_status_codes": GUARD_STATUS_CODES,
    },
    {
        "component_id": "task-branch-guard",
        "component_type": "EXECUTION_TOOL",
        "path": "ignition/evaluation/tools/task_branch_guard_r0_2.py",
        "successor_access": "EXECUTE_STATUS_ONLY",
        "permitted_actions": ["EXECUTE", "OBSERVE_STATUS"],
        "allowed_status_codes": GUARD_STATUS_CODES,
    },
    {
        "component_id": "successor-read-ledger-validator",
        "component_type": "STATUS_VALIDATOR",
        "path": "ignition/evaluation/tools/validate_successor_read_ledger_r0_2.py",
        "successor_access": "EXECUTE_STATUS_ONLY",
        "permitted_actions": ["EXECUTE", "OBSERVE_STATUS"],
        "allowed_status_codes": LEDGER_STATUS_CODES,
    },
    {
        "component_id": "task-authorization-schema",
        "component_type": "GUARD_DEPENDENCY",
        "path": "ignition/evaluation/operational-control/r0.2/task-branch-authorization-r0.2.schema.json",
        "successor_access": "PROHIBITED",
        "permitted_actions": [],
        "allowed_status_codes": [],
    },
    {
        "component_id": "task182-r2-authorization-template",
        "component_type": "BUILDER_PROVISIONING_TEMPLATE",
        "path": "ignition/evaluation/operational-control/r0.2/task182-r2-branch-authorization-template.json",
        "successor_access": "PROHIBITED",
        "permitted_actions": [],
        "allowed_status_codes": [],
    },
)


def digest_file(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    return {
        "path": path.relative_to(REPO_ROOT).as_posix(),
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def payload() -> dict[str, object]:
    cognitive = [digest_file(REPO_ROOT / relative) for relative in COGNITIVE_FILES]
    operational = []
    for component in OPERATIONAL_COMPONENTS:
        row = dict(component)
        row["bytes"] = (REPO_ROOT / row["path"]).stat().st_size
        row["sha256"] = hashlib.sha256((REPO_ROOT / row["path"]).read_bytes()).hexdigest()
        operational.append(row)
    return {
        "schema_version": "heldout-successor-packet-manifest-r0.2",
        "task_id": "IGNITION-20260918-182-R2",
        "isolation_kind": "PROCEDURAL_SURFACE_SEPARATION_NOT_CRYPTOGRAPHIC_SECRECY",
        "manifest_path": MANIFEST_REL,
        "cognitive_evidence_surface": {
            "surface_id": "COGNITIVE_EVIDENCE_SURFACE",
            "read_policy": "ALLOWLISTED_CONTENT_MAY_BE_READ_AND_USED; RECORD_EVERY_READ",
            "files": sorted(cognitive, key=lambda row: str(row["path"])),
        },
        "operational_control_surface": {
            "surface_id": "OPERATIONAL_CONTROL_SURFACE",
            "read_policy": "EXECUTE_ONLY; STATUS_ONLY; SOURCE_AND_RECEIPT_CONTENT_READ_PROHIBITED",
            "components": sorted(operational, key=lambda row: str(row["component_id"])),
        },
        "evaluator_sealed_surface": {
            "path": "ignition/evaluation/heldout/r0.2/evaluator-sealed",
            "successor_access": "PROHIBITED",
            "physically_separate_from": "ignition/evaluation/heldout/r0.2/successor-visible",
            "builder_authored_answer_key": False,
            "builder_authored_evaluator_criteria": False,
        },
        "case_ids": sorted(CASE_SOURCE_FILES),
    }


def validate_packet(manifest: dict[str, object]) -> None:
    try:
        import jsonschema
    except ImportError as exc:
        raise ValueError("jsonschema is required for packet validation") from exc
    schema_path = VISIBLE / "packet-manifest-r0.2.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    errors = list(jsonschema.Draft202012Validator(schema).iter_errors(manifest))
    if errors:
        first = errors[0]
        raise ValueError(f"manifest schema at {list(first.path)}: {first.message}")

    expected = payload()
    if manifest != expected:
        raise ValueError("R0.2 packet manifest differs from the frozen surface definition")
    cognitive_rows = manifest["cognitive_evidence_surface"]["files"]
    if [row["path"] for row in cognitive_rows] != sorted(COGNITIVE_FILES):
        raise ValueError("cognitive allowlist differs from the frozen file set")
    for row in cognitive_rows:
        raw = (REPO_ROOT / row["path"]).read_bytes()
        if row["bytes"] != len(raw) or row["sha256"] != hashlib.sha256(raw).hexdigest():
            raise ValueError(f"cognitive file hash drift: {row['path']}")

    for case_id, source_path in CASE_SOURCE_FILES.items():
        provenance_path = VISIBLE / "cases" / case_id / "provenance.json"
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        raw = (REPO_ROOT / source_path).read_bytes()
        if provenance.get("case_id") != case_id:
            raise ValueError(f"case provenance identity mismatch: {case_id}")
        if provenance.get("source_identity", {}).get("source_path") != source_path:
            raise ValueError(f"case provenance path mismatch: {case_id}")
        if provenance.get("source_sha256") != hashlib.sha256(raw).hexdigest():
            raise ValueError(f"case provenance source digest mismatch: {case_id}")
        if provenance.get("source_bytes") != len(raw):
            raise ValueError(f"case provenance byte count mismatch: {case_id}")

    old_case_ids = {"content-research-01", "engineering-governance-01"}
    if old_case_ids.intersection(manifest["case_ids"]):
        raise ValueError("historical Task182 cases cannot be reused")
    if manifest["evaluator_sealed_surface"]["path"] == "ignition/evaluation/heldout/r0.2/successor-visible":
        raise ValueError("evaluator-sealed surface overlaps cognitive packet")

    expected_visible = {REPO_ROOT / path for path in COGNITIVE_FILES}
    expected_visible.update({MANIFEST, schema_path})
    actual_visible = {path for path in VISIBLE.rglob("*") if path.is_file()}
    if actual_visible != expected_visible:
        extra = sorted(path.relative_to(REPO_ROOT).as_posix() for path in actual_visible - expected_visible)
        missing = sorted(path.relative_to(REPO_ROOT).as_posix() for path in expected_visible - actual_visible)
        raise ValueError(f"successor-visible file set drift extra={extra} missing={missing}")

    sealed = REPO_ROOT / manifest["evaluator_sealed_surface"]["path"]
    if sealed.parent != VISIBLE.parent or not (sealed / "README.md").is_file():
        raise ValueError("evaluator-sealed materials must remain in a sibling path")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = payload()
    if args.check:
        actual = json.loads(MANIFEST.read_text(encoding="utf-8"))
        validate_packet(actual)
        if actual != expected:
            raise SystemExit("HELDOUT_R0_2_MANIFEST_DRIFT")
    else:
        MANIFEST.write_text(json.dumps(expected, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        validate_packet(expected)
    digest = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    print(f"HELDOUT_R0_2_PACKET_VALID cognitive_files={len(COGNITIVE_FILES)} operational_components={len(OPERATIONAL_COMPONENTS)} sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
