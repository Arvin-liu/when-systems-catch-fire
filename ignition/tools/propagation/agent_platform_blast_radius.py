#!/usr/bin/env python3
"""Generate and verify the Agent Platform R2 blast-radius fixtures.

The generator is deliberately small and provider-neutral. It classifies
repository-relative source paths against the explicit R2 source contract,
derives the declared projection set, and refuses unmapped or ambiguous paths.
It does not run a Pack, invoke a validator, access a network, or grant any
authority to the generated report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - repository validation installs jsonschema
    Draft202012Validator = None

try:
    from impact_contract import derive_blast_radius, load_blast_radius_contract
except ModuleNotFoundError:  # package import from repository-root tests
    from tools.propagation.impact_contract import derive_blast_radius, load_blast_radius_contract


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "data/operations/propagation/agent-platform-r2-propagation-contract.json"
CONTRACT_SCHEMA_PATH = ROOT / "schemas/operations/agent-platform-r2-propagation-contract.schema.json"
REPORT_PATH = ROOT / "data/operations/propagation/121-agent-platform-r2-blast-radius-report.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical(document: dict) -> bytes:
    return (json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def validate_contract(contract: dict) -> list[str]:
    problems: list[str] = []
    if Draft202012Validator is None:
        problems.append("jsonschema is required for the R2 propagation contract")
    else:
        schema = _load(CONTRACT_SCHEMA_PATH)
        errors = sorted(Draft202012Validator(schema).iter_errors(contract), key=lambda item: list(item.path))
        problems.extend(f"schema: {error.message}" for error in errors)

    projection_classes = set(contract.get("projection_classes", []))
    domains = contract.get("source_domains", {})
    seen_paths: dict[str, str] = {}
    for domain_id, domain in sorted(domains.items()):
        affected = set(domain.get("affected_projections", []))
        forbidden = set(domain.get("forbidden_projections", []))
        if affected & forbidden:
            problems.append(f"{domain_id}: projection is both affected and forbidden: {sorted(affected & forbidden)}")
        missing = (affected | forbidden) - projection_classes
        if missing:
            problems.append(f"{domain_id}: projections not declared in projection_classes: {sorted(missing)}")
        for path in domain.get("source_paths", []):
            prior = seen_paths.get(path)
            if prior:
                problems.append(f"source path {path} is declared by both {prior} and {domain_id}")
            seen_paths[path] = domain_id

    for fixture_id, fixture in sorted(contract.get("fixtures", {}).items()):
        result = derive_blast_radius(fixture.get("changed_paths", []), contract)
        actual_domains = sorted(result["source_domains"])
        expected_domains = sorted(fixture.get("expected_source_domains", []))
        if result["unmapped_paths"]:
            problems.append(f"{fixture_id}: unmapped paths: {result['unmapped_paths']}")
        if result["ambiguous_paths"]:
            problems.append(f"{fixture_id}: ambiguous paths: {result['ambiguous_paths']}")
        if actual_domains != expected_domains:
            problems.append(f"{fixture_id}: source domains {actual_domains} != expected {expected_domains}")
        actual_projection_set = set(result["affected_projections"])
        expected_projection_set = set(fixture.get("expected_affected_projections", []))
        if actual_projection_set != expected_projection_set:
            problems.append(
                f"{fixture_id}: affected projections {sorted(actual_projection_set)} != "
                f"expected {sorted(expected_projection_set)}"
            )
        forbidden = set(fixture.get("forbidden_affected_projections", []))
        if actual_projection_set & forbidden:
            problems.append(f"{fixture_id}: forbidden projections reached: {sorted(actual_projection_set & forbidden)}")
    return problems


def build_report(contract: dict) -> dict:
    problems = validate_contract(contract)
    if problems:
        raise ValueError("; ".join(problems))
    fixtures: dict[str, dict] = {}
    for fixture_id, fixture in sorted(contract["fixtures"].items()):
        result = derive_blast_radius(fixture["changed_paths"], contract)
        fixtures[fixture_id] = {
            "changed_paths": result["changed_paths"],
            "source_domains": sorted(result["source_domains"]),
            "affected_projections": result["affected_projections"],
            "forbidden_reached": [],
            "status": "PASS",
        }
    source_authorities = {
        CONTRACT_PATH.relative_to(ROOT).as_posix(): _sha256(CONTRACT_PATH),
        "data/operations/change-propagation-topology.json": _sha256(ROOT / "data/operations/change-propagation-topology.json"),
        "data/operations/project-components.json": _sha256(ROOT / "data/operations/project-components.json"),
        "tools/propagation/impact_contract.py": _sha256(ROOT / "tools/propagation/impact_contract.py"),
    }
    return {
        "generator_id": "agent_platform_r2_blast_radius",
        "task_id": contract["task_id"],
        "contract_version": contract["contract_version"],
        "claim_boundary": contract["claim_boundary"],
        "source_authority_sha256": source_authorities,
        "fixtures": fixtures,
        "status": "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write the deterministic report")
    parser.add_argument("--check", action="store_true", help="require the committed report to equal a fresh derivation")
    parser.add_argument("--output", type=Path, default=REPORT_PATH)
    args = parser.parse_args()
    contract = load_blast_radius_contract(str(ROOT))
    try:
        report = build_report(contract)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"BLAST_RADIUS_INVALID: {exc}", file=sys.stderr)
        return 1
    rendered = _canonical(report)
    output = args.output if args.output.is_absolute() else ROOT / args.output
    if args.check:
        if not output.is_file():
            print(f"BLAST_RADIUS_INVALID: missing report {output}", file=sys.stderr)
            return 1
        if output.read_bytes() != rendered:
            print("BLAST_RADIUS_INVALID: committed report is stale", file=sys.stderr)
            return 1
        print(f"BLAST_RADIUS_OK fixtures={len(report['fixtures'])} status=PASS")
        return 0
    if args.write:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(rendered)
        print(f"generated {output.relative_to(ROOT)}")
        return 0
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
