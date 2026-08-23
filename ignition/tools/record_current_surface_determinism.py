#!/usr/bin/env python3
"""Rebuild Current projections twice and record byte-level equality."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
REPORT_PATH = ROOT / "data/operations/iterations/136/step16-deterministic-current-surface-r1.json"
TASK_ID = "IGNITION-20260823-136"
REPORT_SCHEMA = "ignition-136-step16-deterministic-current-surface-r1"
OUTPUTS = [
    "ignition/data/architecture/current-facts.json",
    "ignition/docs/architecture/current-facts.md",
    "ignition/data/operations/current-snapshot-r1.json",
    "ignition/data/operations/current-release-lifecycle-r1.json",
    "ignition/data/operations/current-task-lineage-status.json",
    "ignition/data/operations/task-identity-model-r1.json",
    "ignition/data/operations/current-volatile-fact-registry-r1.json",
    "ignition/data/operations/iterations/136/execution-contract-r1.json",
    ".github/README.md",
    "ignition/docs/project-current-state.md",
    "ignition/AI-START-HERE.md",
    "ignition/AI-HANDOFF.md",
    "ignition/llms.txt",
    "ignition/ARCHITECTURE.md",
    "ignition/STATE-CHANGELOG.md"
]
SURFACES = ["homepage-identity", "project-current-state", "ai-cold-start", "ai-agents-handoff", "machine-entry", "architecture", "state-changelog"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hashes() -> dict[str, str]:
    return {path: sha256(REPO_ROOT / path) for path in OUTPUTS}


def rebuild() -> None:
    commands = [
        [sys.executable, "ignition/tools/generate_current_facts.py", "--write"],
        [sys.executable, "ignition/tools/build_current_snapshot.py", "--write"],
    ]
    commands.extend([sys.executable, "ignition/tools/current_surface_compiler.py", "--write", "--surface-id", surface] for surface in SURFACES)
    for command in commands:
        subprocess.run(command, cwd=REPO_ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def write_report() -> dict[str, Any]:
    rebuild()
    pass_one = hashes()
    rebuild()
    pass_two = hashes()
    result = {
        "schema_version": REPORT_SCHEMA,
        "task_id": TASK_ID,
        "result": "PASS" if pass_one == pass_two else "FAIL",
        "pass_1_sha256": pass_one,
        "pass_2_sha256": pass_two,
        "passes_equal": pass_one == pass_two,
        "output_count": len(OUTPUTS),
        "claim_ceiling": "Deterministic repository projection equality only; no authority, external truth, production readiness, Owner acceptance or epistemic acceptance is inferred."
    }
    REPORT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def check_report() -> list[str]:
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []
    if report.get("schema_version") != REPORT_SCHEMA:
        errors.append("determinism report schema is invalid")
    if report.get("task_id") != TASK_ID:
        errors.append("determinism report task id is invalid")
    if report.get("result") != "PASS" or report.get("passes_equal") is not True:
        errors.append("determinism report does not record two equal PASS hashes")
    current = hashes()
    if current != report.get("pass_2_sha256"):
        errors.append("current output hashes differ from recorded pass 2")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.write:
        result = write_report()
        print(f"CURRENT_SURFACE_DETERMINISM_WRITTEN path={REPORT_PATH.relative_to(REPO_ROOT)} result={result['result']} outputs={result['output_count']}")
        return 0 if result["result"] == "PASS" else 1
    errors = check_report()
    if errors:
        print("CURRENT_SURFACE_DETERMINISM_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("CURRENT_SURFACE_DETERMINISM_OK passes=2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
