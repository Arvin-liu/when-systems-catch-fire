#!/usr/bin/env python3
"""Render and upsert the compiler-owned Current Snapshot block."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from tools.build_current_snapshot import build_snapshot
except ImportError:  # direct script / tools-on-PYTHONPATH execution
    from build_current_snapshot import build_snapshot


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
CONTRACT_PATH = ROOT / "data/operations/current-surface-block-contract-r1.json"
BLOCK_BEGIN_RE = re.compile(r"^<!-- CURRENT-SNAPSHOT:BEGIN profile=(human|ai|machine) schema=current-snapshot-r1 -->$")
BLOCK_END = "<!-- CURRENT-SNAPSHOT:END -->"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def _overlay_labels(snapshot: dict[str, Any]) -> str:
    return ", ".join(item["label"] for item in snapshot["active_architecture_overlays"])


def _count_summary(snapshot: dict[str, Any]) -> str:
    counts = snapshot["architecture_counts"]
    return "registry={registry_components}; visible_nodes={visible_map_nodes}; visible_edges={visible_typed_edges}".format(**counts)


def render_block(snapshot: dict[str, Any], profile: str) -> str:
    if profile not in {"human", "ai", "machine"}:
        raise ValueError(f"unknown Current Snapshot profile: {profile}")
    identity = snapshot["identity"]
    task = snapshot["current_task"]
    map_data = snapshot["map"]
    status = snapshot["engineering_status"]
    lineage = snapshot["task_lineage"]
    release = snapshot["release_lifecycle"]
    begin = f"<!-- CURRENT-SNAPSHOT:BEGIN profile={profile} schema=current-snapshot-r1 -->"
    if profile == "machine":
        lines = [
            begin,
            f"CURRENT_SNAPSHOT identity_epoch={identity['epoch']} system_role={json.dumps(identity['system_role'], ensure_ascii=False)} current_method_version={snapshot['current_method_version']} current_task_id={task['task_id']} current_task_status={task['execution_status']} current_task_terminal={str(task['terminal']).lower()} current_map_version={map_data['current_version']} historical_map_version={map_data['historical_versions'][0]} current_state_status={status['current_state_status']} epistemic_acceptance={status['epistemically_accepted']} live_external_ceiling={snapshot['live_external_ceiling']} release_phase={release['phase']} release_publication_state={release['publication_state']} release_task_branch_projection={release['task_branch_projection']} source_digest={snapshot['generated_from_source_digest']}",
            f"CURRENT_SNAPSHOT architecture_counts={json.dumps(snapshot['architecture_counts'], ensure_ascii=False, sort_keys=True)} overlays={json.dumps(_overlay_labels(snapshot), ensure_ascii=False)} lineage_current={lineage['current_task_id']} lineage_status={lineage['current_task_status']} lineage_predecessor_status={lineage['predecessor_status']} lineage_predecessor_requirement={lineage['predecessor_requirement_lineage']} lineage_successor_status={lineage['successor_status']}",
            f"CURRENT_SNAPSHOT claim_ceiling={json.dumps(snapshot['claim_ceiling'], ensure_ascii=False)}",
            BLOCK_END,
        ]
    else:
        label = "Current Snapshot（机器生成；请勿手改）" if profile == "human" else "Current Snapshot（generated; read this block before interpreting prose）"
        source_hint = "source: ignition/data/operations/current-snapshot-r1.json"
        lines = [
            begin,
            f"- {label}。",
            f"- current_identity_epoch: `{identity['epoch']}`；system_role: `{identity['system_role']}`。",
            f"- current_task: `{task['task_id']}`；status: `{task['execution_status']}`；terminal: `{str(task['terminal']).lower()}`；latest_architecture_changing_task: `{snapshot['latest_architecture_changing_task']}`。",
            f"- release_lifecycle: phase `{release['phase']}`；publication `{release['publication_state']}`；projection `{release['task_branch_projection']}`。",
            f"- current_method: `{snapshot['current_method_version']}` Current；current_map: `{map_data['current_version']}` Current；historical_map: `{map_data['historical_versions'][0]}` Historical。",
            f"- current_state_status: `{status['current_state_status']}`；EPISTEMICALLY_ACCEPTED={status['epistemically_accepted']}；epistemic_acceptance: `{status['epistemically_accepted']}`；live_external_ceiling: `{snapshot['live_external_ceiling']}`。",
            f"- architecture_counts: `{_count_summary(snapshot)}`；active_overlays: `{_overlay_labels(snapshot)}`。",
            f"- task_lineage: current `{lineage['current_task_id']}` `{lineage['current_task_status']}`；predecessor `{lineage['predecessor_status']}` / `{lineage['predecessor_requirement_lineage']}`；successor `{lineage['successor_status']}`。",
            f"- {source_hint}；source_digest: `{snapshot['generated_from_source_digest']}`。",
            f"- claim_ceiling: {snapshot['claim_ceiling']}",
            BLOCK_END,
        ]
    return "\n".join(lines) + "\n"


def replace_existing_block(text: str, block: str) -> tuple[str, bool]:
    pattern = re.compile(r"<!-- CURRENT-SNAPSHOT:BEGIN profile=(?:human|ai|machine) schema=current-snapshot-r1 -->\n.*?<!-- CURRENT-SNAPSHOT:END -->\n?", re.DOTALL)
    if pattern.search(text):
        return pattern.sub(block, text, count=1), True
    return text, False


def insert_block(text: str, block: str, surface: dict[str, Any]) -> str:
    updated, replaced = replace_existing_block(text, block)
    if replaced:
        return updated
    if surface.get("insert_before_first_heading"):
        match = re.search(r"^##\s+", updated, re.MULTILINE)
        if not match:
            raise ValueError(f"no H2 anchor for {surface['surface_id']}")
        return updated[:match.start()] + block + "\n" + updated[match.start():]
    if "insert_after" in surface:
        needle = surface["insert_after"]
        lines = updated.splitlines(keepends=True)
        for index, line in enumerate(lines):
            if needle in line:
                lines.insert(index + 1, block)
                return "".join(lines)
        raise ValueError(f"insert_after anchor not found for {surface['surface_id']}: {needle}")
    needle = surface["insert_before"]
    index = updated.find(needle)
    if index < 0:
        raise ValueError(f"insert_before anchor not found for {surface['surface_id']}: {needle}")
    line_start = updated.rfind("\n", 0, index) + 1
    return updated[:line_start] + block + "\n" + updated[line_start:]


def compile_surface(text: str, surface: dict[str, Any], snapshot: dict[str, Any] | None = None) -> str:
    return insert_block(text, render_block(snapshot or build_snapshot(), surface["profile"]), surface)


def extract_block(text: str) -> str | None:
    match = re.search(r"<!-- CURRENT-SNAPSHOT:BEGIN profile=(?:human|ai|machine) schema=current-snapshot-r1 -->\n.*?<!-- CURRENT-SNAPSHOT:END -->\n?", text, re.DOTALL)
    return match.group(0) if match else None


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--surface-id")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.surface_id:
        print("CURRENT_SURFACE_COMPILER_LIBRARY_READY")
        return 0
    contract = load_json(CONTRACT_PATH)
    surfaces = {row["surface_id"]: row for row in contract["surfaces"]}
    if args.surface_id not in surfaces:
        parser.error(f"unknown surface id: {args.surface_id}")
    surface = surfaces[args.surface_id]
    path = REPO_ROOT / surface["path"]
    source = path.read_text(encoding="utf-8")
    expected = compile_surface(source, surface)
    if args.write:
        path.write_text(expected, encoding="utf-8")
        print(f"CURRENT_SURFACE_WRITTEN surface={args.surface_id} path={surface['path']}")
        return 0
    if args.check:
        if source != expected:
            print(f"CURRENT_SURFACE_STALE surface={args.surface_id}", file=sys.stderr)
            return 1
        print(f"CURRENT_SURFACE_OK surface={args.surface_id}")
        return 0
    parser.error("choose --write or --check when --surface-id is supplied")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
