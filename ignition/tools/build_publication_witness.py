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


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
SCHEMA_PATH = ROOT / "schemas/operations/publication-witness-r1.schema.json"
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
    return [f"{error.json_path}: {error.message}" for error in errors]


def build_witness(
    *,
    task_id: str,
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
