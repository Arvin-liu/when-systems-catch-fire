#!/usr/bin/env python3
"""Validate R2 generator source contracts against the generator registry."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "data/operations/generator-source-contracts.json"
SCHEMA = ROOT / "schemas/operations/generator-source-contract.schema.json"
REGISTRY = ROOT / "data/operations/generator-registry.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(repo_root: Path = ROOT) -> list[str]:
    contract = json.loads((repo_root / CONTRACT.relative_to(ROOT)).read_text(encoding="utf-8"))
    schema = json.loads((repo_root / SCHEMA.relative_to(ROOT)).read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(contract), key=lambda item: list(item.path))
    problems = [f"schema: {error.message}" for error in errors]
    registry = json.loads((repo_root / REGISTRY.relative_to(ROOT)).read_text(encoding="utf-8"))
    seen_outputs: set[str] = set()
    for item in contract.get("generators", []):
        gid = item["generator_id"]
        entry = registry.get("generators", {}).get(gid)
        if entry is None:
            problems.append(f"{gid}: missing from generator-registry.json")
            continue
        tool = repo_root / item["canonical_tool"]
        if not tool.is_file():
            problems.append(f"{gid}: canonical tool missing: {item['canonical_tool']}")
        else:
            live = sha256(tool)
            if entry.get("canonical_tool_digest_sha256") != live:
                problems.append(f"{gid}: registry tool digest does not match live source")
        if entry.get("canonical_tool") != item["canonical_tool"]:
            problems.append(f"{gid}: registry canonical_tool mismatch")
        if set(entry.get("required_input_authorities", [])) != set(item["source_authorities"]):
            problems.append(f"{gid}: registry source authorities mismatch")
        if set(entry.get("allowed_output_paths", [])) != set(item["output_paths"]):
            problems.append(f"{gid}: registry output paths mismatch")
        for source in item["source_authorities"]:
            if not (repo_root / source).is_file():
                problems.append(f"{gid}: source authority missing: {source}")
            if source in item["output_paths"]:
                problems.append(f"{gid}: source/output authority overlap: {source}")
        for output in item["output_paths"]:
            if output in seen_outputs:
                problems.append(f"duplicate generator output path: {output}")
            seen_outputs.add(output)
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=ROOT)
    args = parser.parse_args()
    problems = validate(args.repo.resolve())
    if problems:
        for problem in problems:
            print(f"GENERATOR_SOURCE_CONTRACT_INVALID: {problem}", file=sys.stderr)
        return 1
    print("GENERATOR_SOURCE_CONTRACT_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
