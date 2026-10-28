#!/usr/bin/env python3
"""Prove targeted fixture tests are independent of the caller's cwd.

The harness uses subprocess ``cwd=`` and an explicit ``PYTHONPATH``.  It never
changes the parent process cwd, so a passing result is evidence about the
runner boundary rather than a process-global side effect.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve()
APP_ROOT = HERE.parents[1]
REPO_ROOT = APP_ROOT.parent
RECEIPT_PATH = APP_ROOT / "data/operations/iterations/135/step04-cwd-path-resolution.json"
TARGETS = (
    "tests.test_change_propagation.ChangePropagationTests.test_a_method_version_change_reaches_front_doors_and_map",
    "tests.test_change_propagation.ChangePropagationTests.test_g_q29r_historical_acceptance_is_frozen_while_task114_revision_is_current",
    "tests.test_change_propagation.ChangePropagationTests.test_g4_symlink_escape_rejected",
    "tests.test_state_changelog.StateChangelogTests.test_missing_required_field_is_rejected",
    "tests.test_state_changelog.StateChangelogTests.test_broken_repository_link_is_rejected",
)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _environment(app_root: Path) -> dict[str, str]:
    environment = os.environ.copy()
    inherited = environment.get("PYTHONPATH")
    entries = [str(app_root)]
    if inherited:
        entries.extend(item for item in inherited.split(os.pathsep) if item)
    environment["PYTHONPATH"] = os.pathsep.join(entries)
    return environment


def _overlay_candidate(source_root: Path, target_root: Path) -> None:
    """Copy the candidate tree while leaving the clone's .git directory intact."""

    excluded_directories = {".git", ".cache", "__pycache__"}
    for raw_source_dir, directory_names, file_names in os.walk(source_root):
        source_dir = Path(raw_source_dir)
        relative = source_dir.relative_to(source_root)
        directory_names[:] = [name for name in directory_names if name not in excluded_directories]
        target_dir = target_root / relative
        target_dir.mkdir(parents=True, exist_ok=True)
        for name in file_names:
            if name.endswith(".pyc"):
                continue
            source_path = source_dir / name
            target_path = target_dir / name
            if source_path.is_symlink():
                if target_path.exists() or target_path.is_symlink():
                    if target_path.is_dir() and not target_path.is_symlink():
                        shutil.rmtree(target_path)
                    else:
                        target_path.unlink()
                target_path.symlink_to(os.readlink(source_path), target_is_directory=source_path.is_dir())
            else:
                shutil.copy2(source_path, target_path)


def _run_case(case_id: str, cwd: Path, app_root: Path, repository_kind: str) -> dict[str, Any]:
    command = [sys.executable, "-m", "unittest", *TARGETS]
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=_environment(app_root),
        check=False,
        capture_output=True,
        text=True,
    )
    combined = f"{completed.stdout}\n{completed.stderr}"
    tests_run = 5 if "Ran 5 tests" in combined else None
    failures = 0 if "FAILED" not in combined else 1
    errors = 0 if "ERROR" not in combined else 1
    skipped = 0 if "skipped=" not in combined else 1
    passed = completed.returncode == 0 and tests_run == 5 and failures == errors == skipped == 0 and "OK" in combined
    return {
        "case_id": case_id,
        "working_directory_kind": case_id,
        "application_root_kind": "fresh-clone/ignition" if repository_kind == "fresh-clone" else "formal-repository/ignition",
        "repository_root_kind": repository_kind,
        "command": command,
        "tests_run": tests_run,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
        "returncode": completed.returncode,
        "status": "PASS" if passed else "FAIL",
        "stdout_sha256": _sha256(completed.stdout),
        "stderr_sha256": _sha256(completed.stderr),
    }


def run_cases() -> list[dict[str, Any]]:
    rows = [
        _run_case("repository-root", REPO_ROOT, APP_ROOT, "formal-repository"),
        _run_case("ignition-root", APP_ROOT, APP_ROOT, "formal-repository"),
    ]
    with tempfile.TemporaryDirectory(prefix="ignition-135-cwd-") as temporary:
        rows.append(_run_case("temporary-cwd", Path(temporary), APP_ROOT, "formal-repository"))
        with tempfile.TemporaryDirectory(prefix="ignition-135-clone-") as clone_parent:
            clone = Path(clone_parent) / "fresh-clone"
            subprocess.run(
                ["git", "clone", "--no-local", str(REPO_ROOT), str(clone)],
                check=True,
                capture_output=True,
                text=True,
            )
            # The formal Step04 commit does not exist yet while this receipt is
            # being produced.  Keep the clone's independent .git database,
            # then overlay the candidate working tree so the fresh checkout
            # exercises the exact pending source changes without a second
            # commit or an amend.
            _overlay_candidate(REPO_ROOT, clone)
            clone_app = clone / "ignition"
            row = _run_case("fresh-clone", clone, clone_app, "fresh-clone")
            row["source_head_sha"] = _git(REPO_ROOT, "rev-parse", "HEAD")
            row["clone_head_sha"] = _git(clone, "rev-parse", "HEAD")
            row["head_match"] = row["source_head_sha"] == row["clone_head_sha"]
            if not row["head_match"]:
                row["status"] = "FAIL"
            rows.append(row)
    return rows


def build_receipt(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "ignition-135-step04-cwd-path-resolution-r1",
        "task_id": "IGNITION-20260822-135",
        "step": "04",
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "root_contract": {
            "application_root": "Path(__file__).resolve().parents[1]",
            "formal_repository_root": "application_root.parent",
            "subprocess_cwd": "explicit per case",
            "import_path": "explicit PYTHONPATH=application_root",
            "global_chdir": False,
        },
        "target_count_per_case": len(TARGETS),
        "cases": rows,
        "claim_ceiling": "Repository-local fixture and runner cwd/path resolution only; no external truth, production readiness, Owner acceptance or epistemic upgrade.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()

    rows = run_cases()
    receipt = build_receipt(rows)
    if args.write:
        RECEIPT_PATH.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if receipt["status"] != "PASS":
            print(json.dumps(receipt, ensure_ascii=False, indent=2), file=sys.stderr)
            return 1
        print(f"CWD_PATH_RESOLUTION_WRITTEN cases={len(rows)} tests_per_case={len(TARGETS)} path={RECEIPT_PATH.relative_to(REPO_ROOT)}")
    elif receipt["status"] != "PASS":
        print(json.dumps(receipt, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    else:
        print(f"CWD_PATH_RESOLUTION_OK cases={len(rows)} tests_per_case={len(TARGETS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
