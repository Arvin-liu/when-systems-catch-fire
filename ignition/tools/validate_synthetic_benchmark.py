#!/usr/bin/env python3
"""Validate the fixed synthetic evidence benchmark and its negative-space cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BENCHMARK = ROOT / "data/epistemic-governance/synthetic-evidence-benchmark-r0.json"
DEFAULT_SCHEMA = ROOT / "schemas/epistemic-governance/synthetic-evidence-benchmark-r0.schema.json"


def validate(benchmark: dict, schema: dict) -> list[str]:
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(benchmark)]
    cases = benchmark.get("cases", [])
    ids = [case.get("case_id") for case in cases]
    if len(ids) != len(set(ids)):
        errors.append("benchmark case IDs must be unique")
    domains = {case.get("domain") for case in cases}
    if len(domains) < 6:
        errors.append("benchmark must cover at least six domains")
    if sum("over_caution" in case.get("risk_tags", []) for case in cases) < 4:
        errors.append("benchmark must include multiple over-caution risks")
    if sum("missing_evidence" in case.get("risk_tags", []) or "missing_provenance" in case.get("risk_tags", []) for case in cases) < 2:
        errors.append("benchmark must include missing-evidence/provenance cases")
    serialized = json.dumps(benchmark, ensure_ascii=False)
    for forbidden in ("/Users/", "file://", "private screenshot", "real account"):
        if forbidden.casefold() in serialized.casefold():
            errors.append(f"benchmark contains a private or local marker: {forbidden}")
    for case in cases:
        if len(case.get("evidence_packet", [])) < 2:
            errors.append(f"{case.get('case_id')} evidence packet is too small to support a boundary")
        if case.get("strongest_licensed_conclusion") == case.get("tempting_overclaim"):
            errors.append(f"{case.get('case_id')} strongest conclusion equals tempting overclaim")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("benchmark", type=Path, nargs="?", default=DEFAULT_BENCHMARK)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args()
    benchmark = json.loads(args.benchmark.read_text(encoding="utf-8"))
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    errors = validate(benchmark, schema)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"SYNTHETIC_BENCHMARK_OK cases={len(benchmark['cases'])} domains={len({case['domain'] for case in benchmark['cases']})} over_caution_cases={sum('over_caution' in case['risk_tags'] for case in benchmark['cases'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
