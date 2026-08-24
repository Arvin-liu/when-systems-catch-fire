#!/usr/bin/env python3
"""Fail-closed Current release verification with an observed remote main ref."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "tools"))

try:
    from tools import build_current_snapshot
    from tools import current_surface_compiler
    from tools import generate_current_facts
    from tools import validate_current_release_lifecycle as lifecycle
    from tools import validate_current_state_sync as state_sync
    from tools import validate_current_surface_semantics as semantics
    from tools import validate_current_task_lineage as task_lineage
    from tools import validate_release_state_model as state_model
    from tools import validate_iteration_ordinal_binding as ordinal_binding
except ImportError:  # direct script / tools-on-PYTHONPATH execution
    import build_current_snapshot
    import current_surface_compiler
    import generate_current_facts
    import validate_current_release_lifecycle as lifecycle
    import validate_current_state_sync as state_sync
    import validate_current_surface_semantics as semantics
    import validate_current_task_lineage as task_lineage
    import validate_release_state_model as state_model
    import validate_iteration_ordinal_binding as ordinal_binding


CONTRACT_PATH = ROOT / "data/operations/current-surface-block-contract-r1.json"
LINEAGE_PATH = ROOT / "data/operations/current-task-lineage-status.json"
LIFECYCLE_PATH = ROOT / "data/operations/current-release-lifecycle-r1.json"
REMOTE_REF = "refs/heads/main"
REMOTE_TRACKING_REF = "refs/remotes/origin/main"
HEX_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class GitCommandError(RuntimeError):
    """A sanitized Git failure; stderr is intentionally not retained."""


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _current_paths() -> tuple[Path, Path, Path]:
    lineage = load_json(LINEAGE_PATH)
    task_id = lineage["task_identity"]["current_formal_task"]
    ordinal = int(task_id.rsplit("-", 1)[1])
    return (
        ROOT / f"data/operations/iterations/{ordinal}/execution-contract-r1.json",
        ROOT / f"agent-results/{task_id}-result.md",
        ROOT / f"data/operations/iterations/{ordinal}/step17-post-publication-task-binding-report.json",
    )


EXECUTION_CONTRACT_PATH, FORMAL_RESULT_PATH, REPORT_PATH = _current_paths()


def relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def git(*args: str) -> str:
    """Run Git without exposing remote URLs or command stderr in evidence."""

    completed = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise GitCommandError(f"git command failed: {' '.join(args)} (exit={completed.returncode})")
    return completed.stdout.strip()


def _probe(*args: str) -> tuple[str | None, str | None]:
    try:
        return git(*args), None
    except GitCommandError as error:
        return None, str(error)


def parse_remote_ref(output: str, ref: str = REMOTE_REF) -> tuple[str | None, str | None]:
    """Parse exactly one SHA/ref pair from git ls-remote output."""

    rows: list[tuple[str, str]] = []
    for line in output.splitlines():
        fields = line.split()
        if len(fields) != 2:
            continue
        rows.append((fields[0], fields[1]))
    matching = [(sha, row_ref) for sha, row_ref in rows if row_ref == ref]
    if len(matching) != 1:
        return None, f"remote ref observation is ambiguous or missing for {ref}"
    sha, _row_ref = matching[0]
    if not HEX_SHA_RE.fullmatch(sha):
        return None, f"remote ref observation returned an invalid SHA for {ref}"
    return sha, None


def _record(checks: list[dict[str, Any]], name: str, result: str, errors: list[str] | None = None) -> None:
    checks.append({"check": name, "result": result, "errors": errors or []})


def _current_task_id() -> str:
    return load_json(LINEAGE_PATH)["current_task"]["task_id"]


def _formal_result_task_id(path: Path = FORMAL_RESULT_PATH) -> str | None:
    if not path.is_file():
        return None
    if path.suffix == ".json":
        record = load_json(path)
        return record.get("task_id") or record.get("formal_task_id")
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("Task ID:"):
            return line.split(":", 1)[1].strip().strip("`")
    return None


def _validate_task_id_binding(
    *,
    expected_task_id: str,
    formal_result_task_id: str | None,
    contract: dict[str, Any],
    lineage_record: dict[str, Any],
    lifecycle_record: dict[str, Any],
    snapshot: dict[str, Any],
) -> list[str]:
    """Validate task identity independently of Git SHA equality.

    This deliberately compares the same role across the execution contract,
    canonical source, lifecycle and compiled snapshot. A matching remote SHA
    cannot make a stale or misbound task identity pass.
    """

    errors: list[str] = []

    def equal(label: str, observed: Any) -> None:
        if observed != expected_task_id:
            errors.append(f"TASK_ID_BINDING_MISMATCH:{label}:expected={expected_task_id}:observed={observed}")

    equal("execution_contract.task_id", contract.get("task_id"))
    expectations = contract.get("identity_expectations", {})
    equal("execution_contract.identity_expectations.current_formal_task", expectations.get("current_formal_task"))
    equal("execution_contract.identity_expectations.release_candidate_task", expectations.get("release_candidate_task"))

    equal("lineage.current_task.task_id", lineage_record.get("current_task", {}).get("task_id"))
    lineage_identity = lineage_record.get("task_identity", {})
    equal("lineage.task_identity.current_formal_task", lineage_identity.get("current_formal_task"))
    equal("lineage.task_identity.release_candidate_task", lineage_identity.get("release_candidate_task"))
    equal("lineage.task_identity.publication_witness_task", lineage_identity.get("publication_witness_task"))

    equal("lifecycle.task_id", lifecycle_record.get("task_id"))

    equal("snapshot.current_task.task_id", snapshot.get("current_task", {}).get("task_id"))
    snapshot_identity = snapshot.get("task_identity", {})
    equal("snapshot.task_identity.current_formal_task", snapshot_identity.get("current_formal_task"))
    equal("snapshot.task_identity.release_candidate_task", snapshot_identity.get("release_candidate_task"))
    equal("snapshot.task_identity.publication_witness_task", snapshot_identity.get("publication_witness_task"))
    equal("snapshot.release_lifecycle.task_id", snapshot.get("release_lifecycle", {}).get("task_id"))

    latest_architecture_ids = {
        "execution_contract": expectations.get("latest_architecture_changing_task"),
        "lineage": lineage_identity.get("latest_architecture_changing_task"),
        "lifecycle": lifecycle_record.get("latest_architecture_changing_task"),
        "snapshot": snapshot.get("latest_architecture_changing_task"),
    }
    expected_architecture_task = latest_architecture_ids["execution_contract"]
    for label, observed in latest_architecture_ids.items():
        if observed != expected_architecture_task:
            errors.append(
                f"ARCHITECTURE_TASK_BINDING_MISMATCH:{label}:expected={expected_architecture_task}:observed={observed}"
            )
    if expected_architecture_task == expected_task_id and not (
        contract.get("task_id") == expected_task_id and contract.get("identity_impact") == "ARCHITECTURE_CHANGED"
    ):
        errors.append("ARCHITECTURE_TASK_PROMOTED_TO_FORMAL_TASK")

    if formal_result_task_id is None:
        errors.append("FORMAL_RESULT_TASK_ID_MISSING")
    elif formal_result_task_id != expected_task_id:
        errors.append(
            f"TASK_ID_BINDING_MISMATCH:formal_result.task_id:expected={expected_task_id}:observed={formal_result_task_id}"
        )
    formal_result = None
    if formal_result_task_id is not None:
        try:
            from tools import task_identity
        except ImportError:
            import task_identity
        try:
            formal_result = {"task_id": formal_result_task_id, "current_formal_task_ordinal": task_identity.parse_task_id(formal_result_task_id)["ordinal"]}
        except task_identity.TaskIdentityError:
            formal_result = {"task_id": formal_result_task_id}
    ordinal_errors, _records = ordinal_binding.validate_documents(
        contract=contract,
        lineage=lineage_record,
        lifecycle=lifecycle_record,
        snapshot=snapshot,
        facts=load_json(ROOT / "data/architecture/current-facts.json"),
        formal_result=formal_result,
    )
    errors.extend(f"ORDINAL_BINDING:{error}" for error in ordinal_errors)
    return errors


def _validate_static_publication_semantics(snapshot: dict[str, Any], lifecycle_record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if lifecycle_record.get("publication_authority") != "REMOTE_REF_OBSERVATION":
        errors.append("static lifecycle publication authority is not REMOTE_REF_OBSERVATION")
    if lifecycle_record.get("embedded_publication_assertion") != "NONE":
        errors.append("static lifecycle carries an embedded publication assertion")
    if "publication_state" in lifecycle_record or "post_publication_remote_check_status" in lifecycle_record:
        errors.append("static lifecycle carries a legacy publication state field")
    release = snapshot.get("release_lifecycle", {})
    if release.get("publication_authority") != "REMOTE_REF_OBSERVATION":
        errors.append("Current Snapshot publication authority is not REMOTE_REF_OBSERVATION")
    if release.get("embedded_publication_assertion") != "NONE":
        errors.append("Current Snapshot carries an embedded publication assertion")
    if "publication_state" in release:
        errors.append("Current Snapshot carries a static publication state")
    return errors


def run_checks(
    post_publication: bool,
    expected_sha: str | None = None,
    expected_task_id: str | None = None,
    formal_result_task_id: str | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    checks: list[dict[str, Any]] = []
    blocked = False
    branch: str | None = None
    head_sha: str | None = None
    remote_sha: str | None = None
    lifecycle_record = load_json(LIFECYCLE_PATH)
    task_id = _current_task_id()
    lineage_record = load_json(LINEAGE_PATH)

    if post_publication:
        if expected_sha is None or not HEX_SHA_RE.fullmatch(expected_sha):
            errors.append("post-publication mode requires a 40-character expected SHA")

        remote_names, remote_error = _probe("remote")
        if remote_error:
            blocked = True
            errors.append("cannot inspect configured Git remotes")
            _record(checks, "origin_available", "BLOCKED_WITH_EVIDENCE", [remote_error])
        elif "origin" not in (remote_names or "").splitlines():
            blocked = True
            errors.append("origin remote is missing")
            _record(checks, "origin_available", "BLOCKED_WITH_EVIDENCE", ["origin remote is missing"])
        else:
            _record(checks, "origin_available", "PASS")
            _fetch_output, fetch_error = _probe("fetch", "--quiet", "--prune", "origin", f"{REMOTE_REF}:{REMOTE_TRACKING_REF}")
            if fetch_error:
                blocked = True
                errors.append("fresh fetch of origin main failed")
                _record(checks, "fresh_fetch", "BLOCKED_WITH_EVIDENCE", [fetch_error])
            else:
                _record(checks, "fresh_fetch", "PASS")

            observed_output, observed_error = _probe("ls-remote", "origin", REMOTE_REF)
            if observed_error:
                blocked = True
                errors.append("remote main ref observation failed")
                _record(checks, "remote_ref_observation", "BLOCKED_WITH_EVIDENCE", [observed_error])
            else:
                remote_sha, parse_error = parse_remote_ref(observed_output or "")
                if parse_error:
                    blocked = True
                    errors.append(parse_error)
                    _record(checks, "remote_ref_observation", "BLOCKED_WITH_EVIDENCE", [parse_error])
                else:
                    _record(checks, "remote_ref_observation", "PASS", [f"observed_sha={remote_sha}"])

        branch, branch_error = _probe("branch", "--show-current")
        if branch_error:
            blocked = True
            errors.append("cannot determine current branch")
            _record(checks, "current_branch", "BLOCKED_WITH_EVIDENCE", [branch_error])
        elif branch != "main":
            errors.append(f"post-publication check must run on branch main (observed {branch or 'detached'})")
            _record(checks, "current_branch", "FAIL", [f"observed={branch or 'detached'}"])
        else:
            _record(checks, "current_branch", "PASS")

        head_sha, head_error = _probe("rev-parse", "HEAD")
        if head_error:
            blocked = True
            errors.append("cannot determine local HEAD")
            _record(checks, "local_head", "BLOCKED_WITH_EVIDENCE", [head_error])
        else:
            _record(checks, "local_head", "PASS", [f"observed_sha={head_sha}"])

        equality_errors: list[str] = []
        if expected_sha and head_sha and head_sha != expected_sha:
            equality_errors.append("local HEAD differs from expected candidate SHA")
        if expected_sha and remote_sha and remote_sha != expected_sha:
            equality_errors.append("remote main SHA differs from expected candidate SHA")
        if head_sha and remote_sha and head_sha != remote_sha:
            equality_errors.append("local HEAD differs from observed remote main SHA")
        if not remote_sha:
            equality_errors.append("remote main SHA was not observed")
        if equality_errors:
            errors.extend(equality_errors)
            _record(checks, "expected_remote_local_sha_equality", "FAIL", equality_errors)
        else:
            _record(checks, "expected_remote_local_sha_equality", "PASS")
    else:
        branch, _branch_error = _probe("branch", "--show-current")
        head_sha, _head_error = _probe("rev-parse", "HEAD")

    lifecycle_errors = lifecycle.validate()
    _record(checks, "release_lifecycle", "PASS" if not lifecycle_errors else "FAIL", lifecycle_errors)
    errors.extend(lifecycle_errors)
    if post_publication:
        content_errors: list[str] = []
        if lifecycle_record.get("content_phase") != "RELEASE_READY":
            content_errors.append("post-publication check requires content_phase RELEASE_READY")
        if not lifecycle_record.get("current_task_terminal"):
            content_errors.append("post-publication check requires terminal Current task")
        _record(checks, "content_release_ready", "PASS" if not content_errors else "FAIL", content_errors)
        errors.extend(content_errors)
    else:
        content_errors = []
        if lifecycle_record.get("content_phase") not in {"RUNNING", "TERMINAL_CANDIDATE", "RELEASE_READY"}:
            content_errors.append("pre-publication check requires a valid content-owned lifecycle phase")
        _record(checks, "content_lifecycle", "PASS" if not content_errors else "FAIL", content_errors)
        errors.extend(content_errors)

    state_model_errors = state_model.validate()
    _record(checks, "release_state_model", "PASS" if not state_model_errors else "FAIL", state_model_errors)
    errors.extend(state_model_errors)

    facts_errors = generate_current_facts.check()
    _record(checks, "current_facts", "PASS" if not facts_errors else "FAIL", facts_errors)
    errors.extend(facts_errors)
    snapshot_errors = build_current_snapshot.check()
    _record(checks, "current_snapshot", "PASS" if not snapshot_errors else "FAIL", snapshot_errors)
    errors.extend(snapshot_errors)
    try:
        snapshot = build_current_snapshot.build_snapshot()
        publication_errors = _validate_static_publication_semantics(snapshot, lifecycle_record)
    except Exception as exc:  # pragma: no cover - defensive gate reporting
        snapshot = {}
        publication_errors = [f"cannot build Current Snapshot for publication semantics: {type(exc).__name__}"]
    _record(checks, "static_publication_semantics", "PASS" if not publication_errors else "FAIL", publication_errors)
    errors.extend(publication_errors)

    if expected_task_id is None:
        _record(checks, "task_id_binding", "NOT_APPLICABLE", ["task-id binding is enforced when expected_task_id is supplied"])
    else:
        contract_identity = load_json(EXECUTION_CONTRACT_PATH)
        task_binding_errors = _validate_task_id_binding(
            expected_task_id=expected_task_id,
            formal_result_task_id=formal_result_task_id,
            contract=contract_identity,
            lineage_record=lineage_record,
            lifecycle_record=lifecycle_record,
            snapshot=snapshot,
        )
        observed_formal_result_task_id = _formal_result_task_id()
        if observed_formal_result_task_id is None:
            task_binding_errors.append("FORMAL_RESULT_TASK_ID_NOT_OBSERVED")
        elif formal_result_task_id != observed_formal_result_task_id:
            task_binding_errors.append(
                "FORMAL_RESULT_TASK_ID_FILE_MISMATCH:"
                f"expected={formal_result_task_id}:observed={observed_formal_result_task_id}"
            )
        _record(checks, "task_id_binding", "PASS" if not task_binding_errors else "FAIL", task_binding_errors)
        errors.extend(task_binding_errors)

    contract = load_json(CONTRACT_PATH)
    compiler_errors: list[str] = []
    for surface in contract["surfaces"]:
        path = REPO_ROOT / surface["path"]
        if not path.is_file():
            compiler_errors.append(f"missing surface: {surface['surface_id']}")
            continue
        source = path.read_text(encoding="utf-8")
        try:
            expected = current_surface_compiler.compile_surface(source, surface, snapshot=snapshot)
        except Exception as exc:
            compiler_errors.append(f"cannot compile surface {surface['surface_id']}: {type(exc).__name__}")
            continue
        if source != expected:
            compiler_errors.append(f"stale compiler output: {surface['surface_id']}")
    _record(checks, "current_surface_compiler", "PASS" if not compiler_errors else "FAIL", compiler_errors)
    errors.extend(compiler_errors)

    semantic_result = semantics.validate_repository()
    semantic_errors = semantic_result["issues"]
    _record(checks, "typed_semantic_gate", "PASS" if not semantic_errors else "FAIL", semantic_errors)
    errors.extend(str(item) for item in semantic_errors)

    lineage_errors = task_lineage.validate()
    _record(checks, "task_lineage", "PASS" if not lineage_errors else "FAIL", lineage_errors)
    errors.extend(lineage_errors)
    sync_errors = state_sync.run_check()
    _record(checks, "current_state_sync", "PASS" if not sync_errors else "FAIL", sync_errors)
    errors.extend(sync_errors)

    if post_publication:
        status, status_error = _probe("status", "--porcelain=v1", "--untracked-files=all")
        if status_error:
            blocked = True
            errors.append("cannot inspect working tree cleanliness")
            _record(checks, "clean_worktree", "BLOCKED_WITH_EVIDENCE", [status_error])
        elif status:
            errors.append("fresh post-publication checkout working tree is not clean")
            _record(checks, "clean_worktree", "FAIL", ["working tree has changes"])
        else:
            _record(checks, "clean_worktree", "PASS")
    else:
        _record(checks, "clean_worktree", "NOT_APPLICABLE", ["clean clone is enforced only in post-publication mode"])

    if post_publication and blocked:
        result = "BLOCKED_WITH_EVIDENCE"
    else:
        result = "PASS" if not errors else "FAIL"
    return {
        "schema_version": "post-publication-current-check-r2",
        "task_id": task_id,
        "mode": "POST_PUBLICATION" if post_publication else "PRE_PUBLICATION",
        "result": result,
        "head_sha": head_sha,
        "branch": branch,
        "expected_sha": expected_sha,
        "expected_task_id": expected_task_id,
        "formal_result_task_id": formal_result_task_id,
        "observed_ref": REMOTE_REF if post_publication else None,
        "observed_remote_sha": remote_sha,
        "checks": checks,
        "errors": errors,
        "claim_ceiling": "Fresh-clone Current and observation-time Git ref evidence only; this does not prove external truth, production readiness, Owner acceptance or epistemic acceptance."
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--pre-publication", action="store_true")
    mode.add_argument("--post-publication", action="store_true")
    parser.add_argument("--expected-sha")
    parser.add_argument("--expected-task-id")
    parser.add_argument("--formal-result-task-id")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = run_checks(
        post_publication=args.post_publication,
        expected_sha=args.expected_sha,
        expected_task_id=args.expected_task_id,
        formal_result_task_id=args.formal_result_task_id,
    )
    if args.write:
        REPORT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"POST_PUBLICATION_CURRENT_CHECK_WRITTEN path={relative(REPORT_PATH)} result={result['result']}")
    if result["result"] != "PASS":
        print(f"POST_PUBLICATION_CURRENT_CHECK_INVALID result={result['result']}", file=sys.stderr)
        for error in result["errors"]:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"POST_PUBLICATION_CURRENT_CHECK_OK mode={result['mode']} head={result['head_sha']} remote={result['observed_remote_sha'] or 'not-observed'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
