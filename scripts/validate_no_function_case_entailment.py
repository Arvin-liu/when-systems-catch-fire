#!/usr/bin/env python3
"""
Validate that no function-case entailment phrasing exists in the repository.

Usage:
    python3 scripts/validate_no_function_case_entailment.py --check
    python3 scripts/validate_no_function_case_entailment.py --report
    python3 scripts/validate_no_function_case_entailment.py --fix-safe
"""

import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Forbidden substrings — checked with simple `in` for precision
FORBIDDEN_SUBSTRINGS = [
    # Chinese
    "必然推导出",
    "必然推出",
    "必然指向",
    "证明了该",
    "证明了函数",
    "唯一推出",
    "唯一解释",
    "必然对应",
    "唯一对应",
    "铁证",
    "互锁",
    "闭锁",
    "数学上互锁",
    "证明该函数成立",
    "证明该案例只能如此解释",
    # English
    "the case proves the function",
    "the function proves the case",
    "the case necessarily derives the function",
    "the function necessarily points to the case",
    "the only explanation",
    "unique entailment",
    "necessary entailment",
    "definitive proof",
    "locked correspondence",
    "bidirectional proof",
    "function-case mutual lock",
]

# Safe phrases that indicate proper inferential language (NOT forbidden — these are OK)
SAFE_PHRASES = [
    "推论", "启发", "触发", "支持", "限制", "反证", "部分验证",
    "可以解释", "用于重读", "当前映射", "候选解释", "证据关系",
    "inferential", "inspired by", "triggered by", "supported by",
    "limited by", "can explain", "current mapping", "candidate explanation",
    "non_entailing", "推论而非定论", "推论关系", "不是定论",
    "not a definitive entailment", "revisable mapping",
    "相关案例", "相关函数", "Related Cases", "Related Functions",
    "案例验证", "关联函数", "关联案例",
]

# Contexts that are acceptable even if they contain a forbidden substring
ACCEPTABLE_CONTEXTS = [
    # "推方案几乎必然对应假退出权" — about proposal posture -> exit rights, not function-case
    "推方案几乎必然对应假退出权",
    # "互锁子集" — mathematical concept about mutually locking subsets, not function-case entailment
    "互锁子集",
    # Forbidden phrase listings in rule docs (AGENT_ENTRY.md, llms.txt) are meta-references, not violations
    "禁止 / Forbidden:",
    "禁止:",
    "Forbidden:",
    "## 函数 —案例非互锁规则",
    "Function-Case Non-Entailment Rule:",
    # Lines starting with "- " in the forbidden list
    "案例必然推导出",
    "案例必然推出",
    "案例证明函数",
    "函数必然指向",
    "函数证明案例",
    "双向证明",
    "the only explanation of a case",
    "a function and a case prove each other",
    # English descriptions in the rule itself contain these words but are not violations
    "must not be described as necessarily deriving",
    "must not be described as necessarily pointing",
    "a function-case relation must not be written as",
    "must state that they are inferences, not definitive",
    "bidirectional necessary entailment",
    # Rule listing patterns (the - item lines)
    "- 案例必然推导出",
    "- 函数必然指向",
    "- 案例证明函数",
    "- 函数证明案例",
    "- 唯一解释",
    "- 双向证明",
    "- necessary entailment",
    "- definitive proof",
    # Full rule description paragraphs (not violations)
    "案例不能被描述为必然推出某函数",
]

# Files to scan — exclude legacy/rebuild dirs
SCAN_TOP_LEVEL = [
    "README.md",
    "AGENT_ENTRY.md",
    "llms.txt",
    "FUNCTIONS.md",
    "CASES.md",
]

SCAN_GLOBS = [
    "docs/zh/functions/**/*.md",
    "docs/zh/cases/**/*.md",
    "data/functions/**/*.json",
    "data/functions/**/*.jsonl",
    "data/cases/**/*.json",
    "data/cases/**/*.jsonl",
    "data/relations/**/*.json",
    "data/relations/**/*.jsonl",
]

