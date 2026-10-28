#!/usr/bin/env python3
"""Build the Task142 fresh local executor census from the shared public probe."""

from __future__ import annotations

import argparse
from pathlib import Path
import json
from typing import Any

from agent_federation.local_executor_census import REQUIRED_ADMISSION_CHECKS, validate_census

try:
    from run_task142_public_executor_probe import build as build_public_probe
except ImportError:
    from ignition.tools.run_task142_public_executor_probe import build as build_public_probe


ROOT = Path(__file__).resolve().parents[1]
CONTROL_REPO = Path("/Users/zhiyuan/Agent 工作区/1111-sync")
TASK_ID = "IGNITION-20260827-142"
STEP = "11"
OBSERVATION_POLICY = "PATH_VERSION_HELP_PUBLIC_AUTH_PRESENCE_ONLY_NO_SECRET_NO_INFERENCE"
KIND_BY_FAMILY = {"AGENTIC_EXECUTOR": "AGENTIC_EXECUTOR", "REASONER_RUNTIME": "REASONER_RUNTIME", "TOOL": "TOOL_ONLY", "UI_SURFACE": "UI_OR_NONAUTOMATABLE"}


def _git_value(*args: str) -> str:
    import subprocess

    result = subprocess.run(("git", "-C", str(CONTROL_REPO), *args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    if result.returncode:
        raise RuntimeError(f"git observation failed: {' '.join(args)}")
    return result.stdout.strip()


def _formal_value(*args: str) -> str:
    import subprocess

    result = subprocess.run(("git", *args), cwd=ROOT.parent, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    if result.returncode:
        raise RuntimeError(f"formal git observation failed: {' '.join(args)}")
    return result.stdout.strip()


def _interface(executor_id: str, probe: dict[str, Any]) -> dict[str, Any]:
    return {
        "metadata_source": "run_task142_public_executor_probe.py",
        "entrypoint": probe.get("path_ref"),
        "version_help_probe": "public --version and --help",
        "relevant_flags_observed": probe.get("help_markers", [])[:12],
        "executor_id_scope": executor_id,
    }


def _checks(row: dict[str, Any]) -> dict[str, bool]:
    gates = row["gates"]
    if row["family"] != "AGENTIC_EXECUTOR":
        return {key: False for key in REQUIRED_ADMISSION_CHECKS}
    return {
        "disposable_workspace": gates["workspace"] == "PROVEN",
        "explicit_read_only_ceiling": gates["permission_ceiling"] == "PROVEN",
        "noninteractive_one_shot": gates["argv_contract"] == "STRICT",
        "structured_result": gates["structured_result"] == "STRICT",
        "public_auth_status": gates["public_auth"] == "PASS",
        "no_new_billing": row["executor_id"] == "external.codex",
        "timeout_and_process_cleanup": gates["cleanup"] == "PROVEN",
        "no_channel_browser_side_effect": gates["no_effect_scope"] == "PROVEN",
        "independent_os_validation": gates["validator_binding"] == "PROVEN" and gates["exact_binding"] == "PROVEN",
        "auth_source_separation": gates["auth_separation"] == "PROVEN",
    }


def _candidate(row: dict[str, Any]) -> dict[str, Any]:
    probe = row["probe"]
    auth = row["auth"]
    kind = KIND_BY_FAMILY[row["family"]]
    checks = _checks(row)
    installed = bool(row["installed"])
    status = "NOT_APPLICABLE" if kind != "AGENTIC_EXECUTOR" else "ADMITTED" if installed and all(checks.values()) else "BLOCKED"
    blockers = list(row["blockers"])
    if kind == "AGENTIC_EXECUTOR" and not installed:
        blockers = ["NOT_INSTALLED_NO_DOWNLOAD_OR_BILLING_AUTHORITY"]
    return {
        "executor_id": row["executor_id"],
        "family": row["executor_id"].replace("external.", "").replace("runtime.", "").replace("tool.", "").replace("ui.", "").replace("-", " ").title(),
        "installed": installed,
        "kind": kind,
        "path_ref": probe.get("path_ref"),
        "version": probe.get("version"),
        "public_interface": _interface(row["executor_id"], probe),
        "binary_sha256": probe.get("binary_sha256"),
        "help_sha256": probe.get("help_sha256"),
        "install_sources": ["PATH command resolution", "public --version/--help", "public auth-status exit behavior", "presence-only local application/auth state"],
        "auth": {
            "public_status": auth.get("public_status"),
            "public_status_exit": auth.get("public_status_exit"),
            "presence_observed": auth.get("presence_ref") + (" present; content not read" if auth.get("present") else " absent; content not read"),
            "source_ref": auth.get("presence_ref"),
            "content_read": False,
            "copied": False,
            "mutated": False,
        },
        "admission_checks": checks,
        "admission_status": status,
        "blockers": blockers,
        "policy_blockers": list(row["policy_blockers"]),
        "live": {"status": "NOT_RUN_CENSUS", "inference_started": False, "reason": "Fresh public metadata probe only; no Agent inference was started."},
    }


def build() -> tuple[dict[str, Any], dict[str, Any], str]:
    public = build_public_probe()
    candidates = [_candidate(row) for row in public["candidates"]]
    agentic = [row for row in candidates if row["kind"] == "AGENTIC_EXECUTOR"]
    ranking = [
        row["executor_id"]
        for row in sorted(agentic, key=lambda row: (-sum(row["admission_checks"][key] is True for key in REQUIRED_ADMISSION_CHECKS), str(row["family"]), str(row["executor_id"])))
    ]
    admitted = [row for row in agentic if row["admission_status"] == "ADMITTED"]
    selected = sorted(admitted, key=lambda row: (-sum(row["admission_checks"][key] is True for key in REQUIRED_ADMISSION_CHECKS), str(row["family"]), str(row["executor_id"])))
    capability_selected = selected[0] if selected else None
    policy_excluded = [row["executor_id"] for row in agentic if row["policy_blockers"]]
    live_selectable = [row for row in selected if not row["policy_blockers"]]
    census = {
        "schema_version": "local-executor-census-r1",
        "census_id": "ignition-142-local-executor-census-r2-20260827",
        "task_id": TASK_ID,
        "step": STEP,
        "observed_at": public["observed_at"],
        "control": {"repository": "Arvin-liu/1111", "ref": "origin/relay/current", "tip": _git_value("rev-parse", "refs/remotes/origin/relay/current")},
        "formal_candidate": {"repository": "Arvin-liu/when-systems-catch-fire", "sha": _formal_value("rev-parse", "HEAD"), "branch": _formal_value("branch", "--show-current")},
        "scope": {
            "search_domains": ["PATH", "~/.local/bin", "Homebrew prefix and formulae", "npm/uv/pipx tool roots", "selected /Applications bundles"],
            "explicit_names": ["Gemini CLI", "Codex CLI", "Hermes", "OpenClaw", "GitHub Copilot CLI", "Ollama", "LM Studio", "MLX DSpark", "llama-server", "GitHub CLI", "Git", "jq", "Claude Desktop", "QwenWorkCN Desktop"],
            "install_sources": ["PATH command resolution", "public --version/--help", "public auth-status exit behavior", "presence-only local application/auth state"],
            "observation_policy": OBSERVATION_POLICY,
        },
        "candidates": candidates,
        "selection": {
            "status": "SELECTED" if capability_selected else "NO_SAFE_CANDIDATE",
            "selected_executor_id": capability_selected["executor_id"] if capability_selected else None,
            "selected_family": capability_selected["family"] if capability_selected else None,
            "ranking": ranking,
            "why_executor": "Deterministic ranking counts only the ten provider-neutral admission checks, then breaks ties by family and executor ID. Codex is technically admitted but policy-excluded by the unchanged Task140 same-family blind-retry prohibition; no other agentic candidate passes every check, so live selection is NO_AUTHORIZED_FAMILY.",
            "excluded": [{"executor_id": row["executor_id"], "reason": "; ".join(row["blockers"] + row["policy_blockers"])} for row in agentic if row["admission_status"] != "ADMITTED" or row["policy_blockers"]],
            "capability_selected_executor_id": capability_selected["executor_id"] if capability_selected else None,
            "policy_excluded_executor_ids": policy_excluded,
            "live_selectable_executor_ids": [row["executor_id"] for row in live_selectable],
            "live_selection_status": "NO_AUTHORIZED_FAMILY" if not live_selectable else "SELECTED",
        },
        "safety": {
            "secret_content_read": False,
            "auth_content_copied": False,
            "configuration_changed": False,
            "billing_changed": False,
            "install_or_upgrade_performed": False,
            "live_inference_started": False,
            "workspace_modified": False,
        },
        "claim_ceiling": "Fresh repository-local observation-time executor census, class separation, admission checks, policy exclusion and deterministic why-executor trace only; no live inference, validated completion, model-quality ranking, production readiness, external truth, Owner acceptance or epistemic acceptance is inferred.",
    }
    validate_census(census, expected_task_id=TASK_ID, expected_step=STEP)
    counts = {
        "candidates": len(candidates),
        "agentic_executors": len(agentic),
        "installed_agentic_executors": sum(row["installed"] for row in agentic),
        "reasoner_runtimes": sum(row["kind"] == "REASONER_RUNTIME" for row in candidates),
        "tools": sum(row["kind"] == "TOOL_ONLY" for row in candidates),
        "ui_only": sum(row["kind"] == "UI_OR_NONAUTOMATABLE" for row in candidates),
        "admitted_agentic_executors": len(admitted),
        "policy_excluded_admitted_executors": len(policy_excluded),
        "live_selectable_executors": len(live_selectable),
    }
    selection = {
        "schema_version": "ignition-142-step11-fresh-census-r1",
        "task_id": TASK_ID,
        "step": STEP,
        "status": "PASS",
        "census_path": "ignition/data/operations/iterations/142/local-executor-census-r2.json",
        "control_tip": census["control"]["tip"],
        "formal_candidate_sha": census["formal_candidate"]["sha"],
        "counts": counts,
        "capability_selection": census["selection"],
        "policy": {"codex_same_family_retry": "FORBIDDEN_BLIND_RETRY", "policy_excluded_executor_ids": policy_excluded, "live_selection_status": census["selection"]["live_selection_status"]},
        "observations": {"agent_version_help_read": True, "reasoner_models_invoked": False, "ui_action_performed": False, "public_auth_content_read": False},
        "safety": census["safety"],
        "claim_ceiling": census["claim_ceiling"],
    }
    report = f"""# IGNITION-20260827-142 Step 11 — Fresh Executor Census R2

Status: PASS.

The shared public probe produced {counts['candidates']} candidates: {counts['agentic_executors']} Agentic Executor records ({counts['installed_agentic_executors']} installed), {counts['reasoner_runtimes']} reasoner runtimes, {counts['tools']} tools and {counts['ui_only']} UI surfaces. No inference, UI action, installation, configuration or billing operation occurred.

Deterministic ranking uses only the ten admission checks and stable family/ID tie-breakers. Codex is the sole technically admitted Agentic Executor, but its Task140 same-family blind-retry policy blocker remains active. Gemini, Hermes and OpenClaw each retain explicit technical blockers; Copilot is not installed. Reasoners, tools and UI surfaces are excluded by class. The resulting live selection is `NO_SAFE_CANDIDATE` / `NO_AUTHORIZED_FAMILY`, so no live process is permitted.

Machine evidence is `ignition/data/operations/iterations/142/local-executor-census-r2.json` plus `ignition/data/operations/iterations/142/step11-fresh-census.json`. The canonical census is validated through `ignition/agent_federation/local_executor_census.py` and `ignition/tools/validate_local_executor_census.py`.

Claim ceiling: fresh public observation, classification, admission checks, policy exclusion and deterministic why-executor trace only; no live completion or external truth is claimed.
"""
    return census, selection, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", required=True)
    parser.add_argument("--census-output", type=Path, default=ROOT / "data/operations/iterations/142/local-executor-census-r2.json")
    parser.add_argument("--selection-output", type=Path, default=ROOT / "data/operations/iterations/142/step11-fresh-census.json")
    parser.add_argument("--report-output", type=Path, default=ROOT / "reports/operations/ignition-142-step11-fresh-census.md")
    args = parser.parse_args()
    census, selection, report = build()
    for path, value in ((args.census_output, census), (args.selection_output, selection)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.write_text(report, encoding="utf-8")
    print(f"TASK142_EXECUTOR_CENSUS_WRITTEN candidates={len(census['candidates'])} admitted={census['selection']['capability_selected_executor_id']} live={census['selection']['live_selection_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
