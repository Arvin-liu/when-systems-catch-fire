#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "data" / "publication-atlas-20260712.json"
REPORT_MD = ROOT / "outputs" / "publication-atlas-20260712" / "coverage-ledger.md"
REPORT_JSON = ROOT / "outputs" / "publication-atlas-20260712" / "coverage-ledger.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    atlas = json.loads(ATLAS.read_text())
    dirs = atlas["directions"]
    refs = [ref for d in dirs for ref in d["evidence"]]
    ref_counts = Counter(refs)

    scanned_dirs = [
        "统一函数总表",
        "统一案例总表",
        "新故事",
        "outputs/collisions",
        "outputs/book-collisions",
        "outputs/research",
        "outputs/stories",
        "data/meta-protocols",
    ]
    file_counts = {}
    for rel in scanned_dirs:
        base = ROOT / rel
        file_counts[rel] = sum(1 for p in base.rglob("*") if p.is_file()) if base.exists() else 0

    report = {
        "atlas_id": atlas["atlas_id"],
        "direction_count": len(dirs),
        "unique_evidence_refs": len(ref_counts),
        "evidence_ref_total": len(refs),
        "evidence_refs": dict(sorted(ref_counts.items())),
        "scanned_file_counts": file_counts,
        "source_sha256": sha256(ATLAS),
        "story_57_note_id": atlas["story_57"]["note_id"],
        "license_split": atlas["licenses"],
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")

    md = [
        "# 070 publication atlas coverage ledger",
        "",
        f"- atlas_id: `{atlas['atlas_id']}`",
        f"- direction_count: `{len(dirs)}`",
        f"- unique_evidence_refs: `{len(ref_counts)}`",
        f"- evidence_ref_total: `{len(refs)}`",
        f"- source_sha256: `{report['source_sha256']}`",
        f"- story_57_note_id: `{atlas['story_57']['note_id']}`",
        "",
        "## Scanned file counts",
    ]
    for rel, count in file_counts.items():
        md.append(f"- {rel}: `{count}`")
    md += ["", "## Evidence refs"]
    for ref, count in sorted(ref_counts.items()):
        md.append(f"- {ref}: `{count}`")
    REPORT_MD.write_text("\n".join(md) + "\n")


if __name__ == "__main__":
    main()
