#!/usr/bin/env python3
"""Validate the ESI literature review as a bounded source-to-test boundary."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORD = ROOT / "data/epistemic-governance/literature-boundary-r0.json"
DEFAULT_SCHEMA = ROOT / "schemas/epistemic-governance/literature-boundary-r0.schema.json"


def validate(record: dict, schema: dict) -> list[str]:
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(record)]
    sources = record.get("sources", [])
    source_ids = [source.get("source_id") for source in sources]
    if len(source_ids) != len(set(source_ids)):
        errors.append("literature source IDs must be unique")
    if sum(source.get("source_kind", "").startswith("PRIMARY") for source in sources) < 4:
        errors.append("at least four primary sources are required")
    allowed_domains = ("arxiv.org", "direct.mit.edu", "aclanthology.org")
    for source in sources:
        if not any(domain in source.get("url", "") for domain in allowed_domains):
            errors.append(f"source is outside the reviewed primary-source domains: {source.get('source_id')}")
    bounded_text = " ".join(record.get("bounded_conclusions", []) + record.get("not_established", []) + record.get("claim_ceiling", []))
    if re.search(r"\b(first|novel|proven|proves)\b", bounded_text, re.IGNORECASE):
        errors.append("bounded literature text must not make an unqualified novelty or proof claim")
    if not any(
        "not establish" in item.lower()
        or "not established" in item.lower()
        or "does not establish" in item.lower()
        or "no reviewed source establishes" in item.lower()
        for item in record.get("not_established", [])
    ):
        errors.append("not_established must contain an explicit non-establishment boundary")
    if not any("live" in item.lower() for item in record.get("pending_tests", [])):
        errors.append("pending_tests must preserve the live-provider boundary")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", type=Path, default=DEFAULT_RECORD)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args()
    record = json.loads(args.record.read_text(encoding="utf-8"))
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    errors = validate(record, schema)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"LITERATURE_BOUNDARY_OK sources={len(record['sources'])} novelty={record['novelty_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