SKIP_PREFIXES = [
    os.path.join("archive", "book-legacy", "book"),
    os.path.join("archive", "framework"),
    os.path.join("data", "rebuild"),
]

# Scripts that contain forbidden words in their own replacement tables
SKIP_SCRIPTS = [
    "validate_no_function_case_entailment.py",
    "migrate_function_case_relations.py",
]


def should_skip_file(filepath, base=BASE_DIR):
    rel = os.path.relpath(filepath, base)
    for prefix in SKIP_PREFIXES:
        if rel.startswith(prefix):
            return True
    fname = os.path.basename(filepath)
    if fname in SKIP_SCRIPTS:
        return True
    return False


def collect_files():
    files = []
    for fname in SCAN_TOP_LEVEL:
        fpath = os.path.join(BASE_DIR, fname)
        if os.path.isfile(fpath) and not should_skip_file(fpath):
            files.append(fpath)
    for pattern in SCAN_GLOBS:
        full_pattern = os.path.join(BASE_DIR, pattern)
        for f in glob.glob(full_pattern, recursive=True):
            if not should_skip_file(f):
                files.append(f)
    return sorted(set(files))


def scan_for_forbidden(files):
    findings = []
    for fpath in files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except (UnicodeDecodeError, PermissionError):
            continue

        for i, line in enumerate(lines, 1):
            # Check acceptable contexts first
            skip = False
            for ctx in ACCEPTABLE_CONTEXTS:
                if ctx in line:
                    skip = True
                    break
            if skip:
                continue

            for phrase in FORBIDDEN_SUBSTRINGS:
                if phrase in line:
                    findings.append({
                        "file": fpath,
                        "line_num": i,
                        "matched": phrase,
                        "line": line.rstrip("\n"),
                    })
                    break  # one finding per line

    return findings


def fix_safe(findings, files):
    if not findings:
        return {"auto_fixed": 0, "changes": [], "needs_human_review": 0}

    # Deduplicate by (file, line_num)
    seen = set()
    deduped = []
    for f in findings:
        key = (f["file"], f["line_num"])
        if key not in seen:
            seen.add(key)
            deduped.append(f)

    # Read all files into memory
    file_contents = {}
    for fpath in files:
        try:
            with open(fpath, "r", encoding="utf-8") as fh:
                file_contents[fpath] = fh.readlines()
        except (UnicodeDecodeError, PermissionError):
            continue

    fixed = 0
    changes = []
    for f in deduped:
        fpath = f["file"]
        if fpath not in file_contents:
            continue
        lines = file_contents[fpath]
        i = f["line_num"] - 1
        if i >= len(lines):
            continue

        orig = lines[i]
        matched = f["matched"]

        # Safe replacements
        replacements = {
            "证明了该": "支持该 / 启发该",
            "证明了函数": "支持该函数",
            "必然推出": "可推论出候选关系",
            "必然指向": "可映射到候选解释",
            "必然推导出": "可推论出候选关系",
            "唯一解释": "当前解释路径之一",
            "唯一推出": "候选解释路径之一",
            "必然对应": "存在当前映射",
            "唯一对应": "当前解释路径之一",
            "铁证": "支持性证据",
            "互锁": "关联",
            "闭锁": "关联",
            "数学上互锁": "数学上关联",
            "definitive proof": "supporting evidence",
            "necessary entailment": "inferential relation",
            "unique entailment": "candidate explanation",
            "locked correspondence": "current mapping",
            "bidirectional proof": "non_entailing relation",
            "the case proves the function": "the case supports the function",
            "the function proves the case": "the function explains the case",
            "the case necessarily derives the function": "the case suggests the function",
            "the function necessarily points to the case": "the function can be applied to the case",
            "the only explanation": "one possible explanation",
            "function-case mutual lock": "function-case relation",
        }

        replaced = False
        for old, new in replacements.items():
            if old in matched:
                lines[i] = lines[i].replace(matched, new, 1)
                changes.append({
                    "file": fpath,
                    "line_num": i + 1,
                    "original": matched,
                    "replacement": new,
                })
                fixed += 1
                replaced = True
                break

        if not replaced:
            pass  # could not safely replace

        file_contents[fpath] = lines

    # Write back
    for fpath, lines in file_contents.items():
        try:
            with open(fpath, "w", encoding="utf-8") as fh:
                fh.writelines(lines)
        except PermissionError:
            pass

    return {
        "auto_fixed": fixed,
        "changes": changes,
        "needs_human_review": len(deduped) - fixed,
    }


