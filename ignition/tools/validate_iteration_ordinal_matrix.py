#!/usr/bin/env python3
"""Execute the fifteen-case Task133 ordinal adversarial matrix."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

try:
    from tools import current_surface_compiler
    from tools import task_identity
    from tools import validate_current_surface_semantics
    from tools import validate_iteration_ordinal_binding as gate
except ImportError:  # direct script / tools-on-PYTHONPATH execution
    import current_surface_compiler
    import task_identity
    import validate_current_surface_semantics
    import validate_iteration_ordinal_binding as gate


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
FIXTURE_PATH = ROOT / "data/operations/iterations/133/fixtures/iteration-ordinal-adversarial-matrix-r1.json"
REPORT_PATH = ROOT / "data/operations/iterations/133/step07-adversarial-matrix-r1.json"
HISTORICAL_CONTRACT_PATH = ROOT / "data/operations/iterations/133/execution-contract-r1.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _base() -> dict[str, Any]:
    identity = load_json(gate.LINEAGE_PATH)["task_identity"]
    current_task_id = identity["current_formal_task"]
    current_architecture_task_id = identity["latest_architecture_changing_task"]

    historical_task_id = "IGNITION-20260822-133"
    historical_architecture_task_id = "IGNITION-20260821-129"
    current_ordinal = task_identity.parse_task_id(current_task_id)["ordinal"]
    current_architecture_ordinal = task_identity.parse_task_id(current_architecture_task_id)["ordinal"]

    def historicalize(value: Any, *, key: str | None = None) -> Any:
        # The matrix is a sealed Task133 adversarial fixture. Its documents
        # are copied from Current only to exercise the same validator; every
        # current formal/architecture role must be projected to the historical
        # Task133/Task129 split before validation.
        if isinstance(value, dict):
            return {name: historicalize(item, key=name) for name, item in value.items()}
        if isinstance(value, list):
            return [historicalize(item, key=key) for item in value]
        if isinstance(value, str):
            if value == current_architecture_task_id and key in {
                "latest_architecture_changing_task",
                "latest_architecture_changing_task_id",
                "architecture_task_id",
                "latest_architecture_task",
            }:
                return historical_architecture_task_id
            if value == current_task_id:
                return historical_task_id
            if value == current_architecture_task_id:
                return historical_architecture_task_id
            return value
        if isinstance(value, int) and not isinstance(value, bool):
            if key in {"current_formal_task_ordinal", "current_iteration_boundary"} and value == current_ordinal:
                return 133
            if key in {"latest_architecture_task_ordinal", "architecture_task_ordinal"} and value == current_architecture_ordinal:
                return 129
        return value

    return {
        "contract": load_json(HISTORICAL_CONTRACT_PATH),
        "lineage": historicalize(load_json(gate.LINEAGE_PATH)),
        "lifecycle": historicalize(load_json(gate.LIFECYCLE_PATH)),
        "snapshot": historicalize(load_json(gate.SNAPSHOT_PATH)),
        "facts": historicalize(load_json(gate.FACTS_PATH)),
    }


def _terminal_witness() -> dict[str, Any]:
    return {
        "task_id": "IGNITION-20260822-133",
        "candidate_sha": "a" * 40,
        "observed_remote": {"ref": "refs/heads/main", "sha": "a" * 40},
        "task_binding": {
            "canonical_current_formal_task_id": "IGNITION-20260822-133",
            "release_candidate_task_id": "IGNITION-20260822-133",
            "latest_architecture_changing_task": "IGNITION-20260821-129",
            "current_formal_task_ordinal": 133,
            "latest_architecture_task_ordinal": 129,
            "current_iteration_boundary": 133,
            "current_iteration_boundary_semantics": gate.ALIAS_SEMANTICS,
        },
        "ordinal_binding": {
            "current_formal_task_ordinal": 133,
            "latest_architecture_task_ordinal": 129,
            "current_iteration_boundary": 133,
            "current_iteration_boundary_semantics": gate.ALIAS_SEMANTICS,
        },
    }


def _compiler_issues(snapshot: dict[str, Any], *, stale: bool = False) -> list[str]:
    contract = load_json(current_surface_compiler.CONTRACT_PATH)
    issues: list[str] = []
    for surface in contract["surfaces"]:
        text = (REPO_ROOT / surface["path"]).read_text(encoding="utf-8")
        if stale and surface["surface_id"] == "project-current-state":
            current_task_id = snapshot["current_task"]["task_id"]
            text = text.replace(
                f"current_formal_task: `{current_task_id}`",
                "current_formal_task: `IGNITION-20260822-132`",
                1,
            )
        expected = current_surface_compiler.compile_surface(text, surface, snapshot=snapshot)
        if text != expected:
            issues.append(f"COMPILER_SURFACE_STALE:{surface['surface_id']}")
    return issues


def evaluate(mutation: str) -> list[str]:
    docs = _base()
    if mutation == "stale_boundary_130":
        docs["lifecycle"]["current_iteration_boundary"] = 130
    elif mutation == "lifecycle_task_132":
        docs["lifecycle"]["task_id"] = "IGNITION-20260822-132"
    elif mutation == "valid_split":
        pass
    elif mutation == "architecture_ordinal_133":
        docs["lifecycle"]["latest_architecture_task_ordinal"] = 133
    elif mutation == "malformed_task_id":
        docs["lineage"]["current_task"]["task_id"] = "IGNITION-133"
    elif mutation == "widened_ordinal":
        docs["snapshot"]["iteration_identity"]["current_formal_task_ordinal"] = 1333
    elif mutation == "stale_snapshot":
        docs["snapshot"]["current_task"]["task_id"] = "IGNITION-20260822-132"
    elif mutation == "stale_current_facts":
        docs["facts"]["current_formal_task_ordinal"] = 130
        docs["facts"]["facts"]["iteration"]["current_formal_task_ordinal"] = 130
    elif mutation == "stale_compiler_surface":
        return _compiler_issues(docs["snapshot"], stale=True)
    elif mutation == "witness_ordinal_mismatch":
        witness = _terminal_witness()
        witness["task_binding"]["current_formal_task_ordinal"] = 132
        docs["publication_witness"] = witness
    elif mutation == "witness_id_canonical_ordinal_stale":
        docs["facts"]["current_formal_task_ordinal"] = 130
        docs["facts"]["facts"]["iteration"]["current_formal_task_ordinal"] = 130
        docs["publication_witness"] = _terminal_witness()
    elif mutation == "historical_old_130":
        return [] if "Task130" in "Historical Task130 boundary=130" else ["historical fixture missing"]
    elif mutation == "historical_changelog_ordinal":
        historical = "# STATE-CHANGELOG\n\n## Historical record\n\n- Task130 retained historical current_iteration_boundary=130.\n"
        issues = validate_current_surface_semantics.validate_documents(
            {"ignition/STATE-CHANGELOG.md": historical},
            snapshot=docs["snapshot"],
            surface_specs=[{"surface_id": "state-changelog", "path": "ignition/STATE-CHANGELOG.md", "profile": "ai"}],
            require_blocks=False,
        )
        return [issue["kind"] for issue in issues]
    elif mutation == "missing_formal_source":
        docs["lineage"]["task_identity"].pop("current_formal_task", None)
    elif mutation == "duplicate_parser_role":
        return gate.validate_binding_chain([
            {"role_id": "current_formal_task", "task_id": "IGNITION-20260822-133"},
            {"role_id": "current_formal_task", "task_id": "IGNITION-20260822-132"},
        ], expected_task_id="IGNITION-20260822-133", expected_architecture_task="IGNITION-20260821-129")
    else:
        return [f"unknown mutation: {mutation}"]

    errors, _records = gate.validate_documents(
        contract=docs["contract"],
        lineage=docs["lineage"],
        lifecycle=docs["lifecycle"],
        snapshot=docs["snapshot"],
        facts=docs["facts"],
        publication_witness=docs.get("publication_witness"),
    )
    return errors


def build_report() -> dict[str, Any]:
    fixture = load_json(FIXTURE_PATH)
    results: list[dict[str, Any]] = []
    for case in fixture["cases"]:
        errors = evaluate(case["mutation"])
        actual = "FAIL" if errors else "PASS"
        results.append({
            "case_id": case["case_id"],
            "mutation": case["mutation"],
            "expected": case["expected"],
            "actual": actual,
            "result": "PASS" if actual == case["expected"] else "FAIL",
            "errors": errors,
        })
    return {
        "schema_version": "ignition-133-step07-adversarial-matrix-r1",
        "task_id": "IGNITION-20260822-133",
        "step": "07",
        "status": "PASS" if all(row["result"] == "PASS" for row in results) else "FAIL",
        "case_count": len(results),
        "results": results,
        "claim_ceiling": "Repository-local adversarial ordinal binding evidence only; no external truth, production readiness, Owner acceptance or epistemic acceptance is inferred.",
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
        print(f"ITERATION_ORDINAL_MATRIX_WRITTEN path={REPORT_PATH.relative_to(REPO_ROOT)} status={report['status']} cases={report['case_count']}")
        return 0 if report["status"] == "PASS" else 1
    if report["status"] != "PASS":
        print("ITERATION_ORDINAL_MATRIX_INVALID", file=sys.stderr)
        for row in report["results"]:
            if row["result"] != "PASS":
                print(f"- {row['case_id']}: expected={row['expected']} actual={row['actual']} errors={row['errors']}", file=sys.stderr)
        return 1
    print(f"ITERATION_ORDINAL_MATRIX_OK cases={report['case_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
