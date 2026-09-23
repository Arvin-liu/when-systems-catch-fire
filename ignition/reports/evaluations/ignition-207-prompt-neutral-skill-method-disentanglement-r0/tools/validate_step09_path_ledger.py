#!/usr/bin/env python3
"""Validate Task207 path accounting and no-projection/no-canonical boundaries."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
TASK_DIR = REPO_ROOT / "ignition/reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0"
TASK_PREFIX = TASK_DIR.relative_to(REPO_ROOT).as_posix() + "/"
BASE_COMMIT = "8e70ba196739cf1a79600e02ace36f90ad2c130c"
LEDGER = TASK_DIR / "provenance/path-accounting-r0.json"
SUMMARY = TASK_DIR / "provenance/path-accounting-r0.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL_TASK207_STEP09: {message}")


def verify_sidecar(path: Path, rel: str) -> None:
    sidecar = path.with_name(path.name + ".sha256")
    expected = f"{sha256(path)}  {rel}\n"
    require(sidecar.is_file() and sidecar.read_text(encoding="utf-8") == expected, f"sidecar mismatch: {rel}")


def main() -> int:
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    require(data.get("artifact_type") == "EVALUATION_EVIDENCE" and data.get("step") == "Step09", "wrong artifact type or step")
    require(data.get("base_commit") == BASE_COMMIT, "wrong exact base")
    require(data.get("task_root") == TASK_PREFIX.rstrip("/"), "wrong accounting root")
    require(data.get("canonical_claim_ids") == [] and data.get("canonical_promotion") == "NONE", "canonical evidence/promotion present")
    require(data.get("successor") == "NOT_RUN" and data.get("evaluator") == "NOT_RUN", "Successor/Evaluator ran")
    require(data.get("cross_model_execution") == "NOT_AUTHORIZED" and data.get("r1") == "NOT_AUTHORIZED", "authorization boundary changed")
    require(data.get("projection_generators_run") == [], "projection generator was run")
    projections = {row["target"]: row for row in data.get("downstream_projections", [])}
    require(projections.get("human-results", {}).get("required") is False, "human-results propagation required")
    require(projections.get("human-results", {}).get("disposition") == "NO_PROPAGATION_REQUIRED", "human-results disposition changed")
    require(len(data.get("paths", [])) == data.get("path_count_excluding_this_ledger_and_sidecars"), "path inventory count mismatch")
    seen = set()
    for row in data.get("paths", []):
        rel = row.get("path", "")
        require(rel.startswith(TASK_PREFIX), f"path escaped Task207 root: {rel}")
        require(rel not in seen, f"duplicate path: {rel}")
        seen.add(rel)
        path = REPO_ROOT / rel
        require(path.is_file() and not path.is_symlink(), f"accounted path missing/non-regular: {rel}")
        require(sha256(path) == row.get("sha256"), f"accounted hash mismatch: {rel}")
        require(path.stat().st_size == row.get("size_bytes"), f"accounted byte count mismatch: {rel}")
        require(row.get("artifact_type") == "EVALUATION_EVIDENCE", f"wrong path artifact type: {rel}")
        require(row.get("canonical_claim_ids") == [] and row.get("canonical_promotion") == "NONE", f"canonical path entry: {rel}")
        sidecar_rel = row.get("sha256_sidecar")
        if sidecar_rel is not None:
            sidecar_path = REPO_ROOT / sidecar_rel
            require(sidecar_path.is_file(), f"declared sidecar missing: {sidecar_rel}")
            sidecar_text = sidecar_path.read_text(encoding="utf-8")
            parts = sidecar_text.rstrip("\n").split("  ", 1)
            allowed_display_paths = {rel, path.relative_to(TASK_DIR).as_posix()}
            require(len(parts) == 2 and parts[0] == row["sha256"], f"declared sidecar digest mismatch: {sidecar_rel}")
            require(parts[1] in allowed_display_paths, f"declared sidecar path mismatch: {sidecar_rel}")

    changed = subprocess.run(["git", "diff", "--name-only", f"{BASE_COMMIT}...HEAD"], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    require(changed.returncode == 0, "cannot enumerate exact-base branch diff")
    changed_paths = [line for line in changed.stdout.splitlines() if line]
    require(all(path.startswith(TASK_PREFIX) for path in changed_paths), "branch changes include a path outside Task207 evaluation directory")
    require(not any("human-results/" in path or "foundation/" in path.lower() or "current" in path.lower() for path in changed_paths), "downstream/canonical projection path changed")

    self_meta = data.get("self_accounting", {})
    require(self_meta.get("ledger_sha256") == "PROTECTED_BY_DETACHED_SHA256_SIDECAR", "ledger self-hash rule changed")
    require(self_meta.get("summary_sha256") == "PROTECTED_BY_DETACHED_SHA256_SIDECAR", "summary self-hash rule changed")
    verify_sidecar(LEDGER, LEDGER.relative_to(REPO_ROOT).as_posix())
    verify_sidecar(SUMMARY, SUMMARY.relative_to(REPO_ROOT).as_posix())
    print(f"TASK207_STEP09_PATH_LEDGER_VALID: {len(seen)} hashed paths; no outside or canonical projection paths changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
