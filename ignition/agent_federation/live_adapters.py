"""Thin live adapters over already-installed public executor CLIs."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .contracts import FederationContractError, canonical_json
from .live_bridge import LiveCapabilityLease, LiveDispatchEnvelope
from .live_transport import LiveProcessResult, LiveProcessTransport, LiveTransportError, interface_digest, parse_bounded_jsonl


class LiveAdapterError(FederationContractError):
    """Raised when a live adapter cannot prove its public safety boundary."""


@dataclass(frozen=True)
class LiveAdapterObservation:
    executor_id: str
    adapter_id: str
    version: str
    interface_digest: str
    process: LiveProcessResult
    parsed_events: tuple[Mapping[str, Any], ...]
    parsed: bool
    parse_error: str
    summary: str
    response_digest: str | None
    session_pointer: str | None


def _response_digest(text: str) -> str | None:
    return hashlib.sha256(text.encode("utf-8")).hexdigest() if text else None


def _summary(text: str) -> str:
    clean = " ".join(line.strip() for line in text.splitlines() if line.strip())
    return clean[-1000:] if clean else "public executor returned no summary"


def _session_pointer(events: Sequence[Mapping[str, Any]]) -> str | None:
    for event in events:
        value = event.get("thread_id") or event.get("session_id")
        if isinstance(value, str) and value.strip():
            return "opaque:" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]
    return None


def _binary_digest(executable: str, version: str) -> str:
    """Hash the observed executable when readable; never fall back to secrets."""

    try:
        path = Path(executable).resolve(strict=True)
        if path.is_file():
            return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        pass
    return hashlib.sha256(version.encode("utf-8")).hexdigest()


class LiveCodexAdapter:
    """R2 adapter for Codex's current public JSONL read-only exec surface."""

    executor_id = "external.codex"
    family = "Codex CLI"

    def __init__(
        self,
        workspace: str | Path,
        *,
        executable: str = "/Users/zhiyuan/.local/bin/codex",
        transport: LiveProcessTransport | Any | None = None,
        authentication_observed: bool = False,
        adapter_id: str = "codex-live-r2",
    ) -> None:
        root = Path(workspace)
        if not root.is_absolute() or not root.is_dir():
            raise LiveAdapterError("Codex live adapter requires an existing absolute disposable workspace")
        if not isinstance(executable, str) or not executable.startswith("/"):
            raise LiveAdapterError("Codex executable must be an absolute path")
        self.workspace = root
        self.executable = executable
        self.transport = transport or LiveProcessTransport(executable_allowlist=(executable,))
        self.authentication_observed = authentication_observed
        self.adapter_id = adapter_id
        self._probe_cache: tuple[LiveProcessResult, LiveProcessResult] | None = None

    def _run(self, argv: Sequence[str], timeout_seconds: float = 5) -> LiveProcessResult:
        try:
            return self.transport.run(argv, cwd=self.workspace, timeout_seconds=timeout_seconds)
        except (OSError, LiveTransportError) as exc:
            raise LiveAdapterError(f"Codex public process probe failed: {type(exc).__name__}") from exc

    def _probe(self) -> tuple[LiveProcessResult, LiveProcessResult]:
        if self._probe_cache is None:
            self._probe_cache = (
                self._run((self.executable, "--version")),
                self._run((self.executable, "exec", "--help")),
            )
        return self._probe_cache

    def observe_lease(self, *, lease_id: str, observed_at: str, expires_at: str, ttl_seconds: float) -> LiveCapabilityLease:
        version_result, help_result = self._probe()
        version = _summary(version_result.stdout or version_result.stderr)
        help_text = (help_result.stdout or "") + ("\n" + help_result.stderr if help_result.stderr else "")
        required_flags = ("--json", "--ephemeral", "--ignore-user-config", "--ignore-rules", "--sandbox", "--cd", "--output-schema")
        missing = [flag for flag in required_flags if flag not in help_text]
        blockers: list[str] = []
        if version_result.returncode != 0 or not version:
            blockers.append("VERSION_PROBE_FAILED")
        if help_result.returncode != 0:
            blockers.append("HELP_PROBE_FAILED")
        blockers.extend("MISSING_PUBLIC_FLAG:" + flag for flag in missing)
        if not self.authentication_observed:
            blockers.append("AUTH_NOT_OBSERVED")
        eligibility = "ELIGIBLE_FOR_LIVE_READONLY" if not blockers else "SKIPPED_INTERFACE_UNSUPPORTED" if any(item.startswith(("MISSING_PUBLIC_FLAG", "HELP_PROBE", "VERSION_PROBE")) for item in blockers) else "SKIPPED_NOT_AUTHENTICATED"
        return LiveCapabilityLease.build(
            lease_id=lease_id, executor_id=self.executor_id, executor_version=version,
            observed_at=observed_at, expires_at=expires_at, ttl_seconds=ttl_seconds,
            binary_digest=_binary_digest(self.executable, version), interface_digest=interface_digest(help_text),
            observed_capabilities=("repo.read", "structured_progress") if not missing else ("repo.read",),
            forbidden_capabilities=("repo.write", "repo.test", "terminal.run", "browser.read", "browser.act", "web.read", "messaging.send", "subagents", "scheduler"),
            unknown_capabilities=(), workspace_semantics="EXPLICIT_DISPOSABLE_READ_ONLY_CWD",
            approval_sandbox_semantics="CODEX_READ_ONLY_EPHEMERAL_IGNORE_USER_CONFIG_AND_RULES",
            structured_output_semantics="JSONL_PUBLIC_EVENTS_AND_OUTPUT_SCHEMA", timeout_supported=True, cancel_supported=True,
            resume_supported=False, live_eligibility=eligibility, eligibility_blockers=tuple(blockers), source="codex-public-cli-probe-r3",
        )

    def build_argv(self, envelope: LiveDispatchEnvelope) -> tuple[str, ...]:
        if envelope.executor_id != self.executor_id or envelope.adapter_id != self.adapter_id:
            raise LiveAdapterError("Codex live envelope is not bound to this adapter")
        if envelope.workspace_mode not in {"DISPOSABLE_READ_ONLY", "DISPOSABLE_SYNTHETIC_READ_ONLY"}:
            raise LiveAdapterError("Codex live adapter accepts only disposable read-only workspaces")
        if envelope.side_effect_class != "READ_ONLY_SYNTHETIC" or envelope.permission_ceiling != ("repo.read",):
            raise LiveAdapterError("Codex live adapter refuses a widened side-effect or permission ceiling")
        prompt = "IGNITION_LIVE_SYNTHETIC_READONLY_TASK\n" + canonical_json({
            "task_id": envelope.task_id,
            "synthetic_input_ref": envelope.synthetic_input_ref,
            "success_criteria": list(envelope.success_criteria),
            "output_contract": dict(envelope.output_contract),
            "instruction": "Read only the disposable fixture. Do not write, delete, execute shell, use network, message, browse, or inspect private state. Return only the requested public result.",
        })
        if len(prompt.encode("utf-8")) > 32 * 1024:
            raise LiveAdapterError("Codex live synthetic prompt exceeds the bounded input")
        argv = (
            self.executable, "exec", "--json", "--ephemeral", "--ignore-user-config", "--ignore-rules",
            "--sandbox", "read-only", "--cd", str(self.workspace), prompt,
        )
        if any("dangerously" in item or item == "--add-dir" or "workspace-write" in item for item in argv):
            raise LiveAdapterError("unsafe Codex flag leaked into the live argv")
        return argv

    def dispatch(self, envelope: LiveDispatchEnvelope) -> LiveAdapterObservation:
        argv = self.build_argv(envelope)
        process = self._run(argv, timeout_seconds=envelope.timeout_seconds)
        events: tuple[Mapping[str, Any], ...] = ()
        parsed = False
        parse_error = ""
        if not process.timed_out and not process.output_truncated and process.stdout.strip():
            try:
                events = parse_bounded_jsonl(process.stdout)
                parsed = True
            except LiveTransportError as exc:
                parse_error = str(exc)
        return LiveAdapterObservation(
            self.executor_id, self.adapter_id,
            _summary(self._probe()[0].stdout or self._probe()[0].stderr),
            self._probe()[1].stdout and interface_digest(self._probe()[1].stdout) or interface_digest(self._probe()[1].stderr),
            process, events, parsed, parse_error, _summary(process.stdout or process.stderr),
            _response_digest(process.stdout), _session_pointer(events),
        )


