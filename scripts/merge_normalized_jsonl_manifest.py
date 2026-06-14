#!/usr/bin/env python3
"""
Merge/update manifest.json for Phase B normalized JSONL files.
Reads actual file contents and updates line counts + sha256 hashes.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE / "data" / "normalized-jsonl"


def sha256_file(path):
    try:
        h = hashlib.sha256()
        h.update(path.read_bytes())
        return h.hexdigest()[:16]
    except Exception:
        return ""


def count_lines(path):
    try:
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            return 0
        return len([l for l in content.split('\n') if l.strip()])
    except Exception:
        return 0


def main():
    parser = argparse.ArgumentParser(description="Merge manifest for Phase B JSONL")
    parser.add_argument("--check", action="store_true", help="Verify manifest consistency")
    args = parser.parse_args()

    # Collect all Phase B files
    phase_b_files = [
        "discoveries.jsonl",
        "predictions.jsonl",
        "answers.jsonl",
        "analytic-solutions.jsonl",
        "function-case-relations.jsonl",
        "object-classification-crosswalk.jsonl",
    ]

    # Also include core files if they exist (they may have been updated)
    core_files = ["functions.jsonl", "cases.jsonl"]

    files = []
    for fname in phase_b_files + core_files:
        fpath = OUTPUT_DIR / fname
        if fpath.exists():
            files.append({
                "path": f"data/normalized-jsonl/{fname}",
                "line_count": count_lines(fpath),
                "sha256": sha256_file(fpath),
            })

    manifest_path = OUTPUT_DIR / "manifest.json"

    if args.check:
        if not manifest_path.exists():
            print("CHECK FAILED: manifest.json not found")
            sys.exit(1)
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        files_raw = existing.get("files", [])
        if isinstance(files_raw, dict):
            existing_paths = set(files_raw.keys())
        elif isinstance(files_raw, list):
            existing_paths = {item.get("path", "") for item in files_raw}
        else:
            existing_paths = set()
        for f in files:
            if f["path"] not in existing_paths:
                print(f"CHECK FAILED: {f['path']} not in manifest")
                sys.exit(1)
        print(f"CHECK PASSED: manifest contains {len(existing_paths)} files")
        sys.exit(0)

    # Merge: update existing manifest or create new
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {"schema_version": "normalized-jsonl-v1", "generated_at": "", "files": []}
    else:
        manifest = {"schema_version": "normalized-jsonl-v1", "generated_at": "", "files": []}

    manifest["files"] = {f["path"]: f for f in files}

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"Manifest updated: {len(files)} files")
    for f in files:
        print(f"  {f['path']}: {f['line_count']} lines, sha256={f['sha256']}")


if __name__ == "__main__":
    main()
