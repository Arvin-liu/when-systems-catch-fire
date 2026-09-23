#!/usr/bin/env python3
"""Validate Task207 Step09 accounting with the exact authorized R2 scope."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
TASK_DIR = REPO_ROOT / "ignition/reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0"
TASK_PREFIX = TASK_DIR.relative_to(REPO_ROOT).as_posix() + "/"
BASE_COMMIT = "8e70ba196739cf1a79600e02ace36f90ad2c130c"
LEDGER = TASK_DIR / "provenance/path-accounting-r0.json"
SUMMARY = TASK_DIR / "provenance/path-accounting-r0.md"
R2_RECEIPT = TASK_DIR / "provenance/task207-r2-scope-repair-receipt.json"
R1_HISTORICAL_SCOPE = "ALL_TASK207_PREPARATION_FILES; NO_REPOSITORY_WIDE_RECLASSIFICATION"
R2_SCOPE = "OWNER_AUTHORIZED_TASK207_R2_NARROW_DERIVED_PROJECTION_CLOSURE"
TASK207_HUMAN_RESULTS_PREFIX = "reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0/"
CLASSIFICATION_MANIFEST = "ignition/data/foundation/repository-path-classification/classification-manifest.jsonl"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL_TASK207_STEP09: {message}")


def current_changed_paths() -> list[str]:
    commands = [
        ["git", "diff", "--name-only", f"{BASE_COMMIT}...HEAD"],
        ["git", "diff", "--cached", "--name-only"],
        ["git", "diff", "--name-only"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ]
    paths: set[str] = set()
    for command in commands:
        result = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
        require(result.returncode == 0, "cannot enumerate exact-base branch and worktree paths")
        paths.update(line for line in result.stdout.splitlines() if line)
    return sorted(paths)


def exact_scope_accepts(paths: list[str], allowlist: set[str]) -> bool:
    return all(path in allowlist for path in paths)


def digest_equal(expected: str, observed: str) -> bool:
    return expected == observed


def verify_sidecar(path: Path, rel: str) -> None:
    sidecar = path.with_name(path.name + ".sha256")
    expected = f"{sha256(path)}  {rel}\n"
    require(sidecar.is_file() and sidecar.read_text(encoding="utf-8") == expected, f"sidecar mismatch: {rel}")


def task_files_excluding_self() -> set[str]:
    paths: set[str] = set()
    for root, dirs, files in os.walk(TASK_DIR, followlinks=False):
        dirs[:] = sorted(name for name in dirs if not (Path(root) / name).is_symlink())
        for name in files:
            path = Path(root) / name
            if path.is_symlink() or not path.is_file():
                raise SystemExit("FAIL_TASK207_STEP09: non-regular Task207 path: " + path.relative_to(REPO_ROOT).as_posix())
            if path in {LEDGER, SUMMARY} or path.name in {"path-accounting-r0.json.sha256", "path-accounting-r0.md.sha256"}:
                continue
            paths.add(path.relative_to(REPO_ROOT).as_posix())
    return paths


def verify_human_results_isolation(config: dict) -> tuple[int, int]:
    excluded = config.get("excluded_prefixes", [])
    require(TASK207_HUMAN_RESULTS_PREFIX in excluded, "exact Task207 human-results prefix exclusion missing")
    require("reports/evaluations/" not in excluded, "broad evaluation-tree exclusion is forbidden")
    sys.path.insert(0, str(REPO_ROOT / "ignition/tools/governance"))
    builder = importlib.import_module("build_human_results")
    discovered = builder.discover(config)
    task_markdown = [path for path in builder.tracked_paths() if path.startswith(TASK207_HUMAN_RESULTS_PREFIX) and path.endswith(".md")]
    unrelated_evaluation_markdown = [
        path for path in discovered if path.startswith("reports/evaluations/") and path.endswith(".md")
    ]
    require(task_markdown, "Task207 isolation negative test has no task Markdown fixture")
    require(not any(path.startswith(TASK207_HUMAN_RESULTS_PREFIX) for path in discovered), "Task207 Markdown entered human-results discovery")
    require(unrelated_evaluation_markdown, "unrelated evaluation Markdown is no longer discoverable")
    return len(task_markdown), len(unrelated_evaluation_markdown)


def run_negative_tests(allowlist: set[str], protected_hashes: list[dict]) -> None:
    require(exact_scope_accepts([CLASSIFICATION_MANIFEST], allowlist), "authorized classification output failed exact allowlist test")
    canonical_claim_path = "ignition/data/foundation/claims/claims.jsonl"
    require(not exact_scope_accepts([canonical_claim_path], allowlist), "simulated canonical claim mutation was accepted")
    require(not exact_scope_accepts(["ignition/docs/foundation/canonical-claim-test.md"], allowlist), "simulated unauthorized path was accepted")
    packet = next((row for row in protected_hashes if "/packets/" in row["path"]), None)
    require(packet is not None, "protected-input inventory lacks a packet hash fixture")
    altered_digest = ("0" if packet["sha256"][0] != "0" else "1") + packet["sha256"][1:]
    require(not digest_equal(packet["sha256"], altered_digest), "simulated packet byte mutation did not fail hash comparison")


def main() -> int:
    require(R2_RECEIPT.is_file(), "missing R2 continuation receipt")
    receipt = json.loads(R2_RECEIPT.read_text(encoding="utf-8"))
    authorization = receipt.get("authorization", {})
    require(authorization.get("r1_stop") == "TASK207_AUTHORITY_SCOPE_CONFLICT", "R1 stop state changed")
    require(authorization.get("r1_scope_historical_verbatim") == R1_HISTORICAL_SCOPE, "historical R1 scope changed")
    require(authorization.get("r2_scope") == R2_SCOPE, "R2 authorization scope missing or changed")
    require(authorization.get("successor") == "NOT_RUN" and authorization.get("evaluator") == "NOT_RUN", "Successor or Evaluator state changed")
    require(authorization.get("r1") == "NOT_AUTHORIZED" and authorization.get("cross_model_execution") == "NOT_RUN", "R1/cross-model boundary changed")
    require(authorization.get("canonical_promotion") == "NONE", "canonical promotion recorded")

    baseline = receipt.get("protected_input_baseline", {})
    require(baseline.get("commit") == receipt.get("exact_head_at_start"), "protected-input baseline commit drifted")
    require(baseline.get("algorithm") == "SHA-256" and baseline.get("raw_contents_included") is False, "protected-input baseline format invalid")
    protected_hashes = baseline.get("path_hashes", [])
    require(len(protected_hashes) == baseline.get("path_count") == 280, "protected-input baseline count mismatch")
    protected_paths = [row.get("path") for row in protected_hashes]
    require(len(set(protected_paths)) == len(protected_paths), "protected-input baseline contains duplicate paths")
    for row in protected_hashes:
        rel = row.get("path", "")
        require(rel.startswith(TASK_PREFIX), "protected-input baseline path escaped Task207 root")
        path = REPO_ROOT / rel
        require(path.is_file() and not path.is_symlink(), "protected Task207 input missing/non-regular: " + rel)
        require(sha256(path) == row.get("sha256"), "protected Task207 input hash changed: " + rel)

    allow_rows = receipt.get("exact_non_task207_allowlist", [])
    require(isinstance(allow_rows, list) and len(allow_rows) == len(set(allow_rows)), "R2 exact non-Task207 allowlist malformed/duplicated")
    require(all(isinstance(path, str) and path.startswith("ignition/") and not path.endswith("/") and "*" not in path for path in allow_rows), "R2 allowlist contains a broad path")
    allowlist = set(allow_rows)
    require(receipt.get("authorized_configuration_changes"), "R2 configuration change is not recorded")
    config_changes = set()
    for change in receipt["authorized_configuration_changes"]:
        require(change.get("status") == "APPLIED", "authorized configuration change not applied")
        require(change.get("path") in allowlist, "configuration path outside exact allowlist")
        config_changes.update(change.get("changed_paths", []))

    generator_runs = receipt.get("generator_runs", [])
    require(isinstance(generator_runs, list) and generator_runs, "actual projection generator runs are not recorded")
    generator_names = set()
    generator_changed_paths = set()
    for run in generator_runs:
        require(run.get("name") and run.get("name") not in generator_names, "generator run name missing/duplicated")
        generator_names.add(run["name"])
        require(run.get("script") and run.get("script_blob_at_start"), "generator source/version not recorded")
        require(run.get("status") == "PASS" and run.get("check_status") == "PASS", "generator/check did not pass")
        outputs = set(run.get("output_paths", []))
        changed = set(run.get("changed_paths", []))
        require(outputs and all(path.startswith("ignition/") and not path.endswith("/") and "*" not in path for path in outputs), "generator output path list is malformed")
        require(changed.issubset(outputs), "generator changed a path outside its declared output map")
        require(changed.issubset(allowlist), "generator changed a path outside the exact R2 diff allowlist")
        generator_changed_paths.update(changed)
    require(generator_changed_paths.isdisjoint(config_changes), "configuration and generator changed-path records overlap")

    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    require(data.get("artifact_type") == "EVALUATION_EVIDENCE" and data.get("step") == "Step09", "wrong artifact type or step")
    require(data.get("base_commit") == BASE_COMMIT and data.get("task_root") == TASK_PREFIX.rstrip("/"), "wrong exact base or accounting root")
    require(data.get("scope") == R2_SCOPE and data.get("historical_r1_scope") == R1_HISTORICAL_SCOPE, "R1/R2 scope lineage missing")
    require(data.get("r2_scope_receipt") == R2_RECEIPT.relative_to(REPO_ROOT).as_posix(), "wrong R2 receipt reference")
    require(data.get("r2_authorized_non_task207_paths") == sorted(allowlist), "ledger and receipt exact allowlists differ")
    require(data.get("projection_generators_run") == generator_runs, "ledger generator record differs from R2 receipt")
    require(data.get("canonical_claim_ids") == [] and data.get("canonical_promotion") == "NONE", "canonical evidence/promotion present")
    require(data.get("successor") == "NOT_RUN" and data.get("evaluator") == "NOT_RUN", "Successor/Evaluator ran")
    require(data.get("cross_model_execution") == "NOT_AUTHORIZED" and data.get("r1") == "NOT_AUTHORIZED", "authorization boundary changed")

    projections = data.get("downstream_projections", [])
    human = next((row for row in projections if row.get("target") == "human-results"), None)
    require(human is not None and human.get("semantic_canonical_propagation_required") is False, "human-results semantic promotion boundary changed")
    require(human.get("mechanical_isolation_required") is True and human.get("exact_excluded_prefix") == TASK207_HUMAN_RESULTS_PREFIX, "Task207 mechanical isolation is not recorded")

    rows = data.get("paths", [])
    require(len(rows) == data.get("path_count_excluding_this_ledger_and_sidecars"), "path inventory count mismatch")
    seen = set()
    for row in rows:
        rel = row.get("path", "")
        require(rel.startswith(TASK_PREFIX), "accounted path escaped Task207 root")
        require(rel not in seen, "duplicate accounted path")
        seen.add(rel)
        path = REPO_ROOT / rel
        require(path.is_file() and not path.is_symlink(), "accounted path missing/non-regular")
        require(sha256(path) == row.get("sha256"), "accounted file hash mismatch")
        require(path.stat().st_size == row.get("size_bytes"), "accounted byte count mismatch")
        require(row.get("artifact_type") == "EVALUATION_EVIDENCE", "wrong path artifact type")
        require(row.get("canonical_claim_ids") == [] and row.get("canonical_promotion") == "NONE", "canonical path entry")
        sidecar_rel = row.get("sha256_sidecar")
        if sidecar_rel is not None:
            sidecar_path = REPO_ROOT / sidecar_rel
            require(sidecar_path.is_file(), "declared sidecar missing")
            parts = sidecar_path.read_text(encoding="utf-8").rstrip("\n").split("  ", 1)
            allowed_display_paths = {rel, path.relative_to(TASK_DIR).as_posix()}
            require(len(parts) == 2 and parts[0] == row["sha256"], "declared sidecar digest mismatch")
            require(parts[1] in allowed_display_paths, "declared sidecar path mismatch")
    require(seen == task_files_excluding_self(), "Task207 local ledger does not cover the exact current path set")

    changed_paths = current_changed_paths()
    outside_task = {path for path in changed_paths if not path.startswith(TASK_PREFIX)}
    require(exact_scope_accepts(sorted(outside_task), allowlist), "branch/worktree contains an unauthorized non-Task207 path")
    actual_outside = receipt.get("actual_non_task207_changed_paths", [])
    require(outside_task == set(actual_outside), "receipt does not enumerate the exact non-Task207 diff")
    require(outside_task == generator_changed_paths | config_changes, "every non-Task207 change must be an authorized generator output or exact configuration change")

    config = json.loads((REPO_ROOT / "ignition/data/governance/human-results/config.json").read_text(encoding="utf-8"))
    task_markdown_count, unrelated_report_count = verify_human_results_isolation(config)
    run_negative_tests(allowlist, protected_hashes)

    self_meta = data.get("self_accounting", {})
    require(self_meta.get("ledger_sha256") == "PROTECTED_BY_DETACHED_SHA256_SIDECAR", "ledger self-hash rule changed")
    require(self_meta.get("summary_sha256") == "PROTECTED_BY_DETACHED_SHA256_SIDECAR", "summary self-hash rule changed")
    verify_sidecar(LEDGER, LEDGER.relative_to(REPO_ROOT).as_posix())
    verify_sidecar(SUMMARY, SUMMARY.relative_to(REPO_ROOT).as_posix())
    print(f"TASK207_STEP09_PATH_LEDGER_VALID: paths={len(seen)} protected_hashes={len(protected_hashes)} outside_paths={len(outside_task)} generators={len(generator_runs)}")
    print(f"TASK207_KNOWLEDGE_ISOLATION_VALID: task_markdown_excluded={task_markdown_count} unrelated_reports_discovered={unrelated_report_count}")
    print("TASK207_R2_NEGATIVE_TESTS_VALID: unauthorized_path canonical_claim_mutation packet_hash_mutation rejected; exact_manifest_path accepted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
