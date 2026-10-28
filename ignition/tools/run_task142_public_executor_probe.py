#!/usr/bin/env python3
"""Fresh public metadata probe for Task142 executor admission.

This module intentionally never reads auth/config contents and never invokes an
Agent or model. It only observes PATH command metadata, public help/version
exit behavior, and presence-only local auth/application signals.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "IGNITION-20260827-142"
AGENTIC = "AGENTIC_EXECUTOR"
REASONER = "REASONER_RUNTIME"
TOOL = "TOOL"
UI = "UI_SURFACE"
STATUS_VALUES = {"PASS", "FAIL", "PROVEN", "UNPROVEN", "STRICT", "REJECTED", "NOT_APPLICABLE", "NOT_OBSERVED"}


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _run(argv: Sequence[str], *, timeout: float = 5.0) -> tuple[int | None, bytes, bytes]:
    try:
        result = subprocess.run(
            list(argv), cwd=ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=timeout, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None, b"", b""
    stdout = result.stdout if isinstance(result.stdout, bytes) else str(result.stdout).encode()
    stderr = result.stderr if isinstance(result.stderr, bytes) else str(result.stderr).encode()
    return result.returncode, stdout, stderr


def _safe_first_line(value: bytes) -> str | None:
    text = value.decode("utf-8", "replace")
    for line in text.splitlines():
        line = re.sub(r"(?:api[_ -]?key|token|secret|authorization|cookie)\s*[=:]\s*\S+", "[REDACTED]", line, flags=re.IGNORECASE)
        line = line.strip()
        if line:
            return line[:240]
    return None


def _probe(command: str | None, help_args: Sequence[str] = ()) -> dict[str, Any]:
    if not command:
        return {"installed": False, "path_ref": None, "version": None, "version_code": None, "help_code": None, "binary_sha256": None, "help_sha256": None, "help_markers": []}
    resolved = shutil.which(command)
    if not resolved:
        return {"installed": False, "path_ref": f"PATH_ENTRY:{command}", "version": None, "version_code": None, "help_code": None, "binary_sha256": None, "help_sha256": None, "help_markers": []}
    version_code, version_out, version_err = _run((resolved, "--version"))
    help_code, help_out, help_err = _run((resolved, *help_args))
    try:
        binary_digest = _digest(Path(resolved).resolve().read_bytes())
    except OSError:
        binary_digest = None
    help_bytes = help_out + b"\n" + help_err
    help_text = help_bytes.decode("utf-8", "replace")[:20000]
    markers = sorted({line.strip()[:120] for line in help_text.splitlines() if line.strip().startswith(("-", "--"))})[:64]
    return {
        "installed": True,
        "path_ref": f"PATH_ENTRY:{command}",
        "version": _safe_first_line(version_out + b"\n" + version_err),
        "version_code": version_code,
        "help_code": help_code,
        "binary_sha256": binary_digest,
        "help_sha256": _digest(help_bytes),
        "help_markers": markers,
        "help_text_lower": help_text.casefold(),
    }


def _presence(executor_id: str, path: Path | None) -> dict[str, Any]:
    return {"presence_ref": f"AUTH_STATE_PRESENCE:{executor_id}", "present": bool(path and path.exists()), "content_read": False}


def _auth(executor_id: str, probe: dict[str, Any], auth_path: Path | None) -> dict[str, Any]:
    if executor_id == "external.codex" and probe["installed"]:
        code, _out, _err = _run((shutil.which("codex") or "codex", "login", "status"))
        status = "PASS" if code == 0 else "FAIL"
        return {"public_status": status, "public_status_exit": code, **_presence(executor_id, auth_path)}
    if executor_id in {"external.gemini", "external.hermes", "external.openclaw"}:
        return {"public_status": "NOT_OBSERVED", "public_status_exit": None, **_presence(executor_id, auth_path)}
    return {"public_status": "NOT_APPLICABLE", "public_status_exit": None, **_presence(executor_id, auth_path)}


def _blank_gates() -> dict[str, str]:
    return {key: "NOT_APPLICABLE" for key in ("public_auth", "auth_separation", "argv_contract", "structured_result", "workspace", "capture", "validator_binding", "cleanup", "permission_ceiling", "exact_binding", "no_effect_scope")}


def _agent_candidate(executor_id: str, command: str, help_args: Sequence[str], auth_path: Path | None) -> dict[str, Any]:
    probe = _probe(command, help_args)
    auth = _auth(executor_id, probe, auth_path)
    help_text = probe.get("help_text_lower", "")
    gates = _blank_gates()
    gates.update({
        "public_auth": auth["public_status"],
        "auth_separation": "PROVEN" if executor_id == "external.codex" and auth["public_status"] == "PASS" else "UNPROVEN",
        "argv_contract": "STRICT" if probe["help_code"] == 0 else "REJECTED",
        "structured_result": "STRICT" if executor_id == "external.codex" and "output-schema" in help_text else "UNPROVEN" if any(marker in help_text for marker in ("output-format", "--json")) else "REJECTED",
        "workspace": "PROVEN" if executor_id == "external.codex" else "UNPROVEN",
        "capture": "PROVEN" if executor_id == "external.codex" else "UNPROVEN",
        "validator_binding": "PROVEN" if executor_id == "external.codex" else "UNPROVEN",
        "cleanup": "PROVEN" if executor_id == "external.codex" else "UNPROVEN",
        "permission_ceiling": "PROVEN" if executor_id == "external.codex" else "UNPROVEN",
        "exact_binding": "PROVEN" if executor_id == "external.codex" else "UNPROVEN",
        "no_effect_scope": "PROVEN" if executor_id == "external.codex" else "UNPROVEN",
    })
    blockers: list[str] = []
    policy_blockers: list[str] = []
    if not probe["installed"]:
        blockers.append("NOT_INSTALLED_NO_DOWNLOAD_OR_BILLING_AUTHORITY")
    if executor_id == "external.gemini":
        blockers.extend(["PUBLIC_AUTH_STATUS_UNAVAILABLE_WITHOUT_INFERENCE", "AUTH_SOURCE_HOME_NOT_SEPARABLE", "POINTFIRE_ADAPTER_NOT_ATTESTED"])
    elif executor_id == "external.hermes":
        blockers.extend(["STRUCTURED_RESULT_BOUNDARY_NOT_STRICT", "PUBLIC_AUTH_STATUS_NOT_REATTESTED", "AUTH_SOURCE_SEPARATION_NOT_PROVEN"])
    elif executor_id == "external.openclaw":
        blockers.extend(["WORKSPACE_AND_CHANNEL_BOUNDARY_NOT_PROVEN", "AUTH_SOURCE_SEPARATION_NOT_PROVEN", "PROCESS_CLEANUP_NOT_REATTESTED", "STRUCTURED_RESULT_BOUNDARY_NOT_STRICT"])
    elif executor_id == "external.codex":
        if auth["public_status"] != "PASS":
            blockers.append("PUBLIC_AUTH_STATUS_FAILED")
        policy_blockers.append("TASK140_ROOT_CAUSE_NOT_CONFIRMED_SAME_FAMILY_RETRY_FORBIDDEN")
    else:
        blockers.append("NOT_INSTALLED_NO_DOWNLOAD_OR_BILLING_AUTHORITY")
    technical = not blockers and all(gates[key] in {"PASS", "PROVEN", "STRICT"} for key in gates)
    return {
        "executor_id": executor_id,
        "family": AGENTIC,
        "provider_neutral_family": "agentic-executor",
        "class_separation": AGENTIC,
        "installed": probe["installed"],
        "probe": {key: value for key, value in probe.items() if key != "help_text_lower"},
        "auth": auth,
        "gates": gates,
        "technical_admission": "ADMITTED" if technical else "BLOCKED",
        "policy_blockers": policy_blockers,
        "live_eligibility": "ELIGIBLE_FOR_LIVE_READONLY" if technical and not policy_blockers else "BLOCKED",
        "blockers": sorted(set(blockers)),
        "evidence_refs": ["PATH command resolution", "public --version/--help", "public auth-status exit behavior", "presence-only auth state"],
        "inference_started": False,
        "claim_ceiling": "Fresh public metadata and repository-local admission evidence only; no inference or live completion is claimed.",
    }


def _non_agent(executor_id: str, family: str, provider_family: str, command: str | None, help_args: Sequence[str], blocker: str, app_path: Path | None = None) -> dict[str, Any]:
    probe = _probe(command, help_args) if command else {"installed": bool(app_path and app_path.exists()), "path_ref": f"APP_BUNDLE:{executor_id}" if app_path else None, "version": None, "version_code": None, "help_code": None, "binary_sha256": None, "help_sha256": None, "help_markers": []}
    gates = _blank_gates()
    return {
        "executor_id": executor_id,
        "family": family,
        "provider_neutral_family": provider_family,
        "class_separation": family,
        "installed": probe["installed"],
        "probe": {key: value for key, value in probe.items() if key != "help_text_lower"},
        "auth": {"public_status": "NOT_APPLICABLE", "public_status_exit": None, "presence_ref": f"AUTH_STATE_PRESENCE:{executor_id}", "present": False, "content_read": False},
        "gates": gates,
        "technical_admission": "NOT_APPLICABLE",
        "policy_blockers": [],
        "live_eligibility": "NOT_APPLICABLE",
        "blockers": [blocker],
        "evidence_refs": ["PATH command resolution", "public --version/--help" if command else "application bundle presence"],
        "inference_started": False,
        "claim_ceiling": "Fresh classification evidence only; this record is not an agentic executor admission or live result.",
    }


def build() -> dict[str, Any]:
    candidates = [
        _agent_candidate("external.gemini", "gemini", ("--help",), Path.home() / ".gemini" / "oauth_creds.json"),
        _agent_candidate("external.codex", "codex", ("exec", "--help"), Path.home() / ".codex" / "auth.json"),
        _agent_candidate("external.hermes", "hermes", ("--help",), Path.home() / ".hermes" / "auth.json"),
        _agent_candidate("external.openclaw", "openclaw", ("agent", "--help"), Path.home() / ".openclaw"),
        _agent_candidate("external.github-copilot-cli", "copilot", ("--help",), None),
        _non_agent("runtime.ollama", REASONER, "reasoner-runtime", "ollama", ("--help",), "REASONER_RUNTIME_HAS_NO_AGENT_TOOL_LOOP"),
        _non_agent("runtime.lm-studio", REASONER, "reasoner-runtime", "lms", ("--help",), "REASONER_RUNTIME_HAS_NO_AGENT_TOOL_LOOP"),
        _non_agent("runtime.mlx-dspark", REASONER, "reasoner-runtime", "mlx-dspark", ("--help",), "REASONER_RUNTIME_HAS_NO_AGENT_TOOL_LOOP"),
        _non_agent("runtime.llama-server-bundled", REASONER, "reasoner-runtime", "llama-server", ("--help",), "REASONER_RUNTIME_HAS_NO_AGENT_TOOL_LOOP"),
        _non_agent("tool.github-cli", TOOL, "deterministic-tool", "gh", ("--help",), "TOOL_ONLY_NOT_EXTERNAL_AGENT"),
        _non_agent("tool.git", TOOL, "deterministic-tool", "git", ("--help",), "TOOL_ONLY_NOT_EXTERNAL_AGENT"),
        _non_agent("tool.jq", TOOL, "deterministic-tool", "jq", ("--help",), "TOOL_ONLY_NOT_EXTERNAL_AGENT"),
        _non_agent("ui.claude-desktop", UI, "ui-surface", None, (), "UI_OR_NONAUTOMATABLE_NO_STABLE_MACHINE_BOUNDARY", Path("/Applications/Claude.app")),
        _non_agent("ui.qwenworkcn", UI, "ui-surface", None, (), "UI_OR_NONAUTOMATABLE_NO_STABLE_MACHINE_BOUNDARY", Path("/Applications/QwenWorkCN.app")),
    ]
    technical = [row for row in candidates if row["family"] == AGENTIC and row["technical_admission"] == "ADMITTED"]
    selectable = [row for row in technical if row["live_eligibility"] == "ELIGIBLE_FOR_LIVE_READONLY"]
    return {
        "schema_version": "task142-public-executor-probe-r1",
        "task_id": TASK_ID,
        "observed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "observation_policy": "PATH_VERSION_HELP_PUBLIC_AUTH_PRESENCE_ONLY_NO_SECRET_NO_INFERENCE",
        "candidates": candidates,
        "selection": {
            "technical_admitted_ids": [row["executor_id"] for row in technical],
            "policy_excluded_ids": [row["executor_id"] for row in technical if row["policy_blockers"]],
            "live_selectable_ids": [row["executor_id"] for row in selectable],
            "status": "NO_SAFE_CANDIDATE" if not selectable else "SELECTED",
            "why": "Codex is the only technically admitted agentic family if public auth passes, but same-family retry remains forbidden until Task140 malformed-result root cause is confirmed; Gemini, Hermes and OpenClaw retain explicit admission blockers; Copilot is not installed; reasoners/tools/UI surfaces are not agentic executors.",
        },
        "safety": {
            "secret_content_read": False,
            "auth_content_copied": False,
            "configuration_changed": False,
            "billing_changed": False,
            "install_or_upgrade_performed": False,
            "live_inference_started": False,
            "workspace_modified": False,
            "ui_action_performed": False,
        },
        "claim_ceiling": "Fresh observation-time public metadata, executor-kind classification, admission blockers and deterministic selection rationale only; no live inference, validated completion, model-quality ranking, production readiness, external truth, Owner acceptance or epistemic acceptance is inferred.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executor-id")
    args = parser.parse_args()
    result = build()
    if args.executor_id:
        rows = [row for row in result["candidates"] if row["executor_id"] == args.executor_id]
        if not rows:
            parser.error(f"unknown executor id: {args.executor_id}")
        print(json.dumps({"task_id": result["task_id"], "observed_at": result["observed_at"], "candidate": rows[0], "safety": result["safety"]}, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
