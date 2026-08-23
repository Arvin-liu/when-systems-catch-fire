#!/usr/bin/env python3
"""Audit Task123-135 historical compatibility without rewriting history."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from tools import iteration_boundary
    from tools import task_identity
    from tools import validate_current_state_sync
except ImportError:  # direct script / tools-on-PYTHONPATH execution
    import iteration_boundary
    import task_identity
    import validate_current_state_sync


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
BASELINE_SHA = "3acf15ea4c1b1c27eb6e8b9cadbc4f0526bdfddb"
REPORT_PATH = ROOT / "data/operations/iterations/136/step16-historical-compatibility-r1.json"
HISTORICAL_RECEIPTS = {
    123: ROOT / "data/operations/iterations/123/current-state-sync-receipt.json",
    124: ROOT / "data/operations/iterations/124/current-state-sync-receipt.json",
    126: ROOT / "data/operations/iterations/126/current-state-sync-receipt.json",
    127: ROOT / "data/operations/iterations/127/current-state-sync-receipt.json",
    128: ROOT / "data/operations/iterations/128/current-state-sync-receipt.json",
    129: ROOT / "data/operations/iterations/129/current-state-sync-receipt.json",
    130: ROOT / "data/operations/iterations/130/current-state-sync-receipt.json",
    133: ROOT / "data/operations/iterations/133/current-state-sync-receipt.json",
    134: ROOT / "data/operations/iterations/134/current-state-sync-receipt.json",
    135: ROOT / "data/operations/iterations/135/current-state-sync-receipt.json",
}

CONSUMER_AUDIT = [
    {"path": "ignition/data/operations/iteration-boundary-semantics-r1.json", "classification": "CURRENT_SEMANTIC_SOURCE", "rule": "named formal/architecture roles and deprecated alias policy"},
    {"path": "ignition/tools/iteration_boundary.py", "classification": "CURRENT_DERIVATION", "rule": "parse canonical task IDs; never read an independent numeric source"},
    {"path": "ignition/data/architecture/current-system-identity.json", "classification": "CURRENT_PROJECTION", "rule": "materialized named ordinals and alias validated against derivation"},
    {"path": "ignition/data/operations/current-release-lifecycle-r1.json", "classification": "CURRENT_PROJECTION", "rule": "formal/lifecycle/architecture fields and alias validated against derivation"},
    {"path": "ignition/data/architecture/current-facts.json", "classification": "CURRENT_GENERATED_PROJECTION", "rule": "top-level and facts.iteration values generated from canonical sources"},
    {"path": "ignition/data/operations/current-snapshot-r1.json", "classification": "CURRENT_GENERATED_PROJECTION", "rule": "iteration_identity is generated and compiler-owned"},
    {"path": "ignition/data/operations/current-volatile-fact-registry-r1.json", "classification": "CURRENT_REGISTRY", "rule": "formal/architecture ordinals derive through task_identity_ordinal extractor"},
    {"path": "ignition/tools/current_surface_compiler.py", "classification": "CURRENT_CONSUMER", "rule": "human/AI/machine blocks render generated named ordinal values"},
    {"path": "ignition/tools/validate_iteration_ordinal_binding.py", "classification": "CURRENT_RELEASE_GATE", "rule": "all formal roles share one derived formal ordinal; architecture ordinal remains independent"},
    {"path": "ignition/data/operations/iterations/{123,124,126,127,128,129,130,133}/current-state-sync-receipt.json", "classification": "HISTORICAL_RECORD", "rule": "captured values preserved and never loaded as Current source"}
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unchanged_from_baseline(path: Path) -> bool:
    completed = subprocess.run(
        ["git", "diff", "--quiet", BASELINE_SHA, "HEAD", "--", path.relative_to(REPO_ROOT).as_posix()],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )
    return completed.returncode == 0


def _current_projection_audit() -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    expected = iteration_boundary.derive()
    identity = load_json(ROOT / "data/architecture/current-system-identity.json")
    lifecycle = load_json(ROOT / "data/operations/current-release-lifecycle-r1.json")
    facts = load_json(ROOT / "data/architecture/current-facts.json")
    snapshot = load_json(ROOT / "data/operations/current-snapshot-r1.json")
    receipt = load_json(ROOT / "data/operations/iterations/136/current-state-sync-receipt.json")
    identity_projection = {
        "current_formal_task_id": identity.get("current_formal_task_id"),
        "current_formal_task_ordinal": identity.get("current_formal_task_ordinal"),
        "latest_architecture_changing_task_id": identity.get("latest_architecture_changing_task_id"),
        "latest_architecture_task_ordinal": identity.get("latest_architecture_task_ordinal"),
        "current_iteration_boundary": identity.get("current_iteration_boundary"),
    }
    lifecycle_projection = {
        "current_formal_task_id": lifecycle.get("current_formal_task_id"),
        "current_formal_task_ordinal": lifecycle.get("current_formal_task_ordinal"),
        "latest_architecture_changing_task_id": lifecycle.get("latest_architecture_changing_task"),
        "latest_architecture_task_ordinal": lifecycle.get("latest_architecture_task_ordinal"),
        "current_iteration_boundary": lifecycle.get("current_iteration_boundary"),
    }
    facts_projection = {key: facts.get(key) for key in expected if key != "current_method_version" and key != "current_iteration_boundary_semantics"}
    snapshot_projection = snapshot.get("iteration_identity", {})
    receipt_projection = {key: receipt.get(key) for key in expected if key != "current_method_version"}
    for label, projection in (
        ("current-system-identity", identity_projection),
        ("current-release-lifecycle", lifecycle_projection),
        ("current-facts", facts_projection),
        ("current-snapshot", snapshot_projection),
        ("current-state-sync-receipt", receipt_projection),
    ):
        for key, value in expected.items():
            if key in {"current_method_version", "current_iteration_boundary_semantics"}:
                continue
            if projection.get(key) != value:
                errors.append(f"CURRENT_PROJECTION_MISMATCH:{label}:{key}:expected={value}:observed={projection.get(key)}")
    if identity.get("current_iteration_boundary_semantics", {}).get("status") != "DEPRECATED_COMPATIBILITY_ALIAS":
        errors.append("CURRENT_PROJECTION_MISMATCH:current-system-identity:alias status")
    if lifecycle.get("current_iteration_boundary_semantics") != expected["current_iteration_boundary_semantics"]:
        errors.append("CURRENT_PROJECTION_MISMATCH:current-release-lifecycle:alias semantics")
    if facts.get("current_iteration_boundary_semantics") != expected["current_iteration_boundary_semantics"] or facts.get("facts", {}).get("iteration", {}).get("current_iteration_boundary_semantics") != expected["current_iteration_boundary_semantics"]:
        errors.append("CURRENT_PROJECTION_MISMATCH:current-facts:alias semantics")
    if snapshot_projection.get("current_iteration_boundary_semantics") != expected["current_iteration_boundary_semantics"]:
        errors.append("CURRENT_PROJECTION_MISMATCH:current-snapshot:alias semantics")
    if receipt.get("current_iteration_boundary_semantics") != expected["current_iteration_boundary_semantics"]:
        errors.append("CURRENT_PROJECTION_MISMATCH:current-state-sync-receipt:alias semantics")
    errors.extend(f"CURRENT_RECEIPT_VALIDATION:{error}" for error in validate_current_state_sync.validate_receipt(validate_current_state_sync.load_json(validate_current_state_sync.CONTRACT_PATH), receipt))
    return errors, {
        "formal_task_id": expected["current_formal_task_id"],
        "formal_task_ordinal": expected["current_formal_task_ordinal"],
        "architecture_task_id": expected["latest_architecture_changing_task_id"],
        "architecture_task_ordinal": expected["latest_architecture_task_ordinal"],
        "current_iteration_boundary": expected["current_iteration_boundary"],
        "current_iteration_boundary_semantics": expected["current_iteration_boundary_semantics"],
    }


def _historical_audit() -> tuple[list[str], list[dict[str, Any]]]:
    errors: list[str] = []
    rows: list[dict[str, Any]] = []
    contract = validate_current_state_sync.load_json(validate_current_state_sync.CONTRACT_PATH)
    for ordinal, path in HISTORICAL_RECEIPTS.items():
        record = load_json(path)
        task_id = record.get("task_id")
        try:
            parsed = task_identity.parse_task_id(task_id)
        except task_identity.TaskIdentityError as exc:
            errors.append(f"HISTORICAL_TASK_ID_INVALID:{path.name}:{exc}")
            continue
        row_errors = validate_current_state_sync.validate_receipt(contract, record)
        expected_path_ordinal = int(path.parent.name)
        if parsed["ordinal"] != expected_path_ordinal:
            row_errors.append(f"path ordinal {expected_path_ordinal} differs from task ordinal {parsed['ordinal']}")
        if not isinstance(record.get("current_iteration_boundary"), int):
            row_errors.append("historical captured boundary is not an integer")
        for field in ("current_formal_task_ordinal", "latest_architecture_task_ordinal", "current_iteration_boundary_semantics"):
            if expected_path_ordinal < 133 and record.get(field) is not None:
                row_errors.append(f"historical artifact was rewritten with Current semantic field: {field}")
        if not unchanged_from_baseline(path):
            row_errors.append("historical artifact differs from formal baseline")
        if row_errors:
            errors.extend(f"{task_id}:{error}" for error in row_errors)
        rows.append({
            "path": path.relative_to(REPO_ROOT).as_posix(),
            "task_id": task_id,
            "task_ordinal_from_id": parsed["ordinal"],
            "captured_current_iteration_boundary": record.get("current_iteration_boundary"),
            "historical": True,
            "current_semantic_fields_present": any(record.get(field) is not None for field in ("current_formal_task_ordinal", "latest_architecture_task_ordinal", "current_iteration_boundary_semantics")),
            "unchanged_from_baseline": unchanged_from_baseline(path),
            "sha256": sha256(path),
            "validation": "PASS" if not row_errors else "FAIL",
        })
    return errors, rows


def build_report() -> dict[str, Any]:
    current_errors, current = _current_projection_audit()
    historical_errors, historical = _historical_audit()
    errors = current_errors + historical_errors
    return {
        "schema_version": "ignition-136-step16-historical-compatibility-r1",
        "task_id": "IGNITION-20260823-136",
        "step": "16",
        "status": "PASS" if not errors else "FAIL",
        "compatibility_contract": {
            "deprecated_field": "current_iteration_boundary",
            "alias_of": "current_formal_task_ordinal",
            "current_source": "ignition/data/operations/iteration-boundary-semantics-r1.json",
            "historical_policy": "Task123-135 captured values remain historical records and are not rewritten or reinterpreted as Current source.",
            "new_consumers": "Must use current_formal_task_ordinal or latest_architecture_task_ordinal by name.",
        },
        "current_projection": current,
        "historical_receipts": historical,
        "consumer_audit": CONSUMER_AUDIT,
        "errors": errors,
        "claim_ceiling": "Repository-local historical compatibility and migration evidence only; no external truth, production readiness, Owner acceptance or epistemic acceptance is inferred.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    report = build_report()
    if args.write:
        REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"ITERATION_BOUNDARY_COMPATIBILITY_WRITTEN path={REPORT_PATH.relative_to(REPO_ROOT)} status={report['status']} historical={len(report['historical_receipts'])}")
        return 0 if report["status"] == "PASS" else 1
    if report["status"] != "PASS":
        print("ITERATION_BOUNDARY_COMPATIBILITY_INVALID", file=sys.stderr)
        for error in report["errors"]:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"ITERATION_BOUNDARY_COMPATIBILITY_OK historical={len(report['historical_receipts'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
