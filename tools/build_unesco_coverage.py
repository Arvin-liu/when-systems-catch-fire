#!/usr/bin/env python3
"""Build a conservative UNESCO four-digit coverage ledger from explicit evidence."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

STATUS_ORDER = [
    "UNASSESSED",
    "NOT_TOUCHED",
    "CASE_ONLY",
    "METAPHOR_ONLY",
    "FUNCTION_PARTIAL",
    "THEORY_CORE_EXTRACTED",
    "EXTERNAL_EVIDENCE_PENDING",
    "COLLISION_VALIDATED",
    "NARRATIVE_READY",
]


@dataclass
class SourceRow:
    major_code: str
    discipline_name: str
    unesco_code: str
    main_theory: str
    classic_question: str
    open_question: str


def parse_source_table(path: Path) -> list[SourceRow]:
    rows: list[SourceRow] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| "):
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) != 6 or cols[0] == "大类":
            continue
        rows.append(
            SourceRow(
                major_code=cols[0].split()[0],
                discipline_name=cols[2],
                unesco_code=cols[1],
                main_theory=cols[3],
                classic_question=cols[4],
                open_question=cols[5],
            )
        )
    return rows


def load_evidence_map(path: Path) -> dict[str, dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {item["unesco_code"]: item for item in data.get("records", [])}


def build_record(row: SourceRow, evidence: dict[str, Any] | None, source_note: dict[str, str]) -> dict[str, Any]:
    if evidence:
        status = evidence["status"]
        evidence_refs = evidence.get("coverage_evidence", [])
        matched_function_ids = evidence.get("matched_function_ids", [])
        matched_case_ids = evidence.get("matched_case_ids", [])
        matched_collision_artifacts = evidence.get("matched_collision_artifacts", [])
        matched_story_artifacts = evidence.get("matched_story_artifacts", [])
        review_method = evidence.get("review_method", "explicit evidence mapping")
        search_terms = evidence.get("search_terms", [])
        theory_match = evidence.get("theory_match", "")
        counterevidence_or_limits = evidence.get("counterevidence_or_limits", "")
        review_reason = evidence.get("review_reason", "")
        confidence_basis = evidence.get("confidence_basis", "")
        next_action = evidence.get("next_action", "")
    else:
        status = "UNASSESSED"
        evidence_refs = []
        matched_function_ids = []
        matched_case_ids = []
        matched_collision_artifacts = []
        matched_story_artifacts = []
        review_method = "source inventory only; no explicit evidence mapping"
        search_terms = [row.discipline_name, row.unesco_code, row.main_theory]
        theory_match = ""
        counterevidence_or_limits = "No explicit repository evidence mapped in this pass."
        review_reason = "Inventory confirmed; coverage evidence not yet established."
        confidence_basis = "LOW: inventory only."
        next_action = "Keep UNASSESSED until a direct repository evidence mapping exists."

    return {
        "unesco_code": row.unesco_code,
        "discipline_name": row.discipline_name,
        "major_code": row.major_code,
        "inventory_source": {
            "type": "unesco_source_table",
            "note_id": source_note["note_id"],
            "title": source_note["title"],
            "path": source_note["path"],
        },
        "status": status,
        "review_method": review_method,
        "search_terms": search_terms,
        "coverage_evidence": evidence_refs,
        "matched_function_ids": matched_function_ids,
        "matched_case_ids": matched_case_ids,
        "matched_collision_artifacts": matched_collision_artifacts,
        "matched_story_artifacts": matched_story_artifacts,
        "theory_match": theory_match,
        "counterevidence_or_limits": counterevidence_or_limits,
        "review_reason": review_reason,
        "confidence_basis": confidence_basis,
        "next_action": next_action,
    }


def aggregate(records: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(r["status"] for r in records)
    touched = sum(1 for r in records if r["status"] != "UNASSESSED")
    by_major = defaultdict(lambda: Counter())
    for r in records:
        by_major[r["major_code"]][r["status"]] += 1
    return {
        "total_records": len(records),
        "touched_rows": touched,
        "status_counts": dict(counts),
        "major_summary": {k: dict(v) for k, v in sorted(by_major.items())},
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "---",
        "title: IGNITION 059 UNESCO coverage ledger",
        "task_id: IGNITION-20260709-059",
        "---",
        "# IGNITION 059 UNESCO coverage ledger",
        "",
        "This ledger is conservative and evidence-led.",
        "",
        f"- total records: {summary['total_records']}",
        f"- touched rows: {summary['touched_rows']}",
        f"- UNASSESSED: {summary['status_counts'].get('UNASSESSED', 0)}",
        "",
        "## Status counts",
    ]
    for status in STATUS_ORDER:
        lines.append(f"- {status}: {summary['status_counts'].get(status, 0)}")
    lines.extend([
        "",
        "## Notes",
        "- `UNASSESSED` means inventory confirmed, but no explicit repository evidence mapping was assigned in this pass.",
        "- `NOT_TOUCHED` remains available for future direct search results; this run does not force it.",
        "- All non-UNASSESSED rows must be backed by real coverage evidence.",
    ])
    return "\n".join(lines) + "\n"


def render_roadmap(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    return "\n".join(
        [
            "# IGNITION 059 next collision roadmap",
            "",
            f"- total rows reviewed from inventory: {summary['total_records']}",
            f"- rows with explicit coverage evidence in this pass: {summary['touched_rows']}",
            "- next step: manually map only those four-digit disciplines with direct function/case/collision/story anchors.",
            "- next step: keep the remainder UNASSESSED rather than inheriting major-level status.",
            "- next step: refresh the Get note copy with the corrected conservative wording.",
            "",
            "## Operating rule",
            "- inventory source is not coverage evidence.",
            "- summary is derived only from row-level records.",
        ]
    ) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--source-label", default=None)
    parser.add_argument("--evidence-map", required=True, type=Path)
    parser.add_argument("--json-out", required=True, type=Path)
    parser.add_argument("--md-out", required=True, type=Path)
    parser.add_argument("--roadmap-out", required=True, type=Path)
    args = parser.parse_args()

    source_rows = parse_source_table(args.source)
    if len(source_rows) != 250:
        raise SystemExit(f"expected 250 source rows, found {len(source_rows)}")
    evidence_map = load_evidence_map(args.evidence_map)
    source_note = json.loads(args.evidence_map.read_text(encoding="utf-8"))["source_note"]

    records = []
    seen = set()
    for row in source_rows:
        if row.unesco_code in seen:
            raise SystemExit(f"duplicate unesco_code: {row.unesco_code}")
        seen.add(row.unesco_code)
        records.append(build_record(row, evidence_map.get(row.unesco_code), source_note))

    payload = {
        "task_id": "IGNITION-20260709-059",
        "source": args.source_label or args.source.name,
        "evidence_map": str(args.evidence_map),
        "records": records,
        "summary": aggregate(records),
    }

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(payload), encoding="utf-8")
    args.roadmap_out.write_text(render_roadmap(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
