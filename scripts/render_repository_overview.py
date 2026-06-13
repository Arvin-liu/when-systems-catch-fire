#!/usr/bin/env python3
"""Render the README repository overview from live counts."""

from __future__ import annotations

import argparse
from pathlib import Path

from repository_overview_utils import readme_overview_matches, render_readme_overview

REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the README repository overview block.")
    parser.add_argument("--check", action="store_true", help="Validate the README overview block without changing it.")
    args = parser.parse_args()

    if args.check:
        if not readme_overview_matches(README):
            print("README overview block is out of date")
            return 1
        print("README overview block is up to date")
        return 0

    updated = render_readme_overview(README)
    current = README.read_text(encoding="utf-8")
    if updated != current:
        README.write_text(updated, encoding="utf-8", newline="\n")
    print("README overview block rendered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
