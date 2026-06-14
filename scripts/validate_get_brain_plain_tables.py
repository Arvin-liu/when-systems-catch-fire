#!/usr/bin/env python3
"""
validate_get_brain_plain_tables.py
Validate the Get Brain plain-text entry tables.

Usage:
    python3 scripts/validate_get_brain_plain_tables.py --check
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def check(condition, msg):
    if condition:
        print(f"  [PASS] {msg}")
        return True
    else:
        print(f"  [FAIL] {msg}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Validate Get Brain plain-text tables")
    parser.add_argument("--check", action="store_true", help="Run validation checks")
    args = parser.parse_args()

    if not args.check:
        print("[ERROR] Specify --check", file=sys.stderr)
        sys.exit(1)

    print("=== Get Brain Plain Tables Validation ===\n")
    all_pass = True

    # 1. Check files exist
    print("[1] File existence:")
    required_files = [
        REPO_ROOT / "get-brain" / "unified-functions-full.md",
        REPO_ROOT / "get-brain" / "unified-cases-full.md",
        REPO_ROOT / "get-brain" / "unified-functions-full.txt",
        REPO_ROOT / "get-brain" / "unified-cases-full.txt",
        REPO_ROOT / "get-brain" / "README.md",
    ]
    for f in required_files:
        all_pass &= check(f.exists(), f"{f} exists")

    # 2. Check README has Get Brain entry
    print("\n[2] README entry:")
    getbrain_readme = (REPO_ROOT / "get-brain" / "README.md").read_text(encoding="utf-8")
    all_pass &= check("得到大脑专用入口" in getbrain_readme or "Get Brain Dedicated Entry" in getbrain_readme,
                      "get-brain/README.md has Get Brain entry")
    all_pass &= check("unified-functions-full.md" in getbrain_readme,
                      "get-brain/README.md mentions functions table")
    all_pass &= check("unified-cases-full.md" in getbrain_readme,
                      "get-brain/README.md mentions cases table")

    # 3. Check root README
    print("\n[3] Root README:")
    root_readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    all_pass &= check("得到大脑专用入口" in root_readme or "Get Brain Dedicated Entry" in root_readme,
                      "root README has Get Brain entry")
    all_pass &= check(
        "raw.githubusercontent.com/Arvin-liu/when-systems-catch-fire/main/get-brain/unified-functions-full.md" in root_readme,
        "root README has functions raw link"
    )
    all_pass &= check(
        "raw.githubusercontent.com/Arvin-liu/when-systems-catch-fire/main/get-brain/unified-cases-full.md" in root_readme,
        "root README has cases raw link"
    )

    # 4. Load JSONL and compare counts
    print("\n[4] Object count validation:")
    functions_jsonl = REPO_ROOT / "data" / "normalized-jsonl" / "functions.jsonl"
    cases_jsonl = REPO_ROOT / "data" / "normalized-jsonl" / "cases.jsonl"

    if functions_jsonl.exists():
        func_count = sum(1 for line in functions_jsonl.read_text(encoding="utf-8").strip().split("\n") if line.strip())
    else:
        func_count = 0

    if cases_jsonl.exists():
        case_count = sum(1 for line in cases_jsonl.read_text(encoding="utf-8").strip().split("\n") if line.strip())
    else:
        case_count = 0

    # Count objects in tables
    func_table = (REPO_ROOT / "get-brain" / "unified-functions-full.md").read_text(encoding="utf-8") if (REPO_ROOT / "get-brain" / "unified-functions-full.md").exists() else ""
    case_table = (REPO_ROOT / "get-brain" / "unified-cases-full.md").read_text(encoding="utf-8") if (REPO_ROOT / "get-brain" / "unified-cases-full.md").exists() else ""

    # Count section headers (## ID)
    func_headers = len([l for l in func_table.split("\n") if l.startswith("## ") and any(c.isdigit() for c in l.split("## ")[1][:5])])
    case_headers = len([l for l in case_table.split("\n") if l.startswith("## ") and any(c.isdigit() for c in l.split("## ")[1][:5])])

    all_pass &= check(func_headers == func_count,
                      f"Function table count ({func_headers}) matches JSONL ({func_count})")
    all_pass &= check(case_headers == case_count,
                      f"Case table count ({case_headers}) matches JSONL ({case_count})")

    # 5. Check function table structure
    print("\n[5] Function table structure:")
    all_pass &= check("全量统一函数总表" in func_table or "Full Unified Function Table" in func_table,
                      "Function table has title")
    all_pass &= check("数学函数" in func_table or "Mathematical Function" in func_table or "Expression" in func_table,
                      "Function table has math function section")
    all_pass &= check("推理推导过程" in func_table or "Derivation" in func_table,
                      "Function table has derivation section")
    all_pass &= check("相关案例" in func_table or "Related Cases" in func_table,
                      "Function table has related cases section")

    # 6. Check case table structure
    print("\n[6] Case table structure:")
    all_pass &= check("全量统一案例总表" in case_table or "Full Unified Case Table" in case_table,
                      "Case table has title")
    all_pass &= check("完整案例内容" in case_table or "Full Case Content" in case_table,
                      "Case table has full case content section")
    all_pass &= check("关键发现" in case_table or "Key Discovery" in case_table,
                      "Case table has key discovery section")
    all_pass &= check("相关函数" in case_table or "Related Functions" in case_table,
                      "Case table has related functions section")

    # 7. Check no function body in case table and vice versa
    print("\n[7] Content separation:")
    # Case table should not have full function sections
    all_pass &= check("## D-" not in case_table or "related_functions" in case_table.lower() or "相关函数" in case_table,
                      "Case table does not contain full function bodies")

    # 8. Check report exists
    print("\n[8] Report:")
    report_path = REPO_ROOT / "data" / "rebuild" / "get-brain-plain-tables-report.json"
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        all_pass &= check(report.get("safety", {}).get("canonical_modified") is False,
                          "report confirms canonical not modified")
        all_pass &= check(report.get("safety", {}).get("eff_migrated") is False,
                          "report confirms EFF not migrated")
        all_pass &= check(report.get("safety", {}).get("active_promoted") is False,
                          "report confirms no active promoted")
        all_pass &= check(report.get("safety", {}).get("academic_novelty_passed_generated") is False,
                          "report confirms no academic_novelty.passed")
        all_pass &= check(report.get("root_readme_has_get_brain_entry") is True,
                          "report confirms root README entry")
    else:
        all_pass &= check(False, "Report JSON exists")

    # 9. Check project identity lock preserved
    print("\n[9] Project identity lock:")
    root_md = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    all_pass &= check("一个人类在好奇心的驱动下" in root_md,
                      "Project positioning lock preserved in README")

    # Summary
    print(f"\n{'='*50}")
    if all_pass:
        print("ALL CHECKS PASSED")
    else:
        print("SOME CHECKS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
