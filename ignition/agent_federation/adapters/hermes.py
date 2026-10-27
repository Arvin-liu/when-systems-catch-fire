"""Hermes Agent text-bridge adapter for External Agent Federation R1.

Hermes exposes a stable one-shot CLI, but its final response is text and the
one-shot mode auto-bypasses approvals.  This adapter therefore declares a
degraded, read-only bridge only.  It runs in Hermes safe mode with user config,
rules, plugins, MCP and memory customizations disabled, and never imports or
copies Hermes-owned session/memory state.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Callable, Mapping, Sequence

from ..contracts import (
    ArtifactRef,
    ExecutorDescriptor,
    ExecutorHealth,
    ExternalSessionRef,
    FederatedHandoffBundle,
    FederatedProgressEvent,
    FederatedResultReceipt,
    FederatedTaskEnvelope,
    FederationContractError,
    UnsupportedExecutorOperation,
    canonical_digest,
    canonical_json,
)
from ..conformance import IdempotencyLedger
from ..sdk import (
    AdapterSDKError,
    MalformedOutput,
    SafeProcessResult,
    build_receipt,
    redact_text,
    require_capabilities,
    run_safe_subprocess,
    session_ref,
)


Runner = Callable[[Sequence[str], float], SafeProcessResult]


class HermesAdapterError(AdapterSDKError):
    """Raised when the observed Hermes public one-shot boundary is unusable."""


@dataclass(frozen=True)
class _ProbeSnapshot:
    version: str
    help_text: str
    help_sha256: str
    version_ok: bool
    help_ok: bool
    version_error: str = ""
    help_error: str = ""

    @property
    def oneshot(self) -> bool:
        return "--oneshot" in self.help_text or "-z PROMPT" in self.help_text

    @property
    def safe_mode(self) -> bool:
        return "--safe-mode" in self.help_text

    @property
    def ignore_user_config(self) -> bool:
        return "--ignore-user-config" in self.help_text

    @property
    def ignore_rules(self) -> bool:
        return "--ignore-rules" in self.help_text

    @property
    def resume(self) -> bool:
        return "--resume" in self.help_text

    @property
    def no_restore_cwd(self) -> bool:
        return "--no-restore-cwd" in self.help_text


_PRIVATE_TEXT_MARKERS = (
    "authorization",
    "api_key",
    "cookie",
    "password",
    "secret",
    "token",
)
_FORBIDDEN_EFFECT_MARKERS = (
    "write",
    "delete",
    "modify",
    "send",
    "message",
    "browser",
    "device",
    "terminal",
    "execute",
    "network",
    "gateway",
    "install",
    "publish",
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_text(text: str) -> str:
    result = redact_text(text)
    for marker in _PRIVATE_TEXT_MARKERS:
        result = result.replace(marker, "[REDACTED_FIELD]")
    return result.strip()[:2000]


class HermesAdapter:
    """A bounded read-only text bridge over Hermes ``--oneshot``."""

    executor_id = "external.hermes"
    family = "Hermes Agent"

    def __init__(
        self,
        executable: str = "/Users/zhiyuan/.local/bin/hermes",
        *,
        runner: Runner | None = None,
        resume_session: str | None = None,
        adapter_version: str = "hermes-adapter-r1",
        output_cap_bytes: int = 64 * 1024,
    ) -> None:
        if not isinstance(executable, str) or not executable.strip():
            raise FederationContractError("Hermes executable must be non-empty")
        if resume_session is not None and (not isinstance(resume_session, str) or not resume_session.strip()):
            raise FederationContractError("Hermes resume_session must be null or non-empty")
        if not isinstance(output_cap_bytes, int) or isinstance(output_cap_bytes, bool) or output_cap_bytes <= 0:
            raise FederationContractError("Hermes output_cap_bytes must be positive")
        self.executable = executable
        self.resume_session = resume_session
        self.adapter_version = adapter_version
        self.output_cap_bytes = output_cap_bytes
        self._runner = runner or self._default_runner
        self._probe_snapshot: _ProbeSnapshot | None = None
        self._health: ExecutorHealth | None = None
        self._events: dict[str, FederatedProgressEvent] = {}
        self._responses: dict[str, str] = {}
        self._session_refs: dict[str, ExternalSessionRef] = {}
        self._ledger = IdempotencyLedger()

    def _default_runner(self, argv: Sequence[str], timeout_seconds: float) -> SafeProcessResult:
        return run_safe_subprocess(
            argv,
            timeout_seconds=timeout_seconds,
            output_cap_bytes=self.output_cap_bytes,
            executable_allowlist=(self.executable,),
        )

    def _call(self, argv: Sequence[str], timeout_seconds: float) -> SafeProcessResult:
        try:
            result = self._runner(tuple(argv), float(timeout_seconds))
        except (FileNotFoundError, PermissionError, OSError) as exc:
            raise HermesAdapterError(f"Hermes CLI is unavailable: {type(exc).__name__}") from exc
        if not isinstance(result, SafeProcessResult):
            raise HermesAdapterError("injected Hermes runner must return SafeProcessResult")
        return result

    def _ensure_probe(self) -> _ProbeSnapshot:
        if self._probe_snapshot is not None:
            return self._probe_snapshot
        version = "unknown"
        help_text = ""
        version_ok = False
        help_ok = False
        version_error = ""
        help_error = ""
        try:
            result = self._call((self.executable, "--version"), 5)
            version_ok = result.returncode == 0
            combined = (result.stdout or result.stderr).strip()
            version = combined.splitlines()[0] if combined else "unknown"
            if not version_ok:
                version_error = f"version returncode={result.returncode}"
        except HermesAdapterError as exc:
            version_error = str(exc)
        try:
            result = self._call((self.executable, "--help"), 5)
            help_ok = result.returncode == 0
            help_text = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
            if not help_ok:
                help_error = f"help returncode={result.returncode}"
        except HermesAdapterError as exc:
            help_error = str(exc)
        help_sha256 = hashlib.sha256(help_text.encode("utf-8")).hexdigest()
        self._probe_snapshot = _ProbeSnapshot(version, help_text, help_sha256, version_ok, help_ok, version_error, help_error)
        return self._probe_snapshot

    def probe(self) -> ExecutorHealth:
        snapshot = self._ensure_probe()
        if snapshot.version_ok and snapshot.help_ok:
            status = "HEALTHY"
            reason = "observed --version and --help on the public Hermes CLI"
        elif snapshot.version_ok or snapshot.help_ok:
            status = "DEGRADED"
            reason = "; ".join(item for item in (snapshot.version_error, snapshot.help_error) if item) or "one public probe failed"
        else:
            status = "UNAVAILABLE"
            reason = "; ".join(item for item in (snapshot.version_error, snapshot.help_error) if item) or "public CLI probes failed"
        capability_digest = canonical_digest({
            "executor_id": self.executor_id,
            "version": snapshot.version,
            "help_sha256": snapshot.help_sha256,
            "bridge": "read-only-text",
        })
        self._health = ExecutorHealth(status, _now(), reason, capability_digest=capability_digest)
        return self._health

    def describe(self) -> ExecutorDescriptor:
        snapshot = self._ensure_probe()
        health = self.probe()
        return ExecutorDescriptor(
            executor_id=self.executor_id,
            family=self.family,
            version=snapshot.version,
            transport_kind=("CLI_TEXT_ONESHOT",),
            availability="AVAILABLE" if snapshot.version_ok or snapshot.help_ok else "UNAVAILABLE",
            health=health,
            capability_tokens=("repo.read",) if snapshot.oneshot and snapshot.safe_mode and snapshot.ignore_user_config and snapshot.ignore_rules else (),
            supported_task_granularities=("ACTION",),
            workspace_semantics="INHERITS_CWD_WITHOUT_HERMES_WORKTREE",
            permission_control_semantics="OS_READ_ONLY_ALLOWLIST; HERMES_ONESHOT_APPROVALS_NOT_AUTHORITY",
            structured_output_support=False,
            progress_support=False,
            cancel_support=False,
            native_resume_support=False,
            external_session_refs=("hermes-resume-session",) if snapshot.resume else (),
            network_semantics="EXTERNAL_AGENT_OWNED_NOT_ENABLED_BY_ADAPTER",
            max_task_duration_seconds=None,
            adapter_version=self.adapter_version,
            limitations=(
                "DEGRADED_TEXT_BRIDGE: final stdout is not a structured event stream.",
                "Only explicit repo.read low-risk envelopes are accepted.",
                "Hermes one-shot approvals are auto-bypassed; the adapter never grants write, tool, channel or device effects.",
                "Hermes memory, skills, subagents, provider, gateway and session history remain external-owned.",
                "LIVE_SMOKE_NOT_RUN: Step 05 used a captured final-text fixture and injected runner.",
            ),
        )

    def _require_read_only_bridge(self, envelope: FederatedTaskEnvelope) -> _ProbeSnapshot:
        snapshot = self._ensure_probe()
        if not (snapshot.version_ok or snapshot.help_ok):
            raise HermesAdapterError("Hermes public CLI is unavailable")
        if not snapshot.oneshot or not snapshot.safe_mode or not snapshot.ignore_user_config or not snapshot.ignore_rules:
            raise UnsupportedExecutorOperation("Hermes one-shot, safe-mode and configuration-isolation flags were not all observed")
        require_capabilities(envelope.required_capabilities, ("repo.read",))
        if set(envelope.required_capabilities) != {"repo.read"}:
            raise UnsupportedExecutorOperation("Hermes text bridge accepts repo.read only")
        if not envelope.forbidden_effects:
            raise UnsupportedExecutorOperation("Hermes text bridge requires explicit forbidden effects")
        for effect in envelope.allowed_effects:
            normalized = effect.casefold()
            if any(marker in normalized for marker in _FORBIDDEN_EFFECT_MARKERS) or not any(marker in normalized for marker in ("read", "inspect", "list", "summar")):
                raise UnsupportedExecutorOperation("Hermes text bridge accepts only explicit low-risk read effects")
        return snapshot

    def _task_prompt(self, envelope: FederatedTaskEnvelope) -> str:
        body = {
            "federation_task_id": envelope.federation_task_id,
            "goal": envelope.goal,
            "success_criteria": list(envelope.success_criteria),
            "required_capabilities": list(envelope.required_capabilities),
            "allowed_effects": list(envelope.allowed_effects),
            "forbidden_effects": list(envelope.forbidden_effects),
            "workspace_scope": list(envelope.workspace_scope),
            "output_contract": envelope.output_contract.to_dict(),
            "instruction": "Perform only the explicitly allowed read-only inspection. Return a concise final text summary; do not claim Ignition validation.",
        }
        prompt = "IGNITION_FEDERATED_READ_ONLY_TASK\n" + canonical_json(body)
        if len(prompt.encode("utf-8")) > 32 * 1024:
            raise AdapterSDKError("Hermes text bridge prompt exceeds 32768 UTF-8 bytes")
        return prompt

    def dispatch(self, envelope: FederatedTaskEnvelope) -> FederatedProgressEvent:
        if not isinstance(envelope, FederatedTaskEnvelope):
            raise FederationContractError("Hermes dispatch expects FederatedTaskEnvelope")
        if not self._ledger.claim(envelope.idempotency_key):
            raise AdapterSDKError(f"duplicate federation idempotency key: {envelope.idempotency_key}")
        snapshot = self._require_read_only_bridge(envelope)
        argv: list[str] = [self.executable, "--safe-mode", "--ignore-user-config", "--ignore-rules"]
        if self.resume_session is not None:
            if not snapshot.resume:
                raise UnsupportedExecutorOperation("Hermes --resume was not observed in the public help")
            argv.extend(("--resume", self.resume_session))
            if snapshot.no_restore_cwd:
                argv.append("--no-restore-cwd")
        argv.extend(("-z", self._task_prompt(envelope)))
        process = self._call(argv, float(envelope.budget.max_seconds))
        if process.returncode != 0:
            state = "FAILED"
            summary = _safe_text(process.stderr or f"Hermes CLI returned non-zero status {process.returncode}")
        else:
            if not process.stdout.strip():
                raise MalformedOutput("Hermes one-shot final response is empty")
            state = "COMPLETED_UNVALIDATED"
            summary = _safe_text(process.stdout)
        external_ref = None
        refs: tuple[str, ...] = ()
        if self.resume_session is not None:
            external_ref = session_ref(self.executor_id, self.resume_session, "hermes-resume-session", _now())
            self._session_refs[envelope.federation_task_id] = external_ref
            refs = (f"external-session:{self.resume_session}",)
        event = FederatedProgressEvent(
            envelope.federation_task_id,
            self.executor_id,
            1,
            state,
            summary or "Hermes final text observed; Ignition validation remains pending.",
            refs,
        )
        self._events[envelope.federation_task_id] = event
        self._responses[envelope.federation_task_id] = process.stdout
        return event

    def status(self, federation_task_id: str) -> FederatedProgressEvent:
        if not isinstance(federation_task_id, str) or not federation_task_id.strip():
            raise FederationContractError("federation_task_id must be non-empty")
        return self._events.get(federation_task_id) or FederatedProgressEvent(
            federation_task_id,
            self.executor_id,
            0,
            "UNKNOWN",
            "No public Hermes status is cached; external state was not queried.",
            (),
        )

    def cancel(self, federation_task_id: str) -> FederatedProgressEvent:
        raise UnsupportedExecutorOperation("Hermes one-shot help did not expose a supported cancellation operation")

    def resume(self, bundle: FederatedHandoffBundle) -> FederatedProgressEvent:
        raise UnsupportedExecutorOperation("Hermes resume requires an explicit task envelope and is not synthesized from a handoff")

    def receipt_from_response(self, federation_task_id: str) -> FederatedResultReceipt:
        if federation_task_id not in self._responses or federation_task_id not in self._events:
            raise FederationContractError("no Hermes response is cached for this task")
        event = self._events[federation_task_id]
        terminal_state = "FAILED" if event.state == "FAILED" else "REQUIRES_RECONCILIATION"
        return build_receipt(
            federation_task_id=federation_task_id,
            executor_id=self.executor_id,
            terminal_state=terminal_state,
            claimed_actions=(),
            artifacts=(),
            validation_refs=(),
            external_session_ref=self._session_refs.get(federation_task_id),
            telemetry={"adapter": self.adapter_version, "executor_status": event.state, "text_response_bytes": len(self._responses[federation_task_id].encode("utf-8"))},
            unresolveds=() if terminal_state == "FAILED" else ("OS_VALIDATION_NOT_PERFORMED",),
            handoff_eligible=False,
            handoff_reason="text-only executor output is not OS validation proof",
        )
