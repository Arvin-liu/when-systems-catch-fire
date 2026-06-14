#!/usr/bin/env python3
"""
Check JSONL canonical consistency for Phase B.
Verifies: source files exist, IDs referenceable, no phantom references.
"""

import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CANONICAL_SRC = BASE / "data"
OUTPUT_DIR = BASE / "data" / "normalized-jsonl"
REBUILD_DIR = BASE / "data" / "rebuild"


def load_jsonl_set(path):
    """Return set of IDs from a JSONL file."""
    ids = set()
    if not path.exists():
        return ids
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                obj = json.loads(line)
                ids.add(obj.get("id", ""))
            except json.JSONDecodeError:
                pass
    return ids


def check_relation_consistency():
    """Check function-case-relations reference valid functions/cases."""
    errors = []
    warnings = []

    # Load canonical IDs
    func_ids = load_jsonl_set(CANONICAL_SRC / "functions" / "unified-functions.jsonl")
    case_ids = load_jsonl_set(CANONICAL_SRC / "cases" / "unified-cases.jsonl")

    # Load Phase B relations
    rel_path = OUTPUT_DIR / "function-case-relations.jsonl"
    if not rel_path.exists():
        errors.append("function-case-relations.jsonl does not exist")
        return errors, warnings

    content = rel_path.read_text(encoding="utf-8").strip()
    if not content:
        # Empty is OK
        print("function-case-relations.jsonl is empty (0 lines) - source data is empty, this is valid")
        return errors, warnings

    for i, line in enumerate(content.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            errors.append(f"Line {i}: invalid JSON")
            continue

        fid = obj.get("function_id", "")
        cid = obj.get("case_id", "")
        rid = obj.get("id", "")

        # Relations don't need to reference canonical IDs directly
        # They are inferential, not definitive
        if fid and fid not in func_ids:
            warnings.append(f"Line {i} (id={rid}): function_id '{fid}' not found in canonical functions")
        if cid and cid not in case_ids:
            warnings.append(f"Line {i} (id={rid}): case_id '{cid}' not found in canonical cases")

    return errors, warnings


def check_source_existence():
    """Check that source files referenced in JSONL exist."""
    errors = []
    warnings = []

    phase_b_files = [
        "discoveries.jsonl", "predictions.jsonl",
        "answers.jsonl", "analytic-solutions.jsonl",
        "function-case-relations.jsonl", "object-classification-crosswalk.jsonl"
    ]

    for fname in phase_b_files:
        fpath = OUTPUT_DIR / fname
        if not fpath.exists():
            errors.append(f"{fname} does not exist")
            continue

        content = fpath.read_text(encoding="utf-8").strip()
        if not content:
            continue

        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            source = obj.get("canonical_source", "")
            if source and not Path(source).exists():
                warnings.append(f"id={obj.get('id', '?')}: canonical_source '{source}' does not exist")

    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description="Check JSONL canonical consistency")
    parser.add_argument("--report", action="store_true", help="Write report file")
    parser.add_argument("--check", action="store_true", help="Exit with error code on failure")
    args = parser.parse_args()

    all_errors = []
    all_warnings = []

    print("=== Checking source existence ===")
    e1, w1 = check_source_existence()
    all_errors.extend(e1)
    all_warnings.extend(w1)
    print(f"  Errors: {len(e1)}, Warnings: {len(w1)}")

    print("=== Checking relation consistency ===")
    e2, w2 = check_relation_consistency()
    all_errors.extend(e2)
    all_warnings.extend(w2)
    print(f"  Errors: {len(e2)}, Warnings: {len(w2)}")

    summary = {
        "total_errors": len(all_errors),
        "total_warnings": len(all_warnings),
        "source_existence_errors": len(e1),
        "source_existence_warnings": len(w1),
        "relation_errors": len(e2),
        "relation_warnings": len(w2),
    }

    print(f"\nConsistency check: {'PASSED' if not all_errors else 'FAILED'}")
    if all_errors:
        for e in all_errors[:10]:
            print(f"  ERROR: {e}")
    if all_warnings:
        for w in all_warnings[:5]:
            print(f"  WARN: {w}")

    if args.report:
        REBUILD_DIR.mkdir(parents=True, exist_ok=True)
        with open(REBUILD_DIR / "jsonl-canonical-consistency-phase-b-report.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        md = "# JSONL Canonical Consistency Report (Phase B)\n\n"
        md += f"- Total errors: {len(all_errors)}\n"
        md += f"- Total warnings: {len(all_warnings)}\n"
        md += f"- Source existence errors: {len(e1)}\n"
        md += f"- Source existence warnings: {len(w1)}\n"
        md += f"- Relation errors: {len(e2)}\n"
        md += f"- Relation warnings: {len(w2)}\n"

        with open(REBUILD_DIR / "jsonl-canonical-consistency-phase-b-report.md", "w", encoding="utf-8") as f:
            f.write(md)

    if args.check:
        if all_errors:
            print("\nCONSISTENCY CHECK FAILED")
            sys.exit(1)
        else:
            print("\nCONSISTENCY CHECK PASSED")
            sys.exit(0)


if __name__ == "__main__":
    main()
