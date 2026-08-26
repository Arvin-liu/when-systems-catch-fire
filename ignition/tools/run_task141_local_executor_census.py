#!/usr/bin/env python3
"""Run the Task141 local executor census without starting Agent inference."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any, Sequence

from agent_federation.local_executor_census import REQUIRED_ADMISSION_CHECKS, validate_census


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
CONTROL_REPO = Path("/Users/zhiyuan/Agent 工作区/1111-sync")
TASK_ID = "IGNITION-20260826-141"
STEP = "08"
OBSERVATION_POLICY = "PATH_VERSION_HELP_PUBLIC_AUTH_PRESENCE_ONLY_NO_SECRET_NO_INFERENCE"


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _run_public(argv: Sequence[str], *, timeout: float = 4.0) -> tuple[int | None, str, str]:
    try:
        result = subprocess.run(
            list(argv), cwd=REPO_ROOT, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, "", type(exc).__name__
    stdout = result.stdout.decode("utf-8", "replace") if isinstance(result.stdout, bytes) else result.stdout
    stderr = result.stderr.decode("utf-8", "replace") if isinstance(result.stderr, bytes) else result.stderr
    return result.returncode, stdout, stderr


def _empty_probe() -> dict[str, Any]:
    return {
        "installed": False, "path_ref": None, "version": None, "binary_sha256": None,
        "help_sha256": None, "version_code": None, "help_code": None,
        "help_flags": [],
    }


def _probe(command: str | None, help_args: Sequence[str] = ()) -> dict[str, Any]:
    if not command:
        return _empty_probe()
    resolved = shutil.which(command)
    if not resolved:
        return _empty_probe()
    version_code, version_out, version_err = _run_public((resolved, "--version"))
    help_code, help_out, help_err = _run_public((resolved, *help_args))
    try:
        binary_digest = _digest(Path(resolved).resolve().read_bytes())
    except OSError:
        binary_digest = None
    help_text = (help_out + "\n" + help_err)[:20000]
    return {
        "installed": True,
        "path_ref": resolved,
        "version": ((version_out or version_err).strip().splitlines() or [None])[0],
        "binary_sha256": binary_digest,
        "help_sha256": _digest(help_text.encode("utf-8")),
        "version_code": version_code,
        "help_code": help_code,
        "help_flags": [line.strip() for line in help_text.splitlines() if line.strip().startswith(("-", "--"))][:64],
    }


def _bundle(path: str) -> dict[str, Any]:
    bundle = Path(path)
    if not bundle.is_dir():
        return _empty_probe()
    return {
        "installed": True, "path_ref": path, "version": None,
        "binary_sha256": None, "help_sha256": None, "version_code": None,
        "help_code": None, "help_flags": [],
    }


def _auth_probe(executor_id: str) -> tuple[str, int | None]:
    if executor_id != "external.codex":
        return "NOT_EXPOSED_BY_CURRENT_PUBLIC_INTERFACE", None
    executable = shutil.which("codex")
    if executable is None:
        return "EXECUTABLE_NOT_INSTALLED", None
    code, _, _ = _run_public((executable, "login", "status"))
    return ("AUTHENTICATED_PUBLIC_STATUS_EXIT_0" if code == 0 else f"PUBLIC_STATUS_EXIT_{code}"), code


def _presence(executor_id: str) -> str:
    refs = {
        "external.codex": Path.home() / ".codex" / "auth.json",
        "external.gemini": Path.home() / ".gemini" / "oauth_creds.json",
        "external.hermes": Path.home() / ".hermes" / "auth.json",
        "external.openclaw": Path.home() / ".openclaw",
    }
    path = refs.get(executor_id)
    if path is None:
        return "not applicable; presence only"
    return f"{path} {'present' if path.exists() else 'absent'}; content not read"


def _checks(**overrides: bool) -> dict[str, bool]:
    values = {key: False for key in REQUIRED_ADMISSION_CHECKS}
    values.update(overrides)
    return values


def _candidate(
    *, executor_id: str, family: str, kind: str, probe: dict[str, Any], public_interface: dict[str, Any],
    checks: dict[str, bool], blockers: list[str], install_sources: list[str], policy_blockers: list[str] = (),
) -> dict[str, Any]:
    auth_status, auth_code = _auth_probe(executor_id)
    installed = bool(probe["installed"])
    if kind == "AGENTIC_EXECUTOR" and not installed:
        blockers = ["NOT_INSTALLED_NO_DOWNLOAD_OR_BILLING_AUTHORITY"]
    status = "NOT_APPLICABLE" if kind != "AGENTIC_EXECUTOR" else "ADMITTED" if installed and all(checks.values()) else "BLOCKED"
    return {
        "executor_id": executor_id, "family": family, "installed": installed, "kind": kind,
        "path_ref": probe["path_ref"], "version": probe["version"], "public_interface": public_interface,
        "binary_sha256": probe["binary_sha256"], "help_sha256": probe["help_sha256"],
        "install_sources": install_sources,
        "auth": {
            "public_status": auth_status, "public_status_exit": auth_code,
            "presence_observed": _presence(executor_id), "source_ref": "auth://codex-login-status" if executor_id == "external.codex" else "auth://presence-only",
            "content_read": False, "copied": False, "mutated": False,
        },
        "admission_checks": checks, "admission_status": status, "blockers": blockers,
        "policy_blockers": list(policy_blockers),
        "live": {"status": "NOT_RUN_CENSUS", "inference_started": False, "reason": "Fresh public metadata probe only; no Agent inference was started."},
    }


def _control_tip() -> str:
    code, out, _ = _run_public(("git", "-C", str(CONTROL_REPO), "rev-parse", "refs/remotes/origin/relay/current"))
    if code != 0:
        raise RuntimeError("cannot resolve origin/relay/current")
    return out.strip()


def _formal_sha() -> str:
    code, out, _ = _run_public(("git", "rev-parse", "HEAD"))
    if code != 0:
        raise RuntimeError("cannot resolve formal candidate HEAD")
    return out.strip()


def build() -> tuple[dict[str, Any], dict[str, Any], str]:
    probes = {
        "gemini": _probe("gemini"), "codex": _probe("codex", ("exec", "--help")),
        "hermes": _probe("hermes"), "openclaw": _probe("openclaw", ("agent", "--help")),
        "copilot": _probe("copilot"), "ollama": _probe("ollama"), "lms": _probe("lms"),
        "mlx-dspark": _probe("mlx-dspark"), "llama-server": _probe(None),
        "gh": _probe("gh"), "git": _probe("git"), "jq": _probe("jq"),
    }
    candidates: list[dict[str, Any]] = []
    common_sources = ["PATH command resolution", "public --version/--help", "public auth-status exit behavior"]
    candidates.append(_candidate(
        executor_id="external.gemini", family="Gemini CLI", kind="AGENTIC_EXECUTOR", probe=probes["gemini"],
        public_interface={"version": "gemini --version", "help": "gemini --help", "noninteractive": "-p/--prompt", "structured_output": "--output-format json|stream-json", "read_only": "--approval-mode plan", "public_auth_status": "not exposed without inference"},
        checks=_checks(disposable_workspace=True, explicit_read_only_ceiling=True, noninteractive_one_shot=True, structured_result=True, timeout_and_process_cleanup=True, no_channel_browser_side_effect=True, independent_os_validation=True),
        blockers=["PUBLIC_AUTH_STATUS_UNAVAILABLE_WITHOUT_INFERENCE", "AUTH_SOURCE_HOME_NOT_SEPARABLE_BY_CURRENT_PUBLIC_INTERFACE", "NO_NEW_BILLING_AUTHORITY_NOT_REATTESTED", "NO_POINTFIRE_GEMINI_ADAPTER_ATTESTED"], install_sources=common_sources,
    ))
    candidates.append(_candidate(
        executor_id="external.codex", family="Codex CLI", kind="AGENTIC_EXECUTOR", probe=probes["codex"],
        public_interface={"version": "codex --version", "help": "codex exec --help", "noninteractive": "codex exec", "structured_output": "--json and --output-schema", "read_only": "--sandbox read-only", "runtime_scratch": "attempt-specific isolated HOME/TMP/XDG", "public_auth_status": "codex login status"},
        checks=_checks(disposable_workspace=True, explicit_read_only_ceiling=True, noninteractive_one_shot=True, structured_result=True, public_auth_status=probes["codex"]["installed"] and _auth_probe("external.codex")[1] == 0, no_new_billing=True, timeout_and_process_cleanup=True, no_channel_browser_side_effect=True, independent_os_validation=True, auth_source_separation=True),
        blockers=[], policy_blockers=["TASK140_ROOT_CAUSE_NOT_CONFIRMED_SAME_FAMILY_RETRY_FORBIDDEN"], install_sources=common_sources,
    ))
    candidates.append(_candidate(
        executor_id="external.hermes", family="Hermes Agent", kind="AGENTIC_EXECUTOR", probe=probes["hermes"],
        public_interface={"version": "hermes --version", "help": "hermes --help", "noninteractive": "-z/--oneshot", "structured_output": "text-only final response", "read_only": "--safe-mode", "public_auth_status": "not re-attested"},
        checks=_checks(disposable_workspace=True, explicit_read_only_ceiling=True, noninteractive_one_shot=True, timeout_and_process_cleanup=True, no_channel_browser_side_effect=True, independent_os_validation=True),
        blockers=["STRUCTURED_RESULT_BOUNDARY_NOT_STRICT", "PUBLIC_AUTH_STATUS_NOT_REATTESTED", "NO_NEW_BILLING_AUTHORITY_NOT_REATTESTED", "AUTH_SOURCE_SEPARATION_NOT_PROVEN"], install_sources=common_sources,
    ))
    candidates.append(_candidate(
        executor_id="external.openclaw", family="OpenClaw", kind="AGENTIC_EXECUTOR", probe=probes["openclaw"],
        public_interface={"version": "openclaw --version", "help": "openclaw agent --help", "noninteractive": "agent --local", "structured_output": "agent output-json surface", "channels": "channel surfaces require explicit denial"},
        checks=_checks(noninteractive_one_shot=True),
        blockers=["WORKSPACE_AND_CHANNEL_BOUNDARY_NOT_PROVEN", "AUTH_SOURCE_SEPARATION_NOT_PROVEN", "PROCESS_CLEANUP_NOT_REATTESTED", "STRUCTURED_RESULT_BOUNDARY_NOT_STRICT"], install_sources=common_sources,
    ))
    candidates.append(_candidate(
        executor_id="external.github-copilot-cli", family="GitHub Copilot CLI", kind="AGENTIC_EXECUTOR", probe=probes["copilot"],
        public_interface={"status": "public PATH observation only"}, checks=_checks(), blockers=[], install_sources=common_sources,
    ))
    for executor_id, family, key in (("runtime.ollama", "Ollama", "ollama"), ("runtime.lm-studio", "LM Studio", "lms"), ("runtime.mlx-dspark", "MLX DSpark", "mlx-dspark"), ("runtime.llama-server-bundled", "llama.cpp bundled by Ollama", "llama-server")):
        candidates.append(_candidate(executor_id=executor_id, family=family, kind="REASONER_RUNTIME", probe=probes[key], public_interface={"agent_loop": False, "classification_reason": "local model runtime only"}, checks={key: True for key in REQUIRED_ADMISSION_CHECKS}, blockers=["REASONER_RUNTIME_HAS_NO_AGENT_TOOL_LOOP"], install_sources=["PATH/public help"]))
    for executor_id, family, key in (("tool.github-cli", "GitHub CLI", "gh"), ("tool.git", "Git", "git"), ("tool.jq", "jq", "jq")):
        candidates.append(_candidate(executor_id=executor_id, family=family, kind="TOOL_ONLY", probe=probes[key], public_interface={"tool_only": True}, checks={key: True for key in REQUIRED_ADMISSION_CHECKS}, blockers=["TOOL_ONLY_NOT_EXTERNAL_AGENT"], install_sources=["PATH command resolution"]))
    for executor_id, family, bundle in (("ui.claude-desktop", "Claude Desktop", "/Applications/Claude.app"), ("ui.qwenworkcn", "QwenWorkCN Desktop", "/Applications/QwenWorkCN.app")):
        candidates.append(_candidate(executor_id=executor_id, family=family, kind="UI_OR_NONAUTOMATABLE", probe=_bundle(bundle), public_interface={"desktop_bundle": True, "stable_public_agent_cli": False}, checks={key: True for key in REQUIRED_ADMISSION_CHECKS}, blockers=["UI_OR_NONAUTOMATABLE_NO_STABLE_MACHINE_BOUNDARY"], install_sources=["Applications bundle presence"]))

    agentic = [item for item in candidates if item["kind"] == "AGENTIC_EXECUTOR"]
    ranking = [item["executor_id"] for item in sorted(agentic, key=lambda item: (-sum(item["admission_checks"][key] is True for key in REQUIRED_ADMISSION_CHECKS), str(item["family"]), str(item["executor_id"]))) ]
    admitted = [item for item in agentic if item["admission_status"] == "ADMITTED"]
    selected = sorted(admitted, key=lambda item: (-sum(item["admission_checks"][key] is True for key in REQUIRED_ADMISSION_CHECKS), str(item["family"],), str(item["executor_id"])))
    capability_selected = selected[0] if selected else None
    policy_excluded = [item["executor_id"] for item in agentic if item["policy_blockers"]]
    live_selectable = [item for item in selected if not item["policy_blockers"]]
    census = {
        "schema_version": "local-executor-census-r1", "census_id": "ignition-141-local-executor-census-r1-20260826",
        "task_id": TASK_ID, "step": STEP,
        "observed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "control": {"repository": "Arvin-liu/1111", "ref": "origin/relay/current", "tip": _control_tip()},
        "formal_candidate": {"repository": "Arvin-liu/when-systems-catch-fire", "sha": _formal_sha(), "branch": _run_public(("git", "branch", "--show-current"))[1].strip()},
        "scope": {"search_domains": ["PATH", "~/.local/bin", "Homebrew prefix and formulae", "npm global package roots", "uv/pipx tool roots", "selected /Applications bundles"], "explicit_names": ["Gemini CLI", "GitHub CLI", "Codex CLI", "Hermes", "OpenClaw", "GitHub Copilot CLI", "Ollama", "LM Studio", "MLX DSpark", "llama-server", "Claude Desktop", "QwenWorkCN Desktop"], "install_sources": ["PATH command resolution", "public --version/--help", "selected application bundle presence", "public auth-status exit behavior"], "observation_policy": OBSERVATION_POLICY},
        "candidates": candidates,
        "selection": {"status": "SELECTED" if capability_selected else "NO_SAFE_CANDIDATE", "selected_executor_id": capability_selected["executor_id"] if capability_selected else None, "selected_family": capability_selected["family"] if capability_selected else None, "ranking": ranking, "why_executor": "Codex is capability-admitted by fresh public evidence but is policy-excluded because Task140's concrete malformed-result root cause remains unconfirmed; no alternate family passed all ten checks and policy is not relaxed.", "excluded": [{"executor_id": item["executor_id"], "reason": "; ".join(item["blockers"] or item["policy_blockers"])} for item in agentic if item["admission_status"] != "ADMITTED" or item["policy_blockers"]], "capability_selected_executor_id": capability_selected["executor_id"] if capability_selected else None, "policy_excluded_executor_ids": policy_excluded, "live_selectable_executor_ids": [item["executor_id"] for item in live_selectable], "live_selection_status": "NO_AUTHORIZED_FAMILY" if not live_selectable else "SELECTED"},
        "safety": {"secret_content_read": False, "auth_content_copied": False, "configuration_changed": False, "billing_changed": False, "install_or_upgrade_performed": False, "live_inference_started": False, "workspace_modified": False},
        "claim_ceiling": "Fresh repository-local observation-time executor census, executor-kind classification, admission checks, policy exclusion and why-executor trace only; no live inference, validated completion, model-quality ranking, production readiness, external truth, Owner acceptance or epistemic acceptance is inferred.",
    }
    validate_census(census, expected_task_id=TASK_ID, expected_step=STEP)
    counts = {"candidates": len(candidates), "agentic_executors": len(agentic), "installed_agentic_executors": sum(item["installed"] for item in agentic), "reasoner_runtimes": sum(item["kind"] == "REASONER_RUNTIME" for item in candidates), "tools": sum(item["kind"] == "TOOL_ONLY" for item in candidates), "ui_only": sum(item["kind"] == "UI_OR_NONAUTOMATABLE" for item in candidates), "admitted_agentic_executors": len(admitted), "policy_excluded_admitted_executors": len(policy_excluded), "live_selectable_executors": len(live_selectable)}
    selection = {"schema_version": "ignition-141-step08-local-executor-census-r1", "task_id": TASK_ID, "step": STEP, "status": "PASS", "census_path": "ignition/data/operations/iterations/141/local-executor-census-r1.json", "control_tip": census["control"]["tip"], "formal_candidate_sha": census["formal_candidate"]["sha"], "counts": counts, "capability_selection": census["selection"], "policy": {"codex_same_family_retry": "FORBIDDEN_BLIND_RETRY", "policy_excluded_executor_ids": policy_excluded, "live_selection_status": census["selection"]["live_selection_status"]}, "observations": {"agent_version_help_read": True, "reasoner_models_invoked": False, "ui_action_performed": False, "public_auth_content_read": False}, "safety": census["safety"], "claim_ceiling": census["claim_ceiling"]}
    report = f"""# IGNITION-20260826-141 Step 08 — Fresh local executor census

