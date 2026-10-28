#!/usr/bin/env python3
"""Write an append-only artifact for the exact protected-main push result."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.operations.route_component_validation import (  # noqa: E402
    MAP_PATH,
    RoutingBlocked,
    build_exact_plan,
    digest_json,
    load_json,
)
from tools.operations.verify_component_validation_evidence import verify_evidence  # noqa: E402

SHA40 = re.compile(r"^[0-9a-f]{40}$")
ZERO_SHA = "0" * 40


def _git(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), *args], capture_output=True, text=True, check=False,
    )
    if completed.returncode:
        raise RoutingBlocked(f"git {' '.join(args[:2])} failed: {completed.stderr.strip()}")
    return completed.stdout.strip()


def _remote_main_sha(repo_root: Path) -> str:
    output = _git(repo_root, "ls-remote", "origin", "refs/heads/main")
    rows = [line.split() for line in output.splitlines() if line.strip()]
    if len(rows) != 1 or len(rows[0]) != 2 or rows[0][1] != "refs/heads/main":
        raise RoutingBlocked("origin must expose exactly one refs/heads/main SHA")
    return rows[0][0]


def create_witness(
    *, repo_root: Path, evidence_dir: Path, output_dir: Path, expected_sha: str,
    event_before: str, event_name: str, event_ref: str, mode: str,
    route_result: str, validate_result: str, full_result: str,
    run_id: str, run_attempt: str, remote_main_sha: str | None = None,
) -> dict[str, Any]:
    if not SHA40.fullmatch(expected_sha):
        raise RoutingBlocked("final main SHA must be an exact lowercase commit SHA")
    if event_name != "push" or event_ref != "refs/heads/main":
        raise RoutingBlocked("final-main witness is limited to a push event on refs/heads/main")
    if mode not in {"TARGETED", "FULL"}:
        raise RoutingBlocked("main validation mode is absent or invalid")
    if route_result != "success" or validate_result != "success":
        raise RoutingBlocked("route and combined validation jobs must both succeed")
    if mode == "FULL" and full_result != "success":
        raise RoutingBlocked("full Foundation regression did not succeed for this main push")

    head = _git(repo_root, "rev-parse", "HEAD")
    if head != expected_sha:
        raise RoutingBlocked("witness checkout HEAD does not match the exact push SHA")
    if _git(repo_root, "status", "--porcelain", "--untracked-files=all"):
        raise RoutingBlocked("witness checkout is dirty")
    remote_sha = remote_main_sha if remote_main_sha is not None else _remote_main_sha(repo_root)
    if remote_sha != expected_sha:
        raise RoutingBlocked("remote refs/heads/main moved away from this workflow's exact push SHA")

    if event_before == ZERO_SHA:
        before_sha: str | None = None
    elif SHA40.fullmatch(event_before):
        before_sha = event_before
        _git(repo_root, "rev-parse", "--verify", f"{before_sha}^{{commit}}")
    else:
        raise RoutingBlocked("push event before SHA must be exact or the all-zero initial-push marker")

    plan_path = evidence_dir / "component-validation-plan.json"
    receipt_path = evidence_dir / "component-validation-receipt.json"
    has_plan, has_receipt = plan_path.is_file(), receipt_path.is_file()
    if has_receipt and not has_plan:
        raise RoutingBlocked("main validation receipt is present without its exact plan")
    evidence: dict[str, Any] | None = None
    if has_plan:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        if has_receipt:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            evidence = verify_evidence(
                plan, receipt, expected_validation_sha=expected_sha, expected_mode=mode,
                repo_root=repo_root,
            )
            if plan["source"]["head_sha"] != expected_sha:
                raise RoutingBlocked("main validation plan head SHA is not the actual pushed main SHA")
        elif mode == "FULL" and full_result == "success" and before_sha is not None:
            recomputed_plan = build_exact_plan(repo_root, before_sha, expected_sha, expected_sha)
            if plan != recomputed_plan:
                raise RoutingBlocked("full-only plan differs from the exact main-push impact plan")
            source = plan.get("source")
            plan_body = dict(plan)
            plan_hash = plan_body.pop("plan_sha256", None)
            validation_map = load_json(MAP_PATH)
            assignments = {item["component_id"]: item for item in validation_map["components"]}
            closure = plan.get("affected_component_closure")
            changed_test_targets = plan.get("changed_validation_test_targets")
            selected_targets = plan.get("selected_target_ids")
            reasons = plan.get("full_regression_reasons")
            expected_targets: set[str] = set()
            if isinstance(closure, list):
                for component_id in closure:
                    assignment = assignments.get(component_id) if isinstance(component_id, str) else None
                    if assignment is not None:
                        expected_targets.update(assignment.get("validation_targets", []))
            if isinstance(changed_test_targets, list):
                expected_targets.update(item for item in changed_test_targets if isinstance(item, str))
            if (
                plan.get("schema_version") != "1.0.0"
                or plan.get("mode") != "FULL"
                or not isinstance(plan_hash, str)
                or not SHA40.fullmatch(expected_sha)
                or digest_json(plan_body) != plan_hash
                or not isinstance(source, dict)
                or source.get("base_sha") != before_sha
                or source.get("head_sha") != expected_sha
                or source.get("validation_sha") != expected_sha
                or plan.get("validation_map_sha256") != digest_json(validation_map)
                or not isinstance(selected_targets, list)
                or selected_targets != sorted(expected_targets)
                or bool(expected_targets)
                or not isinstance(closure, list)
                or not any(
                    isinstance(component_id, str)
                    and component_id in assignments
                    and assignments[component_id].get("requires_full_regression") is True
                    and not assignments[component_id].get("validation_targets")
                    for component_id in closure
                )
                or not isinstance(reasons, list)
                or not reasons
                or any(
                    not isinstance(reason, dict)
                    or not isinstance(reason.get("kind"), str)
                    or not reason["kind"]
                    or not (
                        (isinstance(reason.get("paths"), list) and bool(reason["paths"]))
                        or (isinstance(reason.get("component_id"), str) and bool(reason["component_id"]))
                    )
                    for reason in reasons
                )
            ):
                raise RoutingBlocked("full-only plan is not bound to this push, map, and a reviewed full-regression cause")
            evidence = {
                "validation_sha": expected_sha,
                "mode": "FULL",
                "plan_sha256": plan_hash,
                "receipt_sha256": None,
                "validation_map_sha256": plan["validation_map_sha256"],
                "selected_target_ids": [],
                "full_regression_reasons": reasons,
            }
        else:
            raise RoutingBlocked("main push requires a verified plan and target receipt or a reviewed full-only plan")
    elif mode != "FULL" or full_result != "success":
        raise RoutingBlocked("selected validation evidence is missing and there is no successful full-regression receipt")
    elif before_sha is not None:
        raise RoutingBlocked("normal main push is missing its exact component plan and target receipt")

    output_dir.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    if has_plan:
        shutil.copyfile(plan_path, output_dir / plan_path.name)
        copied.append(plan_path.name)
        if has_receipt:
            shutil.copyfile(receipt_path, output_dir / receipt_path.name)
            copied.append(receipt_path.name)
    witness: dict[str, Any] = {
        "schema_version": "final-main-witness-r1",
        "event_name": event_name,
        "event_ref": event_ref,
        "event_before_sha": before_sha,
        "final_main_sha": expected_sha,
        "remote_main_sha": remote_sha,
        "validation_mode": mode,
        "route_result": route_result,
        "validate_result": validate_result,
        "full_regression_result": full_result,
        "workflow_run_id": str(run_id),
        "workflow_run_attempt": str(run_attempt),
        "validation_evidence_files": copied,
        "validation_evidence": evidence,
        "claim_ceiling": "the GitHub push commit and repository validation evidence recorded by this workflow run",
    }
    (output_dir / "final-main-witness.json").write_text(
        json.dumps(witness, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    return witness


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--event-before", required=True)
    parser.add_argument("--event-name", required=True)
    parser.add_argument("--event-ref", required=True)
    parser.add_argument("--mode", required=True)
    parser.add_argument("--route-result", required=True)
    parser.add_argument("--validate-result", required=True)
    parser.add_argument("--full-result", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--run-attempt", required=True)
    args = parser.parse_args()
    try:
        witness = create_witness(
            repo_root=args.repo_root.resolve(), evidence_dir=args.evidence_dir.resolve(),
            output_dir=args.output_dir.resolve(), expected_sha=args.expected_sha,
            event_before=args.event_before, event_name=args.event_name, event_ref=args.event_ref,
            mode=args.mode, route_result=args.route_result, validate_result=args.validate_result,
            full_result=args.full_result, run_id=args.run_id, run_attempt=args.run_attempt,
        )
    except (OSError, json.JSONDecodeError, KeyError, TypeError, RoutingBlocked, ValueError) as exc:
        print(f"final-main witness rejected: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(witness, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
