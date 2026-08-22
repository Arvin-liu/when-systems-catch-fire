#!/usr/bin/env python3
"""Run the repository's deterministic projection checks before full regression.

The default mode is read-only.  It derives repository/application roots from this
file, runs every declared validator from the application root, and fails closed if
any check is stale, any check mutates the tree, or ``--require-clean`` finds a dirty
tree.  ``--record`` is an explicit receipt-writing action; it is never implicit in
``--check``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
CONTRACT_PATH = ROOT / "data/operations/projection-preflight-r1.json"
SCHEMA_PATH = ROOT / "schemas/operations/projection-preflight-r1.schema.json"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git_output(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT)


def worktree_snapshot() -> dict[str, Any]:
    status = git_output("status", "--porcelain=v1", "--untracked-files=all")
    paths = [path for path in git_output("ls-files", "-z").split(b"\0") if path]
    digest = hashlib.sha256()
    for path_bytes in paths:
        path = path_bytes.decode("utf-8")
        digest.update(path_bytes)
        digest.update(b"\0")
        digest.update(hashlib.sha256((REPO_ROOT / path).read_bytes()).digest())
        digest.update(b"\0")
    return {
        "clean": not status,
        "status_sha256": sha256_bytes(status),
        "tracked_content_sha256": digest.hexdigest(),
        "tracked_path_count": len(paths),
    }


def load_contract() -> dict[str, Any]:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if contract.get("schema_version") != "projection-preflight-r1":
        raise ValueError("projection preflight contract schema is invalid")
    if contract.get("contract_id") != "GENERATED_OUTPUT_BEFORE_FULL_SUITE_INVARIANT":
        raise ValueError("projection preflight contract id is invalid")
    if contract.get("application_root") != "ignition" or contract.get("execution_cwd") != "ignition":
        raise ValueError("projection preflight root contract is invalid")
    commands = contract.get("commands")
    if not isinstance(commands, list) or not commands:
        raise ValueError("projection preflight command list is empty")
    seen: set[str] = set()
    for row in commands:
        if not isinstance(row, dict) or not row.get("id") or row.get("id") in seen:
            raise ValueError("projection preflight command ids must be unique")
        seen.add(row["id"])
        if row.get("read_only") is not True:
            raise ValueError(f"projection preflight command is not read-only: {row.get('id')}")
        argv = row.get("argv")
        if not isinstance(argv, list) or not argv or any(not isinstance(part, str) or not part for part in argv):
            raise ValueError(f"projection preflight argv is invalid: {row.get('id')}")
    return contract


def canonical_environment() -> dict[str, str]:
    env = os.environ.copy()
    paths = [str(ROOT), str(ROOT / "tests"), str(ROOT / "tools" / "foundation")]
    existing = env.get("PYTHONPATH")
    if existing:
        paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(paths)
    env.setdefault("PYTHONHASHSEED", "0")
    return env


def command_line(argv: list[str]) -> list[str]:
    return [sys.executable, *argv]


def run_checks(contract: dict[str, Any], selected: set[str] | None = None) -> dict[str, Any]:
    before = worktree_snapshot()
    results: list[dict[str, Any]] = []
    for row in contract["commands"]:
        if selected is not None and row["id"] not in selected:
            continue
        argv = command_line(row["argv"])
        started = time.monotonic()
        process = subprocess.run(
            argv,
            cwd=ROOT,
            env=canonical_environment(),
            capture_output=True,
            text=True,
            check=False,
        )
        elapsed = time.monotonic() - started
        results.append(
            {
                "id": row["id"],
                "category": row["category"],
                "argv": argv,
                "returncode": process.returncode,
                "status": "PASS" if process.returncode == 0 else "FAIL",
                "duration_seconds": round(elapsed, 3),
                "stdout_sha256": sha256_bytes(process.stdout.encode("utf-8")),
                "stderr_sha256": sha256_bytes(process.stderr.encode("utf-8")),
                "stdout_tail": process.stdout[-1200:],
                "stderr_tail": process.stderr[-1200:],
            }
        )
    after = worktree_snapshot()
    side_effect = (
        before["status_sha256"] != after["status_sha256"]
        or before["tracked_content_sha256"] != after["tracked_content_sha256"]
        or before["tracked_path_count"] != after["tracked_path_count"]
    )
    failed = [row["id"] for row in results if row["returncode"] != 0]
    return {
        "checks": results,
        "check_count": len(results),
        "failed_checks": failed,
        "projection_checks_pass": not failed and bool(results),
        "worktree_before": before,
        "worktree_after": after,
        "side_effect_detected": side_effect,
    }


def gate_admission(run: dict[str, Any], require_clean: bool) -> dict[str, Any]:
    clean_ok = (
        run["worktree_before"]["clean"]
        and run["worktree_after"]["clean"]
        if require_clean
        else True
    )
    result = "PASS" if run["projection_checks_pass"] and not run["side_effect_detected"] and clean_ok else "FAIL"
    return {
        "result": result,
        "release_admission": result == "PASS",
        "require_clean": require_clean,
        "clean_tree_gate_pass": clean_ok,
        "projection_checks_pass": run["projection_checks_pass"],
        "side_effect_detected": run["side_effect_detected"],
        "failed_checks": run["failed_checks"],
    }


def build_report(contract: dict[str, Any], run: dict[str, Any], gate: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "projection-preflight-r1",
        "contract_id": contract["contract_id"],
        "task_id": contract["task_id"],
        "result": gate["result"],
        "release_admission": gate["release_admission"],
        "claim_ceiling": contract["claim_ceiling"],
        **gate,
        "check_count": run["check_count"],
        "checks": run["checks"],
        "worktree_before": run["worktree_before"],
        "worktree_after": run["worktree_after"],
        "execution_policy": {
            "runner_root_derived_from": "ignition/tools/run_projection_preflight.py",
            "subprocess_cwd": "ignition",
            "check_mode_writes": False,
            "regeneration_is_explicit": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="run read-only projection checks")
    parser.add_argument("--require-clean", action="store_true", help="fail unless the tree is clean before and after checks")
    parser.add_argument("--only", action="append", help="run one declared check id; repeatable")
    parser.add_argument("--record", action="store_true", help="explicitly write the JSON receipt")
    parser.add_argument("--output", type=Path, help="receipt path used only with --record")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required; regeneration is intentionally a separate action")
    if args.output and not args.record:
        parser.error("--output requires --record")
    try:
        contract = load_contract()
        declared = {row["id"] for row in contract["commands"]}
        selected = set(args.only) if args.only else None
        if selected is not None and not selected.issubset(declared):
            unknown = ", ".join(sorted(selected - declared))
            parser.error(f"unknown check id: {unknown}")
        run = run_checks(contract, selected)
        gate = gate_admission(run, args.require_clean)
        report = build_report(contract, run, gate)
    except (OSError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        print(f"PROJECTION_PREFLIGHT_CONTRACT_ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if args.record:
        output = args.output or (ROOT / "data/operations/iterations/135/step02-projection-preflight.json")
        if not output.is_absolute():
            output = REPO_ROOT / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"PROJECTION_PREFLIGHT_RECEIPT_WRITTEN path={output.relative_to(REPO_ROOT)}")
    return 0 if gate["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
