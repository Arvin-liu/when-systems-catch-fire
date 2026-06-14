#!/usr/bin/env python3
"""Apply the repository-wide academic novelty gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "data/novelty-gate"
REPORT_JSON = OUT_DIR / "universal-academic-novelty-report.json"
REPORT_MD = OUT_DIR / "universal-academic-novelty-report.md"
EXISTING_JSON = OUT_DIR / "existing-references.json"
EXISTING_JSONL = OUT_DIR / "existing-references.jsonl"
REBUILD_JSON = REPO_ROOT / "data/rebuild/universal-academic-novelty-gate-report.json"
REBUILD_MD = REPO_ROOT / "data/rebuild/universal-academic-novelty-gate-report.md"


def read_json(path: Path, default):
    if not path.exists():
        return default
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return default
    return json.loads(text)


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, payloads: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for item in payloads:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def scan_layer(path: Path) -> list[dict]:
    return read_json(path, [])


def novelty_of(item: dict) -> str:
    return item.get("academic_novelty", {}).get("status") or "pending"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the universal academic novelty gate.")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    layers = {
        "analytic_solutions": scan_layer(REPO_ROOT / "data/analytic-solutions/unified-analytic-solutions.json"),
        "discoveries": scan_layer(REPO_ROOT / "data/discoveries/unified-discoveries.json"),
        "predictions": scan_layer(REPO_ROOT / "data/predictions/unified-predictions.json"),
        "answers": scan_layer(REPO_ROOT / "data/answers/unified-answers.json"),
    }

    counts = {
        "claimed_new_scanned": sum(len(items) for items in layers.values()),
        "passed": 0,
        "failed": 0,
        "pending": 0,
        "inconclusive": 0,
    }
    existing_refs = []
    for layer_name, items in layers.items():
        for item in items:
            status = item.get("status", "")
            novelty = novelty_of(item)
            if status == "active":
                counts[novelty if novelty in counts else "pending"] += 1
            if novelty in {"failed", "pending", "inconclusive"}:
                existing_refs.append(
                    {
                        "layer": layer_name,
                        "id": item.get("id"),
                        "status": status,
                        "novelty": novelty,
                    }
                )
            elif novelty == "passed":
                counts["passed"] += 1

    report = {
        "generated_at": "",
        "claimed_new_scanned": counts["claimed_new_scanned"],
        "novelty_passed": counts["passed"],
        "novelty_failed": counts["failed"],
        "novelty_pending": counts["pending"],
        "novelty_inconclusive": counts["inconclusive"],
        "active_items_without_passed_novelty": [
            {"layer": layer_name, "id": item.get("id"), "novelty": novelty_of(item)}
            for layer_name, items in layers.items()
            for item in items
            if item.get("status") == "active" and novelty_of(item) != "passed"
        ],
        "existing_references_count": len(existing_refs),
    }

    if args.check:
        if report["active_items_without_passed_novelty"]:
            print("Active items without passed novelty:", json.dumps(report["active_items_without_passed_novelty"], ensure_ascii=False))
            return 1
        print("Academic novelty gate check passed")
        return 0

    if args.dry_run:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    write_json(REPORT_JSON, report)
    write_text(
        REPORT_MD,
        "\n".join(
            [
                "# Universal Academic Novelty Gate Report",
                "",
                f"- Claimed new scanned: {report['claimed_new_scanned']}",
                f"- Passed: {report['novelty_passed']}",
                f"- Failed: {report['novelty_failed']}",
                f"- Pending: {report['novelty_pending']}",
                f"- Inconclusive: {report['novelty_inconclusive']}",
                f"- Active items without passed novelty: {len(report['active_items_without_passed_novelty'])}",
                f"- Existing references: {report['existing_references_count']}",
            ]
        )
        + "\n",
    )
    write_json(REBUILD_JSON, report)
    write_text(REBUILD_MD, "\n".join(["# Universal Academic Novelty Gate Report", "", f"- Claimed new scanned: {report['claimed_new_scanned']}", f"- Active items without passed novelty: {len(report['active_items_without_passed_novelty'])}"]) + "\n")
    write_json(EXISTING_JSON, existing_refs)
    write_jsonl(EXISTING_JSONL, existing_refs)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
