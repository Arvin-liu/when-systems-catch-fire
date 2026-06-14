#!/usr/bin/env python3
"""
Minimal JSONL validator for the normalized data layer.
Checks: valid JSON, required fields, array types, manifest consistency,
         no active伪装, inference_not_conclusion=true.
"""

import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE / "data" / "normalized-jsonl"
REBUILD_DIR = BASE / "data" / "rebuild"

REQUIRED_COMMON = ["id", "object_class", "canonical_source", "schema_version",
                   "generated_at", "source_commit", "source_sha", "inference_not_conclusion"]

FUNCTION_FIELDS = ["id", "name", "definition", "expression", "derivation",
                   "related_cases", "extended_notes"]
CASE_FIELDS = ["id", "layer", "grid", "status", "core_function", "description",
               "key_discovery"]

def check_jsonl(path, class_type, extra_fields):
    """Check a JSONL file. Returns (ok, errors, warnings)."""
    errors = []
    warnings = []
    if not path.exists():
        return False, [f"File not found: {path}"], []

    line_count = 0
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            errors.append(f"Line {i}: empty line")
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            errors.append(f"Line {i}: invalid JSON: {e}")
            continue

        line_count += 1

        # Required common fields
        for f in REQUIRED_COMMON:
            if f not in obj:
                errors.append(f"Line {i} (id={obj.get('id', '?')}): missing required field '{f}'")

        # Object class check
        if obj.get("object_class") != class_type:
            errors.append(f"Line {i}: object_class is '{obj.get('object_class')}', expected '{class_type}'")

        # Schema version
        if obj.get("schema_version") != "normalized-jsonl-v1":
            errors.append(f"Line {i}: schema_version is '{obj.get('schema_version')}'")

        # inference_not_conclusion
        if obj.get("inference_not_conclusion") is not True:
            errors.append(f"Line {i}: inference_not_conclusion is not True")

        # Extra required fields
        for f in extra_fields:
            if f not in obj:
                errors.append(f"Line {i} (id={obj.get('id', '?')}): missing field '{f}'")

        # Array type checks
        for f in ["related_cases", "related_functions", "core_functions"]:
            if f in obj and not isinstance(obj[f], list):
                errors.append(f"Line {i}: '{f}' is not an array")

        # Case entailment check
        if class_type == "case":
            if obj.get("entailment_status") != "non_entailing":
                warnings.append(f"Line {i}: case entailment_status is '{obj.get('entailment_status')}', expected 'non_entailing'")

        # Source SHA check
        if not obj.get("source_sha"):
            warnings.append(f"Line {i}: source_sha is empty")

    return line_count > 0, errors, warnings

def check_manifest():
    """Check manifest.json consistency."""
    path = OUTPUT_DIR / "manifest.json"
    errors = []
    warnings = []
    if not path.exists():
        return False, [f"manifest.json not found"], []

    try:
        m = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return False, [f"manifest.json invalid JSON: {e}"], []

    if m.get("schema_version") != "normalized-jsonl-v1":
        errors.append("manifest schema_version mismatch")
    if m.get("format") != "jsonl":
        errors.append("manifest format is not jsonl")
    if m.get("rules", {}).get("counts_are_dynamic") is not True:
        errors.append("manifest counts_are_dynamic is not true")
    if m.get("rules", {}).get("canonical_data_not_replaced") is not True:
        errors.append("manifest canonical_data_not_replaced is not true")

    # Verify line counts match actual files
    for fname, finfo in m.get("files", {}).items():
        base_name = Path(fname).name
        if base_name not in {"functions.jsonl", "cases.jsonl"}:
            continue
        actual = Path(OUTPUT_DIR / base_name)
        if not actual.exists():
            errors.append(f"File in manifest but not on disk: {fname}")
            continue
        actual_count = sum(1 for l in actual.read_text(encoding="utf-8").splitlines() if l.strip())
        if finfo.get("line_count") != actual_count:
            errors.append(f"Line count mismatch for {fname}: manifest={finfo.get('line_count')}, actual={actual_count}")

    return True, errors, warnings

def main():
    parser = argparse.ArgumentParser(description="Validate normalized JSONL")
    parser.add_argument("--report", action="store_true", help="Generate report files")
    parser.add_argument("--check", action="store_true", help="Check and exit with code")
    args = parser.parse_args()

    all_errors = []
    all_warnings = []
    counts = {}

    files_to_check = [
        ("functions.jsonl", "function", FUNCTION_FIELDS),
        ("cases.jsonl", "case", CASE_FIELDS),
    ]

    for fname, class_type, extra_fields in files_to_check:
        path = OUTPUT_DIR / fname
        ok, errors, warnings = check_jsonl(path, class_type, extra_fields)
        if ok:
            line_count = sum(1 for l in path.read_text(encoding="utf-8").splitlines() if l.strip())
            counts[fname] = line_count
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    # Check manifest
    manifest_ok, m_errors, m_warnings = check_manifest()
    all_errors.extend(m_errors)
    all_warnings.extend(m_warnings)

    # Report
    total_errors = len(all_errors)
    total_warnings = len(all_warnings)
    status = "PASS" if total_errors == 0 else "FAIL"

    report_content = {
        "status": status,
        "total_errors": total_errors,
        "total_warnings": total_warnings,
        "errors": all_errors,
        "warnings": all_warnings,
        "files": counts,
        "manifest_ok": manifest_ok,
    }

    report_path = REBUILD_DIR / "normalized-jsonl-validation-minimal-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_content, f, ensure_ascii=False, indent=2)

    # Markdown report
    md = f"""# Validation Report

- Status: {status}
- Errors: {total_errors}
- Warnings: {total_warnings}

## File Counts

| File | Lines |
|------|-------|
"""
    for fname, cnt in counts.items():
        md += f"| {fname} | {cnt} |\n"

    if all_errors:
        md += "\n## Errors\n\n"
        for e in all_errors[:50]:
            md += f"- {e}\n"
        if len(all_errors) > 50:
            md += f"... and {len(all_errors) - 50} more errors\n"

    if all_warnings:
        md += "\n## Warnings\n\n"
        for w in all_warnings[:30]:
            md += f"- {w}\n"

    md_path = REBUILD_DIR / "normalized-jsonl-validation-minimal-report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"Validation: {status} ({total_errors} errors, {total_warnings} warnings)")
    if all_errors:
        print("First 5 errors:")
        for e in all_errors[:5]:
            print(f"  - {e}")

    if args.check:
        sys.exit(0 if total_errors == 0 else 1)

if __name__ == "__main__":
    main()
