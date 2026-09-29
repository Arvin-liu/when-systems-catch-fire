#!/usr/bin/env python3
"""Fail-closed Task229 gate; consumes verified GitHub evidence without opening targets."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PREREG = HERE.parent
REPO = PREREG.parents[3]
PARENT_SHA = "d82a52077df6d4e96e998ace3757f2fb343b4db5"
TASK228_BRANCH = "work/IGNITION-20260929-228-policy-contract-reconciliation-r0"
TASK228_SUMS_SHA = "864c4b91dc12b7f3166d1f0101b8e4dc300551fd4e83f28bb9e1be96a0312538"
TASK225_FREEZE_SHA = "f6201ea25d3614af34ef05d36cc8f620a8c149902fcef8937d259445b0b302a8"
TASK227_FREEZE_SHA = "91a33c38f209b88644ef473c21a133463bf7839d1bd5afc9c1507b88d128b7ec"
REQUIRED_WORKFLOWS = {
    "architecture-pages",
    "repository-path-accounting-preflight",
    "q33-governance-validation",
    "foundation-validation",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fail(message: str):
    raise SystemExit(f"TASK229_TARGET_OPENING_GATE=FAIL {message}")


def read_json(path: pathlib.Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"cannot parse {path}: {exc}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True, type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, default=PREREG / "run/target-opening-gate-receipt.json")
    args = parser.parse_args()
    evidence = read_json(args.evidence)

    freeze_check = subprocess.run(
        [sys.executable, str(HERE / "freeze_manifest.py"), "--check"],
        cwd=REPO, capture_output=True, text=True
    )
    if freeze_check.returncode != 0:
        fail("frozen preregistration verification failed")
    freeze_path = PREREG / "freeze-manifest.json"
    freeze_sha = digest(freeze_path.read_bytes())
    if evidence.get("freeze_manifest_sha256") != freeze_sha:
        fail("live evidence is not bound to the frozen manifest")

    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    parent = subprocess.run(["git", "rev-parse", "HEAD^"], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    if head != evidence.get("task229_head_sha") or parent != PARENT_SHA or evidence.get("task229_head_parent") != PARENT_SHA:
        fail("committed exact head or Task228 parent mismatch")
    if evidence.get("task229_branch") != "work/IGNITION-20260929-229-transfer-interface-clean-r0":
        fail("Task229 branch identity mismatch")

    pr = evidence.get("task229_pr", {})
    if pr.get("state") != "open" or pr.get("draft") is not True or pr.get("merged") is not False:
        fail("Task229 PR must be OPEN + DRAFT + UNMERGED")
    if pr.get("head_sha") != head or pr.get("base_ref") != TASK228_BRANCH or pr.get("base_sha") != PARENT_SHA:
        fail("Task229 PR head/base binding mismatch")

    workflows = evidence.get("workflow_runs", [])
    found = {}
    for run in workflows:
        if run.get("head_sha") != head or run.get("status") != "completed" or run.get("conclusion") != "success":
            continue
        found.setdefault(run.get("workflow_key"), []).append(run)
    if set(found) != REQUIRED_WORKFLOWS or any(len(found[name]) != 1 for name in REQUIRED_WORKFLOWS):
        fail("exact-head required workflow set is missing, duplicated, or unsuccessful")

    anchors = evidence.get("immutable_anchors", {})
    expected_anchors = {
        "task228_manifest_sha256": TASK228_SUMS_SHA,
        "task225_freeze_manifest_sha256": TASK225_FREEZE_SHA,
        "task227_freeze_manifest_sha256": TASK227_FREEZE_SHA,
    }
    if any(anchors.get(key) != value for key, value in expected_anchors.items()):
        fail("immutable preregistered asset anchor mismatch")

    # Confirm the Task225 and Task227 manifests, policy bytes, and Task228 sum manifest remain unchanged.
    task228_sums = REPO / "ignition/reports/evaluations/ignition-228-policy-contract-reconciliation-r0/SHA256SUMS"
    if not task228_sums.is_file() or digest(task228_sums.read_bytes()) != TASK228_SUMS_SHA:
        fail("Task228 SHA256SUMS changed")
    task227_manifest = REPO / "ignition/reports/evaluations/ignition-227-cognitive-evolution-component-isolation-r0/freeze/freeze-manifest.json"
    if not task227_manifest.is_file() or digest(task227_manifest.read_bytes()) != TASK227_FREEZE_SHA:
        fail("Task227 freeze manifest changed")
    task225_path = "ignition/reports/evaluations/ignition-225-cognitive-evolution-r0-1/freeze-manifest.json"
    task225_raw = subprocess.run(["git", "show", f"{PARENT_SHA}:{task225_path}"], cwd=REPO, check=True, capture_output=True).stdout
    if digest(task225_raw) != TASK225_FREEZE_SHA:
        fail("Task225 freeze manifest changed at pinned base")

    manifest = read_json(PREREG / "condition-manifest.json")
    for lineage in manifest["lineages"]:
        policy_path = REPO / lineage["policy_path"]
        if not policy_path.is_file() or digest(policy_path.read_bytes()) != lineage["policy_sha256"]:
            fail(f"Task228 policy changed: {lineage['policy_id']}")
    forbidden_runtime_paths = [
        PREREG / "run/raw-sessions", PREREG / "run/sanitized-packets",
        PREREG / "run/evaluations", PREREG / "run/results",
    ]
    if any(path.exists() for path in forbidden_runtime_paths):
        fail("experimental outputs exist before target opening")
    if args.output.exists():
        fail("target-opening gate receipt already exists; refusing to overwrite")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema_version": "task229-target-opening-gate-receipt-r0",
        "gate": "PASS",
        "target_access_authorized": True,
        "checked_at_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "task229_head_sha": head,
        "task229_head_parent": parent,
        "task229_pr": pr,
        "successful_exact_head_workflows": [found[name][0] for name in sorted(REQUIRED_WORKFLOWS)],
        "freeze_manifest_sha256": freeze_sha,
        "immutable_anchors": expected_anchors,
        "preregistration_files_unchanged": True,
        "experimental_outputs_pre_gate": False,
    }
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("TASK229_TARGET_OPENING_GATE=PASS")
    print(f"TASK229_FROZEN_HEAD={head}")
    print("TASK229_EXACT_HEAD_CI=4/4 SUCCESS")
    print("TASK229_TARGET_ACCESS=AUTHORIZED_BY_GATE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
