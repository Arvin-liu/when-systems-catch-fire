#!/usr/bin/env python3
"""
Phase B JSONL validator.
Checks: valid JSON, required fields, array types, manifest consistency,
         relation safety fields, no active伪装, inference_not_conclusion=true.
Phase B specific: allows function-case-relations.jsonl to be 0 lines.
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

PHASE_B_FILES = {
    "discoveries.jsonl": {"class": "discovery", "extra": ["name", "description"]},
    "predictions.jsonl": {"class": "prediction", "extra": ["name", "condition"]},
    "answers.jsonl": {"class": "answer", "extra": ["name", "question", "answer"]},
    "analytic-solutions.jsonl": {"class": "analytic_solution", "extra": ["name", "solution"]},
    "function-case-relations.jsonl": {"class": "function_case_relation", "extra": ["function_id", "case_id", "relation_type"]},
    "object-classification-crosswalk.jsonl": {"class": "classification_crosswalk", "extra": ["source_id", "suggested_class"]},
}

# Files that must be non-empty
NON_EMPTY_REQUIRED = [f for f in PHASE_B_FILES if f != "function-case-relations.jsonl"]
# function-case-relations can be 0 lines

def check_jsonl_file(path, class_type, extra_fields, allow_empty=False):
    errors = []
    warnings = []
    if not path.exists():
        return 0, False, [f"File not found: {path}"], []

    line_count = 0
    content = path.read_text(encoding="utf-8")
    if not content.strip():
        if not allow_empty:
            errors.append(f"File is empty but must have records")
        return 0, allow_empty, errors, warnings

    for i, line in enumerate(content.splitlines(), 1):
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

        # Relation safety fields
        if class_type == "function_case_relation":
            if obj.get("entailment_status") != "non_entailing":
                errors.append(f"Line {i}: entailment_status must be 'non_entailing'")
            if obj.get("is_definitive") is not False:
                errors.append(f"Line {i}: is_definitive must be False")
            if obj.get("is_unique_explanation") is not False:
                errors.append(f"Line {i}: is_unique_explanation must be False")
            if obj.get("is_bidirectional_proof") is not False:
                errors.append(f"Line {i}: is_bidirectional_proof must be False")

        # Source SHA check
        if not obj.get("source_sha"):
            warnings.append(f"Line {i}: source_sha is empty")

    return line_count, allow_empty, errors, warnings


def check_manifest():
    path = OUTPUT_DIR / "manifest.json"
    errors = []
    warnings = []
    if not path.exists():
        return False, [f"manifest.json not found"], []

    try:
        m = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return False, [f"manifest.json invalid JSON: {e}"], []

    if "files" not in m:
        return False, ["manifest.json missing 'files' key"], []

    file_paths = {item.get("path") for item in m.get("files", [])} if isinstance(m.get("files"), list) else set(m.get("files", {}).keys())

    # Check Phase B files are listed
    for fname in PHASE_B_FILES:
        expected = f"data/normalized-jsonl/{fname}"
        if expected not in file_paths:
            errors.append(f"manifest missing {expected}")

    # Check line counts match
    files_raw = m.get("files", [])
    if isinstance(files_raw, dict):
        for fname, item in files_raw.items():
            if isinstance(item, dict):
                p = item.get("path", f"data/normalized-jsonl/{fname}")
                lc = item.get("line_count", -1)
                actual_path = OUTPUT_DIR / fname
                if actual_path.exists():
                    actual_count = len([l for l in actual_path.read_text(encoding="utf-8").strip().split('\n') if l.strip()])
                    if lc >= 0 and lc != actual_count:
                        warnings.append(f"manifest line_count {lc} != actual {actual_count} for {fname}")
    elif isinstance(files_raw, list):
        for item in files_raw:
            p = item.get("path", "")
            lc = item.get("line_count", -1)
            fname = Path(p).name
            if fname in PHASE_B_FILES:
                actual_path = OUTPUT_DIR / fname
                if actual_path.exists():
                    actual_count = len([l for l in actual_path.read_text(encoding="utf-8").strip().split('\n') if l.strip()])
                    if lc >= 0 and lc != actual_count:
                        warnings.append(f"manifest line_count {lc} != actual {actual_count} for {fname}")

    return True, errors, warnings


def main():
    parser = argparse.ArgumentParser(description="Validate Phase B JSONL")
    parser.add_argument("--report", action="store_true", help="Write report file")
    parser.add_argument("--check", action="store_true", help="Exit with error code on failure")
    args = parser.parse_args()

    all_errors = []
    all_warnings = []
    file_results = {}

    for fname, spec in PHASE_B_FILES.items():
        path = OUTPUT_DIR / fname
        allow_empty = (fname == "function-case-relations.jsonl")
        lc, _, errors, warnings = check_jsonl_file(path, spec["class"], spec["extra"], allow_empty)
        file_results[fname] = {"line_count": lc, "errors": errors, "warnings": warnings}
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    # Manifest check
    manifest_ok, m_errors, m_warnings = check_manifest()
    all_errors.extend(m_errors)
    all_warnings.extend(m_warnings)

    # Summary
    total_files = len(PHASE_B_FILES)
    files_with_errors = sum(1 for f in file_results.values() if f["errors"])

    summary = {
        "total_files": total_files,
        "files_with_errors": files_with_errors,
        "total_errors": len(all_errors),
        "total_warnings": len(all_warnings),
        "manifest_ok": manifest_ok,
        "file_results": {k: {"line_count": v["line_count"], "errors": len(v["errors"]), "warnings": len(v["warnings"])} for k, v in file_results.items()},
    }

    print(f"Phase B validation: {total_files - files_with_errors}/{total_files} files passed")
    if all_errors:
        print(f"  Errors: {len(all_errors)}")
        for e in all_errors[:10]:
            print(f"    - {e}")
    if all_warnings:
        print(f"  Warnings: {len(all_warnings)}")
        for w in all_warnings[:5]:
            print(f"    - {w}")

    if args.report:
        REBUILD_DIR.mkdir(parents=True, exist_ok=True)
        with open(REBUILD_DIR / "normalized-jsonl-phase-b-validation-report.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        md = "# Phase B Validation Report\n\n"
        md += f"- Files checked: {total_files}\n"
        md += f"- Files with errors: {files_with_errors}\n"
        md += f"- Total errors: {len(all_errors)}\n"
        md += f"- Total warnings: {len(all_warnings)}\n"
        md += f"- Manifest OK: {manifest_ok}\n\n"
        md += "| File | Lines | Errors | Warnings |\n"
        md += "|------|-------|--------|----------|\n"
        for fname, res in file_results.items():
            md += f"| {fname} | {res['line_count']} | {res['errors']} | {res['warnings']} |\n"

        with open(REBUILD_DIR / "normalized-jsonl-phase-b-validation-report.md", "w", encoding="utf-8") as f:
            f.write(md)
        print(f"\nReport written: data/rebuild/normalized-jsonl-phase-b-validation-report.json")

    if args.check:
        if all_errors:
            print("\nVALIDATION FAILED")
            sys.exit(1)
        else:
            print("\nVALIDATION PASSED")
            sys.exit(0)


if __name__ == "__main__":
    main()
