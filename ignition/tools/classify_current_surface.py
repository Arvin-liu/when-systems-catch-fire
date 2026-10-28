#!/usr/bin/env python3
"""Classify Current/Historical mentions without treating every old token as drift."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from tools.build_current_snapshot import build_snapshot
    from tools.current_surface_compiler import BLOCK_END, BLOCK_BEGIN_RE
except ImportError:  # direct script / tools-on-PYTHONPATH execution
    from build_current_snapshot import build_snapshot
    from current_surface_compiler import BLOCK_END, BLOCK_BEGIN_RE


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
REGISTRY_PATH = ROOT / "data/operations/current-volatile-fact-registry-r1.json"
CONTRACT_PATH = ROOT / "data/operations/current-surface-block-contract-r1.json"
REPORT_PATH = ROOT / "data/operations/iterations/130/step07-classification-report.json"

TASK_RE = re.compile(r"\b(?:IGNITION-[0-9A-Z-]+|Task\s*\d{2,3})\b", re.I)
VERSION_RE = re.compile(r"\b\d+\.\d+\.\d+\b")
CURRENT_MARKER_RE = re.compile(r"(?:\bcurrent\b|当前|本轮|当前任务|当前地图|current task|current map|current version)", re.I)
HISTORICAL_MARKER_RE = re.compile(r"(?:\bhistorical\b|历史|旧版|更早|上一版|predecessor|previous)", re.I)
EXAMPLE_MARKER_RE = re.compile(r"(?:example|fixture|示例|夹具)", re.I)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def _volatile_matches(line: str, snapshot: dict[str, Any]) -> list[str]:
    matches: list[str] = []
    if snapshot["identity"]["epoch"] in line:
        matches.append("current_identity_epoch")
    if snapshot["current_task"]["task_id"] in line or re.search(r"\bTask\s*\d{2,3}\b", line, re.I):
        matches.append("current_task_id")
    if any(token in line for token in ("CURRENT_WITH_OPEN_OBLIGATIONS", "EPISTEMICALLY_ACCEPTED")):
        matches.append("current_state_status")
    if VERSION_RE.search(line):
        matches.append("version_token")
    if any(token in line for token in ("COMPLETED_WITH_CLASSIFIED_RESIDUALS", "IN_PROGRESS", "terminal")):
        matches.append("current_task_status")
    return sorted(set(matches))


def _section_kind(heading: str, inherited: str, path: str) -> str:
    folded = heading.casefold()
    if any(token in folded for token in ("historical", "历史", "history", "旧任务", "旧版本")):
        return "HISTORICAL"
    if any(token in folded for token in ("example", "fixture", "示例", "夹具")):
        return "EXAMPLE"
    # STATE-CHANGELOG is append-only provenance.  Its dated/task entries are
    # historical context even when their prose says that a value was Current
    # at that earlier main transition; the generated block is handled before
    # this section state is consulted.
    if path.endswith("ignition/STATE-CHANGELOG.md") and inherited == "HISTORICAL":
        return "HISTORICAL"
    # A nested heading under an explicitly historical section does not reopen
    # a Current authority merely because the old heading used that vocabulary.
    if inherited in {"HISTORICAL", "EXAMPLE"}:
        return inherited
    if any(token in folded for token in ("current", "当前")):
        return "CURRENT"
    return inherited


def classify_text(text: str, path: str = "fixture", snapshot: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    snapshot = snapshot or build_snapshot()
    rows: list[dict[str, Any]] = []
    section_kind = "HISTORICAL" if path.endswith("ignition/STATE-CHANGELOG.md") else "CURRENT"
    in_fence = False
    in_generated = False
    generated_profile = None
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        begin = BLOCK_BEGIN_RE.match(stripped)
        if begin:
            in_generated = True
            generated_profile = begin.group(1)
            rows.append({"path": path, "line": line_number, "classification": "GENERATED_CURRENT", "profile": generated_profile, "matches": ["snapshot_block"]})
            continue
        if in_generated:
            rows.append({"path": path, "line": line_number, "classification": "GENERATED_CURRENT", "profile": generated_profile, "matches": _volatile_matches(line, snapshot)})
            if stripped == BLOCK_END:
                in_generated = False
                generated_profile = None
            continue
        heading = re.match(r"^#{1,6}\s+(.+)$", stripped)
        if heading:
            section_kind = _section_kind(heading.group(1), section_kind, path)
        matches = _volatile_matches(line, snapshot)
        if not matches:
            continue
        if in_fence:
            classification = "EXAMPLE"
        elif stripped.startswith(">") and (HISTORICAL_MARKER_RE.search(line) or matches):
            classification = "QUOTED_OLD_TEXT"
        elif section_kind == "EXAMPLE" or EXAMPLE_MARKER_RE.search(line):
            classification = "EXAMPLE"
        elif section_kind == "HISTORICAL" or (HISTORICAL_MARKER_RE.search(line) and not CURRENT_MARKER_RE.search(line)):
            classification = "HISTORICAL"
        elif CURRENT_MARKER_RE.search(line):
            classification = "CURRENT_ASSERTION"
        else:
            classification = "UNCLASSIFIED_VOLATILE"
        rows.append({"path": path, "line": line_number, "classification": classification, "matches": matches, "text": line.strip()})
    if in_generated:
        rows.append({"path": path, "line": len(text.splitlines()), "classification": "UNTERMINATED_GENERATED_BLOCK", "matches": []})
    return rows


def report() -> dict[str, Any]:
    snapshot = build_snapshot()
    contract = load_json(CONTRACT_PATH)
    surfaces = []
    for surface in contract["surfaces"]:
        path = REPO_ROOT / surface["path"]
        rows = classify_text(path.read_text(encoding="utf-8"), surface["path"], snapshot)
        surfaces.append({
            "surface_id": surface["surface_id"],
            "path": surface["path"],
            "profile": surface["profile"],
            "generated_block_count": sum(1 for row in rows if row["classification"] == "GENERATED_CURRENT" and "snapshot_block" in row.get("matches", [])),
            "classifications": rows,
        })
    return {
        "schema_version": "current-surface-classification-report-r1",
        "task_id": "IGNITION-20260821-130",
        "snapshot_source_digest": snapshot["generated_from_source_digest"],
        "surfaces": surfaces,
        "claim_ceiling": "Classification is repository-local parsing evidence; it does not infer external truth or authority."
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = report()
    if args.write:
        REPORT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"CURRENT_SURFACE_CLASSIFICATION_WRITTEN path={relative(REPORT_PATH)}")
        return 0
    bad = [row for surface in result["surfaces"] for row in surface["classifications"] if row["classification"] == "UNTERMINATED_GENERATED_BLOCK"]
    if bad:
        print("CURRENT_SURFACE_CLASSIFIER_INVALID", file=sys.stderr)
        for row in bad:
            print(f"- {row}", file=sys.stderr)
        return 1
    print("CURRENT_SURFACE_CLASSIFIER_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