class LiveHermesAdapter:
    """R2 adapter for Hermes' bounded safe one-shot text surface."""

    executor_id = "external.hermes"
    family = "Hermes Agent"

    def __init__(
        self,
        workspace: str | Path,
        *,
        executable: str = "/Users/zhiyuan/.local/bin/hermes",
        transport: LiveProcessTransport | Any | None = None,
        authentication_observed: bool = False,
        read_only_guard_observed: bool = False,
        adapter_id: str = "hermes-live-r2",
        provider: str = "openai-codex",
        model: str = "gpt-5.6-luna",
    ) -> None:
        root = Path(workspace)
        if not root.is_absolute() or not root.is_dir():
            raise LiveAdapterError("Hermes live adapter requires an existing absolute disposable workspace")
        if not isinstance(executable, str) or not executable.startswith("/"):
            raise LiveAdapterError("Hermes executable must be an absolute path")
        self.workspace = root
        self.executable = executable
        self.transport = transport or LiveProcessTransport(executable_allowlist=(executable,))
        self.authentication_observed = authentication_observed
        self.read_only_guard_observed = read_only_guard_observed
        self.adapter_id = adapter_id
        self.provider = provider
        self.model = model
        self._probe_cache: tuple[LiveProcessResult, LiveProcessResult] | None = None

    def _run(self, argv: Sequence[str], timeout_seconds: float = 5) -> LiveProcessResult:
        try:
            return self.transport.run(argv, cwd=self.workspace, timeout_seconds=timeout_seconds)
        except (OSError, LiveTransportError) as exc:
            raise LiveAdapterError(f"Hermes public process probe failed: {type(exc).__name__}") from exc

    def _probe(self) -> tuple[LiveProcessResult, LiveProcessResult]:
        if self._probe_cache is None:
            self._probe_cache = (self._run((self.executable, "--version")), self._run((self.executable, "--help")))
        return self._probe_cache

    def observe_lease(self, *, lease_id: str, observed_at: str, expires_at: str, ttl_seconds: float) -> LiveCapabilityLease:
        version_result, help_result = self._probe()
        version = _summary(version_result.stdout or version_result.stderr)
        help_text = (help_result.stdout or "") + ("\n" + help_result.stderr if help_result.stderr else "")
        required_flags = ("-z", "--safe-mode", "--ignore-user-config", "--ignore-rules", "--no-restore-cwd")
        missing = [flag for flag in required_flags if flag not in help_text]
        blockers: list[str] = []
        if version_result.returncode != 0 or not version:
            blockers.append("VERSION_PROBE_FAILED")
        if help_result.returncode != 0:
            blockers.append("HELP_PROBE_FAILED")
        blockers.extend("MISSING_PUBLIC_FLAG:" + flag for flag in missing)
        if not self.authentication_observed:
            blockers.append("AUTH_NOT_OBSERVED")
        if not self.read_only_guard_observed:
            blockers.append("READ_ONLY_FILESYSTEM_GUARD_NOT_OBSERVED")
        if any(item.startswith(("MISSING_PUBLIC_FLAG", "HELP_PROBE", "VERSION_PROBE")) for item in blockers):
            eligibility = "SKIPPED_INTERFACE_UNSUPPORTED"
        elif "AUTH_NOT_OBSERVED" in blockers:
            eligibility = "SKIPPED_NOT_AUTHENTICATED"
        elif "READ_ONLY_FILESYSTEM_GUARD_NOT_OBSERVED" in blockers:
            eligibility = "SKIPPED_UNSAFE_WORKSPACE_OR_CHANNEL_BOUNDARY"
        else:
            eligibility = "ELIGIBLE_FOR_LIVE_READONLY"
        return LiveCapabilityLease.build(
            lease_id=lease_id, executor_id=self.executor_id, executor_version=version,
            observed_at=observed_at, expires_at=expires_at, ttl_seconds=ttl_seconds,
            binary_digest=hashlib.sha256(version.encode("utf-8")).hexdigest(), interface_digest=interface_digest(help_text),
            observed_capabilities=("repo.read",), forbidden_capabilities=("repo.write", "repo.test", "terminal.run", "browser.read", "browser.act", "web.read", "messaging.send", "subagents", "scheduler"),
            unknown_capabilities=(), workspace_semantics="EXPLICIT_DISPOSABLE_CWD_WITH_READ_ONLY_FILESYSTEM_GUARD",
            approval_sandbox_semantics="HERMES_SAFE_MODE_IGNORE_USER_CONFIG_AND_RULES",
            structured_output_semantics="BOUNDED_SINGLE_JSON_TEXT_OBJECT", timeout_supported=True, cancel_supported=True,
            resume_supported=False, live_eligibility=eligibility, eligibility_blockers=tuple(blockers), source="hermes-public-cli-probe-r2",
        )

    def build_argv(self, envelope: LiveDispatchEnvelope) -> tuple[str, ...]:
        if envelope.executor_id != self.executor_id or envelope.adapter_id != self.adapter_id:
            raise LiveAdapterError("Hermes live envelope is not bound to this adapter")
        if envelope.workspace_mode not in {"DISPOSABLE_READ_ONLY", "DISPOSABLE_SYNTHETIC_READ_ONLY"} or envelope.side_effect_class != "READ_ONLY_SYNTHETIC" or envelope.permission_ceiling != ("repo.read",):
            raise LiveAdapterError("Hermes live adapter refuses a widened workspace, effect, or permission ceiling")
        prompt = "IGNITION_LIVE_SYNTHETIC_READONLY_TASK\n" + canonical_json({
            "task_id": envelope.task_id,
            "synthetic_input_ref": envelope.synthetic_input_ref,
            "success_criteria": list(envelope.success_criteria),
            "output_contract": dict(envelope.output_contract),
            "instruction": "Read only the disposable fixture. Do not write, delete, execute shell, use network, message, browse, or inspect private state. Return exactly one JSON object and no commentary.",
        })
        if len(prompt.encode("utf-8")) > 32 * 1024:
            raise LiveAdapterError("Hermes live synthetic prompt exceeds the bounded input")
        argv = (
            self.executable, "--safe-mode", "--ignore-user-config", "--ignore-rules", "--no-restore-cwd",
            "--provider", self.provider, "--model", self.model, "--reasoning", "low", "-z", prompt,
        )
        if any(item in {"--resume", "--continue", "--worktree", "--yolo", "--accept-hooks"} or item in {"gateway", "send", "message"} for item in argv):
            raise LiveAdapterError("unsafe Hermes session, worktree, approval, or channel flag leaked into live argv")
        return argv

    def dispatch(self, envelope: LiveDispatchEnvelope) -> LiveAdapterObservation:
        argv = self.build_argv(envelope)
        process = self._run(argv, timeout_seconds=envelope.timeout_seconds)
        events: tuple[Mapping[str, Any], ...] = ()
        parsed = False
        parse_error = ""
        if not process.timed_out and not process.output_truncated and process.stdout.strip():
            try:
                value = json.loads(process.stdout.strip())
                if not isinstance(value, dict):
                    raise ValueError("final response is not an object")
                events = (value,)
                parsed = True
            except (ValueError, json.JSONDecodeError) as exc:
                parse_error = f"Hermes final text is not the exact JSON contract: {exc}"
        version_result, help_result = self._probe()
        help_text = help_result.stdout or help_result.stderr
        return LiveAdapterObservation(
            self.executor_id, self.adapter_id, _summary(version_result.stdout or version_result.stderr), interface_digest(help_text),
            process, events, parsed, parse_error, _summary(process.stdout or process.stderr), _response_digest(process.stdout), None,
        )


