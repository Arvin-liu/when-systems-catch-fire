#!/usr/bin/env python3
"""Normalize public attribution strings to the display name 之元.

This script updates explicit human-facing attribution text while preserving the
GitHub repository path and URL.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET_TEXT = "Arvin Liu"
REPLACEMENT_TEXT = "之元"

TEXT_FILES = [
    ROOT / "README.md",
    ROOT / "AGENT_ENTRY.md",
    ROOT / "llms.txt",
    ROOT / "LICENSE",
    ROOT / "LICENSE-SUMMARY.md",
    ROOT / "tools/build-function-items.py",
]


def normalize_text(path: Path) -> tuple[bool, str]:
    text = path.read_text(encoding="utf-8")
    if TARGET_TEXT not in text:
        return False, text
    return True, text.replace(TARGET_TEXT, REPLACEMENT_TEXT)


def normalize_json_items() -> list[Path]:
    changed: list[Path] = []
    items_dir = ROOT / "data/functions/items"
    for path in sorted(items_dir.glob("*.json")):
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        attribution = data.get("attribution")
        if not isinstance(attribution, dict):
            continue
        dirty = False
        for key in ("discoverer", "maintainer"):
            if attribution.get(key) == TARGET_TEXT:
                attribution[key] = REPLACEMENT_TEXT
                dirty = True
        if dirty:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            changed.append(path)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize public attribution display names.")
    parser.add_argument("--check", action="store_true", help="Validate attribution text without writing.")
    args = parser.parse_args()

    touched: list[Path] = []
    for path in TEXT_FILES:
        if not path.exists():
            continue
        changed, normalized = normalize_text(path)
        if changed:
            if not args.check:
                path.write_text(normalized, encoding="utf-8")
            touched.append(path)

    json_changed = normalize_json_items()
    touched.extend(json_changed)

    if args.check:
        if touched:
            print("Attribution normalization would change:")
            for path in touched:
                print(f"- {path.relative_to(ROOT).as_posix()}")
            return 1
        print("Attribution normalization check passed")
        return 0

    print(f"normalized attribution display name in {len(touched)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