def ensure_disclaimers(files):
    modifications = []
    disclaimer_zh = "函数与案例之间的关系是推论、映射、支持、限制或反证关系，不是必然证明关系。\n"
    disclaimer_en = "Relations between functions and cases are inferential, mapping, supporting, limiting, or falsifying relations, not necessary proof relations.\n"

    for fname in ["FUNCTIONS.md", "CASES.md"]:
        fpath = os.path.join(BASE_DIR, fname)
        if not os.path.exists(fpath):
            continue
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
        except (UnicodeDecodeError, PermissionError):
            continue

        if "推论" in content and ("案例" in content or "case" in content.lower()):
            continue

        lines = content.split("\n")
        insert_pos = None
        for j, line in enumerate(lines):
            if line.startswith("## "):
                insert_pos = j + 1
                break

        if insert_pos is not None:
            new_lines = lines[:insert_pos] + [disclaimer_zh, disclaimer_en] + lines[insert_pos:]
            with open(fpath, "w", encoding="utf-8") as f:
                f.write("\n".join(new_lines))
            modifications.append(fname)

    return modifications


def run_check():
    files = collect_files()
    findings = scan_for_forbidden(files)
    return {
        "total_files_scanned": len(files),
        "risky_phrases_found": len(findings),
        "findings": findings[:50],
        "blocking_entailment_phrases": len(findings),
        "check_passed": len(findings) == 0,
    }


def run_report():
    files = collect_files()
    findings = scan_for_forbidden(files)
    safe_fix = fix_safe(findings, files)
    mods = ensure_disclaimers(files)
    return {
        "total_files_scanned": len(files),
        "risky_phrases_found": len(findings),
        "auto_fixed": safe_fix["auto_fixed"],
        "needs_human_review": safe_fix["needs_human_review"],
        "disclaimer_modifications": mods,
        "blocking_entailment_phrases": safe_fix["needs_human_review"],
    }


def main():
    parser = argparse.ArgumentParser(description="Validate no function-case entailment")
    parser.add_argument("--check", action="store_true", help="Check only")
    parser.add_argument("--report", action="store_true", help="Scan + fix + report")
    parser.add_argument("--fix-safe", action="store_true", help="Apply safe fixes")
    args = parser.parse_args()

    rebuild_dir = os.path.join(BASE_DIR, "data", "rebuild")
    os.makedirs(rebuild_dir, exist_ok=True)
    report_path = os.path.join(rebuild_dir, "no-function-case-entailment-scan-report.json")
    md_report_path = os.path.join(rebuild_dir, "no-function-case-entailment-scan-report.md")

    if args.check:
        result = run_check()
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result["blocking_entailment_phrases"] > 0:
            print(f"\nFAIL: {result['blocking_entailment_phrases']} blocking entailment phrases found")
            sys.exit(1)
        else:
            print("\nPASS: No blocking entailment phrases found")
            sys.exit(0)

    elif args.report:
        result = run_report()
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        with open(md_report_path, "w", encoding="utf-8") as f:
            f.write("# No Function-Case Entailment Scan Report\n\n")
            f.write(f"Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n")
            f.write(f"Files scanned: {result['total_files_scanned']}\n")
            f.write(f"Risky phrases found: {result['risky_phrases_found']}\n")
            f.write(f"Auto fixed: {result['auto_fixed']}\n")
            f.write(f"Needs human review: {result['needs_human_review']}\n")
            f.write(f"Blocking entailment phrases remaining: {result['blocking_entailment_phrases']}\n")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)

    elif args.fix_safe:
        result = run_report()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)

    else:
        result = run_check()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result["blocking_entailment_phrases"] == 0 else 1)


if __name__ == "__main__":
    main()