class LiveOpenClawAdapter:
    """Safety probe for OpenClaw; refuses the current gateway-owned surface."""

    executor_id = "external.openclaw"
    family = "OpenClaw"

    def __init__(
        self,
        workspace: str | Path,
        *,
        executable: str = "/Users/zhiyuan/.local/bin/openclaw",
        transport: LiveProcessTransport | Any | None = None,
        adapter_id: str = "openclaw-live-r2",
    ) -> None:
        root = Path(workspace)
        if not root.is_absolute() or not root.is_dir():
            raise LiveAdapterError("OpenClaw safety probe requires an existing absolute disposable workspace")
        self.workspace = root
        self.executable = executable
        self.transport = transport or LiveProcessTransport(executable_allowlist=(executable,))
        self.adapter_id = adapter_id
        self._probe_cache: tuple[LiveProcessResult, LiveProcessResult] | None = None

    def _run(self, argv: Sequence[str], timeout_seconds: float = 5) -> LiveProcessResult:
        try:
            return self.transport.run(argv, cwd=self.workspace, timeout_seconds=timeout_seconds)
        except (OSError, LiveTransportError) as exc:
            raise LiveAdapterError(f"OpenClaw public process probe failed: {type(exc).__name__}") from exc

    def _probe(self) -> tuple[LiveProcessResult, LiveProcessResult]:
        if self._probe_cache is None:
            self._probe_cache = (self._run((self.executable, "--version")), self._run((self.executable, "agent", "--help")))
        return self._probe_cache

    def observe_lease(self, *, lease_id: str, observed_at: str, expires_at: str, ttl_seconds: float) -> LiveCapabilityLease:
        version_result, help_result = self._probe()
        version = _summary(version_result.stdout or version_result.stderr)
        help_text = (help_result.stdout or "") + ("\n" + help_result.stderr if help_result.stderr else "")
        blockers = [
            "MISSING_PUBLIC_DISPOSABLE_WORKSPACE_BINDING",
            "GATEWAY_OR_LOCAL_AGENT_SESSION_SURFACE_NOT_CHANNEL_OFF_PROVABLE",
            "NO_EXPLICIT_READ_ONLY_PERMISSION_CEILING",
            "MESSAGE_AND_CHANNEL_OPTIONS_PRESENT_IN_PUBLIC_AGENT_SURFACE",
        ]
        if version_result.returncode != 0:
            blockers.append("VERSION_PROBE_FAILED")
        if help_result.returncode != 0:
            blockers.append("HELP_PROBE_FAILED")
        return LiveCapabilityLease.build(
            lease_id=lease_id, executor_id=self.executor_id, executor_version=version,
            observed_at=observed_at, expires_at=expires_at, ttl_seconds=ttl_seconds,
            binary_digest=hashlib.sha256(version.encode("utf-8")).hexdigest(), interface_digest=interface_digest(help_text),
            observed_capabilities=(), forbidden_capabilities=("repo.read", "repo.write", "repo.test", "terminal.run", "browser.read", "browser.act", "web.read", "messaging.send", "subagents", "scheduler"),
            unknown_capabilities=("workspace.binding", "channel.disable", "read_only_permission", "daemon.persistence"),
            workspace_semantics="GATEWAY_OWNED_OR_CONFIGURED_WORKSPACE_NOT_DISPOSABLE",
            approval_sandbox_semantics="NOT_PROVEN_FROM_AGENT_HELP",
            structured_output_semantics="JSON_RESULT_ADVERTISED_BUT_BINDING_UNSAFE",
            timeout_supported=True, cancel_supported=False, resume_supported=False,
            live_eligibility="SKIPPED_UNSAFE_WORKSPACE_OR_CHANNEL_BOUNDARY", eligibility_blockers=tuple(blockers), source="openclaw-agent-help-safety-probe-r2",
        )

    def build_argv(self, envelope: LiveDispatchEnvelope) -> tuple[str, ...]:
        raise LiveAdapterError("OpenClaw live dispatch is refused until disposable workspace and channel-off boundary are publicly provable")

    def dispatch(self, envelope: LiveDispatchEnvelope) -> LiveAdapterObservation:
        raise LiveAdapterError("OpenClaw live dispatch is intentionally not attempted under the current safety lease")


__all__ = ["LiveAdapterError", "LiveAdapterObservation", "LiveCodexAdapter", "LiveHermesAdapter", "LiveOpenClawAdapter"]
