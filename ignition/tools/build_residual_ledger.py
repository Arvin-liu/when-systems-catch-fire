#!/usr/bin/env python3
"""Build the deterministic Task134 residual ledger from validator outputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "tools"))

from foundation import validate_repository_path_classification as path_classification  # noqa: E402
from tools import validate_residual_ledger  # noqa: E402

LEDGER_PATH = ROOT / "data/operations/residual-ledger-r1.json"
MATERIALITY_PATH = ROOT / "data/governance/human-surface/materiality-manifest.json"
FULL_DISCOVERY_PATH = ROOT / "data/operations/iterations/134/step10-full-unittest-discovery.json"


def source_sha(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def human_drift_objects() -> list[str]:
    manifest = json.loads(MATERIALITY_PATH.read_text(encoding="utf-8"))
    out: list[str] = []
    for entry in manifest.get("entries", []):
        source = ROOT / entry.get("source_path", "")
        observed = source_sha(source)
        recorded = entry.get("source_sha256")
        if observed and recorded != observed:
            out.append(f"{entry['machine_id']}@{observed}")
    return sorted(out)


def propagation_objects() -> list[str]:
    objects: list[str] = []
    for task_number in (104, 105, 106):
        path = ROOT / f"data/operations/propagation/106-impact/{task_number}-impact.json"
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for dimension in sorted(data.get("dimensions", {})):
            objects.append(f"{task_number}:{dimension}")
    return objects


def sympy_objects() -> list[str]:
    path = ROOT / "data/agent-federation/executor-inventory-r1.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return ["T16_SYMPY_COUNTEREXAMPLE"] if any("T16_SYMPY_COUNTEREXAMPLE" in str(item) for item in data.get("repository_audit", {}).get("residuals", [])) else []


def full_discovery_observation() -> tuple[list[str], list[str], str, str]:
    command = "PYTHONPATH=ignition python3 -m unittest discover -s ignition/tests -p 'test*.py'"
    if not FULL_DISCOVERY_PATH.is_file():
        return ["FULL_DISCOVERY:TIMEOUT_CLASSIFIED_AT_30_SECONDS"], ["FULL_DISCOVERY_TIMEOUT"], "OPEN_INHERITED", command
    record = json.loads(FULL_DISCOVERY_PATH.read_text(encoding="utf-8"))
    status = record.get("status", "BLOCKED")
    if status == "PASS":
        return [], [], "RESOLVED_CURRENT", command
    blocker = record.get("blocker") or record.get("status") or "FULL_DISCOVERY_BLOCKED"
    return [f"FULL_DISCOVERY:{blocker}"], ["FULL_DISCOVERY_BLOCKER"], "OPEN_INHERITED", command


def make_entry(*, residual_id: str, origin_task: str, classification: str, objects: list[str], dimensions: list[str], command: str, validator: str, provenance: list[str], allowed: str, impact: str, status: str | None = None, baseline_objects: list[str] | None = None, baseline_dimensions: list[str] | None = None, baseline_command: str | None = None) -> dict[str, Any]:
    baseline_objects = sorted(set(objects if baseline_objects is None else baseline_objects))
    baseline_dimensions = sorted(set(dimensions if baseline_dimensions is None else baseline_dimensions))
    current_objects = sorted(set(objects))
    current_dimensions = sorted(set(dimensions))
    if status is None:
        status = "RESOLVED_CURRENT" if not current_objects and not current_dimensions else "OPEN_INHERITED"
    return {
        "residual_id": residual_id,
        "origin_task": origin_task,
        "classification": classification,
        "status": status,
        "baseline_fingerprint": validate_residual_ledger.fingerprint(count=len(baseline_objects), objects=baseline_objects, failure_dimensions=baseline_dimensions),
        "current_fingerprint": validate_residual_ledger.fingerprint(count=len(current_objects), objects=current_objects, failure_dimensions=current_dimensions),
        "baseline_count": len(baseline_objects),
        "current_count": len(current_objects),
        "baseline_objects": baseline_objects,
        "current_objects": current_objects,
        "baseline_failure_dimensions": baseline_dimensions,
        "current_failure_dimensions": current_dimensions,
        "baseline_source_command": baseline_command or command,
        "current_source_command": command,
        "validator": validator,
        "provenance_paths": sorted(set(provenance)),
        "allowed_persistence_rule": allowed,
        "release_impact": impact,
    }


def build() -> dict[str, Any]:
    live = path_classification.live_classification()
    manifest = path_classification.read_manifest()
    missing = sorted(set(live) - set(manifest))
    human = human_drift_objects()
    full_objects, full_dimensions, full_status, full_command = full_discovery_observation()
    entries = [
        make_entry(
            residual_id="CURRENT_PATH_MANIFEST_UNACCOUNTED",
            origin_task="IGNITION-20260820-127",
            classification="CURRENT_PROJECTION_RESIDUAL",
            objects=missing,
            dimensions=["MANIFEST_MISSING_PATH"] if missing else [],
            command="PYTHONPATH=ignition python3 ignition/tools/foundation/validate_repository_path_classification.py --check",
            validator="ignition/tools/foundation/validate_repository_path_classification.py",
            provenance=["ignition/data/foundation/repository-path-classification/classification-manifest.jsonl", "ignition/agent-results/IGNITION-20260822-133-result.md"],
            allowed="Current manifest must be regenerated; only an unchanged sealed historical observation may remain in historical receipts.",
            impact="NON_BLOCKING_RESOLVED" if not missing else "RELEASE_BLOCKING",
            status="RESOLVED_CURRENT" if not missing else "OPEN_INHERITED",
            baseline_objects=missing if missing else None,
            baseline_dimensions=["MANIFEST_MISSING_PATH"] if missing else [],
        ),
        make_entry(
            residual_id="HUMAN_SURFACE_SOURCE_HASH_DRIFT",
            origin_task="IGNITION-20260821-129",
            classification="CURRENT_HUMAN_SURFACE_PROJECTION_RESIDUAL",
            objects=human,
            dimensions=["SOURCE_HASH_DRIFT"] if human else [],
            command="PYTHONPATH=ignition python3 ignition/tools/validate_human_front_door.py",
            validator="ignition/tools/governance/validate_human_surface_contract.py",
            provenance=["ignition/data/governance/human-surface/materiality-manifest.json", "ignition/agent-results/IGNITION-20260822-133-result.md"],
            allowed="A source revision requires a semantic decision before fingerprint refresh; Current drift must be zero.",
            impact="NON_BLOCKING_RESOLVED" if not human else "RELEASE_BLOCKING",
            status="RESOLVED_CURRENT" if not human else "OPEN_INHERITED",
            baseline_objects=human if human else None,
            baseline_dimensions=["SOURCE_HASH_DRIFT"] if human else [],
        ),
        make_entry(
            residual_id="PROPAGATION_TASK104_106_MISMATCH",
            origin_task="IGNITION-20260713-104-106",
            classification="SEALED_HISTORICAL",
            objects=propagation_objects(),
            dimensions=["MACHINE_RECORD_IMPACT", "PROJECT_STATE_IMPACT", "SYSTEM_MAP_IMPACT"],
            command="PYTHONPATH=ignition python3 ignition/tools/propagation/validate_reconciliation.py --check",
            validator="ignition/tools/propagation/validate_reconciliation.py",
            provenance=["ignition/data/operations/propagation/106-impact/104-impact.json", "ignition/data/operations/propagation/106-impact/105-impact.json", "ignition/data/operations/propagation/106-impact/106-impact.json"],
            allowed="Historical sealed fingerprints may persist unchanged; any added object or dimension is a new regression.",
            impact="HISTORICAL_ONLY",
            status="SEALED_HISTORICAL",
        ),
        make_entry(
            residual_id="T16_SYMPY_COUNTEREXAMPLE",
            origin_task="IGNITION-20260816-121",
            classification="ENVIRONMENTAL",
            objects=sympy_objects(),
            dimensions=["SYMPY_UNAVAILABLE"] if sympy_objects() else [],
            command="PYTHONPATH=ignition python3 ignition/tools/foundation/verify_core_claims.py --check",
            validator="ignition/tools/foundation/verify_core_claims.py",
            provenance=["ignition/data/agent-federation/executor-inventory-r1.json", "ignition/agent-results/IGNITION-20260822-133-result.md"],
            allowed="Declared dependency availability is independent of proof status; unavailable SymPy is environmental, never PASS.",
            impact="ENVIRONMENTAL_ONLY",
            status="ENVIRONMENTAL",
        ),
        make_entry(
            residual_id="FULL_UNITTEST_DISCOVERY_TERMINAL_STATE",
            origin_task="IGNITION-20260822-133",
            classification="FULL_DISCOVERY_EXECUTION_STATE",
            objects=full_objects,
            dimensions=full_dimensions,
            command=full_command,
            validator="python3 -m unittest discover",
            provenance=["ignition/data/operations/iterations/134/step10-full-unittest-discovery.json", "ignition/agent-results/IGNITION-20260822-133-result.md"],
            allowed="Only the actual long-window terminal result or a located blocker may be recorded; arbitrary short timeout is not a release result.",
            impact="NON_BLOCKING_IF_UNCHANGED" if full_objects else "NON_BLOCKING_RESOLVED",
            status=full_status,
            baseline_objects=["FULL_DISCOVERY:TIMEOUT_CLASSIFIED_AT_30_SECONDS"],
            baseline_dimensions=["FULL_DISCOVERY_TIMEOUT"],
        ),
    ]
    return {
        "schema_version": "residual-ledger-r1",
        "task_id": "IGNITION-20260822-134",
        "baseline_ref": {"repository": "Arvin-liu/when-systems-catch-fire", "ref": "refs/heads/main", "sha": "517510aed545ff440c3464536ba2964c94e5f560"},
        "residuals": entries,
        "claim_ceiling": "Current residual identity, delta and projection hygiene evidence only; no external truth, production readiness, Owner acceptance or epistemic acceptance is inferred.",
    }


def main() -> int:
    document = build()
    LEDGER_PATH.write_text(json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"RESIDUAL_LEDGER_WRITTEN path={LEDGER_PATH.relative_to(REPO_ROOT)} entries={len(document['residuals'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
