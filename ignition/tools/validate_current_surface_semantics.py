#!/usr/bin/env python3
"""Fail-closed semantic checks for compiler-owned Current Surface blocks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

try:
    from tools.build_current_snapshot import build_snapshot
    from tools.classify_current_surface import _section_kind, classify_text
    from tools.current_surface_compiler import CONTRACT_PATH, BLOCK_END, BLOCK_BEGIN_RE, render_block
except ImportError:  # direct script / tools-on-PYTHONPATH execution
    from build_current_snapshot import build_snapshot
    from classify_current_surface import _section_kind, classify_text
    from current_surface_compiler import CONTRACT_PATH, BLOCK_END, BLOCK_BEGIN_RE, render_block


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
REPORT_PATH = ROOT / "data/operations/iterations/135/step15-current-surface-semantic-gate-r1.json"

TASK_TOKEN_RE = re.compile(r"\b(?:IGNITION-[0-9A-Z-]+|Task\s*\d{2,3})\b", re.I)
VERSION_TOKEN_RE = re.compile(r"\b\d+\.\d+\.\d+\b")
CURRENT_WORD_RE = re.compile(r"(?:\bcurrent\b|当前|本轮)", re.I)
GENERATED_BLOCK_RE = re.compile(
    r"<!-- CURRENT-SNAPSHOT:BEGIN profile=(human|ai|machine) schema=current-snapshot-r1 -->\n.*?<!-- CURRENT-SNAPSHOT:END -->\n?",
    re.DOTALL,
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def _issue(kind: str, path: str, message: str, line: int | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"kind": kind, "path": path, "message": message}
    if line is not None:
        result["line"] = line
    return result


def _outside_rows(text: str, path: str, snapshot: dict[str, Any]) -> Iterable[dict[str, Any]]:
    classified = {row["line"]: row for row in classify_text(text, path, snapshot)}
    section_by_line: dict[int, str] = {}
    section_kind = "HISTORICAL" if path.endswith("ignition/STATE-CHANGELOG.md") else "CURRENT"
    for line_number, line in enumerate(text.splitlines(), start=1):
        heading = re.match(r"^#{1,6}\s+(.+)$", line.strip())
        if heading:
            section_kind = _section_kind(heading.group(1), section_kind, path)
        section_by_line[line_number] = section_kind
    in_generated = False
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if BLOCK_BEGIN_RE.match(stripped):
            in_generated = True
            continue
        if in_generated:
            if stripped == BLOCK_END:
                in_generated = False
            continue
        row = classified.get(line_number, {
            "path": path,
            "line": line_number,
            "classification": section_by_line.get(line_number, "CURRENT"),
            "matches": [],
            "text": line.strip(),
        })
        if row.get("text"):
            yield row


def _has_explicit_historical(row: dict[str, Any]) -> bool:
    return row["classification"] in {"HISTORICAL", "EXAMPLE", "QUOTED_OLD_TEXT"}


def _unmanaged_current_assertion(line: str, snapshot: dict[str, Any]) -> str | None:
    """Return a typed violation for a registry-managed fact copied into prose."""

    folded = line.casefold()
    current_task_id = snapshot["current_task"]["task_id"]
    current_map = snapshot["map"]["current_version"]
    historical_map = snapshot["map"]["historical_versions"][0]

    if re.search(r"(?:current|当前|本轮)\s*(?:task|任务)", line, re.I):
        match = TASK_TOKEN_RE.search(line)
        if match and match.group(0).casefold() != current_task_id.casefold():
            return "current_task_conflict"
        if match:
            return "unmanaged_current_task"

    if re.search(r"(?:latest\s+architecture[- ]changing\s+task|最新架构变更任务)", line, re.I):
        match = TASK_TOKEN_RE.search(line)
        if match:
            return "unmanaged_latest_architecture_task"

    if re.search(r"(?:current\s+identity|当前身份|identity_epoch)", line, re.I):
        if "epoch" in folded or snapshot["identity"]["epoch"] in line:
            return "unmanaged_identity_epoch"

    if re.search(r"(?:historical\s+map|历史地图)", line, re.I) and CURRENT_WORD_RE.search(line):
        return "historical_map_labeled_current"

    if re.search(r"(?:current\s+map|当前地图|current\s+version|当前版本)", line, re.I) and VERSION_TOKEN_RE.search(line):
        if current_map not in line or re.search(r"(?:historical\s+map|历史地图)", line, re.I):
            return "current_map_conflict"
        return "unmanaged_current_map"

    if re.search(r"(?:iteration\s+method|迭代方法|当前方法|current\s+method|方法\s*`?\d+\.\d+\.\d+)", line, re.I):
        if VERSION_TOKEN_RE.search(line) and CURRENT_WORD_RE.search(line):
            if "generated Current Snapshot" in line or "generated current snapshot" in line.casefold():
                return None
            if re.search(r"(?:historical|earlier|历史|更早)", line, re.I):
                return None
            return "unmanaged_current_method"

    if re.search(r"(?:current_state_status|CURRENT_WITH_OPEN_OBLIGATIONS|EPISTEMICALLY_ACCEPTED\s*=)", line):
        return "unmanaged_current_state"

    if re.search(r"architecture_counts|registry=\d+.*visible_(?:nodes|edges)", line, re.I):
        return "unmanaged_architecture_counts"

    if re.search(r"live_external_ceiling|NOT_RUN_LIVE_EXTERNAL_INVOCATION", line):
        return "unmanaged_live_external_ceiling"

    return None


def _authority_escalation(line: str) -> bool:
    if "Structural Governance Surface" not in line:
        return False
    if re.search(r"(?:grant|grants|becomes|is)\s+(?:Owner\s+)?authority|授予.*(?:权威|权限)|成为.*(?:权威|权限)", line, re.I):
        return not re.search(r"(?:not|cannot|不能|不授予|advisory|advisory-only|不改变|只提供)", line, re.I)
    return False


def validate_documents(
    documents: dict[str, str],
    *,
    snapshot: dict[str, Any] | None = None,
    surface_specs: list[dict[str, Any]] | None = None,
    require_blocks: bool = True,
) -> list[dict[str, Any]]:
    """Validate supplied documents; used by both the CLI and negative fixtures."""

    snapshot = snapshot or build_snapshot()
    contract = load_json(CONTRACT_PATH)
    specs = surface_specs or [row for row in contract["surfaces"] if row["path"] in documents]
    issues: list[dict[str, Any]] = []

    for surface in specs:
        path = surface["path"]
        profile = surface["profile"]
        text = documents.get(path)
        if text is None:
            if require_blocks:
                issues.append(_issue("missing_surface", path, "required Current surface is missing"))
            continue
        blocks = list(GENERATED_BLOCK_RE.finditer(text))
        if require_blocks and len(blocks) != 1:
            issues.append(_issue("generated_block_count", path, f"expected exactly one generated block, found {len(blocks)}"))
        if blocks:
            actual_profile = blocks[0].group(1)
            if actual_profile != profile:
                issues.append(_issue("generated_block_profile", path, f"expected profile={profile}, found profile={actual_profile}"))
            expected = render_block(snapshot, profile)
            if blocks[0].group(0) != expected:
                issues.append(_issue("generated_block_stale_or_edited", path, "generated block differs from canonical snapshot"))
        for row in _outside_rows(text, path, snapshot):
            if _has_explicit_historical(row):
                continue
            if _authority_escalation(row["text"]):
                issues.append(_issue("soft_governance_authority_escalation", path, "Structural Governance Surface is written as authority", row["line"]))
            assertion = _unmanaged_current_assertion(row["text"], snapshot)
            if assertion:
                issues.append(_issue(assertion, path, "registry-managed Current value appears outside the generated block", row["line"]))

    # The semantic gate is intentionally cross-surface: two blocks that each
    # look locally plausible but disagree are still a split brain.
    blocks_by_profile: dict[str, str] = {}
    for surface in specs:
        text = documents.get(surface["path"])
        if not text:
            continue
        match = GENERATED_BLOCK_RE.search(text)
        if match:
            profile = surface["profile"]
            previous = blocks_by_profile.get(profile)
            if previous is not None and previous != match.group(0):
                issues.append(_issue("cross_surface_block_mismatch", surface["path"], f"profile={profile} blocks disagree"))
            blocks_by_profile[profile] = match.group(0)
    return issues


def validate_repository() -> dict[str, Any]:
    snapshot = build_snapshot()
    contract = load_json(CONTRACT_PATH)
    documents = {
        surface["path"]: (REPO_ROOT / surface["path"]).read_text(encoding="utf-8")
        for surface in contract["surfaces"]
        if (REPO_ROOT / surface["path"]).is_file()
    }
    issues = validate_documents(documents, snapshot=snapshot, require_blocks=True)
    summaries = []
    for surface in contract["surfaces"]:
        text = documents.get(surface["path"], "")
        summaries.append({
            "surface_id": surface["surface_id"],
            "path": surface["path"],
            "profile": surface["profile"],
            "generated_block_count": len(GENERATED_BLOCK_RE.findall(text)),
            "issue_count": sum(1 for issue in issues if issue["path"] == surface["path"]),
        })
    return {
        "schema_version": "current-surface-semantic-gate-r1",
        "task_id": "IGNITION-20260822-135",
        "result": "VALID" if not issues else "INVALID",
        "issue_count": len(issues),
        "snapshot_source_digest": snapshot["generated_from_source_digest"],
        "surfaces": summaries,
        "issues": issues,
        "claim_ceiling": "Typed repository-local semantic consistency only; no authority, external truth, production readiness, Owner acceptance or epistemic upgrade.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = validate_repository()
    if args.write:
        REPORT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"CURRENT_SURFACE_SEMANTIC_GATE_WRITTEN path={relative(REPORT_PATH)} result={result['result']} issues={result['issue_count']}")
        return 0 if result["result"] == "VALID" else 1
    if result["result"] != "VALID":
        print("CURRENT_SURFACE_SEMANTIC_GATE_INVALID", file=sys.stderr)
        for issue in result["issues"]:
            print(f"- {issue}", file=sys.stderr)
        return 1
    print("CURRENT_SURFACE_SEMANTIC_GATE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
