"""Codex CLI adapter for External Agent Federation R1.

Codex is treated as an external coding executor.  The adapter uses the public
``codex exec --json`` JSONL surface, keeps Codex thread IDs as pointer-only
references, and applies a conservative sandbox/approval intersection.  It
never uses the dangerous bypass flag and never turns Codex's own completion
event into Ignition validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from typing import Any, Callable, Mapping, Sequence

from ..contracts import (
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
    parse_jsonl_events,
    redact_text,
    require_capabilities,
    run_safe_subprocess,
    session_ref,
)


Runner = Callable[[Sequence[str], float], SafeProcessResult]


class CodexAdapterError(AdapterSDKError):
    """Raised when the observed Codex public execution boundary is unusable."""


@dataclass(frozen=True)
class _ProbeSnapshot:
    version: str
    help_text: str
    help_sha256: str
    version_ok: bool
    help_ok: bool
    version_error: str = ""
    help_error: str = ""

    def has(self, flag: str) -> bool:
        return flag in self.help_text


_PRIVATE_EVENT_MARKERS = (
    "prompt",
    "system_prompt",
    "chain_of_thought",
    "cot",
    "thoughts",
    "reasoning",
    "token",
    "secret",
    "cookie",
    "authorization",
    "api_key",
    "password",
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_text(text: str) -> str:
    result = redact_text(text)
    return result.strip()[:2000]


def _event_type(event: Mapping[str, Any]) -> str:
    value = event.get("type", "")
    return value.strip().casefold() if isinstance(value, str) else ""


def _public_summary(events: Sequence[Mapping[str, Any]]) -> str:
    candidates: list[str] = []
    for event in events:
        event_type = _event_type(event)
        item = event.get("item")
        if isinstance(item, Mapping):
            for key in ("text", "message", "summary", "output"):
                value = item.get(key)
                if isinstance(value, str) and value.strip():
                    candidates.append(value)
        for key in ("summary", "message", "text"):
            value = event.get(key)
            if isinstance(value, str) and value.strip() and event_type not in {"thread.started", "turn.started"}:
                candidates.append(value)
    if candidates:
        return _safe_text(candidates[-1])
    return "Codex JSONL execution observed; Ignition validation remains pending."


def _thread_id(events: Sequence[Mapping[str, Any]]) -> str | None:
    for event in events:
        for key in ("thread_id", "threadId", "session_id"):
            value = event.get(key)
            if not isinstance(value, str) or not value.strip() or len(value) > 256:
                continue
            normalized = value.casefold()
            if any(marker in normalized for marker in ("token", "secret", "cookie", "api_key", "authorization")):
                continue
            return value.strip()
    return None


def _progress_fraction(events: Sequence[Mapping[str, Any]]) -> float | None:
    value: Any = None
    for event in events:
        if "progress_fraction" in event:
            value = event["progress_fraction"]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= float(value) <= 1:
        return None
    return float(value)


class CodexAdapter:
    """A public JSONL Codex adapter with an explicit permission intersection."""

    executor_id = "external.codex"
    family = "Codex CLI"

    def __init__(
        self,
        executable: str = "/Users/zhiyuan/.local/bin/codex",
        *,
        runner: Runner | None = None,
        sandbox_mode: str = "read-only",
        workspace: str | Path | None = None,
        adapter_version: str = "codex-adapter-r1",
        output_cap_bytes: int = 128 * 1024,
    ) -> None:
        if not isinstance(executable, str) or not executable.strip():
            raise FederationContractError("Codex executable must be non-empty")
        if sandbox_mode not in {"read-only", "workspace-write"}:
            raise FederationContractError("Codex federation sandbox must be read-only or workspace-write")
        if workspace is not None:
            workspace = str(workspace)
            if not workspace.startswith("/"):
                raise FederationContractError("Codex workspace must be an absolute path")
        if not isinstance(output_cap_bytes, int) or isinstance(output_cap_bytes, bool) or output_cap_bytes <= 0:
            raise FederationContractError("Codex output_cap_bytes must be positive")
        self.executable = executable
        self.sandbox_mode = sandbox_mode
        self.workspace = workspace
        self.adapter_version = adapter_version
        self.output_cap_bytes = output_cap_bytes
        self._runner = runner or self._default_runner
        self._probe_snapshot: _ProbeSnapshot | None = None
        self._health: ExecutorHealth | None = None
        self._events: dict[str, FederatedProgressEvent] = {}
        self._responses: dict[str, int] = {}
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
            raise CodexAdapterError(f"Codex CLI is unavailable: {type(exc).__name__}") from exc
        if not isinstance(result, SafeProcessResult):
            raise CodexAdapterError("injected Codex runner must return SafeProcessResult")
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
        except CodexAdapterError as exc:
            version_error = str(exc)
        try:
            result = self._call((self.executable, "exec", "--help"), 5)
            help_ok = result.returncode == 0
            help_text = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
            if not help_ok:
                help_error = f"exec help returncode={result.returncode}"
        except CodexAdapterError as exc:
            help_error = str(exc)
        help_sha256 = hashlib.sha256(help_text.encode("utf-8")).hexdigest()
        self._probe_snapshot = _ProbeSnapshot(version, help_text, help_sha256, version_ok, help_ok, version_error, help_error)
        return self._probe_snapshot

    def probe(self) -> ExecutorHealth:
        snapshot = self._ensure_probe()
        if snapshot.version_ok and snapshot.help_ok:
            status = "HEALTHY"
            reason = "observed --version and exec --help on the public Codex CLI"
        elif snapshot.version_ok or snapshot.help_ok:
            status = "DEGRADED"
            reason = "; ".join(item for item in (snapshot.version_error, snapshot.help_error) if item) or "one public probe failed"
        else:
            status = "UNAVAILABLE"
            reason = "; ".join(item for item in (snapshot.version_error, snapshot.help_error) if item) or "public CLI probes failed"
        tokens = self._capability_tokens(snapshot)
        capability_digest = canonical_digest({
            "executor_id": self.executor_id,
            "version": snapshot.version,
            "help_sha256": snapshot.help_sha256,
            "sandbox_mode": self.sandbox_mode,
            "capability_tokens": list(tokens),
        })
        self._health = ExecutorHealth(status, _now(), reason, capability_digest=capability_digest)
        return self._health

    def _capability_tokens(self, snapshot: _ProbeSnapshot) -> tuple[str, ...]:
        tokens: list[str] = []
        if snapshot.has("--json") and snapshot.has("--sandbox"):
            tokens.append("repo.read")
            tokens.append("structured_progress")
            if self.sandbox_mode == "workspace-write":
                tokens.extend(("repo.write", "repo.test"))
        return tuple(tokens)

    def describe(self) -> ExecutorDescriptor:
        snapshot = self._ensure_probe()
        health = self.probe()
        tokens = self._capability_tokens(snapshot)
        return ExecutorDescriptor(
            executor_id=self.executor_id,
            family=self.family,
            version=snapshot.version,
            transport_kind=("CLI_JSONL",),
            availability="AVAILABLE" if snapshot.version_ok or snapshot.help_ok else "UNAVAILABLE",
            health=health,
            capability_tokens=tokens,
            supported_task_granularities=("ACTION", "SUBTASK"),
            workspace_semantics="EXPLICIT_CD_SCOPE_ONLY" if snapshot.has("--cd") else "UNKNOWN_UNPROBED",
            permission_control_semantics="OS_POLICY_INTERSECTED_WITH_CODEX_SANDBOX_AND_APPROVALS",
            structured_output_support=snapshot.has("--json"),
            progress_support=snapshot.has("--json"),
            cancel_support=False,
            native_resume_support=False,
            external_session_refs=("codex-thread-id",) if "resume" in snapshot.help_text.casefold() else (),
            network_semantics="OS_AND_CODEX_POLICY_INTERSECTION_NOT_ENABLED_BY_ADAPTER",
            max_task_duration_seconds=None,
            adapter_version=self.adapter_version,
            limitations=(
                "Codex thread/session history is pointer-only and is not OS canonical state.",
                "dangerously-bypass-approvals-and-sandbox is forbidden by this adapter.",
                "Default federation sandbox is read-only; workspace-write requires explicit construction.",
                "Codex completion events do not establish Ignition validation or acceptance.",
                "LIVE_SMOKE_NOT_RUN: nested Codex modification of a formal repository was explicitly forbidden.",
            ),
        )

    def _require_surface(self, envelope: FederatedTaskEnvelope) -> _ProbeSnapshot:
        snapshot = self._ensure_probe()
        if not (snapshot.version_ok or snapshot.help_ok):
            raise CodexAdapterError("Codex public CLI is unavailable")
        required = ("--json", "--ephemeral", "--ignore-user-config", "--ignore-rules", "--sandbox")
        missing = [flag for flag in required if not snapshot.has(flag)]
        if missing:
            raise UnsupportedExecutorOperation(f"Codex public exec help did not expose required safe flags: {missing}")
        require_capabilities(envelope.required_capabilities, self._capability_tokens(snapshot))
        if self.sandbox_mode == "read-only" and any(token in envelope.required_capabilities for token in ("repo.write", "repo.test")):
            raise CapabilityMismatch("read-only Codex federation cannot satisfy write/test capabilities")
        if self.sandbox_mode == "workspace-write" and (envelope.approval_policy.mode == "DENY" or not envelope.approval_policy.external_approval_allowed):
            raise CapabilityMismatch("Codex workspace-write requires an OS approval policy that permits external execution")
        if self.workspace is not None and not snapshot.has("--cd"):
            raise UnsupportedExecutorOperation("Codex --cd was not observed in exec help")
        return snapshot

    def _task_prompt(self, envelope: FederatedTaskEnvelope) -> str:
        prompt = "IGNITION_FEDERATED_TASK\n" + canonical_json({
            "federation_task_id": envelope.federation_task_id,
            "goal": envelope.goal,
            "success_criteria": list(envelope.success_criteria),
            "required_capabilities": list(envelope.required_capabilities),
            "allowed_effects": list(envelope.allowed_effects),
            "forbidden_effects": list(envelope.forbidden_effects),
            "workspace_scope": list(envelope.workspace_scope),
            "validation_contract": envelope.validation_contract.to_dict(),
            "output_contract": envelope.output_contract.to_dict(),
            "instruction": "Report observable work only. Do not treat your own completion event as Ignition validation.",
        })
        if len(prompt.encode("utf-8")) > 64 * 1024:
            raise AdapterSDKError("Codex task prompt exceeds 65536 UTF-8 bytes")
        return prompt

    def dispatch(self, envelope: FederatedTaskEnvelope) -> FederatedProgressEvent:
        if not isinstance(envelope, FederatedTaskEnvelope):
            raise FederationContractError("Codex dispatch expects FederatedTaskEnvelope")
        if not self._ledger.claim(envelope.idempotency_key):
            raise AdapterSDKError(f"duplicate federation idempotency key: {envelope.idempotency_key}")
        snapshot = self._require_surface(envelope)
        argv: list[str] = [
            self.executable,
            "exec",
            "--json",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--sandbox",
            self.sandbox_mode,
        ]
        if self.workspace is not None:
            argv.extend(("--cd", str(self.workspace)))
        argv.append(self._task_prompt(envelope))
        process = self._call(argv, float(envelope.budget.max_seconds))
        if process.returncode != 0:
            events: tuple[Mapping[str, Any], ...] = ()
            state = "FAILED"
            summary = _safe_text(process.stderr or f"Codex CLI returned non-zero status {process.returncode}")
        else:
            events = parse_jsonl_events(process.stdout)
            state = "FAILED" if any(_event_type(item) in {"turn.failed", "error", "turn.error"} for item in events) else "COMPLETED_UNVALIDATED"
            summary = _public_summary(events)
        thread = _thread_id(events)
        refs: tuple[str, ...] = ()
        if thread is not None:
            pointer = session_ref(self.executor_id, thread, "codex-thread-id", _now())
            self._session_refs[envelope.federation_task_id] = pointer
            refs = (f"external-session:{thread}",)
        event = FederatedProgressEvent(
            envelope.federation_task_id,
            self.executor_id,
            1,
            state,
            summary or "Codex JSONL execution observed; Ignition validation remains pending.",
            refs,
            _progress_fraction(events),
        )
        self._events[envelope.federation_task_id] = event
        self._responses[envelope.federation_task_id] = len(events)
        return event

    def status(self, federation_task_id: str) -> FederatedProgressEvent:
        if not isinstance(federation_task_id, str) or not federation_task_id.strip():
            raise FederationContractError("federation_task_id must be non-empty")
        return self._events.get(federation_task_id) or FederatedProgressEvent(
            federation_task_id,
            self.executor_id,
            0,
            "UNKNOWN",
            "No public Codex status is cached; external state was not queried.",
            (),
        )

    def cancel(self, federation_task_id: str) -> FederatedProgressEvent:
        raise UnsupportedExecutorOperation("Codex exec help did not expose a supported adapter cancellation operation")

    def resume(self, bundle: FederatedHandoffBundle) -> FederatedProgressEvent:
        raise UnsupportedExecutorOperation("Codex native resume pointer shape is not synthesized from a handoff bundle")

    def receipt_from_response(self, federation_task_id: str) -> FederatedResultReceipt:
        if federation_task_id not in self._responses or federation_task_id not in self._events:
            raise FederationContractError("no Codex response is cached for this task")
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
            telemetry={
                "adapter": self.adapter_version,
                "executor_status": event.state,
                "jsonl_event_count": self._responses[federation_task_id],
                "sandbox_mode": self.sandbox_mode,
            },
            unresolveds=() if terminal_state == "FAILED" else ("OS_VALIDATION_NOT_PERFORMED",),
            handoff_eligible=False,
            handoff_reason="Codex completion is not OS validation proof",
        )
