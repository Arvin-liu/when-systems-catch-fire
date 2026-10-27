#!/usr/bin/env python3
"""Validate the stable five-component homepage content contract."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
HOMEPAGE_PATH = REPO_ROOT / ".github/README.md"
HEADING_RE = re.compile(r"^##\s+(\d+)\.\s+(.+?)\s*$")


def validate(text: str | None = None) -> list[str]:
    source = text if text is not None else HOMEPAGE_PATH.read_text(encoding="utf-8")
    components = []
    for line_number, line in enumerate(source.splitlines(), start=1):
        match = HEADING_RE.match(line)
        if match:
            components.append((int(match.group(1)), match.group(2), line_number))
    errors: list[str] = []
    if [number for number, _title, _line in components] != [1, 2, 3, 4, 5]:
        errors.append(
            "homepage must have exactly five sequential numbered top-level content components "
            f"(observed={[number for number, _title, _line in components]})"
        )
    if any(not title.strip() for _number, title, _line in components):
        errors.append("homepage top-level content component titles must be nonblank")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("HOMEPAGE_COMPONENTS_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("HOMEPAGE_COMPONENTS_OK count=5")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
