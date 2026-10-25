#!/usr/bin/env python3
"""Run the checked-out Evidence Program validator on its fixed repository snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve()
IGNITION_ROOT = HERE.parents[1]
REPO_ROOT = IGNITION_ROOT.parent
EVIDENCE_ROOT_REL = "ignition/evidence-program"
VALIDATOR_REL = "ignition/evidence-program/tools/validate_evidence_program.py"
MAX_TREE_FILES = 4096
MAX_FAILURES_IN_RESULT = 100
SUMMARY_RE = re.compile(r"Total checks: (\d+) \| Failures: (\d+)")


class EvidenceProgramToolError(ValueError):
    """Raised when the fixed local validation run cannot be completed safely."""


def _checked_repo_path(relative_path: str) -> Path:
    root = REPO_ROOT.resolve()
    candidate = root
    for part in Path(relative_path).parts:
        if part in {".", ".."}:
            raise EvidenceProgramToolError("repository source path contains traversal")
        candidate = candidate / part
        if candidate.is_symlink():
            raise EvidenceProgramToolError("repository source path contains a symlink: " + relative_path)
    try:
        candidate.resolve().relative_to(root)
    except ValueError as exc:
        raise EvidenceProgramToolError("repository source path escapes the checkout") from exc
    if not candidate.exists():
        raise EvidenceProgramToolError("required repository source is unavailable: " + relative_path)
    return candidate


def _tree_digest(relative_path: str) -> dict[str, Any]:
    directory = _checked_repo_path(relative_path)
    if not directory.is_dir():
        raise EvidenceProgramToolError("Evidence Program source must be a directory")
    entries = []
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise EvidenceProgramToolError("Evidence Program tree contains a symlink")
        if path.is_file():
            entries.append({
                "path": path.relative_to(REPO_ROOT).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            })
            if len(entries) > MAX_TREE_FILES:
                raise EvidenceProgramToolError("Evidence Program tree exceeds the 4096-file limit")
    payload = json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "path": relative_path,
        "hash_kind": "SHA256_FILE_TREE_R0",
        "sha256": hashlib.sha256(payload).hexdigest(),
        "file_count": len(entries),
    }


def _git_root() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    if completed.returncode != 0:
        raise EvidenceProgramToolError("containing checkout could not be identified by local git")
    try:
        reported = Path(completed.stdout.strip()).resolve()
    except OSError as exc:
        raise EvidenceProgramToolError("local git returned an invalid checkout root") from exc
    if reported != REPO_ROOT.resolve():
        raise EvidenceProgramToolError("local git root differs from the expected Ignition checkout")
    return str(reported)


def build_validation_result() -> dict[str, Any]:
    """Validate only the fixed Evidence Program tree and report a compact result."""
    evidence_root = _checked_repo_path(EVIDENCE_ROOT_REL)
    validator = _checked_repo_path(VALIDATOR_REL)
    git_root = _git_root()
    tree_ref = _tree_digest(EVIDENCE_ROOT_REL)
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["GIT_TERMINAL_PROMPT"] = "0"
    completed = subprocess.run(
        [sys.executable, "-B", str(validator), "--root", str(evidence_root)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
        env=env,
    )
    if completed.returncode not in {0, 1}:
        raise EvidenceProgramToolError("validator exited unexpectedly: " + completed.stderr[-1000:])
    summary = SUMMARY_RE.search(completed.stdout)
    if summary is None:
        raise EvidenceProgramToolError("validator output did not contain a check summary")
    check_count, failure_count = int(summary.group(1)), int(summary.group(2))
    failure_rows = [line.strip() for line in completed.stdout.splitlines() if line.startswith("[FAIL]")]
    if "FAILURES:" in completed.stdout:
        failure_rows.extend(
            line.strip() for line in completed.stdout.split("FAILURES:", 1)[1].splitlines()
            if line.strip().startswith("-")
        )
    failure_rows = list(dict.fromkeys(failure_rows))
    truncated = max(0, len(failure_rows) - MAX_FAILURES_IN_RESULT)
    failure_rows = failure_rows[:MAX_FAILURES_IN_RESULT]
    return {
        "schema_version": "toolbox-evidence-program-validation-r0",
        "result_status": "ALL_CHECKS_PASSED" if completed.returncode == 0 and failure_count == 0 else "VALIDATION_FAILURES_PRESENT",
        "exit_code": completed.returncode,
        "check_count": check_count,
        "failure_count": failure_count,
        "failure_details": failure_rows,
        "failure_details_truncated": truncated,
        "local_git_root": git_root,
        "git_metadata_read_only": True,
        "evidence_program_tree": tree_ref,
        "validator_source": {
            "path": VALIDATOR_REL,
            "sha256": hashlib.sha256(validator.read_bytes()).hexdigest(),
        },
        "claim_ceiling": (
            "The fixed checked-out Evidence Program snapshot passed or failed the repository validator's schemas, "
            "recorded preregistration-order metadata, provenance fields, threshold equality, and metric-leakage checks. "
            "This does not authenticate source origins or prove that files were committed as claimed, validate scientific truth, "
            "or establish independent review or acceptance."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True, help="validate the fixed checked-out Evidence Program snapshot")
    parser.parse_args(argv)
    try:
        result = build_validation_result()
    except (OSError, EvidenceProgramToolError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as exc:
        print("EVIDENCE_PROGRAM_VALIDATION_NOT_AVAILABLE: %s" % exc, file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result["exit_code"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
