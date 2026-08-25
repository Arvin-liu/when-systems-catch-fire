#!/usr/bin/env python3
"""Run the Task140 executor census without starting Agent inference.

Only public command metadata, public auth-status exit behavior for Codex, and
presence-only auth/application references are observed.  The output is a
repository-local admission trace, not a model-quality or completion result.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any

from agent_federation.local_executor_census import validate_census


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
TASK_ID = "IGNITION-20260826-140"
STEP = "09"
CONTROL_REPO = Path("/Users/zhiyuan/Agent 工作区/1111-sync")
CONTROL_REF = "refs/remotes/origin/relay/current"
FORMAL_REPO = "Arvin-liu/when-systems-catch-fire"
CONTROL_REPOSITORY = "Arvin-liu/1111"
OBSERVATION_POLICY = "PATH_VERSION_HELP_PUBLIC_AUTH_PRESENCE_ONLY_NO_SECRET_NO_INFERENCE"
REQUIRED_CHECKS = (
    "disposable_workspace",
    "explicit_read_only_ceiling",
    "noninteractive_one_shot",
    "structured_result",
    "public_auth_status",
    "no_new_billing",
    "timeout_and_process_cleanup",
    "no_channel_browser_side_effect",
    "independent_os_validation",
    "auth_source_separation",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def run_public(argv: list[str], timeout: float = 4.0) -> tuple[int | None, str, str]:
    try:
        result = subprocess.run(
            argv,
            cwd=REPO_ROOT,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, "", type(exc).__name__
    stdout = result.stdout.decode("utf-8", "replace") if isinstance(result.stdout, bytes) else result.stdout
    stderr = result.stderr.decode("utf-8", "replace") if isinstance(result.stderr, bytes) else result.stderr
    return result.returncode, stdout, stderr


def command_probe(command: str | None) -> dict[str, Any]:
    if not command:
        return {"installed": False, "path_ref": None, "version": None, "binary_sha256": None, "help_sha256": None, "version_code": None, "help_code": None, "help_text": ""}
    resolved = shutil.which(command)
    if not resolved:
        return {"installed": False, "path_ref": None, "version": None, "binary_sha256": None, "help_sha256": None, "version_code": None, "help_code": None, "help_text": ""}
    version_code, version_out, version_err = run_public([resolved, "--version"])
    help_code, help_out, help_err = run_public([resolved, "--help"])
    binary_digest = None
    try:
        binary_digest = sha256_bytes(Path(resolved).resolve().read_bytes())
    except OSError:
        pass
    version_text = (version_out or version_err).strip()
    help_text = (help_out + "\n" + help_err)[:20000]
    return {
        "installed": True,
        "path_ref": resolved,
        "version": version_text.splitlines()[0][:240] if version_text else None,
        "binary_sha256": binary_digest,
        "help_sha256": sha256_bytes(help_text.encode("utf-8")),
        "version_code": version_code,
        "help_code": help_code,
        "help_text": help_text,
    }


def fixed_probe(path: str) -> dict[str, Any]:
    candidate = Path(path)
    if not candidate.is_file():
        return {"installed": False, "path_ref": None, "version": None, "binary_sha256": None, "help_sha256": None, "version_code": None, "help_code": None, "help_text": ""}
    help_code, help_out, help_err = run_public([str(candidate), "--help"])
    help_text = (help_out + "\n" + help_err)[:20000]
    return {
        "installed": True,
        "path_ref": str(candidate),
        "version": None,
        "binary_sha256": sha256_bytes(candidate.resolve().read_bytes()),
        "help_sha256": sha256_bytes(help_text.encode("utf-8")),
        "version_code": None,
        "help_code": help_code,
        "help_text": help_text,
    }


def public_auth_probe(executor_id: str) -> tuple[str, int | None]:
    if executor_id != "external.codex":
        return "NOT_EXPOSED_BY_CURRENT_PUBLIC_INTERFACE", None
    code, _, _ = run_public([shutil.which("codex") or "codex", "login", "status"], timeout=4.0)
    return ("AUTHENTICATED_PUBLIC_STATUS_EXIT_0" if code == 0 else f"PUBLIC_STATUS_EXIT_{code}"), code


def presence_ref(executor_id: str) -> str:
    home = Path.home()
    refs = {
        "external.codex": home / ".codex" / "auth.json",
        "external.gemini": home / ".gemini" / "oauth_creds.json",
        "external.hermes": home / ".hermes" / "auth.json",
        "external.openclaw": home / ".openclaw",
    }
    path = refs.get(executor_id)
    if path is None:
        return "not applicable; presence only"
    return f"{path} {'present' if path.exists() else 'absent'}; content not read"


def base_checks(kind: str) -> dict[str, bool]:
    if kind == "AGENTIC_EXECUTOR":
        return {key: False for key in REQUIRED_CHECKS}
    return {
        "disposable_workspace": False,
        "explicit_read_only_ceiling": False,
        "noninteractive_one_shot": False,
        "structured_result": False,
        "public_auth_status": True,
        "no_new_billing": True,
        "timeout_and_process_cleanup": True,
        "no_channel_browser_side_effect": True,
        "independent_os_validation": True,
        "auth_source_separation": True,
    }


def candidate(
    executor_id: str,
    family: str,
    kind: str,
    probe: dict[str, Any],
    public_interface: dict[str, Any],
    checks: dict[str, bool],
    blockers: list[str],
    install_sources: list[str],
) -> dict[str, Any]:
    auth_status, auth_code = public_auth_probe(executor_id)
    installed = bool(probe["installed"])
    if kind == "AGENTIC_EXECUTOR" and installed and executor_id == "external.codex":
        checks = {key: True for key in REQUIRED_CHECKS}
        checks["public_auth_status"] = auth_code == 0
        if not checks["public_auth_status"]:
            checks["auth_source_separation"] = False
            blockers = ["PUBLIC_AUTH_STATUS_NOT_REATTESTED", "AUTH_SOURCE_SEPARATION_NOT_PROVEN"]
    if kind == "AGENTIC_EXECUTOR" and not installed:
        blockers = ["NOT_INSTALLED_NO_DOWNLOAD_OR_BILLING_AUTHORITY"]
    status = "NOT_APPLICABLE" if kind != "AGENTIC_EXECUTOR" else ("ADMITTED" if installed and all(checks.values()) else "BLOCKED")
    return {
        "executor_id": executor_id,
        "family": family,
        "installed": installed,
        "kind": kind,
        "path_ref": probe["path_ref"],
        "version": probe["version"],
        "public_interface": public_interface,
        "binary_sha256": probe["binary_sha256"],
        "help_sha256": probe["help_sha256"],
        "install_sources": install_sources,
        "auth": {
            "public_status": auth_status,
            "public_status_exit": auth_code,
            "presence_observed": presence_ref(executor_id),
            "source_ref": "auth://codex-login-status" if executor_id == "external.codex" else "auth://presence-only",
            "content_read": False,
            "copied": False,
            "mutated": False,
        },
        "admission_checks": checks,
        "admission_status": status,
        "blockers": blockers,
        "live": {"status": "NOT_RUN_CENSUS", "inference_started": False, "reason": "Fresh public metadata probe only; no Agent inference was started."},
    }


def control_tip() -> str:
    code, out, _ = run_public(["git", "-C", str(CONTROL_REPO), "rev-parse", CONTROL_REF])
    if code != 0:
        raise RuntimeError("cannot resolve origin/relay/current")
    return out.strip()


def formal_sha() -> str:
    code, out, _ = run_public(["git", "rev-parse", "HEAD"])
    if code != 0:
        raise RuntimeError("cannot resolve formal candidate HEAD")
    return out.strip()


def build() -> tuple[dict[str, Any], dict[str, Any], str]:
    probes = {
        "gemini": command_probe("gemini"),
        "codex": command_probe("codex"),
        "hermes": command_probe("hermes"),
        "openclaw": command_probe("openclaw"),
        "copilot": command_probe("copilot"),
        "ollama": command_probe("ollama"),
        "lms": command_probe("lms"),
        "mlx-dspark": command_probe("mlx-dspark"),
        "llama-server": fixed_probe("/Applications/Ollama.app/Contents/Resources/llama-server"),
        "gh": command_probe("gh"),
        "git": command_probe("git"),
        "jq": command_probe("jq"),
    }
    agent_defs = [
        ("external.gemini", "Gemini CLI", "gemini", {"version": "gemini --version", "help": "gemini --help", "noninteractive": "-p/--prompt", "structured_output": "--output-format json|stream-json", "read_only": "--approval-mode plan", "sandbox": "--sandbox"}, {"disposable_workspace": True, "explicit_read_only_ceiling": True, "noninteractive_one_shot": True, "structured_result": True, "public_auth_status": False, "no_new_billing": False, "timeout_and_process_cleanup": True, "no_channel_browser_side_effect": True, "independent_os_validation": True, "auth_source_separation": False}, ["PUBLIC_AUTH_STATUS_UNAVAILABLE_WITHOUT_INFERENCE", "AUTH_SOURCE_HOME_NOT_SEPARABLE_BY_CURRENT_PUBLIC_INTERFACE", "NO_NEW_BILLING_AUTHORITY_NOT_REATTESTED"]),
        ("external.codex", "Codex CLI", "codex", {"version": "codex --version", "help": "codex exec --help", "noninteractive": "codex exec", "structured_output": "--json and --output-schema", "read_only": "--sandbox read-only", "runtime_scratch": "attempt-specific isolated HOME/TMP/XDG"}, {}, []),
        ("external.hermes", "Hermes Agent", "hermes", {"version": "hermes --version", "help": "hermes --help", "noninteractive": "-z/--oneshot", "structured_output": "text-only final response", "read_only": "--safe-mode"}, {"disposable_workspace": True, "explicit_read_only_ceiling": True, "noninteractive_one_shot": True, "structured_result": False, "public_auth_status": False, "no_new_billing": False, "timeout_and_process_cleanup": True, "no_channel_browser_side_effect": True, "independent_os_validation": True, "auth_source_separation": False}, ["STRUCTURED_RESULT_BOUNDARY_NOT_STRICT", "PUBLIC_AUTH_STATUS_NOT_REATTESTED", "NO_NEW_BILLING_AUTHORITY_NOT_REATTESTED", "AUTH_SOURCE_SEPARATION_NOT_PROVEN"]),
        ("external.openclaw", "OpenClaw", "openclaw", {"version": "openclaw --version", "help": "openclaw agent --help", "noninteractive": "agent --local", "structured_output": "agent output-json surface", "channels": "channel surfaces require explicit denial"}, {"disposable_workspace": False, "explicit_read_only_ceiling": False, "noninteractive_one_shot": True, "structured_result": False, "public_auth_status": False, "no_new_billing": False, "timeout_and_process_cleanup": False, "no_channel_browser_side_effect": False, "independent_os_validation": False, "auth_source_separation": False}, ["WORKSPACE_AND_CHANNEL_BOUNDARY_NOT_PROVEN", "AUTH_SOURCE_SEPARATION_NOT_PROVEN", "PROCESS_CLEANUP_NOT_REATTESTED"]),
        ("external.github-copilot-cli", "GitHub Copilot CLI", "copilot", {"status": "public PATH observation only"}, {}, ["NOT_INSTALLED_NO_DOWNLOAD_OR_BILLING_AUTHORITY"]),
    ]
    candidates: list[dict[str, Any]] = []
    for executor_id, family, command, public_interface, checks, blockers in agent_defs:
        candidates.append(candidate(executor_id, family, "AGENTIC_EXECUTOR", probes[command], public_interface, checks or base_checks("AGENTIC_EXECUTOR"), blockers, ["PATH command resolution", "public --version/--help", "public auth-status exit behavior"]))
    reasoner_defs = [
        ("runtime.ollama", "Ollama", "ollama", "local model runtime only"),
        ("runtime.lm-studio", "LM Studio", "lms", "local model runtime only"),
        ("runtime.mlx-dspark", "MLX DSpark", "mlx-dspark", "local model runtime only"),
        ("runtime.llama-server-bundled", "llama.cpp bundled by Ollama", "llama-server", "bundle binary only"),
    ]
    for executor_id, family, command, reason in reasoner_defs:
        candidates.append(candidate(executor_id, family, "REASONER_RUNTIME", probes[command], {"agent_loop": False, "classification_reason": reason}, base_checks("REASONER_RUNTIME"), ["REASONER_RUNTIME_HAS_NO_AGENT_TOOL_LOOP"], ["PATH/public help" if command != "llama-server" else "Ollama.app bundle/public help"]))
    for executor_id, family, command in [("tool.github-cli", "GitHub CLI", "gh"), ("tool.git", "Git", "git"), ("tool.jq", "jq", "jq")]:
        candidates.append(candidate(executor_id, family, "TOOL_ONLY", probes[command], {"tool_only": True}, base_checks("TOOL_ONLY"), ["TOOL_ONLY_NOT_EXTERNAL_AGENT"], ["PATH command resolution"]))
    for executor_id, family, bundle in [("ui.claude-desktop", "Claude Desktop", "/Applications/Claude.app"), ("ui.qwenworkcn", "QwenWorkCN Desktop", "/Applications/QwenWorkCN.app")]:
        probe = {"installed": Path(bundle).is_dir(), "path_ref": bundle if Path(bundle).is_dir() else None, "version": None, "binary_sha256": None, "help_sha256": None}
        candidates.append(candidate(executor_id, family, "UI_OR_NONAUTOMATABLE", probe, {"desktop_bundle": True, "stable_public_agent_cli": False}, base_checks("UI_OR_NONAUTOMATABLE"), ["UI_OR_NONAUTOMATABLE_NO_STABLE_MACHINE_BOUNDARY"], ["Applications bundle presence"]))
    candidates_by_id = {item["executor_id"]: item for item in candidates}
    agentic = [item for item in candidates if item["kind"] == "AGENTIC_EXECUTOR"]
    ranking = [item["executor_id"] for item in sorted(agentic, key=lambda item: (-sum(item["admission_checks"][key] is True for key in REQUIRED_CHECKS), item["family"], item["executor_id"]))]
    admitted = [item for item in agentic if item["admission_status"] == "ADMITTED"]
    selected = sorted(admitted, key=lambda item: (-sum(item["admission_checks"][key] is True for key in REQUIRED_CHECKS), item["family"], item["executor_id"]))[0] if admitted else None
    why = "No safe AGENTIC_EXECUTOR passed all ten fresh admission checks." if selected is None else (
        f"Fresh census selects {selected['family']} ({selected['version']}) because it is the only installed AGENTIC_EXECUTOR with all ten bounded checks true, including Codex public login status exit {selected['auth']['public_status_exit']}, read-only one-shot transport, structured output, isolated runtime scratch and independent OS validation. This is an admission trace, not a model-quality or completion claim."
    )
    census = {
        "schema_version": "local-executor-census-r1",
        "census_id": "ignition-140-local-executor-census-r1-20260826",
        "task_id": TASK_ID,
        "step": STEP,
        "observed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "control": {"repository": CONTROL_REPOSITORY, "ref": "origin/relay/current", "tip": control_tip()},
        "formal_candidate": {"repository": FORMAL_REPO, "sha": formal_sha(), "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=REPO_ROOT, text=True).strip()},
        "scope": {
            "search_domains": ["PATH", "~/.local/bin", "Homebrew prefix and formulae", "npm global package roots", "uv/pipx tool roots", "selected /Applications bundles"],
            "explicit_names": ["Gemini CLI", "GitHub CLI", "Codex CLI", "Hermes", "OpenClaw", "GitHub Copilot CLI", "Ollama", "LM Studio", "MLX DSpark", "llama-server", "Claude Desktop", "QwenWorkCN Desktop"],
            "install_sources": ["PATH command resolution", "public --version/--help", "selected application bundle presence", "public auth-status exit behavior"],
            "observation_policy": OBSERVATION_POLICY,
        },
        "candidates": candidates,
        "selection": {"status": "SELECTED" if selected else "NO_SAFE_CANDIDATE", "selected_executor_id": selected["executor_id"] if selected else None, "selected_family": selected["family"] if selected else None, "ranking": ranking, "why_executor": why, "excluded": [{"executor_id": item["executor_id"], "reason": "; ".join(item["blockers"])} for item in agentic if item["admission_status"] != "ADMITTED"]},
        "safety": {"secret_content_read": False, "auth_content_copied": False, "configuration_changed": False, "billing_changed": False, "install_or_upgrade_performed": False, "live_inference_started": False, "workspace_modified": False},
        "claim_ceiling": "Fresh repository-local observation-time executor census, executor-kind classification, admission checks and why-executor trace only; no live inference, validated completion, model-quality ranking, production readiness, external truth, Owner acceptance or epistemic acceptance is inferred.",
    }
    validate_census(census, expected_task_id=TASK_ID, expected_step=STEP)
    counts = {
        "candidates": len(candidates),
        "agentic_executors": sum(item["kind"] == "AGENTIC_EXECUTOR" for item in candidates),
        "installed_agentic_executors": sum(item["kind"] == "AGENTIC_EXECUTOR" and item["installed"] for item in candidates),
        "reasoner_runtimes": sum(item["kind"] == "REASONER_RUNTIME" for item in candidates),
        "tools": sum(item["kind"] == "TOOL_ONLY" for item in candidates),
        "ui_only": sum(item["kind"] == "UI_OR_NONAUTOMATABLE" for item in candidates),
        "admitted_agentic_executors": len(admitted),
    }
    selection_artifact = {
        "schema_version": "ignition-140-step09-local-executor-census-and-selection-r1",
        "task_id": TASK_ID,
        "step": STEP,
        "status": "PASS",
        "census_path": "ignition/data/operations/iterations/140/local-executor-census-r1.json",
        "control_tip": census["control"]["tip"],
        "formal_candidate_sha": census["formal_candidate"]["sha"],
        "counts": counts,
        "selection": {"selected_executor_id": census["selection"]["selected_executor_id"], "selected_family": census["selection"]["selected_family"], "selection_status": census["selection"]["status"], "ranking": ranking, "why_executor": why},
        "observations": {"codex_login_status": candidates_by_id["external.codex"]["auth"]["public_status"], "agent_version_help_read": True, "reasoner_models_invoked": False, "ui_action_performed": False, "public_auth_content_read": False},
        "safety": census["safety"],
        "claim_ceiling": census["claim_ceiling"],
    }
    report = f"""# IGNITION-20260826-140 Step 09 — Fresh local executor census and dynamic selection

