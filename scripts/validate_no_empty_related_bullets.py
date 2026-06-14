#!/usr/bin/env python3
"""validate_no_empty_related_bullets.py — Find and fix empty bullets in Related Objects sections.

Usage:
  python3 scripts/validate_no_empty_related_bullets.py --check
  python3 scripts/validate_no_empty_related_bullets.py --fix-safe
"""

import argparse
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def find_empty_bullets():
    """Find all markdown files with empty bullets."""
    issues = []

    for pattern in ["docs/**/*.md"]:
        base = BASE / pattern.replace("/**", "")
        if not base.exists():
            continue
        for md_file in base.rglob("*.md"):
            if ".git" in str(md_file):
                continue
            try:
                lines = md_file.read_text(encoding="utf-8", errors="ignore").split("\n")
            except Exception:
                continue

            in_related_section = False
            for i, line in enumerate(lines, 1):
                if re.match(r'^##\s*(?:相关对象|Related Objects|相关函数|Related Functions|关联案例|Related Cases|相关发现|Related Discoveries|相关预测|Related Predictions|相关答案|Related Answers|相关解析解|Related Analytic Solutions)', line, re.IGNORECASE):
                    in_related_section = True
                    continue
                if line.startswith("## "):
                    in_related_section = False
                if in_related_section and re.match(r'^\s*[-*•]\s*$', line):
                    issues.append((md_file.relative_to(BASE), i, line))

    return issues


def fix_empty_bullets():
    """Fix empty bullets by replacing with standard placeholder."""
    issues_fixed = 0

    for pattern in ["docs/**/*.md"]:
        base = BASE / pattern.replace("/**", "")
        if not base.exists():
            continue
        for md_file in base.rglob("*.md"):
            if ".git" in str(md_file):
                continue
            try:
                text = md_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            new_text = []
            lines = text.split("\n")
            in_related_section = False

            for i, line in enumerate(lines):
                if re.match(r'^##\s*(?:相关对象|Related Objects|相关函数|Related Functions|关联案例|Related Cases|相关发现|Related Discoveries|相关预测|Related Predictions|相关答案|Related Answers|相关解析解|Related Analytic Solutions)', line, re.IGNORECASE):
                    in_related_section = True
                if line.startswith("## ") and not re.match(r'^##\s*(?:相关对象|Related Objects)', line, re.IGNORECASE):
                    in_related_section = False
                if re.match(r'^\s*[-*•]\s*$', line) and in_related_section:
                    new_text.append(line.rstrip() + " 暂无。 / None.")
                    issues_fixed += 1
                else:
                    new_text.append(line)

            if issues_fixed > 0:
                md_file.write_text("\n".join(new_text), encoding="utf-8")

    return issues_fixed


def main():
    parser = argparse.ArgumentParser(description="Validate no empty bullets in related sections")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--fix-safe", action="store_true")
    args = parser.parse_args()

    issues = find_empty_bullets()

    print(f"Found {len(issues)} empty bullets")
    for file, line, content in issues[:20]:
        print(f"  {file}:{line}: {content!r}")

    if args.fix_safe:
        n = fix_empty_bullets()
        print(f"Fixed {n} empty bullets")

    if args.check:
        if issues:
            print(f"CHECK FAIL: {len(issues)} empty bullets remain")
            return 1
        print("CHECK PASS: No empty bullets in related sections")
        return 0
    return 0


if __name__ == "__main__":
    exit(main())
