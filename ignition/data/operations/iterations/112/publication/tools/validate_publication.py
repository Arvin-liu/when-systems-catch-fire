#!/usr/bin/env python3
"""Deterministic, bounded validator for the task-112 readable publication set."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[6]
REQUIRED = {
    "shelf": ROOT / "PUBLICATIONS/README.md",
    "volume": ROOT / "PUBLICATIONS/volumes/001-pointfire-after-one-hundred-iterations.md",
    "notes": ROOT / "PUBLICATIONS/notes/001-pointfire-research-notes.md",
    "panorama": ROOT / "PUBLICATIONS/what-pointfire-knows-now.md",
    "ledger": ROOT / "PUBLICATIONS/hundred-iteration-achievement-ledger.md",
}
AUDIT_FILES = (
    "R0_SOURCE_LOCK.json",
    "R0_FILE_MANIFEST.json",
    "R0_INTAKE_REPORT.md",
    "R0_ORIGINAL_OUTPUT_INDEX.md",
    "R0_COVERAGE_AUDIT.md",
    "R0_CLAIM_AUDIT.jsonl",
    "R0_NOTE_INDEPENDENCE_AUDIT.md",
    "R0_READER_TEST.md",
    "R0_REVISION_DECISION.md",
    "FINAL_CHAPTER_EVIDENCE_MAP.md",
    "FINAL_SOURCE_APPENDIX.md",
    "FINAL_GLOSSARY.md",
    "FINAL_REVISION_MAP.md",
    "EVIDENCE_FACTUAL_REVIEW.md",
    "ADVERSARIAL_REVIEW.md",
    "EDITORIAL_REVIEW.md",
    "REVIEW_DISPOSITION_MATRIX.md",
    "OUTPUT_ACCOUNTING.md",
    "UNRESOLVED_PUBLICATION_OBLIGATIONS.md",
    "PUBLICATION_MANIFEST.json",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def han_count(text: str) -> int:
    return len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", text))


def fail(message: str) -> None:
    raise SystemExit(f"PUBLICATION_VALIDATION_FAILED: {message}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-final", action="store_true")
    args = parser.parse_args()

    texts: dict[str, str] = {}
    for name, path in REQUIRED.items():
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            fail(f"missing or empty primary artifact: {path.relative_to(ROOT)}")
        texts[name] = path.read_text(encoding="utf-8")

    root_readme = texts["shelf"]
    root = (ROOT / "README.md").read_text(encoding="utf-8")
    if "PUBLICATIONS/README.md" not in root:
        fail("root README does not expose PUBLICATIONS/README.md")
    expected_shelf_links = (
        "volumes/001-pointfire-after-one-hundred-iterations.md",
        "notes/001-pointfire-research-notes.md",
        "what-pointfire-knows-now.md",
        "hundred-iteration-achievement-ledger.md",
    )
    for link in expected_shelf_links:
        if link not in root_readme:
            fail(f"shelf does not link to {link}")

    note_matches = re.findall(r"^### (N\d{2})｜", texts["notes"], flags=re.MULTILINE)
    if len(note_matches) < 60 or len(note_matches) != len(set(note_matches)):
        fail(f"note independence/rendered index heading check failed: {len(note_matches)}")
    index_path = ROOT / "PUBLICATIONS/notes/index.jsonl"
    if not index_path.is_file():
        fail("notes/index.jsonl is missing")
    index_records = [json.loads(line) for line in index_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(index_records) != len(note_matches):
        fail(f"note index count {len(index_records)} != rendered count {len(note_matches)}")
    if [record.get("note_id") for record in index_records] != note_matches:
        fail("note index order/identity does not match rendered volume")
    for field in ("question", "core_insight", "evidence", "boundary", "open_question"):
        if any(not record.get(field) for record in index_records):
            fail(f"note index has empty field: {field}")

    panorama_sections = {
        "supported": r"^## 一、20 项当前能够支持的认识$",
        "corrected": r"^## 二、20 项已纠正、撤回或降级的认识$",
        "unknown": r"^## 三、20 项尚未解决的问题$",
        "directions": r"^## 四、10 项最重要的后续研究方向$",
    }
    expected_counts = {"supported": 20, "corrected": 20, "unknown": 20, "directions": 10}
    for key, pattern in panorama_sections.items():
        if not re.search(pattern, texts["panorama"], flags=re.MULTILINE):
            fail(f"panorama section missing: {key}")
    section_starts = [m.start() for m in re.finditer(r"^## ", texts["panorama"], flags=re.MULTILINE)]
    for key, pattern in panorama_sections.items():
        start_match = re.search(pattern, texts["panorama"], flags=re.MULTILINE)
        start = start_match.start()
        end = next((position for position in section_starts if position > start), len(texts["panorama"]))
        block = texts["panorama"][start:end]
        count = len(re.findall(r"^\d+\. ", block, flags=re.MULTILINE))
        if count != expected_counts[key]:
            fail(f"panorama {key} count {count} != {expected_counts[key]}")

    ledger_count = len(re.findall(r"^### R0-\d{3}｜", texts["ledger"], flags=re.MULTILINE))
    if ledger_count != 80:
        fail(f"ledger entry count {ledger_count} != 80")
    output_classes = (
        "RESEARCH_RESULT",
        "CORRECTION_RESULT",
        "EMPIRICAL_OR_REPLICATION_RESULT",
        "THEORY_OR_FORMALIZATION_RESULT",
        "METHOD_RESULT",
        "INFRASTRUCTURE_ONLY",
        "MAINTENANCE_ONLY",
        "MIXED",
        "NO_RECOVERABLE_KNOWLEDGE_INCREMENT",
    )
    if not all(f"`{output_class}`" in texts["ledger"] for output_class in output_classes):
        fail("ledger does not expose all required output classes")

    audit_root = ROOT / "data/operations/iterations/112/publication"
    missing_audit = [name for name in AUDIT_FILES if not (audit_root / name).is_file()]
    if missing_audit:
        fail(f"missing audit files: {', '.join(missing_audit)}")
    manifest = json.loads((audit_root / "PUBLICATION_MANIFEST.json").read_text(encoding="utf-8"))
    if manifest.get("status") not in {"PUBLISHED_CURRENT", "PUBLISHED_WITH_EXPLICIT_LIMITATIONS"}:
        fail(f"publication manifest status is not publishable: {manifest.get('status')}")
    if manifest.get("review_state") != "COMPLETE":
        fail("publication manifest review_state is not COMPLETE")
    if args.require_final and manifest.get("task112_terminalization_state") != "TERMINAL_SUCCESS":
        fail("final validation requested but terminalization state is not TERMINAL_SUCCESS")
    for name, path in REQUIRED.items():
        expected_hash = manifest.get("artifacts", {}).get(name, {}).get("sha256")
        if expected_hash and expected_hash != sha256(path):
            fail(f"manifest hash mismatch for {name}")
        if "PUBLISHED_WITH_EXPLICIT_LIMITATIONS" not in texts[name]:
            fail(f"primary artifact lacks explicit publication status: {name}")

    if (ROOT / "data/operations/iterations/113").exists():
        fail("task 113 iteration directory exists")
    if (ROOT / "relay/tasks/113.md").exists():
        fail("task 113 control file exists")

    summary = {
        "status": "PASS",
        "primary": {
            name: {"characters": len(text), "han_characters": han_count(text), "sha256": sha256(REQUIRED[name])}
            for name, text in texts.items()
        },
        "notes": len(note_matches),
        "panorama": expected_counts,
        "ledger": ledger_count,
        "audit_files": len(AUDIT_FILES),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
