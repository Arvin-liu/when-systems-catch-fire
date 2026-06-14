#!/usr/bin/env python3
"""
Minimal consistency check: canonical sources exist, source_sha not empty,
IDs not empty, and function/case counts reasonable.
"""

import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE / "data" / "normalized-jsonl"
REBUILD_DIR = BASE / "data" / "rebuild"

def check_consistency():
    errors = []
    warnings = []
    needs_source_review = []

    files_to_check = [
        "functions.jsonl",
        "cases.jsonl",
    ]

    total_lines = 0
    for fname in files_to_check:
        path = OUTPUT_DIR / fname
        if not path.exists():
            errors.append(f"File not found: {fname}")
            continue

        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            total_lines += 1
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            # ID check
            obj_id = obj.get("id", "")
            if not obj_id:
                errors.append(f"{fname}:{i}: id is empty")

            # canonical_source check
            cs = obj.get("canonical_source", "")
            if not cs:
                warnings.append(f"{fname}:{i}: canonical_source is empty (id={obj_id})")
                needs_source_review.append({"file": fname, "line": i, "id": obj_id})
                continue

            # Check if canonical_source file exists
            cs_path = Path(cs)
            if not cs_path.exists():
                # Also try relative to BASE/data
                alt_path = BASE / "data" / cs
                if not alt_path.exists():
                    warnings.append(f"{fname}:{i}: canonical_source file not found: {cs} (id={obj_id})")
                    needs_source_review.append({"file": fname, "line": i, "id": obj_id, "reason": "canonical_source_not_found"})

            # source_sha check
            if not obj.get("source_sha"):
                warnings.append(f"{fname}:{i}: source_sha is empty (id={obj_id})")

    # Count-based sanity checks
    for fname in files_to_check:
        path = OUTPUT_DIR / fname
        if path.exists():
            count = sum(1 for l in path.read_text(encoding="utf-8").splitlines() if l.strip())
            if count == 0:
                errors.append(f"{fname}: 0 lines (unexpected empty file)")
            elif count > 2000:
                warnings.append(f"{fname}: {count} lines seems unusually high")

    # Check manifest matches
    manifest_path = OUTPUT_DIR / "manifest.json"
    if manifest_path.exists():
        m = json.loads(manifest_path.read_text(encoding="utf-8"))
        for fname in files_to_check:
            actual = sum(1 for l in (OUTPUT_DIR / fname).read_text(encoding="utf-8").splitlines() if l.strip()) if (OUTPUT_DIR / fname).exists() else 0
            expected = m.get("files", {}).get(fname, {}).get("line_count", 0)
            if expected != actual and expected > 0:
                warnings.append(f"Manifest line_count for {fname}: {expected} vs actual: {actual}")

    status = "PASS" if not errors else "FAIL"
    report = {
        "status": status,
        "total_lines_checked": total_lines,
        "errors": errors,
        "warnings": warnings,
        "needs_source_review": needs_source_review,
        "needs_source_review_count": len(needs_source_review),
        "canonical_source_missing_count": len([e for e in warnings if "canonical_source file not found" in e]),
        "source_sha_missing_count": len([e for e in warnings if "source_sha is empty" in e]),
    }

    report_path = REBUILD_DIR / "jsonl-canonical-consistency-minimal-report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Markdown
    md = f"""# JSONL Canonical Consistency Report

- Status: {status}
- Total lines checked: {total_lines}
- Errors: {len(errors)}
- Warnings: {len(warnings)}
- Needs source review: {len(needs_source_review)}
- Canonical source missing: {report["canonical_source_missing_count"]}
- Source SHA missing: {report["source_sha_missing_count"]}
"""
    if needs_source_review:
        md += "\n## Needs Source Review\n\n"
        for item in needs_source_review[:20]:
            md += f"- {item.get('file', '?')}:{item.get('line', '?')} id={item.get('id', '?')} {item.get('reason', '')}\n"
        if len(needs_source_review) > 20:
            md += f"... and {len(needs_source_review) - 20} more\n"

    md_path = REBUILD_DIR / "jsonl-canonical-consistency-minimal-report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"Consistency: {status} ({len(errors)} errors, {len(warnings)} warnings)")
    if errors:
        for e in errors[:5]:
            print(f"  - {e}")

    sys.exit(0 if not errors else 1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    check_consistency()
