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
from tools.operations.plan_incremental_execution import plan
from tools.operations.validate_incremental_execution import authority_fingerprint

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


def validate(root: Path = ROOT) -> dict:
    request, demo, manifest, seal = map(load, [root / REQUEST.relative_to(ROOT), root / DEMO.relative_to(ROOT), root / MANIFEST.relative_to(ROOT), root / SEAL.relative_to(ROOT)])
    actual_plan = plan(request)
    require(demo.get("planner_output") == actual_plan, "E_PHASE_E_STALE_PLAN", "demonstration is not the real deterministic planner output")
    require(actual_plan.get("full_rebuild_components") and len(actual_plan["full_rebuild_components"]) == len(actual_plan["component_decisions"]), "E_PHASE_E_FULL_REBUILD", "Q32I authority changes must force every registered component to FULL_REBUILD_REQUIRED")
    require(not actual_plan.get("unresolved_residue"), "E_PHASE_E_PLAN_RESIDUE", "planner has unresolved residue")
    expected_authority = authority_fingerprint(root / "data/operations/project-components.json", root / "data/operations/change-propagation-topology.json", root / "data/operations/component-execution-profiles.json")
    require(demo.get("authority_fingerprint") == expected_authority, "E_PHASE_E_AUTHORITY", "authority fingerprint mismatch")
    require(demo.get("validator_result") == {"status": "PASS", "error_code": None}, "E_PHASE_E_VALIDATOR", "demonstration validator result is not PASS")
    require(manifest.get("method_version") == "1.3.0" and seal.get("method_version") == "1.3.0", "E_PHASE_E_VERSION", "method version must be 1.3.0")
    lifecycle = manifest.get("status")
    require(lifecycle == seal.get("lifecycle"), "E_PHASE_E_LIFECYCLE", "manifest and seal lifecycle diverge")
    candidate_lifecycle = {"candidate": True, "ready_for_gpt_verification": True, "accepted": False, "merged": False, "current": False}
    current_lifecycle = {"candidate": False, "ready_for_gpt_verification": True, "accepted": True, "merged": True, "current": True}
    require(lifecycle in (candidate_lifecycle, current_lifecycle), "E_PHASE_E_LIFECYCLE", "lifecycle is inflated or inconsistent")
    if lifecycle == current_lifecycle:
        branch_pr = manifest.get("branch_pr", {})
        require(branch_pr.get("pr_number") == 62 and branch_pr.get("draft") is False and branch_pr.get("merged") is True, "E_PHASE_E_MERGE", "Current lifecycle lacks merged PR #62 evidence")
        require(branch_pr.get("merge_commit") == "0a13c246172c0338bf8dda5dc08db5a574a8b23f", "E_PHASE_E_MERGE", "Current lifecycle has wrong merge commit")
        chain = {(item.get("phase"), item.get("commit")) for item in manifest.get("commit_chain", [])}
        require(("ACCEPTED_CANDIDATE", "0da9ab7a90bc133190d1684a6da4c8f0750021f2") in chain, "E_PHASE_E_REVIEW", "accepted exact candidate is absent")
        require(("MERGE", "0a13c246172c0338bf8dda5dc08db5a574a8b23f") in chain, "E_PHASE_E_MERGE", "merge evidence is absent")
        require(manifest.get("head_binding", {}).get("review_receipt_commit") == "e4178f4310822d085ce8201b95236bc2ebc48d69", "E_PHASE_E_REVIEW", "independent review receipt is absent")
    require(manifest.get("self_hosting", {}).get("plan_hash") == actual_plan["plan_hash"] == seal.get("self_hosting", {}).get("plan_hash"), "E_PHASE_E_PLAN_HASH", "plan hash binding mismatch")
    require(manifest.get("q29r", {}).get("sha256") == Q29R_SHA256 == seal.get("q29r", {}).get("sha256") == sha(root / Q29R.relative_to(ROOT)), "E_PHASE_E_Q29R", "Q29R frozen hash mismatch")
    require(seal.get("phase_b", {}).get("head_binding", {}).get("embedded_exact_current_head") is False, "E_PHASE_E_SELF_HEAD", "seal must not embed its own current HEAD")
    require(seal.get("boundaries", {}).get("phase_e_candidate_only") is (lifecycle == candidate_lifecycle) and seal.get("boundaries", {}).get("q33_or_q40_started") is False, "E_PHASE_E_SCOPE", "Phase E scope boundary mismatch")
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
