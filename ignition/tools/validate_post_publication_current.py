#!/usr/bin/env python3
"""Run the fresh-clone Current self-check used after main publication."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "tools"))

try:
    from tools import build_current_snapshot
    from tools import current_surface_compiler
    from tools import generate_current_facts
    from tools import validate_current_release_lifecycle as lifecycle
    from tools import validate_current_state_sync as state_sync
    from tools import validate_current_surface_semantics as semantics
    from tools import validate_current_task_lineage as task_lineage
except ImportError:  # direct execution from ignition/tools
    import build_current_snapshot
    import current_surface_compiler
    import generate_current_facts
    import validate_current_release_lifecycle as lifecycle
    import validate_current_state_sync as state_sync
    import validate_current_surface_semantics as semantics
    import validate_current_task_lineage as task_lineage


CONTRACT_PATH = ROOT / "data/operations/current-surface-block-contract-r1.json"
REPORT_PATH = ROOT / "data/operations/iterations/130/step10-post-publication-check-spec.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()


def run_checks(*, post_publication: bool = False, expected_sha: str | None = None) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    lifecycle_errors = lifecycle.validate()
    checks.append({"check": "release_lifecycle", "result": "PASS" if not lifecycle_errors else "FAIL", "errors": lifecycle_errors})
    errors.extend(lifecycle_errors)
    record = load_json(lifecycle.LIFECYCLE_PATH)
    if post_publication:
        if record["current_phase"] not in {"PREPARED_FOR_RELEASE", "POST_PUBLICATION_RECHECK"}:
            errors.append("post-publication check requires PREPARED_FOR_RELEASE or POST_PUBLICATION_RECHECK lifecycle")
        if not record["current_task_terminal"]:
            errors.append("post-publication check requires terminal Current task")
        if git("branch", "--show-current") != "main":
            errors.append("post-publication check must run on branch main")
        if expected_sha:
            actual_sha = git("rev-parse", "HEAD")
            if actual_sha != expected_sha:
                errors.append(f"remote main HEAD {actual_sha} differs from expected published SHA {expected_sha}")
    else:
        if record["current_phase"] not in {"RUNNING", "PREPARED_FOR_RELEASE"}:
            errors.append("pre-publication check requires RUNNING or PREPARED_FOR_RELEASE lifecycle")

    facts_errors = generate_current_facts.check()
    checks.append({"check": "current_facts", "result": "PASS" if not facts_errors else "FAIL", "errors": facts_errors})
    errors.extend(facts_errors)
    snapshot_errors = build_current_snapshot.check()
    checks.append({"check": "current_snapshot", "result": "PASS" if not snapshot_errors else "FAIL", "errors": snapshot_errors})
    errors.extend(snapshot_errors)

    contract = load_json(CONTRACT_PATH)
    compiler_errors: list[str] = []
    for surface in contract["surfaces"]:
        path = REPO_ROOT / surface["path"]
        if not path.is_file():
            compiler_errors.append(f"missing surface: {surface['path']}")
            continue
        source = path.read_text(encoding="utf-8")
        if source != current_surface_compiler.compile_surface(source, surface):
            compiler_errors.append(f"stale compiler output: {surface['surface_id']}")
    checks.append({"check": "current_surface_compiler", "result": "PASS" if not compiler_errors else "FAIL", "errors": compiler_errors})
    errors.extend(compiler_errors)

    semantic_result = semantics.validate_repository()
    semantic_errors = semantic_result["issues"]
    checks.append({"check": "typed_semantic_gate", "result": "PASS" if not semantic_errors else "FAIL", "errors": semantic_errors})
    errors.extend(str(item) for item in semantic_errors)

    lineage_errors = task_lineage.validate()
    checks.append({"check": "task_lineage", "result": "PASS" if not lineage_errors else "FAIL", "errors": lineage_errors})
    errors.extend(lineage_errors)
    sync_errors = state_sync.run_check()
    checks.append({"check": "current_state_sync", "result": "PASS" if not sync_errors else "FAIL", "errors": sync_errors})
    errors.extend(sync_errors)

    status = git("status", "--porcelain")
    if post_publication:
        if status:
            errors.append("fresh self-check working tree is not clean")
        checks.append({"check": "clean_worktree", "result": "PASS" if not status else "FAIL", "errors": [] if not status else [status]})
    else:
        checks.append({"check": "clean_worktree", "result": "NOT_APPLICABLE", "errors": ["clean clone is enforced only in post-publication mode"]})
    result = "PASS" if not errors else "FAIL"
    return {
        "schema_version": "post-publication-current-check-r1",
        "task_id": "IGNITION-20260821-130",
        "mode": "POST_PUBLICATION" if post_publication else "PRE_PUBLICATION",
        "result": result,
        "head_sha": git("rev-parse", "HEAD"),
        "branch": git("branch", "--show-current"),
        "expected_sha": expected_sha,
        "checks": checks,
        "errors": errors,
        "claim_ceiling": "Fresh-clone Current self-check is repository-local projection and release evidence only; it does not prove external truth, production readiness, Owner acceptance or epistemic acceptance."
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--pre-publication", action="store_true")
    mode.add_argument("--post-publication", action="store_true")
    parser.add_argument("--expected-sha")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    post = bool(args.post_publication)
    result = run_checks(post_publication=post, expected_sha=args.expected_sha)
    if args.write:
        REPORT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"POST_PUBLICATION_CURRENT_CHECK_WRITTEN path={REPORT_PATH.relative_to(REPO_ROOT)} result={result['result']}")
    if result["result"] != "PASS":
        print("POST_PUBLICATION_CURRENT_CHECK_INVALID", file=sys.stderr)
        for error in result["errors"]:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"POST_PUBLICATION_CURRENT_CHECK_OK mode={result['mode']} head={result['head_sha']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
