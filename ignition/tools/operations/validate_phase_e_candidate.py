#!/usr/bin/env python3
"""Machine validation for Q32I Phase E self-hosting and lifecycle closeout."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.operations.plan_incremental_execution import plan, build_authority_bundle, git_json, git_show_text

REQUEST = ROOT / "data/operations/propagation/121Q32I-request.json"
DEMO = ROOT / "reports/operations/121Q32I-incremental-execution-demonstration.json"
MANIFEST = ROOT / "data/operations/iterations/121Q32I.json"
SEAL = ROOT / "reports/operations/121Q32I-completion-seal.json"
Q29R = ROOT / "docs/publication/works/when-an-army-believes-its-own-back.md"
Q29R_SHA256 = "c135acd35a2232f0a6b3f933db482932a9fe5d5add51f870af97901faac90d4b"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok: bool, code: str, message: str) -> None:
    if not ok:
        raise ValueError(f"{code}: {message}")


def sha256_at(commit: str, rel: str) -> str:
    """sha256 of a repository file at a git revision; fail closed if absent."""
    try:
        content = git_show_text(commit, rel)
    except (ValueError, FileNotFoundError, OSError) as exc:
        raise ValueError(f"era input unavailable for {rel}@{commit}: {exc}")
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def resolve_demo_era_ref(demo: dict, lower_commit: str, ceiling: str = "HEAD") -> str:
    """Resolve the sealed git revision that produced the persisted Q32I demo.

    The revision must (a) carry the demo's recorded authority digests and
    (b) re-derive the demo's exact plan_hash. The lower bound is the Q32I
    merge commit (a provable sealed manifest field); the walk is bounded by
    the current HEAD. The era ref is therefore derived from the manifest's
    sealed field plus the demo's explicit contract, never hardcoded. Fail
    closed if no revision reproduces the contract.
    """
    dd = demo.get("authority_digests", {})
    target_plan_hash = demo["planner_output"]["plan_hash"]
    req_rel = str(REQUEST.relative_to(ROOT))
    rels = [
        "data/operations/project-components.json",
        "data/operations/change-propagation-topology.json",
        "data/operations/component-execution-profiles.json",
    ]
    for commit in subprocess.check_output(
        ["git", "rev-list", f"{lower_commit}..{ceiling}"], cwd=ROOT, text=True
    ).split():
        try:
            snap = {r: sha256_at(commit, r) for r in rels}
        except ValueError:
            continue
        if any(snap[r] != dd.get(r) for r in rels):
            continue
        try:
            era_request = git_json(commit, req_rel)
            bundle, fp = build_authority_bundle(commit)
            recomputed = plan(era_request, era_ref=commit, authority_bundle=bundle, authority_fingerprint_value=fp)
        except (ValueError, KeyError, json.JSONDecodeError, OSError):
            continue
        if recomputed["plan_hash"] == target_plan_hash:
            return commit
    raise ValueError(
        "E_PHASE_E_ERA_PROVENANCE: no git revision between the Q32I merge commit "
        "and HEAD reproduces the persisted demonstration plan_hash under its "
        "recorded authority digests"
    )


def validate(root: Path = ROOT) -> dict:
    request, demo, manifest, seal = map(
        load,
        [root / REQUEST.relative_to(ROOT), root / DEMO.relative_to(ROOT), root / MANIFEST.relative_to(ROOT), root / SEAL.relative_to(ROOT)],
    )
    candidate_lifecycle = {"candidate": True, "ready_for_gpt_verification": True, "accepted": False, "merged": False, "current": False}
    current_lifecycle = {"candidate": False, "ready_for_gpt_verification": True, "accepted": True, "merged": True, "current": True}
    lifecycle = manifest.get("status")
    require(lifecycle in (candidate_lifecycle, current_lifecycle), "E_PHASE_E_LIFECYCLE", "lifecycle is inflated or inconsistent")

    # Sealed-era binding: a Current/merged iteration is validated against the
    # git revision that actually produced the persisted demo, not the live
    # working tree. Open candidates keep using live authority inputs.
    if lifecycle == current_lifecycle:
        _ler = resolve_demo_era_ref(demo, manifest["branch_pr"]["merge_commit"])
        _request = git_json(_ler, str(REQUEST.relative_to(ROOT)))
        _bundle, _expected_authority = build_authority_bundle(_ler)
    else:
        _ler = None
        _request = request
        _bundle, _expected_authority = build_authority_bundle(None)
    actual_plan = plan(_request, era_ref=_ler, authority_bundle=_bundle, authority_fingerprint_value=_expected_authority)

    require(demo.get("planner_output") == actual_plan, "E_PHASE_E_STALE_PLAN", "demonstration is not the real deterministic planner output")
    require(actual_plan.get("full_rebuild_components") and len(actual_plan["full_rebuild_components"]) == len(actual_plan["component_decisions"]), "E_PHASE_E_FULL_REBUILD", "Q32I authority changes must force every registered component to FULL_REBUILD_REQUIRED")
    require(not actual_plan.get("unresolved_residue"), "E_PHASE_E_PLAN_RESIDUE", "planner has unresolved residue")
    require(demo.get("authority_fingerprint") == _expected_authority, "E_PHASE_E_AUTHORITY", "authority fingerprint mismatch")
    require(demo.get("validator_result") == {"status": "PASS", "error_code": None}, "E_PHASE_E_VALIDATOR", "demonstration validator result is not PASS")
    require(manifest.get("method_version") == "1.3.0" and seal.get("method_version") == "1.3.0", "E_PHASE_E_VERSION", "method version must be 1.3.0")
    require(lifecycle == seal.get("lifecycle"), "E_PHASE_E_LIFECYCLE", "manifest and seal lifecycle diverge")
    if lifecycle == current_lifecycle:
        branch_pr = manifest.get("branch_pr", {})
        require(branch_pr.get("pr_number") == 62 and branch_pr.get("draft") is False and branch_pr.get("merged") is True, "E_PHASE_E_MERGE", "Current lifecycle lacks merged PR #62 evidence")
        require(branch_pr.get("merge_commit") == "0a13c246172c0338bf8dda5dc08db5a574a8b23f", "E_PHASE_E_MERGE", "Current lifecycle has wrong merge commit")
        chain = {(item.get("phase"), item.get("commit")) for item in manifest.get("commit_chain", [])}
        require(("ACCEPTED_CANDIDATE", "0da9ab7a90bc133190d1684a6da4c8f0750021f2") in chain, "E_PHASE_E_REVIEW", "accepted exact candidate is absent")
        require(("MERGE", "0a13c246172c0338bf8dda5dc08db5a574a8b23f") in chain, "E_PHASE_E_MERGE", "merge evidence is absent")
        require(manifest.get("head_binding", {}).get("review_receipt_commit") == "e4178f4310822d085ce8201b95236bc2ebc48d69", "E_PHASE_E_REVIEW", "independent review receipt is absent")
    require(manifest.get("self_hosting", {}).get("plan_hash") == actual_plan["plan_hash"] == seal.get("self_hosting", {}).get("plan_hash"), "E_PHASE_E_PLAN_HASH", "plan hash binding mismatch")
    q29r_ref = _ler or manifest.get("candidate_head") or "HEAD"
    q29r_historical_sha = sha256_at(q29r_ref, str(Q29R.relative_to(ROOT)))
    require(manifest.get("q29r", {}).get("sha256") == Q29R_SHA256 == seal.get("q29r", {}).get("sha256") == q29r_historical_sha, "E_PHASE_E_Q29R", "Q29R frozen hash mismatch")
    require(seal.get("phase_b", {}).get("head_binding", {}).get("embedded_exact_current_head") is False, "E_PHASE_E_SELF_HEAD", "seal must not embed its own current HEAD")
    require(seal.get("boundaries", {}).get("phase_e_candidate_only") is (lifecycle == candidate_lifecycle) and seal.get("boundaries", {}).get("q33_or_q40_started") is False, "E_PHASE_E_SCOPE", "Phase E scope boundary mismatch")
    # Diff coverage is only meaningful for open candidates; a Current/merged
    # iteration's base..HEAD span legitimately includes later work (Q33+).
    if lifecycle == candidate_lifecycle:
        diff = set(subprocess.check_output(["git", "diff", "--name-only", f"{request['base_identity']}...HEAD"], cwd=root, text=True).splitlines())
        if subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True).strip():
            diff |= set(subprocess.check_output(["git", "diff", "--name-only", request["base_identity"]], cwd=root, text=True).splitlines())
            diff |= set(subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=root, text=True).splitlines())
        generated = {item["path"] for item in load(root / "data/operations/generated-output-authority.json")["generated_outputs"]}
        covered = set(request["changed_paths"]) | (generated & diff)
        require(diff == covered, "E_PHASE_E_DIFF_COVERAGE", f"base-to-HEAD paths differ from request plus generated authority: missing={sorted(diff-covered)} stale={sorted(covered-diff)}")
    return {"status": "PASS", "plan_hash": actual_plan["plan_hash"], "components": len(actual_plan["component_decisions"]), "decision": "FULL_REBUILD_REQUIRED", "claim_ceiling": demo["claim_ceiling"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    try:
        print(json.dumps(validate(), sort_keys=True))
        return 0
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