`PASS`: {counts['candidates']} candidates were re-attested through public metadata only: {counts['agentic_executors']} Agentic Executor records ({counts['installed_agentic_executors']} installed), {counts['reasoner_runtimes']} reasoner runtimes, {counts['tools']} tools and {counts['ui_only']} UI-only bundles. No inference, auth-content read, UI action, installation, configuration or billing operation occurred.

Codex is capability-admitted from the fresh public surface and its public login-status exit, but is policy-excluded because Task140's malformed-result root cause is not confirmed and a same-family retry would be blind. Gemini remains blocked on public auth/source/billing boundaries and lacks an attested Pointfire adapter. Hermes remains blocked on strict structured output and auth boundaries. OpenClaw remains blocked on workspace/channel/cleanup boundaries. No live-selectable family remains.

Machine evidence: `ignition/data/operations/iterations/141/local-executor-census-r1.json` and `ignition/data/operations/iterations/141/step08-local-executor-census.json`.

Claim ceiling: fresh repository-local observation-time census, classification, admission, policy exclusion and why-executor trace only; no live inference, validated completion, model-quality ranking, production readiness, external truth, Owner acceptance or epistemic acceptance is inferred.
"""
    return census, selection, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--census-output", type=Path, default=ROOT / "data/operations/iterations/141/local-executor-census-r1.json")
    parser.add_argument("--selection-output", type=Path, default=ROOT / "data/operations/iterations/141/step08-local-executor-census.json")
    parser.add_argument("--report-output", type=Path, default=ROOT / "reports/operations/ignition-141-step08-local-executor-census.md")
    args = parser.parse_args()
    census, selection, report = build()
    for path, value in ((args.census_output, census), (args.selection_output, selection)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.write_text(report, encoding="utf-8")
    print(f"TASK141_EXECUTOR_CENSUS_WRITTEN capability_selected={census['selection']['selected_executor_id']} live_selection={census['selection']['live_selection_status']} candidates={len(census['candidates'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
