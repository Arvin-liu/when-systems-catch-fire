#!/usr/bin/env python3
"""Build lineage-bound Archify snapshots for Task149 Step07.

The snapshot is deliberately derived from Ignition's authored overall
architecture source.  The interactive system map is recorded by the Step07
receipt as context-only evidence; it is not promoted into an Archify node or
edge by this adapter.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from tools.run_task149_archify_adapter import build_ir


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
ITERATION_DIR = ROOT / "data/operations/iterations/149"
DEFAULT_BEFORE_IR = ITERATION_DIR / "step07-archify-before-r0.json"
DEFAULT_AFTER_IR = ITERATION_DIR / "step07-archify-after-r0.json"

BEFORE_SHA = "a1a1d102c3cd2fa12fc962b648b0eea62d8097cf"
AFTER_SHA = "14c2595d796494286caf31378173fd9dd027edcf"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_path_for_checkout(checkout_root: Path, target: str) -> str | None:
    """Return a provider-safe Ignition-relative source path for a real file."""
    target_without_fragment = target.split("#", 1)[0].rstrip("/")
    if not target_without_fragment:
        return None
    ignition_candidate = checkout_root / "ignition" / target_without_fragment
    if ignition_candidate.is_file():
        return f"ignition/{target_without_fragment}"
    repository_candidate = checkout_root / target_without_fragment
    if repository_candidate.is_file():
        return target_without_fragment
    return None


def build_snapshot(
    architecture_path: Path,
    checkout_root: Path,
    revision: str,
) -> dict[str, Any]:
    """Build the same typed projection against a specific lineage checkout."""
    architecture = read_json(architecture_path)
    # build_ir supplies the pinned, already-reviewed geometry and semantic
    # projection.  Passing an empty map is safe because Step05's build_ir only
    # uses architecture data for the typed IR itself; the map is receipt
    # context, not visual truth.
    snapshot = build_ir(architecture, {}, revision)
    for node, component in zip(architecture["nodes"], snapshot["components"]):
        component.pop("sources", None)
        source_path = source_path_for_checkout(checkout_root, node["target"])
        if source_path:
            component["sources"] = [{"path": source_path, "label": "canonical target"}]
    snapshot["meta"]["output"] = "task149-archify-delta-derived"
    return snapshot


def write_snapshot(path: Path, architecture_path: Path, checkout_root: Path, revision: str) -> None:
    snapshot = build_snapshot(architecture_path, checkout_root, revision)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-snapshots", action="store_true")
    parser.add_argument("--before-root", type=Path, required=True)
    parser.add_argument("--after-root", type=Path, required=True)
    parser.add_argument("--before-architecture", type=Path, required=True)
    parser.add_argument("--after-architecture", type=Path, required=True)
    parser.add_argument("--before-ir", type=Path, default=DEFAULT_BEFORE_IR)
    parser.add_argument("--after-ir", type=Path, default=DEFAULT_AFTER_IR)
    args = parser.parse_args()
    if not args.write_snapshots:
        parser.error("--write-snapshots is required")
    if not args.before_root.is_dir() or not args.after_root.is_dir():
        parser.error("both checkout roots must be directories")
    write_snapshot(args.before_ir, args.before_architecture, args.before_root, BEFORE_SHA)
    write_snapshot(args.after_ir, args.after_architecture, args.after_root, AFTER_SHA)
    print(
        "TASK149_STEP07_ARCHIFY_SNAPSHOTS_WRITTEN "
        f"before={sha256(args.before_ir)} after={sha256(args.after_ir)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
