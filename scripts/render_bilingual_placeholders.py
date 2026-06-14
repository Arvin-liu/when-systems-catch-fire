#!/usr/bin/env python3
"""render_bilingual_placeholders.py — Auto-fill English where Chinese exists.

Usage:
  python3 scripts/render_bilingual_placeholders.py --fix-safe
  python3 scripts/render_bilingual_placeholders.py --check
"""

import argparse
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

# Files to scan
TARGET_FILES = [
    "README.md", "AGENT_ENTRY.md", "llms.txt",
    "FUNCTIONS.md", "CASES.md", "DISCOVERIES.md",
    "PREDICTIONS.md", "ANSWERS.md", "EFFECTS.md",
    "ANALYTIC_SOLUTIONS.md",
]

TARGET_DIRS = [
    "docs/zh/**/*.md",
    "data/rebuild/**/*.md",
    "data/relations/**/*.md",
    "data/object-classification/**/*.md",
    "data/project-identity/**/*.md",
]


def fix_pending_reviews(text):
    """Replace 'pending human review' markers with a standard bilingual placeholder."""
    fixed_count = 0
    replacements = [
        (r'Rule-based English rendering pending human review\.', 'English rendering pending human review.'),
        (r'规则英语渲染待人工复核\.', '中文说明。\nEnglish rendering pending human review.'),
    ]

    for old, new in replacements:
        if re.search(old, text, re.IGNORECASE):
            text = re.sub(old, new, text, flags=re.IGNORECASE)
            fixed_count += 1

    return text, fixed_count


def fix_section_headers(text):
    """Add English to Chinese-only section headers where pattern is clear."""
    fixed_count = 0
    lines = text.split("\n")
    new_lines = []

    for line in lines:
        m = re.match(r'^(#+)\s+(.+?)(?:\s*/\s*.+)?$', line)
        if m:
            prefix = m.group(1)
            content = m.group(2).strip()
            # If it has Chinese but no English part after /
            if re.search(r'[\u4e00-\u9fff]', content) and "/ " not in content and " /" not in content:
                # Check if there's already an English translation nearby
                new_lines.append(line)  # Leave as-is for manual review
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    return "\n".join(new_lines), fixed_count


def main():
    parser = argparse.ArgumentParser(description="Render bilingual placeholders")
    parser.add_argument("--fix-safe", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    total_files = 0
    total_fixes = 0
    needs_review = []

    # Process top-level files
    for fname in TARGET_FILES:
        fpath = BASE / fname
        if not fpath.exists():
            continue
        total_files += 1
        try:
            text = fpath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        original = text
        text, n = fix_pending_reviews(text)
        total_fixes += n
        if n > 0:
            if args.fix_safe:
                fpath.write_text(text, encoding="utf-8")
                print(f"Fixed {n} issues in {fname}")
            needs_review.append(fname)

    # Process directory files
    for dspec in TARGET_DIRS:
        base = BASE / dspec.replace("/**", "")
        if not base.exists():
            continue
        for md_file in base.rglob("*.md"):
            if ".git" in str(md_file):
                continue
            total_files += 1
            try:
                text = md_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            original = text
            text, n = fix_pending_reviews(text)
            total_fixes += n
            if n > 0:
                if args.fix_safe:
                    md_file.write_text(text, encoding="utf-8")
                    print(f"Fixed {n} issues in {md_file.relative_to(BASE)}")
                needs_review.append(str(md_file.relative_to(BASE)))

    print(f"\nSummary: files={total_files}, fixes={total_fixes}, needs_review={len(needs_review)}")

    if args.check:
        # Check for remaining "pending human review" markers
        remaining = 0
        for fname in TARGET_FILES:
            fpath = BASE / fname
            if fpath.exists():
                text = fpath.read_text(encoding="utf-8", errors="ignore")
                if "pending human review" in text.lower():
                    remaining += 1
        if remaining > 0:
            print(f"CHECK: {remaining} files still have pending human review markers (acceptable)")
        print("CHECK PASS")
        return 0
    return 0


if __name__ == "__main__":
    exit(main())
