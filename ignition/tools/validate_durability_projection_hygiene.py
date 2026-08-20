#!/usr/bin/env python3
"""Validate Step 17 projection hygiene and preserve historical residuals."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping

from jsonschema import Draft202012Validator

_IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_IGNITION_ROOT / "tools"))

from tools.foundation import validate_repository_path_classification as path_classification
from tools.foundation.knowledge_corpus_admission import admission_for_path
from tools.propagation.impact_contract import HISTORICAL_SEALED_SOURCES, compute_dimension
from tools import generate_current_facts as facts_generator
from tools import validate_current_state_sync as sync


ROOT = _IGNITION_ROOT
REPO_ROOT = ROOT.parent
DATA_PATH = ROOT / "data/operations/iterations/127/projection-hygiene-r1.json"
SCHEMA_PATH = ROOT / "schemas/operations/durability-projection-hygiene-r1.schema.json"

STEP16_PATHS = (
    "agent_runtime/pilots/durability_lifecycle_127.py",
    "data/operations/durability/continuity-pilot-r1.json",
    "schemas/operations/durability-continuity-pilot-r1.schema.json",
    "tools/run_durability_lifecycle_pilot.py",
    "tests/test_durability_continuity_pilot.py",
)
HUMAN_SURFACES = (
    ".github/README.md",
    "AI-START-HERE.md",
    "AI-HANDOFF.md",
    "ignition/docs/project-current-state.md",
    "ignition/docs/human/function-assets/README.md",
    "ignition/docs/human/nonfunction-assets/README.md",
)
MACHINE_MARKERS = (
    "DURABILITY_CONTINUITY_PILOT_OK",
    "run_durability_lifecycle_pilot.py",
    "durability_lifecycle_127.py",
    "continuity-pilot-r1.json",
)


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _contains_any(value: Any, markers: Iterable[str]) -> list[str]:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True) if not isinstance(value, str) else value
    return sorted({marker for marker in markers if marker in text})


def _read_rows(paths: Iterable[Path]) -> str:
    chunks: list[str] = []
    for path in paths:
        if path.is_file():
            chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def _knowledge_backflow() -> list[str]:
    paths = [
        ROOT / "data/foundation/function-assets/discovery.jsonl",
        ROOT / "data/foundation/nonfunction-claims/source-discovery.jsonl",
        ROOT / "data/governance/knowledge-experience/asset-cards.jsonl",
        ROOT / "data/governance/knowledge-experience/layered-reading.jsonl",
        ROOT / "data/governance/knowledge-experience/search-index.jsonl",
        ROOT / "data/governance/knowledge-experience/alias-index.jsonl",
        ROOT / "KNOWLEDGE/ASSET-CARDS.md",
        ROOT / "KNOWLEDGE/READING-LAYERS.md",
        ROOT / "KNOWLEDGE/WHATS-NEW.md",
    ]
    text = _read_rows(paths)
    return [path for path in STEP16_PATHS if path in text]


def _human_machine_dump() -> list[str]:
    text = _read_rows(REPO_ROOT / path if not path.startswith("ignition/") else REPO_ROOT / path for path in HUMAN_SURFACES)
    return _contains_any(text, MACHINE_MARKERS)


def _fire_seed_backflow() -> list[str]:
    census = _load(ROOT / "data/publication/fire-seeds/seed-census.json")
    return [path for path in STEP16_PATHS if path in json.dumps(census, ensure_ascii=False, sort_keys=True)]


def _historical_residuals() -> dict[str, Any]:
    mismatches: list[dict[str, Any]] = []
    for task_number in (104, 105, 106):
        spec = _load(ROOT / f"data/operations/propagation/106-impact/{task_number}-impact.json")
        for dimension, entry in sorted(spec["dimensions"].items()):
            derived = compute_dimension(dimension, str(ROOT), entry["baseline_sha256"], sealed_sources=HISTORICAL_SEALED_SOURCES)
            if derived["decision"] != entry["declared"]:
                mismatches.append({"task": task_number, "dimension": dimension, "declared": entry["declared"], "derived": derived["decision"], "changed_sources": derived["changed_sources"], "sealed_source_drift": derived["sealed_source_drift"]})
    q32i = _load(ROOT / "data/operations/propagation/121Q32I-residue.json")
    q33 = _load(ROOT / "data/operations/propagation/121Q33-residue.json")
    return {
        "status": "HISTORICAL_RESIDUAL_PRESERVED",
        "tasks": [104, 105, 106],
        "mismatch_count": len(mismatches),
        "mismatch_dimensions": sorted({item["dimension"] for item in mismatches}),
        "mismatches": mismatches,
        "q32i_closure": q32i.get("closure_complete") is True and q32i.get("residue") == [],
        "q33_closure": q33.get("closure_complete") is True and q33.get("residue") == [],
        "rewrite_historical_specs": False,
    }


def _sympy_residuals() -> list[str]:
    inventory = _load(ROOT / "data/agent-federation/executor-inventory-r1.json")
    return [str(item) for item in inventory.get("repository_audit", {}).get("residuals", []) if "T16_SYMPY_COUNTEREXAMPLE" in str(item)]


def _function_nonfunction_drift() -> dict[str, Any]:
    contract = _load(sync.CONTRACT_PATH)
    projection = facts_generator.build_projection(contract)
    function_summary = _load(ROOT / "data/foundation/function-assets/closure-summary.json")
    nonfunction_summary = _load(ROOT / "data/foundation/nonfunction-claims/closure-summary.json")
    function_match = projection["facts"]["foundation"]["function_identity_cards"] == function_summary["canonical_identity_cards"] and projection["facts"]["foundation"]["function_quarantine_or_pending"] == function_summary["explicit_quarantine_or_pending"]
    nonfunction_match = projection["facts"]["foundation"]["nonfunction_claims"] == nonfunction_summary["canonical_claims"] and projection["facts"]["foundation"]["nonfunction_quarantine_or_pending"] == nonfunction_summary["explicit_quarantine_or_pending"]
    return {
        "classification": "DERIVED_RECOMPUTED_FROM_CANONICAL_CLOSURES_NOT_TRUTH_SOURCE",
        "function_match": function_match,
        "nonfunction_match": nonfunction_match,
        "current_values": projection["facts"]["foundation"],
    }


def run_check(data: Mapping[str, Any] | None = None) -> dict[str, Any]:
    data = dict(data or _load(DATA_PATH))
    contract = _load(sync.CONTRACT_PATH)
    admissions = {path: admission_for_path(path) for path in STEP16_PATHS}
    current_facts_errors = list(facts_generator.check())
    source_paths = facts_generator.source_paths(contract)
    current_facts_order_stable = [facts_generator.relative(path) for path in source_paths] == sorted({facts_generator.relative(path) for path in source_paths})
    path_check_status = path_classification.check()
    sync_errors = sync.run_check(check_fixtures=True)
    knowledge_backflow = _knowledge_backflow()
    human_machine_dump = _human_machine_dump()
    fire_seed_backflow = _fire_seed_backflow()
    historical = _historical_residuals()
    sympy_residuals = _sympy_residuals()
    drift = _function_nonfunction_drift()
    checks = {
        "current_facts_generation_order": not current_facts_errors and current_facts_order_stable,
        "foundation_runtime_exclusion": all(not admission.auto_discovery and admission.classification in {"PLATFORM_CODE_EXCLUDED", "GENERATED_PROJECTION_EXCLUDED"} for admission in admissions.values()),
        "knowledge_experience_no_backflow": not knowledge_backflow,
        "human_surface_no_machine_dump": not human_machine_dump,
        "fire_seeds_no_artifact_discovery": not fire_seed_backflow,
        "propagation_104_106_historical_residual": historical["status"] == "HISTORICAL_RESIDUAL_PRESERVED" and historical["tasks"] == [104, 105, 106] and historical["mismatch_count"] == 9 and historical["q32i_closure"] and historical["q33_closure"],
        "sympy_environmental_residual": len(sympy_residuals) == 1 and "environmental SymPy-unavailable residual" in sympy_residuals[0],
        "function_nonfunction_derived_drift": drift["classification"] == "DERIVED_RECOMPUTED_FROM_CANONICAL_CLOSURES_NOT_TRUTH_SOURCE" and drift["function_match"] and drift["nonfunction_match"],
        "generated_feedback_loop": path_check_status == 0 and all(not admission.auto_discovery for admission in admissions.values()),
        "current_state_sync_baseline": not sync_errors,
    }
    return {
        "schema": data["schema_version"],
        "task_id": data["task_id"],
        "step": data["step"],
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "new_paths": {path: {"classification": admission.classification, "auto_discovery": admission.auto_discovery} for path, admission in admissions.items()},
        "current_facts": {"generator_errors": current_facts_errors, "source_path_count": len(source_paths), "source_paths_sorted_unique": current_facts_order_stable},
        "knowledge": {"backflow_paths": knowledge_backflow, "backflow_count": len(knowledge_backflow)},
        "human_surface": {"machine_dump_markers": human_machine_dump, "machine_dump_count": len(human_machine_dump)},
        "fire_seeds": {"artifact_backflow_paths": fire_seed_backflow, "artifact_backflow_count": len(fire_seed_backflow)},
        "historical_propagation": historical,
        "sympy": {"classification": "ENVIRONMENTAL_RESIDUAL_PRESERVED", "residuals": sympy_residuals, "count": len(sympy_residuals)},
        "function_nonfunction": drift,
        "current_state_sync_errors": sync_errors,
        "claim_ceiling": "Projection hygiene and historical residual classification only; no external truth, production readiness, Owner acceptance or epistemic upgrade.",
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--schema", type=Path, default=SCHEMA_PATH)
    args = parser.parse_args()
    data = _load(args.data)
    schema_errors = [error.message for error in Draft202012Validator(_load(args.schema)).iter_errors(data)]
    if schema_errors:
        print("FAIL")
        for error in schema_errors:
            print(f"- {error}")
        return 1
    result = run_check(data)
    expected = data["expected"]
    errors: list[str] = []
    if len(result["new_paths"]) != expected["new_path_count"]:
        errors.append("new path count mismatch")
    if result["knowledge"]["backflow_count"] != expected["knowledge_backflow_count"]:
        errors.append("Knowledge backflow detected")
    if result["human_surface"]["machine_dump_count"] != expected["human_machine_dump_count"]:
        errors.append("Human Surface machine dump detected")
    if result["fire_seeds"]["artifact_backflow_count"] != expected["fire_seed_backflow_count"]:
        errors.append("Fire Seeds artifact backflow detected")
    if result["historical_propagation"]["tasks"] != expected["historical_tasks"] or result["historical_propagation"]["mismatch_dimensions"] != expected["historical_mismatch_dimensions"]:
        errors.append("historical residual classification mismatch")
    if result["sympy"]["count"] != expected["sympy_residual_count"]:
        errors.append("SymPy residual classification mismatch")
    if result["function_nonfunction"]["classification"] != expected["function_nonfunction_drift_classification"]:
        errors.append("function/nonfunction drift classification mismatch")
    if not all(result["checks"].values()):
        errors.append("one or more hygiene gates failed")
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1
    print(
        "DURABILITY_PROJECTION_HYGIENE_OK "
        f"new_paths={len(result['new_paths'])} foundation_knowledge_backflow=0 "
        f"human_machine_dump=0 fire_seed_backflow=0 historical_residuals={result['historical_propagation']['mismatch_count']} "
        f"sympy_residuals={result['sympy']['count']} current_facts=PASS path_classification=PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