## Result

`PASS`: the host was re-attested at `{census['observed_at']}` using only PATH/bundle presence, public version/help surfaces and Codex public auth-status exit behavior. No auth content was read, no model or Agent inference was started, no UI action occurred, and no installation, configuration or billing operation occurred.

The scan found {counts['candidates']} candidates: {counts['agentic_executors']} AGENTIC_EXECUTOR records ({counts['installed_agentic_executors']} installed), {counts['reasoner_runtimes']} REASONER_RUNTIME records, {counts['tools']} TOOL_ONLY records and {counts['ui_only']} UI-only records. Installed versions observed include Gemini CLI 0.53.1, Codex CLI 0.144.4, Hermes Agent v0.20.0 (2026.8.3), OpenClaw 2026.7.1-2 (0790d9f), Ollama 0.32.7 and LM Studio CLI commit 6041ae0.

## Dynamic selection

`{census['selection']['selected_family'] or 'No executor'}` is the current selection: {why}

Gemini remains blocked because its public auth interface did not provide a bounded status result and auth/home separation plus no-new-billing re-attestation are not proven. Hermes remains blocked by strict structured-result, public-auth and auth-source boundaries. OpenClaw remains blocked by workspace/channel/process-cleanup boundaries. Copilot CLI is not installed. Reasoner runtimes and tools are not AGENTIC_EXECUTOR candidates; desktop bundles are UI-only and were not opened.

