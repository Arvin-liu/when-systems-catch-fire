#!/usr/bin/env python3
"""Inventory Task207 preparation paths and bind hashes for Step09 accounting."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
TASK_DIR = REPO_ROOT / "ignition/reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0"
TASK_PREFIX = TASK_DIR.relative_to(REPO_ROOT).as_posix() + "/"
BASE_COMMIT = "8e70ba196739cf1a79600e02ace36f90ad2c130c"
LEDGER_PATH = TASK_DIR / "provenance/path-accounting-r0.json"
LEDGER_MD = TASK_DIR / "provenance/path-accounting-r0.md"
R2_RECEIPT_PATH = TASK_DIR / "provenance/task207-r2-scope-repair-receipt.json"
SELF_PATHS = {LEDGER_PATH, LEDGER_MD}
R1_HISTORICAL_SCOPE = "ALL_TASK207_PREPARATION_FILES; NO_REPOSITORY_WIDE_RECLASSIFICATION"
R2_SCOPE = "OWNER_AUTHORIZED_TASK207_R2_NARROW_DERIVED_PROJECTION_CLOSURE"
R2_START_HEAD = "cb418d72dafb7ea4150b12ec732aa6e6a4e7d1d3"
R3_COMMIT = "90cabb9a423ea6ac69f88dd5871afb70580c2657"
R3_TASK179_EXACT_FILES = frozenset(
    {
        "ignition/tests/test_cognitive_inheritance_r0.py",
        "ignition/tools/validate_cognitive_inheritance_r0.py",
    }
)
R5_AUTHORITY_REPOSITORY = "Arvin-liu/1111"
R5_AUTHORITY_PATH = "agent-commands/IGNITION-20260924-207-R5-OVERNIGHT-MULTIAGENT-CLOSEOUT.md"
R5_AUTHORITY_BLOB_OID = "6c46876c75dc06f219003055ca7909a104e1160d"


def git_output(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, text=True, capture_output=True, check=False
    )
    if result.returncode != 0:
        raise SystemExit(result.stderr.strip() or "git lineage check failed")
    return result.stdout.strip()


def verify_r3_lineage() -> dict:
    parent = git_output("rev-parse", f"{R3_COMMIT}^")
    changed = set(git_output("diff-tree", "--no-commit-id", "--name-only", "-r", R3_COMMIT).splitlines())
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", R3_COMMIT, "HEAD"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if parent != R2_START_HEAD:
        raise SystemExit("R3 is not the exact direct child of the R2 starting head")
    if changed != R3_TASK179_EXACT_FILES:
        raise SystemExit("R3 commit changed-path set is not the exact two-file authorization")
    if ancestor.returncode != 0:
        raise SystemExit("R3 authorized commit is not an ancestor of the current branch")
    return {
        "authority_repository": R5_AUTHORITY_REPOSITORY,
        "authority_command": R5_AUTHORITY_PATH,
        "authority_blob_oid": R5_AUTHORITY_BLOB_OID,
        "r2_start_head": R2_START_HEAD,
        "r3_commit": R3_COMMIT,
        "r3_parent": parent,
        "r3_commit_changed_paths": sorted(changed),
    }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify(path: Path) -> tuple[str, str]:
    rel = path.relative_to(TASK_DIR).as_posix()
    if path.name.endswith(".sha256"):
        return "HASH_SIDECAR", "EVALUATION_EVIDENCE"
    if rel.startswith("packets/") or rel.startswith("common/"):
        return "SUCCESSOR_VISIBLE_PACKET_INPUT", "EVALUATION_EVIDENCE"
    if rel.startswith("evaluator/sealed-r0/"):
        return "EVALUATOR_SEALED_PROTOCOL", "EVALUATION_EVIDENCE"
    if rel.startswith("evaluator/"):
        return "EVALUATOR_PROTOCOL", "EVALUATION_EVIDENCE"
    if rel.startswith("future-tasks/"):
        return "FUTURE_TASK_PLAN_NOT_LAUNCHED", "EVALUATION_EVIDENCE"
    if rel.startswith("cases/") or rel.startswith("payload/"):
        return "SYNTHETIC_TASK_INPUT", "EVALUATION_EVIDENCE"
    if rel.startswith("tools/"):
        return "BUILDER_OR_VALIDATOR", "EVALUATION_EVIDENCE"
    if rel.startswith("schema/"):
        return "TASK_LOCAL_SCHEMA", "EVALUATION_EVIDENCE"
    if rel.startswith("design/"):
        return "EXPERIMENTAL_DESIGN_GATE", "EVALUATION_EVIDENCE"
    if rel.startswith("provenance/"):
        return "PROVENANCE_OR_PACKET_PLAN", "EVALUATION_EVIDENCE"
    if path.name == "owner-gpt-adjudication-input.json":
        return "FROZEN_OWNER_GPT_ADJUDICATION", "EVALUATION_EVIDENCE"
    if path.name.startswith("representation-sufficiency"):
        return "REPRESENTATION_AUDIT", "EVALUATION_EVIDENCE"
    return "TASK207_PREPARATION_ARTIFACT", "EVALUATION_EVIDENCE"


def repo_rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def read_r2_receipt() -> dict:
    if not R2_RECEIPT_PATH.is_file():
        raise SystemExit("missing Task207 R2 scope-repair receipt")
    return json.loads(R2_RECEIPT_PATH.read_text(encoding="utf-8"))


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
        if result.returncode != 0:
            raise SystemExit(result.stderr.strip() or "changed-path enumeration failed")
        paths.update(line for line in result.stdout.splitlines() if line)
    return sorted(paths)


def main() -> int:
    rows = []
    for root, dirs, files in os.walk(TASK_DIR, followlinks=False):
        dirs[:] = sorted(name for name in dirs if not (Path(root) / name).is_symlink())
        for filename in sorted(files):
            path = Path(root) / filename
            if path in SELF_PATHS or path.name in {"path-accounting-r0.json.sha256", "path-accounting-r0.md.sha256"}:
                continue
            if path.is_symlink() or not path.is_file():
                raise SystemExit("unexpected non-regular Task207 path: " + repo_rel(path))
            category, artifact_type = classify(path)
            rel = repo_rel(path)
            rows.append(
                {
                    "path": rel,
                    "sha256": sha256(path),
                    "size_bytes": path.stat().st_size,
                    "path_class": category,
                    "artifact_type": artifact_type,
                    "canonical_claim_ids": [],
                    "canonical_promotion": "NONE",
                    "successor_or_evaluator_execution": "NOT_RUN",
                    "sha256_sidecar": f"{rel}.sha256" if path.with_name(path.name + ".sha256").is_file() else None,
                }
            )
    rows.sort(key=lambda row: row["path"])

    receipt = read_r2_receipt()
    if receipt.get("authorization", {}).get("r1_scope_historical_verbatim") != R1_HISTORICAL_SCOPE:
        raise SystemExit("R1 historical scope is missing or changed in the R2 receipt")
    if receipt.get("authorization", {}).get("r2_scope") != R2_SCOPE:
        raise SystemExit("R2 authorization scope is missing or changed")
    allowed_non_task207 = receipt.get("exact_non_task207_allowlist", [])
    actual_r2_paths = receipt.get("actual_non_task207_changed_paths", [])
    if not isinstance(allowed_non_task207, list) or len(set(allowed_non_task207)) != len(allowed_non_task207):
        raise SystemExit("R2 non-Task207 allowlist is malformed or duplicated")
    if any(not isinstance(path, str) or not path.startswith("ignition/") or path.endswith("/") or "*" in path for path in allowed_non_task207):
        raise SystemExit("R2 non-Task207 allowlist must contain exact repository file paths only")
    if not isinstance(actual_r2_paths, list) or len(set(actual_r2_paths)) != len(actual_r2_paths):
        raise SystemExit("R2 actual changed-path record is malformed or duplicated")
    if set(actual_r2_paths) != set(allowed_non_task207):
        raise SystemExit("R2 actual changed paths do not exactly equal its immutable exact allowlist")
    r3_lineage = verify_r3_lineage()
    r2_and_r3_expected = set(allowed_non_task207) | set(R3_TASK179_EXACT_FILES)
    changed_paths = current_changed_paths()
    outside_task = [path for path in changed_paths if not path.startswith(TASK_PREFIX)]
    if set(outside_task) != r2_and_r3_expected:
        missing = sorted(r2_and_r3_expected - set(outside_task))
        extra = sorted(set(outside_task) - r2_and_r3_expected)
        raise SystemExit(f"outside-Task207 paths differ from exact R2+R3 authority; missing={missing}; extra={extra}")
    generator_runs = receipt.get("generator_runs", [])
    if not isinstance(generator_runs, list):
        raise SystemExit("R2 generator run receipt is malformed")

    exact_prefix = "reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0/"
    data = {
        "artifact_type": "EVALUATION_EVIDENCE",
        "task_id": "IGNITION-20260923-207",
        "step": "Step09",
        "schema_version": "task207-path-accounting-r0",
        "base_commit": BASE_COMMIT,
        "pre_step08_head": "0ca97b283f0955a708f6bfe8f24762b3672c0896",
        "scope": R2_SCOPE,
        "historical_r1_scope": R1_HISTORICAL_SCOPE,
        "r2_scope_receipt": repo_rel(R2_RECEIPT_PATH),
        "r2_authorized_non_task207_paths": sorted(allowed_non_task207),
        "r3_authorized_outside_paths": sorted(R3_TASK179_EXACT_FILES),
        "r3_authorization_lineage": r3_lineage,
        "actual_non_task207_changed_paths": sorted(outside_task),
        "task_root": TASK_PREFIX.rstrip("/"),
        "path_count_excluding_this_ledger_and_sidecars": len(rows),
        "paths": rows,
        "self_accounting": {
            "ledger_path": repo_rel(LEDGER_PATH),
            "ledger_sha256": "PROTECTED_BY_DETACHED_SHA256_SIDECAR",
            "ledger_sidecar_path": repo_rel(LEDGER_PATH.with_name(LEDGER_PATH.name + ".sha256")),
            "summary_path": repo_rel(LEDGER_MD),
            "summary_sha256": "PROTECTED_BY_DETACHED_SHA256_SIDECAR",
            "summary_sidecar_path": repo_rel(LEDGER_MD.with_name(LEDGER_MD.name + ".sha256")),
        },
        "downstream_projections": [
            {
                "target": "human-results",
                "semantic_canonical_propagation_required": False,
                "mechanical_isolation_required": True,
                "exact_excluded_prefix": exact_prefix,
                "disposition": "TASK207_SUBTREE_EXCLUDED_FROM_DISCOVERY",
                "proof": "The exact Task207 experiment subtree is excluded by the existing human-results prefix filter; unrelated evaluation reports remain discoverable.",
            },
            {
                "target": "Foundation / Current / knowledge / Fire Seeds / self-correction",
                "semantic_canonical_propagation_required": False,
                "mechanical_generator_runs_recorded_in": repo_rel(R2_RECEIPT_PATH),
                "disposition": "DETERMINISTIC_DERIVED_OUTPUTS_ONLY",
                "proof": "Actual mechanical generator runs and exact changed paths are recorded in the R2 receipt; canonical claims and identities remain unchanged.",
            },
        ],
        "projection_generators_run": generator_runs,
        "canonical_claim_ids": [],
        "canonical_promotion": "NONE",
        "successor": "NOT_RUN",
        "evaluator": "NOT_RUN",
        "cross_model_execution": "NOT_AUTHORIZED",
        "r1": "NOT_AUTHORIZED",
    }
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    generator_names = ", ".join(run.get("name", "UNNAMED") for run in generator_runs)
    summary = [
        "# Task207 Path Accounting R0 with R2 Scope Amendment",
        "",
        "Task-local paths remain evaluation evidence; no canonical claim IDs were added.",
        "",
        f"- Exact base: `{BASE_COMMIT}`",
        f"- Inventory count (excluding this ledger and its sidecars): **{len(rows)}**",
        f"- Exact non-Task207 paths: **{len(outside_task)}** (R2 **{len(allowed_non_task207)}**; R3 **{len(R3_TASK179_EXACT_FILES)}**).",
        f"- Historical R1 scope retained: {R1_HISTORICAL_SCOPE}.",
        f"- Current R2 scope and receipt retained verbatim: {R2_SCOPE}.",
        f"- R3 exact-path authorization: {R3_COMMIT} is a direct child of {R2_START_HEAD} and changes only the two paths listed in r3_authorization_lineage.",
        f"- Official projection generators recorded: **{len(generator_runs)}** ({generator_names or 'none recorded'}).",
        f"- Human-results excludes only `{exact_prefix}`; unrelated reports remain discoverable.",
        "- Semantic/canonical promotion: none. Successor and Evaluator: not run.",
        f"- R2 continuation receipt: `{repo_rel(R2_RECEIPT_PATH)}`.",
        "",
        "The machine-readable ledger lists each Task207 path, SHA-256, byte count, path class, artifact type, canonical status, and available sidecar.",
        "",
    ]
    LEDGER_MD.write_text("\n".join(summary), encoding="utf-8")
    for path in (LEDGER_PATH, LEDGER_MD):
        sidecar = path.with_name(path.name + ".sha256")
        sidecar.write_text(f"{sha256(path)}  {repo_rel(path)}\n", encoding="utf-8")
    print(f"TASK207_STEP09_PATH_LEDGER_BUILT: hashed_paths={len(rows)} outside_task_paths={len(outside_task)} generator_runs={len(generator_runs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
