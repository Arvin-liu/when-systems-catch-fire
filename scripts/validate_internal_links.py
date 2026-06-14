#!/usr/bin/env python3
"""validate_internal_links.py — Check all internal markdown links resolve.

Usage:
  python3 scripts/validate_internal_links.py --check
"""

import argparse
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def find_all_links(text):
    """Find all markdown internal links [text](path)."""
    links = []
    # Match [text](path) patterns
    for m in re.finditer(r'\[([^\]]*)\]\(([^)]+)\)', text):
        path = m.group(2)
        # Skip external URLs
        if path.startswith('http') or path.startswith('mailto'):
            continue
        # Skip anchor-only links
        if path.startswith('#'):
            continue
        links.append(path)
    return links


def validate():
    """Validate all internal links in the repo."""
    broken = []
    total_links = 0
    scanned = 0

    # Collect all markdown files
    md_files = []
    for pattern in ["docs/**/*.md", "*.md", "data/**/*.md", "agent/**/*.md"]:
        md_files.extend(BASE.glob(pattern))

    for md_file in md_files:
        if ".git" in str(md_file):
            continue
        scanned += 1
        try:
            text = md_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        links = find_all_links(text)
        for link in links:
            total_links += 1
            # Resolve relative to the file's directory
            link_path = link.split("#")[0]  # Strip anchors
            resolved = (md_file.parent / link_path).resolve()
            if not resolved.exists():
                broken.append(f"{md_file.relative_to(BASE)}: {link}")

    return scanned, total_links, broken


def main():
    parser = argparse.ArgumentParser(description="Validate internal links")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    scanned, total, broken = validate()

    print(f"Scanned: {scanned} files, {total} internal links, {len(broken)} broken")
    for b in broken[:20]:
        print(f"  BROKEN: {b}")

    if args.check:
        if broken:
            print(f"CHECK FAIL: {len(broken)} broken links")
            return 1
        print("CHECK PASS: All internal links resolve")
        return 0
    return 0


if __name__ == "__main__":
    exit(main())