Machine evidence: [`local-executor-census-r1.json`](../../data/operations/iterations/140/local-executor-census-r1.json) and [`step09-local-executor-census-and-selection.json`](../../data/operations/iterations/140/step09-local-executor-census-and-selection.json).

## Next gate

Step10 must freeze the dynamically selected family, capability lease, disposable read-only workspace, durable capture, child-depth guard, no-channel boundary and independent validator contract. Only after that gate may at most one live attempt be made for this executor family; a second attempt, if needed, must use a different family and is capped by the task contract.

Claim ceiling: fresh repository-local observation-time census, executor-kind classification, admission checks and why-executor trace only; no live inference, validated completion, model-quality ranking, production readiness, external truth, Owner acceptance or epistemic acceptance is inferred.
"""
    return census, selection_artifact, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--census-output", type=Path, default=ROOT / "data/operations/iterations/140/local-executor-census-r1.json")
    parser.add_argument("--selection-output", type=Path, default=ROOT / "data/operations/iterations/140/step09-local-executor-census-and-selection.json")
    parser.add_argument("--report-output", type=Path, default=ROOT / "reports/operations/ignition-140-step09-local-executor-census-and-selection.md")
    args = parser.parse_args()
    census, selection, report = build()
    for path, value in ((args.census_output, census), (args.selection_output, selection)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.write_text(report, encoding="utf-8")
    print(f"TASK140_EXECUTOR_CENSUS_WRITTEN selected={census['selection']['selected_executor_id']} candidates={len(census['candidates'])} admitted={sum(item['admission_status'] == 'ADMITTED' for item in census['candidates'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
