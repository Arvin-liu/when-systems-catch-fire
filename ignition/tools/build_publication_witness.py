#!/usr/bin/env python3
"""Build a provider-neutral, observation-time remote-main publication witness.

The tool emits JSON to stdout by default. A checked-in formal repository should
keep this protocol and its validator, while the final runtime witness belongs on
the 1111 receipt branch.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

try:
    from tools import task_identity
except ImportError:  # direct script / tools-on-PYTHONPATH execution
    import task_identity


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
SCHEMA_PATH = ROOT / "schemas/operations/publication-witness-r1.schema.json"
CONTRACT_PATH = ROOT / "data/operations/iterations/136/execution-contract-r1.json"
LINEAGE_PATH = ROOT / "data/operations/current-task-lineage-status.json"
LIFECYCLE_PATH = ROOT / "data/operations/current-release-lifecycle-r1.json"
FORMAL_RESULT_PATH = ROOT / "agent-results/IGNITION-20260823-136-result.md"
REMOTE_REF = "refs/heads/main"
REMOTE_TRACKING_REF = "refs/remotes/origin/main"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
CLAIM_CEILING = "Observation-time remote Git publication evidence only; no external truth, production readiness, Owner acceptance or epistemic acceptance is inferred."
REQUIRED_GATES = (
    "current_facts",
    "current_snapshot",
    "current_surface_compiler",
    "typed_semantic_gate",
    "task_lineage",
    "current_state_sync",
    "clean_worktree",
)


class WitnessBuildError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise WitnessBuildError(f"git command failed: {' '.join(args)} (exit={completed.returncode})")
    return completed.stdout.strip()


def parse_remote_ref(output: str) -> str:
    matches = []
    for line in output.splitlines():
        fields = line.split()
        if len(fields) == 2 and fields[1] == REMOTE_REF:
            matches.append(fields[0])
    if len(matches) != 1 or not SHA_RE.fullmatch(matches[0]):
        raise WitnessBuildError("remote main ref observation is missing, ambiguous or invalid")
    return matches[0]


def semantic_gates_from_report(path: Path) -> dict[str, str]:
    report = load_json(path)
    if report.get("result") != "PASS":
        raise WitnessBuildError("post-publication semantic report is not PASS")
    by_name = {row.get("check"): row.get("result") for row in report.get("checks", [])}
    gates = {
        "post_publication_validator": report.get("result"),
        **{name: by_name.get(name) for name in REQUIRED_GATES},
        "clean_worktree": by_name.get("clean_worktree"),
    }
    missing_or_failed = [name for name, result in gates.items() if result != "PASS"]
    if missing_or_failed:
        raise WitnessBuildError(f"required semantic gates are missing or failed: {','.join(missing_or_failed)}")
    return gates


def validate_witness(witness: dict[str, Any]) -> list[str]:
    errors = sorted(Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(witness), key=lambda error: list(error.path))
    rendered = [f"{error.json_path}: {error.message}" for error in errors]
    binding = witness.get("task_binding")
    if isinstance(binding, dict):
        task_id = witness.get("task_id")
        binding_ids = {
            "formal_result_task_id": binding.get("formal_result_task_id"),
            "canonical_current_formal_task_id": binding.get("canonical_current_formal_task_id"),
            "lifecycle_task_id": binding.get("lifecycle_task_id"),
            "release_candidate_task_id": binding.get("release_candidate_task_id"),
        }
        for label, observed in binding_ids.items():
            if observed != task_id:
                rendered.append(f"$.task_binding.{label}: does not match $.task_id")
        if binding.get("exact_match") is not True:
            rendered.append("$.task_binding.exact_match: task identity binding is not exact")
        if binding.get("latest_architecture_changing_task") == task_id:
            contract = load_json(CONTRACT_PATH)
            if contract.get("identity_impact") != "ARCHITECTURE_CHANGED":
                rendered.append("$.task_binding.latest_architecture_changing_task: architecture task was promoted to formal task")
        try:
            formal = task_identity.parse_task_id(task_id)
            architecture = task_identity.parse_task_id(binding.get("latest_architecture_changing_task"))
        except task_identity.TaskIdentityError as exc:
            rendered.append(f"$.task_binding.ordinal_source: {exc}")
        else:
            if binding.get("current_formal_task_ordinal") != formal["ordinal"]:
                rendered.append("$.task_binding.current_formal_task_ordinal: does not derive from task id")
            if binding.get("latest_architecture_task_ordinal") != architecture["ordinal"]:
                rendered.append("$.task_binding.latest_architecture_task_ordinal: does not derive from architecture task id")
            if binding.get("current_iteration_boundary") != formal["ordinal"]:
                rendered.append("$.task_binding.current_iteration_boundary: is not the formal ordinal alias")
            if binding.get("current_iteration_boundary_semantics") != "DEPRECATED_COMPATIBILITY_ALIAS_OF_CURRENT_FORMAL_TASK_ORDINAL":
                rendered.append("$.task_binding.current_iteration_boundary_semantics: alias semantics are invalid")
    return rendered


def _formal_result_task_id(path: Path = FORMAL_RESULT_PATH) -> str | None:
    """Read a result task id when the formal result already exists.

    Step 07 is implemented before the formal result is created, so absence is
    allowed here. Final witness creation runs after Step 13 and then verifies
    the checked-in result's explicit Task ID line.
    """

    if not path.is_file():
        return None
    if path.suffix == ".json":
        record = load_json(path)
        return record.get("task_id") or record.get("formal_task_id")
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("Task ID:"):
            return line.split(":", 1)[1].strip().strip("`")
    return None


def _task_binding(*, task_id: str, formal_result_task_id: str) -> dict[str, Any]:
    lineage = load_json(LINEAGE_PATH)
    lifecycle = load_json(LIFECYCLE_PATH)
    contract = load_json(CONTRACT_PATH)
    identity = lineage.get("task_identity", {})
    canonical_current_formal_task_id = identity.get("current_formal_task")
    lifecycle_task_id = lifecycle.get("task_id")
    release_candidate_task_id = contract.get("identity_expectations", {}).get("release_candidate_task")
    latest_architecture_changing_task = identity.get("latest_architecture_changing_task") or lifecycle.get("latest_architecture_changing_task")
    source_result_task_id = _formal_result_task_id()
    if source_result_task_id is not None and source_result_task_id != formal_result_task_id:
        raise WitnessBuildError(
            "formal result task id differs from the supplied task id: "
            f"supplied={formal_result_task_id} observed={source_result_task_id}"
        )
    observed = {
        "formal_result_task_id": formal_result_task_id,
        "canonical_current_formal_task_id": canonical_current_formal_task_id,
        "lifecycle_task_id": lifecycle_task_id,
        "release_candidate_task_id": release_candidate_task_id,
    }
    mismatches = [f"{label}={value}" for label, value in observed.items() if value != task_id]
    if mismatches:
        raise WitnessBuildError("task identity binding mismatch: " + ", ".join(mismatches))
    if not isinstance(latest_architecture_changing_task, str):
        raise WitnessBuildError("latest architecture-changing task must remain distinct from the formal task")
    if latest_architecture_changing_task == task_id and contract.get("identity_impact") != "ARCHITECTURE_CHANGED":
        raise WitnessBuildError("latest architecture-changing task must remain distinct from the formal task")
    if contract.get("task_id") != task_id or lineage.get("current_task", {}).get("task_id") != task_id:
        raise WitnessBuildError("task identity binding does not match the execution contract and canonical current task")
    try:
        formal_ordinal = task_identity.parse_task_id(task_id)["ordinal"]
        architecture_ordinal = task_identity.parse_task_id(latest_architecture_changing_task)["ordinal"]
    except task_identity.TaskIdentityError as exc:
        raise WitnessBuildError(f"cannot derive witness ordinals: {exc}") from exc
    return {
        **observed,
        "latest_architecture_changing_task": latest_architecture_changing_task,
        "current_formal_task_ordinal": formal_ordinal,
        "latest_architecture_task_ordinal": architecture_ordinal,
        "current_iteration_boundary": formal_ordinal,
        "current_iteration_boundary_semantics": "DEPRECATED_COMPATIBILITY_ALIAS_OF_CURRENT_FORMAL_TASK_ORDINAL",
        "exact_match": True,
    }


def classify_followup_remote_observation(witness: dict[str, Any], later_remote_sha: str) -> str:
    """Classify a later ref observation without upgrading the original witness."""

    if not SHA_RE.fullmatch(later_remote_sha):
        raise WitnessBuildError("later remote SHA is not a 40-character lowercase Git SHA")
    return "VALID_AT_OBSERVATION_TIME" if later_remote_sha == witness["observed_remote"]["sha"] else "STALE_OBSERVATION"


def build_witness(
    *,
    task_id: str,
    formal_result_task_id: str,
    subject_repository: str,
    candidate_sha: str,
    fresh_clone_head_sha: str,
    fresh_clone_branch: str,
    fresh_clone_clean: bool,
    semantic_gates: dict[str, str],
    receipt_ref: str,
    observed_at: str | None = None,
) -> dict[str, Any]:
    if not SHA_RE.fullmatch(candidate_sha):
        raise WitnessBuildError("candidate SHA is not a 40-character lowercase Git SHA")
    if fresh_clone_branch != "main" or not fresh_clone_clean:
        raise WitnessBuildError("fresh clone must be clean and on branch main")
    if fresh_clone_head_sha != candidate_sha:
        raise WitnessBuildError("fresh clone HEAD differs from candidate SHA")
    if any(value != "PASS" for value in semantic_gates.values()):
        raise WitnessBuildError("all semantic gates must be PASS")
    task_binding = _task_binding(task_id=task_id, formal_result_task_id=formal_result_task_id)

    remotes = git("remote").splitlines()
    if "origin" not in remotes:
        raise WitnessBuildError("origin remote is missing")
    git("fetch", "--quiet", "--prune", "origin", f"{REMOTE_REF}:{REMOTE_TRACKING_REF}")
    remote_sha = parse_remote_ref(git("ls-remote", "origin", REMOTE_REF))
    branch = git("branch", "--show-current")
    head_sha = git("rev-parse", "HEAD")
    clean = git("status", "--porcelain=v1", "--untracked-files=all") == ""
    if branch != "main":
        raise WitnessBuildError("witness checkout must be on branch main")
    if head_sha != candidate_sha:
        raise WitnessBuildError("witness checkout HEAD differs from candidate SHA")
    if not clean:
        raise WitnessBuildError("witness checkout is not clean")
    if remote_sha != candidate_sha:
        raise WitnessBuildError("observed remote main SHA differs from candidate SHA")

    witness = {
        "schema_version": "publication-witness-r1",
        "witness_kind": "REMOTE_REF_PUBLICATION_WITNESS",
        "task_id": task_id,
        "subject_repository": subject_repository,
        "candidate_sha": candidate_sha,
        "observed_at": observed_at or datetime.now(timezone.utc).isoformat(),
        "observed_remote": {"ref": REMOTE_REF, "sha": remote_sha},
        "local_checkout": {"branch": branch, "head_sha": head_sha, "clean": clean},
        "fresh_clone": {"mode": "FRESH_REMOTE_MAIN_CLONE", "branch": fresh_clone_branch, "head_sha": fresh_clone_head_sha, "clean": fresh_clone_clean},
        "equality": {
            "candidate_equals_remote": candidate_sha == remote_sha,
            "candidate_equals_local_head": candidate_sha == head_sha,
            "candidate_equals_fresh_clone_head": candidate_sha == fresh_clone_head_sha,
            "remote_equals_fresh_clone_head": remote_sha == fresh_clone_head_sha,
            "exact_match": candidate_sha == remote_sha == head_sha == fresh_clone_head_sha,
        },
        "task_binding": task_binding,
        "current_semantic_gates": semantic_gates,
        "witness": {
            "status": "ISSUED_EXACT_MATCH",
            "authority_class": "CONTROL_REPOSITORY_RECEIPT",
            "scope": "OBSERVATION_TIME_ONLY",
            "receipt_repository": "Arvin-liu/1111",
            "receipt_ref": receipt_ref,
            "credentials_included": False,
        },
        "claim_ceiling": CLAIM_CEILING,
    }
    errors = validate_witness(witness)
    if errors:
        raise WitnessBuildError("witness schema validation failed: " + "; ".join(errors))
    return witness


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--formal-result-task-id", required=True)
    parser.add_argument("--subject-repository", required=True)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--fresh-clone-head-sha", required=True)
    parser.add_argument("--fresh-clone-branch", default="main")
    parser.add_argument("--fresh-clone-clean", action="store_true")
    parser.add_argument("--semantic-gates-json", required=True)
    parser.add_argument("--receipt-ref", required=True)
    parser.add_argument("--observed-at")
    parser.add_argument("--write")
    args = parser.parse_args()
    try:
        witness = build_witness(
            task_id=args.task_id,
            formal_result_task_id=args.formal_result_task_id,
            subject_repository=args.subject_repository,
            candidate_sha=args.candidate_sha,
            fresh_clone_head_sha=args.fresh_clone_head_sha,
            fresh_clone_branch=args.fresh_clone_branch,
            fresh_clone_clean=args.fresh_clone_clean,
            semantic_gates=semantic_gates_from_report(Path(args.semantic_gates_json)),
            receipt_ref=args.receipt_ref,
            observed_at=args.observed_at,
        )
    except (OSError, ValueError, WitnessBuildError, json.JSONDecodeError) as error:
        print(f"PUBLICATION_WITNESS_INVALID: {error}", file=sys.stderr)
        return 1
    rendered = json.dumps(witness, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.write:
        Path(args.write).write_text(rendered, encoding="utf-8")
        print(f"PUBLICATION_WITNESS_WRITTEN path={args.write}")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
