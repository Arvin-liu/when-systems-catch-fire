"""OpenClaw CLI adapter for External Agent Federation R1.

The adapter owns only the public OpenClaw CLI boundary.  It does not start a
Gateway, inspect OpenClaw state, copy OpenClaw memory, or expose OpenClaw's
internal plan/tool loop as Ignition state.  A task envelope is written to a
disposable UTF-8 file and passed through the observed ``openclaw agent`` JSON
surface.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import math
from pathlib import Path
import tempfile
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
)
from ..conformance import IdempotencyLedger
from ..sdk import (
    AdapterSDKError,
    MalformedOutput,
    SafeProcessResult,
    build_receipt,
    parse_json_object,
    redact_text,
    run_safe_subprocess,
    session_ref,
)


Runner = Callable[[Sequence[str], float], SafeProcessResult]
"""Injected process runner used by fixture tests; production uses safe argv."""


class OpenClawAdapterError(AdapterSDKError):
    """Raised when the observed OpenClaw public boundary is unusable."""


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
    def json_mode(self) -> bool:
        return "--json" in self.help_text

    @property
    def message_file(self) -> bool:
        return "--message-file" in self.help_text

    @property
    def timeout(self) -> bool:
        return "--timeout" in self.help_text

    @property
    def agent_selection(self) -> bool:
        return "--agent" in self.help_text

    @property
    def session_key(self) -> bool:
        return "--session-key" in self.help_text

    @property
    def session_id(self) -> bool:
        return "--session-id" in self.help_text


_PRIVATE_NAME_MARKERS = (
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


def _safe_public(value: Any, *, depth: int = 0) -> Any:
    """Keep response summaries public and bounded without importing hidden state."""

    if depth > 4:
        return "[nested response omitted]"
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            normalized = name.casefold().replace("-", "_")
            if any(marker in normalized for marker in _PRIVATE_NAME_MARKERS):
                continue
            result[name] = _safe_public(item, depth=depth + 1)
        return result
    if isinstance(value, (list, tuple)):
        return [_safe_public(item, depth=depth + 1) for item in value[:50]]
    if isinstance(value, str):
        return redact_text(value)[:2000]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return redact_text(str(value))[:2000]


def _response_summary(payload: Mapping[str, Any]) -> str:
    for key in ("summary", "message", "result", "text", "output"):
        if key in payload:
            value = _safe_public(payload[key])
            if isinstance(value, str) and value.strip():
                return value.strip()[:2000]
            if value not in ({}, [], None):
                import json

                return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))[:2000]
    return "OpenClaw JSON response observed; Ignition validation remains pending."


def _response_state(payload: Mapping[str, Any]) -> str:
    raw = payload.get("state", payload.get("status", ""))
    if isinstance(raw, str):
        normalized = raw.strip().casefold()
        if normalized in {"failed", "failure", "error", "cancelled", "canceled"}:
            return "FAILED"
        if normalized in {"running", "queued", "pending", "started"}:
            return "RUNNING"
    return "COMPLETED_UNVALIDATED"


def _public_refs(payload: Mapping[str, Any]) -> tuple[str, ...]:
    raw = payload.get("refs", ())
    if not isinstance(raw, (list, tuple)):
        return ()
    refs: list[str] = []
    for item in raw:
        if isinstance(item, str) and item.strip() and len(item) <= 512:
            ref = redact_text(item.strip())
            if ref not in refs:
                refs.append(ref)
    return tuple(refs[:50])


class OpenClawAdapter:
    """A thin, fixture-testable adapter over ``openclaw agent --json``."""

    executor_id = "external.openclaw"
    family = "OpenClaw"

    def __init__(
        self,
        executable: str = "/Users/zhiyuan/.local/bin/openclaw",
        *,
        runner: Runner | None = None,
        agent_id: str | None = None,
        session_key: str | None = None,
        adapter_version: str = "openclaw-adapter-r1",
        output_cap_bytes: int = 64 * 1024,
    ) -> None:
        if not isinstance(executable, str) or not executable.strip():
            raise FederationContractError("OpenClaw executable must be non-empty")
        if agent_id is not None and (not isinstance(agent_id, str) or not agent_id.strip()):
            raise FederationContractError("OpenClaw agent_id must be null or non-empty")
        if session_key is not None and (not isinstance(session_key, str) or not session_key.strip()):
            raise FederationContractError("OpenClaw session_key must be null or non-empty")
        if not isinstance(output_cap_bytes, int) or isinstance(output_cap_bytes, bool) or output_cap_bytes <= 0:
            raise FederationContractError("OpenClaw output_cap_bytes must be positive")
        self.executable = executable
        self.agent_id = agent_id
        self.session_key = session_key
        self.adapter_version = adapter_version
        self.output_cap_bytes = output_cap_bytes
        self._runner = runner or self._default_runner
        self._probe_snapshot: _ProbeSnapshot | None = None
        self._health: ExecutorHealth | None = None
        self._descriptor: ExecutorDescriptor | None = None
        self._events: dict[str, FederatedProgressEvent] = {}
        self._session_refs: dict[str, ExternalSessionRef] = {}
        self._responses: dict[str, Mapping[str, Any]] = {}
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
            raise OpenClawAdapterError(f"OpenClaw CLI is unavailable: {type(exc).__name__}") from exc
        if not isinstance(result, SafeProcessResult):
            raise OpenClawAdapterError("injected OpenClaw runner must return SafeProcessResult")
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
            version_result = self._call((self.executable, "--version"), 5)
            version_ok = version_result.returncode == 0
            version = (version_result.stdout or version_result.stderr).strip().splitlines()[0] if (version_result.stdout or version_result.stderr).strip() else "unknown"
            if not version_ok:
                version_error = f"version returncode={version_result.returncode}"
        except OpenClawAdapterError as exc:
            version_error = str(exc)
        try:
            help_result = self._call((self.executable, "agent", "--help"), 5)
            help_ok = help_result.returncode == 0
            help_text = (help_result.stdout or "") + ("\n" + help_result.stderr if help_result.stderr else "")
            if not help_ok:
                help_error = f"help returncode={help_result.returncode}"
        except OpenClawAdapterError as exc:
            help_error = str(exc)
        help_sha256 = hashlib.sha256(help_text.encode("utf-8")).hexdigest()
        self._probe_snapshot = _ProbeSnapshot(version, help_text, help_sha256, version_ok, help_ok, version_error, help_error)
        return self._probe_snapshot

    def probe(self) -> ExecutorHealth:
        snapshot = self._ensure_probe()
        if snapshot.version_ok and snapshot.help_ok:
            status = "HEALTHY"
            reason = "observed --version and agent --help on the public CLI"
        elif snapshot.version_ok or snapshot.help_ok:
            status = "DEGRADED"
            reason = "; ".join(item for item in (snapshot.version_error, snapshot.help_error) if item) or "one public probe failed"
        else:
            status = "UNAVAILABLE"
            reason = "; ".join(item for item in (snapshot.version_error, snapshot.help_error) if item) or "public CLI probes failed"
        tokens = self._capability_tokens(snapshot)
        capability_digest = canonical_digest({"executor_id": self.executor_id, "version": snapshot.version, "help_sha256": snapshot.help_sha256, "capability_tokens": list(tokens)})
        self._health = ExecutorHealth(status, _now(), reason, capability_digest=capability_digest)
        return self._health

    @staticmethod
    def _capability_tokens(snapshot: _ProbeSnapshot) -> tuple[str, ...]:
        tokens: list[str] = []
        if snapshot.timeout:
            tokens.append("long_task")
        return tuple(tokens)

    def describe(self) -> ExecutorDescriptor:
        snapshot = self._ensure_probe()
        health = self.probe()
        tokens = self._capability_tokens(snapshot)
        session_refs: list[str] = []
        if snapshot.session_key:
            session_refs.append("openclaw-session-key")
        if snapshot.session_id:
            session_refs.append("openclaw-session-id")
        limitations = [
            "OpenClaw internal plan/tool loop and memory remain external-owned.",
            "Gateway, channel, browser and device semantics are not exposed by this adapter.",
            "LIVE_SMOKE_NOT_RUN: Step 04 used disposable CLI contract fixtures only.",
        ]
        if not snapshot.json_mode or not snapshot.message_file:
            limitations.append("Observed help does not prove the JSON message-file invocation is available.")
        return ExecutorDescriptor(
            executor_id=self.executor_id,
            family=self.family,
            version=snapshot.version,
            transport_kind=("CLI_JSON",),
            availability="AVAILABLE" if snapshot.version_ok or snapshot.help_ok else "UNAVAILABLE",
            health=health,
            capability_tokens=tokens,
            supported_task_granularities=("ACTION", "SUBTASK"),
            workspace_semantics="UNKNOWN_UNPROBED",
            permission_control_semantics="OS_POLICY_INTERSECTED_WITH_EXTERNAL_AGENT_POLICY",
            structured_output_support=snapshot.json_mode,
            progress_support=False,
            cancel_support=False,
            native_resume_support=False,
            external_session_refs=tuple(session_refs),
            network_semantics="EXTERNAL_AGENT_OWNED_NOT_ENABLED_BY_ADAPTER",
            max_task_duration_seconds=None,
            adapter_version=self.adapter_version,
            limitations=tuple(limitations),
        )

    def _require_json_surface(self) -> _ProbeSnapshot:
        snapshot = self._ensure_probe()
        if not (snapshot.version_ok or snapshot.help_ok):
            raise OpenClawAdapterError("OpenClaw public CLI is unavailable")
        if not snapshot.json_mode or not snapshot.message_file or not snapshot.timeout:
            raise UnsupportedExecutorOperation("OpenClaw JSON message-file/timeout surface was not observed")
        return snapshot

    def _event_from_payload(
        self,
        envelope: FederatedTaskEnvelope,
        payload: Mapping[str, Any],
        *,
        process: SafeProcessResult,
    ) -> FederatedProgressEvent:
        sequence = self._events[envelope.federation_task_id].sequence + 1 if envelope.federation_task_id in self._events else 1
        state = _response_state(payload)
        refs = _public_refs(payload)
        external_ref = self._session_ref_from_payload(payload)
        if external_ref is not None:
            self._session_refs[envelope.federation_task_id] = external_ref
            refs = tuple(dict.fromkeys((*refs, f"external-session:{external_ref.session_id}")))
        event = FederatedProgressEvent(
            envelope.federation_task_id,
            self.executor_id,
            sequence,
            state,
            _response_summary(payload),
            refs,
            payload.get("progress_fraction") if isinstance(payload.get("progress_fraction"), (int, float)) else None,
        )
        self._events[envelope.federation_task_id] = event
        public_payload = _safe_public(payload)
        self._responses[envelope.federation_task_id] = public_payload if isinstance(public_payload, Mapping) else {}
        return event

    def _session_ref_from_payload(self, payload: Mapping[str, Any]) -> ExternalSessionRef | None:
        value = payload.get("session_id", payload.get("session_key"))
        if not isinstance(value, str) or not value.strip() or len(value) > 256:
            return None
        if any(marker in value.casefold() for marker in ("token", "secret", "api_key", "cookie", "authorization")):
            return None
        return session_ref(self.executor_id, value.strip(), "openclaw-cli-session", _now())

    def dispatch(self, envelope: FederatedTaskEnvelope) -> FederatedProgressEvent:
        if not isinstance(envelope, FederatedTaskEnvelope):
            raise FederationContractError("OpenClaw dispatch expects FederatedTaskEnvelope")
        if not self._ledger.claim(envelope.idempotency_key):
            raise AdapterSDKError(f"duplicate federation idempotency key: {envelope.idempotency_key}")
        snapshot = self._require_json_surface()
        if self.agent_id is not None and not snapshot.agent_selection:
            raise UnsupportedExecutorOperation("OpenClaw --agent was not observed in the public help")
        if self.session_key is not None and not snapshot.session_key:
            raise UnsupportedExecutorOperation("OpenClaw --session-key was not observed in the public help")
        timeout = max(1, math.ceil(float(envelope.budget.max_seconds)))
        argv: list[str] = [self.executable, "agent", "--json"]
        if self.agent_id is not None:
            argv.extend(("--agent", self.agent_id))
        if self.session_key is not None:
            argv.extend(("--session-key", self.session_key))
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".federated-task.json", delete=False) as handle:
                temp_path = Path(handle.name)
                import json

                handle.write(json.dumps(envelope.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
            argv.extend(("--message-file", str(temp_path), "--timeout", str(timeout)))
            process = self._call(argv, float(timeout))
            if process.returncode != 0:
                payload = {"status": "failed", "summary": f"OpenClaw CLI returned non-zero status {process.returncode}: {redact_text(process.stderr)[:500]}"}
            else:
                payload = parse_json_object(process.stdout, field="OpenClaw JSON response")
            return self._event_from_payload(envelope, payload, process=process)
        finally:
            if temp_path is not None:
                try:
                    temp_path.unlink()
                except FileNotFoundError:
                    pass

    def status(self, federation_task_id: str) -> FederatedProgressEvent:
        if not isinstance(federation_task_id, str) or not federation_task_id.strip():
            raise FederationContractError("federation_task_id must be non-empty")
        event = self._events.get(federation_task_id)
        if event is not None:
            return event
        return FederatedProgressEvent(
            federation_task_id,
            self.executor_id,
            0,
            "UNKNOWN",
            "No public OpenClaw status is cached; external state was not queried.",
            (),
        )

    def cancel(self, federation_task_id: str) -> FederatedProgressEvent:
        raise UnsupportedExecutorOperation("OpenClaw agent help did not expose a supported cancellation operation")

    def resume(self, bundle: FederatedHandoffBundle) -> FederatedProgressEvent:
        raise UnsupportedExecutorOperation("OpenClaw agent help did not expose a supported native resume operation")

    def receipt_from_response(self, federation_task_id: str) -> FederatedResultReceipt:
        """Build a conservative receipt; executor completion is never OS validation."""

        if federation_task_id not in self._responses or federation_task_id not in self._events:
            raise FederationContractError("no OpenClaw response is cached for this task")
        payload = self._responses[federation_task_id]
        event = self._events[federation_task_id]
        artifacts: list[ArtifactRef] = []
        raw_artifacts = payload.get("artifacts", ())
        if raw_artifacts is not None:
            if not isinstance(raw_artifacts, (list, tuple)):
                raise MalformedOutput("OpenClaw artifacts must be an array")
            for item in raw_artifacts:
                if not isinstance(item, Mapping):
                    raise MalformedOutput("OpenClaw artifact must be an object")
                artifacts.append(ArtifactRef.from_dict(item))
        raw_actions = payload.get("claimed_actions", ())
        claimed_actions = tuple(item for item in raw_actions if isinstance(item, str) and item.strip()) if isinstance(raw_actions, (list, tuple)) else ()
        raw_validation = payload.get("validation_refs", ())
        validation_refs = tuple(item for item in raw_validation if isinstance(item, str) and item.strip()) if isinstance(raw_validation, (list, tuple)) else ()
        terminal_state = "FAILED" if event.state == "FAILED" else "REQUIRES_RECONCILIATION"
        unresolveds = () if terminal_state == "FAILED" else ("OS_VALIDATION_NOT_PERFORMED",)
        telemetry = {
            "adapter": self.adapter_version,
            "executor_status": event.state,
            "response_keys": len(payload),
            "validation_refs_observed": len(validation_refs),
        }
        return build_receipt(
            federation_task_id=federation_task_id,
            executor_id=self.executor_id,
            terminal_state=terminal_state,
            claimed_actions=claimed_actions,
            artifacts=artifacts,
            validation_refs=validation_refs,
            external_session_ref=self._session_refs.get(federation_task_id),
            telemetry=telemetry,
            unresolveds=unresolveds,
            handoff_eligible=False,
            handoff_reason="executor output is not OS validation proof",
        )
