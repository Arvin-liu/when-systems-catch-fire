#!/usr/bin/env python3
"""Generic era resolver for change-propagation / diff-coverage / authority validation.

Replaces task- and SHA-special-cased constants (e.g. BASE_MAIN, Q32_ERA_REF) with a
single data-driven derivation:

  - base  : the PR base commit, taken from the iteration manifest
             (branch_pr.base_head, else verified_start.main_head).
  - era_ref: the frozen-era boundary commit for a *sealed/merged* iteration
             (branch_pr.merge_commit). For a *live* (unmerged) candidate iteration
             there is no sealed era, so era_ref is None and the caller should use the
             live diff window base..HEAD.

This keeps a sealed historical authority (Q25C/Q32/Q32I) bounded to its own merge
commit while letting a live task (Q33) validate against the current HEAD — without
any hardcoded task id or commit SHA in the production path.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


def _is_sha(value) -> bool:
    return isinstance(value, str) and len(value) == 40 and all(c in "0123456789abcdef" for c in value)


def resolve_era(repo_root: Path, task_id: str) -> Optional[dict]:
    """Return {'base': <sha>, 'era_ref': <sha-or-None>, 'task_id': task_id} or None.

    era_ref is the sealed merge commit for a merged iteration, else None (live).
    """
    manifest_path = repo_root / "data" / "operations" / "iterations" / f"{task_id}.json"
    if not manifest_path.exists():
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    branch_pr = manifest.get("branch_pr", {}) or {}
    verified = manifest.get("verified_start", {}) or {}

    base = branch_pr.get("base_head") or verified.get("main_head")
    if not _is_sha(base):
        return None

    merge = branch_pr.get("merge_commit")
    era_ref = merge if _is_sha(merge) else None
    return {"base": base, "era_ref": era_ref, "task_id": task_id}


def resolve_era_for_request(repo_root: Path, request: dict) -> Optional[dict]:
    """Resolve era from a propagation request by reading its task_id's manifest."""
    task_id = request.get("task_id")
    if not task_id:
        return None
    return resolve_era(repo_root, task_id)


def diff_window(repo_root: Path, task_id: str) -> tuple[str, Optional[str]]:
    """Return (base, era_ref) for a task, suitable for `git diff base..(era_ref or HEAD)`."""
    era = resolve_era(repo_root, task_id)
    if era is None:
        raise ValueError(f"No iteration manifest/era resolvable for task {task_id!r}")
    return era["base"], era["era_ref"]
