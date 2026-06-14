#!/usr/bin/env python3
"""validate_related_object_links.py — Check Related Objects sections have valid links.

Usage:
  python3 scripts/validate_related_object_links.py --check
"""

import argparse
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
LINK_DIR = BASE / "data" / "links"


def load_registry():
    path = LINK_DIR / "object-link-registry.json"
    if path.exists():
        with path.open() as f:
            return json.load(f)
    return {}


def validate():
    registry = load_registry()
    issues = []
    scanned = 0

    # Scan all item pages for Related Objects sections
    for base_dir in ["docs/zh/functions/items", "docs/zh/cases/items", "docs/zh/effects/items",
                      "docs/zh/analytic-solutions/items", "docs/zh/discoveries/items",
                      "docs/zh/predictions/items", "docs/zh/answers/items"]:
        dir_path = BASE / base_dir
        if not dir_path.exists():
            continue
        for md_file in dir_path.glob("*.md"):
            scanned += 1
            try:
                text = md_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            # Find Related Objects section
            in_related = False
            for i, line in enumerate(text.split("\n"), 1):
                if re.match(r'^##\s*(?:相关对象|Related Objects)', line, re.IGNORECASE):
                    in_related = True
                    continue
                if in_related:
                    if line.startswith("## "):
                        in_related = False
                        continue
                    # Check for bare IDs in bullets
                    m = re.match(r'^\s*[-*•]\s+([A-Z]{1,4}[\d-]+)\s*$', line)
                    if m:
                        obj_id = m.group(1)
                        if obj_id not in registry:
                            issues.append(f"{md_file.relative_to(BASE)}:{i}: bare ID {obj_id} not in registry")
                    # Check for linked IDs that might have wrong paths
                    for lm in re.finditer(r'\[([^\]]*)\]\(([^)]+)\)', line):
                        link_path = lm.group(2).split("#")[0]
                        if link_path and not link_path.startswith('http'):
                            resolved = (md_file.parent / link_path).resolve()
                            if not resolved.exists():
                                issues.append(f"{md_file.relative_to(BASE)}:{i}: broken link ({link_path})")

    return scanned, len(issues), issues


def main():
    parser = argparse.ArgumentParser(description="Validate related object links")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    scanned, issue_count, issues = validate()
    print(f"Scanned: {scanned} files, {issue_count} issues")
    for issue in issues[:20]:
        print(f"  ISSUE: {issue}")

    if args.check:
        if issues:
            print(f"CHECK FAIL: {len(issues)} issues")
            return 1
        print("CHECK PASS: All related object links valid")
        return 0
    return 0


if __name__ == "__main__":
    exit(main())
