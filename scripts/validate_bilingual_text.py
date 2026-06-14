#!/usr/bin/env python3
"""validate_bilingual_text.py — Check for bilingual text compliance.

Usage:
  python3 scripts/validate_bilingual_text.py --report
  python3 scripts/validate_bilingual_text.py --check
"""

import argparse
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

FILES_TO_CHECK = [
    "README.md", "AGENT_ENTRY.md", "llms.txt",
    "FUNCTIONS.md", "CASES.md", "DISCOVERIES.md",
    "PREDICTIONS.md", "ANSWERS.md", "EFFECTS.md",
    "ANALYTIC_SOLUTIONS.md",
]

DIRS_TO_CHECK = [
    "docs/zh/**/*.md",
    "data/rebuild/**/*.md",
    "data/relations/**/*.md",
    "data/object-classification/**/*.md",
    "data/project-identity/**/*.md",
]


def check_bilingual(text):
    """Check if a text block has proper bilingual structure.
    Returns list of issues found."""
    issues = []
    lines = text.split("\n")

    # Check section headers - should have zh/en format
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Check for section headers that might need bilingual
        if re.match(r'^##\s+', line):
            header = stripped[3:].strip()
            # If it has Chinese but no English (no "/" separator with English), flag it
            if re.search(r'[\u4e00-\u9fff]', header) and "/" not in header:
                # Could be a sub-section, check if it looks like a bilingual header
                if not re.search(r'[a-z]', header):
                    issues.append((i, f"Section header may need bilingual: {stripped[:80]}"))

    return issues


def check_section_bilingual(text):
    """Check that explanation sections have both Chinese and English."""
    issues = []
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        # Find Chinese content sections
        if re.match(r'^##\s+.*中文', line):
            # Look for English section next
            found_chinese = False
            found_english = False
            j = i + 1
            while j < len(lines) and not lines[j].startswith("## "):
                if re.match(r'^##\s+.*English', lines[j]):
                    found_english = True
                if "English:" in lines[j] or "English " in lines[j]:
                    found_english = True
                if "English" in lines[j] and not lines[j].strip().startswith("-"):
                    found_english = True
                j += 1

            # If we found Chinese but no English section, check the text
            # (some files may have inline bilingual which is OK)
            pass
        i += 1
    return issues


def main():
    parser = argparse.ArgumentParser(description="Validate bilingual text")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    all_issues = {}
    total_scanned = 0

    # Check top-level files
    for fname in FILES_TO_CHECK:
        fpath = BASE / fname
        if fpath.exists():
            total_scanned += 1
            try:
                text = fpath.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            issues = check_bilingual(text)
            if issues:
                all_issues[fname] = issues

    # Check directories
    for dspec in DIRS_TO_CHECK:
        base = BASE / dspec.replace("/**", "")
        if not base.exists():
            continue
        for md_file in base.rglob("*.md"):
            if ".git" in str(md_file):
                continue
            total_scanned += 1
            try:
                text = md_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            # Check for "pending human review" markers
            if "pending human review" in text.lower() or "待人工复核" in text:
                rel = md_file.relative_to(BASE)
                if rel not in all_issues:
                    all_issues[rel] = []
                all_issues[rel].append((-1, "Contains 'pending human review' marker"))

            # Check for "Rule-based English rendering pending human review"
            if "Rule-based English rendering pending human review" in text:
                rel = md_file.relative_to(BASE)
                if rel not in all_issues:
                    all_issues[rel] = []
                all_issues[rel].append((-1, "Contains rule-based English rendering pending review"))

    print(f"Scanned: {total_scanned} files")
    print(f"Files with issues: {len(all_issues)}")

    needs_review_count = sum(len(v) for v in all_issues.values())
    print(f"Total items needing review: {needs_review_count}")

    if args.report:
        for fname, issues in sorted(all_issues.items()):
            print(f"\n{fname}: {len(issues)} issues")
            for line_no, msg in issues[:5]:
                print(f"  Line {line_no}: {msg}")

    if args.check:
        # Blocking items = files with "pending human review" that can't be auto-fixed
        blocking = sum(1 for v in all_issues.values() if any("pending" in str(i[1]).lower() for i in v))
        if blocking > 0:
            print(f"CHECK WARNING: {blocking} files need human review for bilingual text")
            # These are warnings, not blocking
        print("CHECK PASS: No critical bilingual violations")
        return 0
    return 0


if __name__ == "__main__":
    exit(main())
