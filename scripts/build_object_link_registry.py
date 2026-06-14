#!/usr/bin/env python3
"""build_object_link_registry.py — Build object-link-registry from repo sources.

Usage:
  python3 scripts/build_object_link_registry.py
  python3 scripts/build_object_link_registry.py --check
"""

import argparse
import json
import os
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DOCS_ZH = BASE / "docs" / "zh"
DATA = BASE / "data"

# Object class -> (id_pattern, docs path, items subpath, data json path)
OBJECT_SPECS = {
    "function": (re.compile(r"^(D\d+|T\d+)$"), DOCS_ZH / "functions" / "items", "data/functions/unified-functions.json"),
    "meta-function": (re.compile(r"^(MF-\d+)$"), DOCS_ZH / "functions" / "meta", "data/functions/meta-functions.json"),
    "case": (re.compile(r"^C-(\d+)$"), DOCS_ZH / "cases" / "items", "data/cases/unified-cases.json"),
    "discovery": (re.compile(r"^(DISC-\d+)$"), DOCS_ZH / "discoveries" / "items", "data/discoveries/unified-discoveries.json"),
    "prediction": (re.compile(r"^(PRED-\d+)$"), DOCS_ZH / "predictions" / "items", "data/predictions/unified-predictions.json"),
    "answer": (re.compile(r"^(ANS-\d+)$"), DOCS_ZH / "answers" / "items", "data/answers/unified-answers.json"),
    "analytic-solution": (re.compile(r"^(SOL-\d+)$"), DOCS_ZH / "analytic-solutions" / "items", "data/analytic-solutions/unified-analytic-solutions.json"),
}

LINK_DIR = BASE / "data" / "links"


def scan_markdown_ids(md_path):
    """Extract bare object IDs from a markdown file."""
    text = md_path.read_text(encoding="utf-8", errors="ignore")
    ids = set()
    for obj_class, (pattern, items_dir, data_json) in OBJECT_SPECS.items():
        for m in pattern.finditer(text):
            ids.add(m.group(0))
    # Also match bare Dnnn / Tnnn
    for m in re.finditer(r'(?<![`#])\b([DT]\d{2,})\b(?![`])', text):
        ids.add(m.group(1))
    return ids


def build_registry():
    """Scan all objects and build the link registry."""
    registry = {}
    orphans = []
    missing_pages = []

    for obj_class, (pattern, items_dir, data_json) in OBJECT_SPECS.items():
        # Scan items directory for actual files
        if items_dir.exists():
            for f in sorted(items_dir.glob("*.md")):
                obj_id = f.stem  # e.g. D1, SOL-0001
                if pattern.match(obj_id):
                    # Compute relative link path from root
                    rel_path = str(f.relative_to(BASE))
                    # Try to extract title from first heading
                    title = ""
                    first_line = f.read_text(encoding="utf-8", errors="ignore").split("\n", 5)[0]
                    title_match = re.match(r"^#\s+(.+?)(?:\s*/\s*.+)?$", first_line)
                    if title_match:
                        title = title_match.group(1).strip()
                    # Separate zh/en titles if possible
                    zh_title = ""
                    en_title = ""
                    if "/" in title:
                        parts = title.split("/", 1)
                        zh_title = parts[0].strip()
                        en_title = parts[1].strip()
                    else:
                        zh_title = title

                    link_text = zh_title if zh_title else obj_id

                    registry[obj_id] = {
                        "id": obj_id,
                        "object_class": obj_class,
                        "title_zh": zh_title,
                        "title_en": en_title,
                        "canonical_path": str(f.relative_to(BASE)),
                        "exists": True,
                        "link_text": link_text,
                    }

    # Check for orphan references in all markdown files
    referenced_ids = set()
    md_files = list(BASE.rglob("*.md"))
    for md in md_files:
        if ".git" in str(md):
            continue
        ids = scan_markdown_ids(md)
        referenced_ids.update(ids)

    # Report orphans (referenced but not found)
    for rid in referenced_ids:
        if rid not in registry:
            # Check if it's a known pattern
            is_known = False
            for pattern, _, _ in OBJECT_SPECS.values():
                if pattern.match(rid):
                    is_known = True
                    break
            if is_known:
                missing_pages.append(rid)

    return registry, list(referenced_ids), missing_pages


def write_registry(registry, references, missing_pages):
    """Write registry to JSON, JSONL, and Markdown formats."""
    LINK_DIR.mkdir(parents=True, exist_ok=True)

    # JSON
    json_path = LINK_DIR / "object-link-registry.json"
    json_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    # JSONL
    jsonl_path = LINK_DIR / "object-link-registry.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as f:
        for obj_id in sorted(registry.keys()):
            f.write(json.dumps(registry[obj_id], ensure_ascii=False) + "\n")

    # Markdown
    md_path = LINK_DIR / "object-link-registry.md"
    lines = [
        "# Object Link Registry",
        "",
        f"**Total objects registered**: {len(registry)}",
        f"**Missing pages** (referenced but no file): {len(missing_pages)}",
        "",
        "| ID | Class | Link Text | Path |",
        "|----|-------|-----------|------|",
    ]
    for obj_id in sorted(registry.keys()):
        r = registry[obj_id]
        lines.append(f"| [{obj_id}]({r['canonical_path']}) | {r['object_class']} | {r['link_text']} | {r['canonical_path']} |")
    if missing_pages:
        lines.append("")
        lines.append("### Missing Pages")
        for mp in sorted(missing_pages):
            lines.append(f"- {mp} (referenced but page not found)")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Build object link registry")
    parser.add_argument("--check", action="store_true", help="Only check registry exists")
    args = parser.parse_args()

    registry, references, missing_pages = build_registry()
    write_registry(registry, references, missing_pages)

    print(f"Registry built: {len(registry)} objects, {len(references)} referenced, {len(missing_pages)} missing pages")

    if args.check:
        # Validate registry consistency
        json_path = LINK_DIR / "object-link-registry.json"
        if json_path.exists():
            with json_path.open() as f:
                check_data = json.load(f)
            if len(check_data) != len(registry):
                print(f"CHECK FAIL: registry file has {len(check_data)} but rebuilt has {len(registry)}")
                return 1
            print("CHECK PASS: registry consistent")
        else:
            print("CHECK FAIL: registry file missing")
            return 1
    return 0


if __name__ == "__main__":
    exit(main())
