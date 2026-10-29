"""Provider-neutral JSONL boundary for an external planner."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import time
from typing import Any, Mapping, Sequence

from agent_kernel.contracts import KernelValidationError, _id, _summary, _tuple_strings, sha256_json

from .actions import ExecutionPacket


class TransportError(RuntimeError):
    """Raised when the external planner violates the typed transport."""


@dataclass(frozen=True)
class ReasonerRequest:
    phase: str
    run_id: str
    goal_summary: str
    environment_summary: str
    capability_catalog: tuple[str, ...]
    memory_summaries: tuple[str, ...] = ()
    previous_summaries: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _id(self.run_id, "run_id")
        if self.phase not in {"FRAME", "PLAN"}:
            raise KernelValidationError("reasoner phase must be FRAME or PLAN")
        _summary(self.goal_summary, "goal_summary")
        _summary(self.environment_summary, "environment_summary")
        object.__setattr__(self, "capability_catalog", _tuple_strings(self.capability_catalog, "capability_catalog"))
        object.__setattr__(self, "memory_summaries", _tuple_strings(self.memory_summaries, "memory_summaries"))
        object.__setattr__(self, "previous_summaries", _tuple_strings(self.previous_summaries, "previous_summaries"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "run_id": self.run_id,
            "goal_summary": self.goal_summary,
            "environment_summary": self.environment_summary,
            "capability_catalog": list(self.capability_catalog),
            "memory_summaries": list(self.memory_summaries),
            "previous_summaries": list(self.previous_summaries),
        }


@dataclass(frozen=True)
class ReasonerResponse:
    phase: str
    frame_summary: str | None
    packets: tuple[ExecutionPacket, ...]
    status: str = "CONTINUE"
    block_summary: str | None = None

    def __post_init__(self) -> None:
        if self.phase not in {"FRAME", "PLAN"}:
            raise KernelValidationError("reasoner response phase must be FRAME or PLAN")
        if self.frame_summary is not None:
            _summary(self.frame_summary, "frame_summary")
        if self.status not in {"CONTINUE", "STOP", "WAITING_FOR_INPUT"}:
            raise KernelValidationError("unknown reasoner response status")
        if self.block_summary is not None:
            _summary(self.block_summary, "block_summary")
        if not isinstance(self.packets, tuple):
            raise KernelValidationError("reasoner packets must be a tuple")
        if len({packet.action_id for packet in self.packets}) != len(self.packets):
            raise KernelValidationError("reasoner packet action ids must be unique")

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "frame_summary": self.frame_summary,
            "packets": [packet.to_dict() for packet in self.packets],
            "status": self.status,
            "block_summary": self.block_summary,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ReasonerResponse":
        required = {"phase", "frame_summary", "packets", "status", "block_summary"}
        if set(data) != required or not isinstance(data.get("packets"), list):
            raise TransportError("reasoner response keys or packet array are invalid")
        try:
            packets = tuple(ExecutionPacket.from_dict(item) for item in data["packets"])
        except (KeyError, TypeError, ValueError) as exc:
            raise TransportError(f"reasoner returned an invalid execution packet: {exc}") from exc
        return cls(
            phase=data["phase"], frame_summary=data["frame_summary"], packets=packets,
            status=data["status"], block_summary=data["block_summary"],
        )


def action_plan_hash(packets: Sequence[ExecutionPacket]) -> str:
    # The per-packet source_plan_hash is a commitment to this list, so it is
    # intentionally excluded from the list being committed.
    return sha256_json([
        {key: value for key, value in packet.to_dict().items() if key != "source_plan_hash"}
        for packet in packets
    ])


class ScriptedReasoner:
    """Deterministic planner used by offline runs and conformance tests."""

    def __init__(self, packets: Sequence[ExecutionPacket], *, frame_summary: str = "bounded local task frame") -> None:
        self.packets = tuple(packets)
        self.frame_summary = frame_summary

    def request(self, request: ReasonerRequest) -> ReasonerResponse:
        if request.phase == "FRAME":
            return ReasonerResponse(phase="FRAME", frame_summary=self.frame_summary, packets=())
        return ReasonerResponse(phase="PLAN", frame_summary=None, packets=self.packets)


class JsonlReasonerTransport:
    """One request/one response stdio adapter with no provider assumptions."""

    def __init__(self, argv: Sequence[str], *, timeout_seconds: float = 30.0, cwd: str | Path | None = None) -> None:
        if isinstance(argv, str) or not argv:
            raise TransportError("reasoner argv must be a non-empty array")
        self.argv = tuple(str(item) for item in argv)
        if any(not item or any(char in item for char in "|;&<>`\n\r") or "$(" in item for item in self.argv):
            raise TransportError("reasoner argv must be literal and shell-free")
        if timeout_seconds <= 0:
            raise TransportError("reasoner timeout must be positive")
        self.timeout_seconds = float(timeout_seconds)
        self.cwd = str(cwd) if cwd is not None else None

    def request(self, request: ReasonerRequest) -> ReasonerResponse:
        process = subprocess.Popen(
            list(self.argv), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=self.cwd, shell=False, close_fds=True,
        )
        payload = (json.dumps(request.to_dict(), ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        try:
            stdout, stderr = process.communicate(payload, timeout=self.timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            process.kill()
            process.communicate()
            raise TransportError("reasoner transport timeout") from exc
        if process.returncode != 0:
            raise TransportError(f"reasoner process exited {process.returncode}: {stderr[:512].decode('utf-8', errors='replace')}")
        lines = [line for line in stdout.decode("utf-8", errors="strict").splitlines() if line.strip()]
        if len(lines) != 1:
            raise TransportError("reasoner must emit exactly one non-empty JSONL response line")
        try:
            data = json.loads(lines[0])
        except json.JSONDecodeError as exc:
            raise TransportError("reasoner emitted invalid JSON") from exc
        if not isinstance(data, dict):
            raise TransportError("reasoner response must be a JSON object")
        return ReasonerResponse.from_dict(data)


GATEWAY_SCHEMA_VERSION = "reasoner-gateway-r1"
SUPPORTED_GATEWAY_SCHEMA_VERSIONS = frozenset({GATEWAY_SCHEMA_VERSION})
_GATEWAY_SECRET_MARKERS = (
    "api_key", "access_token", "authorization", "bearer ", "client_secret",
    "password", "private model reasoning", "hidden reasoning", "chain-of-thought",
)


class GatewayError(TransportError):
    """Raised when a Reasoner Gateway contract or adapter boundary fails."""


def _public_gateway_strings(values: Any, field_name: str) -> tuple[str, ...]:
    values = _tuple_strings(values, field_name)
    for value in values:
        lowered = value.casefold()
        if any(marker in lowered for marker in _GATEWAY_SECRET_MARKERS) or "prompt" in lowered:
            raise GatewayError(f"{field_name} contains secret, prompt or hidden-reasoning material")
    return values


def _telemetry_pairs(value: Any) -> tuple[tuple[str, str], ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping):
        pairs = list(value.items())
    elif isinstance(value, (list, tuple)):
        pairs = list(value)
    else:
        raise GatewayError("telemetry must be an object or pair array")
    result: list[tuple[str, str]] = []
    for pair in pairs:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise GatewayError("telemetry must contain key/value pairs")
        key, item = pair
        if not isinstance(key, str) or not key.strip() or not isinstance(item, str):
            raise GatewayError("telemetry keys and values must be strings")
        lowered = f"{key}={item}".casefold()
        if any(marker in lowered for marker in _GATEWAY_SECRET_MARKERS) or "prompt" in lowered:
            raise GatewayError("telemetry cannot contain secrets, prompts or hidden reasoning")
        result.append((key, item))
    if len({key for key, _ in result}) != len(result):
        raise GatewayError("telemetry keys must be unique")
    return tuple(sorted(result, key=lambda pair: pair[0]))


@dataclass(frozen=True)
class GatewayRequest:
    """Versioned, digest-bound request sent to an external reasoner."""

    phase: str
    run_id: str
    goal_summary: str
    environment_summary: str
    capability_catalog: tuple[str, ...]
    context_capsule: tuple[str, ...] = ()
    available_packs: tuple[str, ...] = ()
    memory_summaries: tuple[str, ...] = ()
    previous_summaries: tuple[str, ...] = ()
    schema_version: str = GATEWAY_SCHEMA_VERSION
    request_id: str | None = None

    def __post_init__(self) -> None:
        _id(self.run_id, "run_id")
        if self.phase not in {"FRAME", "PLAN"}:
            raise GatewayError("Gateway request phase must be FRAME or PLAN")
        _summary(self.goal_summary, "goal_summary")
        _summary(self.environment_summary, "environment_summary")
        _id(self.schema_version, "schema_version")
        if self.schema_version not in SUPPORTED_GATEWAY_SCHEMA_VERSIONS:
            raise GatewayError(f"unsupported Gateway request schema: {self.schema_version}")
        object.__setattr__(self, "capability_catalog", _public_gateway_strings(self.capability_catalog, "capability_catalog"))
        object.__setattr__(self, "context_capsule", _public_gateway_strings(self.context_capsule, "context_capsule"))
        object.__setattr__(self, "available_packs", _public_gateway_strings(self.available_packs, "available_packs"))
        object.__setattr__(self, "memory_summaries", _public_gateway_strings(self.memory_summaries, "memory_summaries"))
        object.__setattr__(self, "previous_summaries", _public_gateway_strings(self.previous_summaries, "previous_summaries"))
        if self.request_id is not None:
            _id(self.request_id, "request_id")
        else:
            object.__setattr__(self, "request_id", f"request-{sha256_json(self._payload())[:24]}")

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "phase": self.phase,
            "run_id": self.run_id,
            "goal_summary": self.goal_summary,
            "environment_summary": self.environment_summary,
            "capability_catalog": list(self.capability_catalog),
            "context_capsule": list(self.context_capsule),
            "available_packs": list(self.available_packs),
            "memory_summaries": list(self.memory_summaries),
            "previous_summaries": list(self.previous_summaries),
        }

    @property
    def request_digest(self) -> str:
        return sha256_json(self._payload())

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "request_digest": self.request_digest}


@dataclass(frozen=True)
class GatewayResponse:
    """Typed reasoner proposal; it has no execution or authority operation."""

    phase: str
    status: str
    frame_summary: str | None
    packets: tuple[ExecutionPacket, ...]
    block_summary: str | None = None
    schema_version: str = GATEWAY_SCHEMA_VERSION
    request_digest: str | None = None
    requested_capabilities: tuple[str, ...] = ()
    requested_packs: tuple[str, ...] = ()
    authority_claims: tuple[str, ...] = ()
    terminal_claim: str | None = None
    telemetry: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if self.phase not in {"FRAME", "PLAN"}:
            raise GatewayError("Gateway response phase must be FRAME or PLAN")
        if self.status not in {"CONTINUE", "STOP", "WAITING_FOR_INPUT"}:
            raise GatewayError("Gateway response has no generic or untyped success status")
        if self.frame_summary is not None:
            _summary(self.frame_summary, "frame_summary")
        if self.block_summary is not None:
            _summary(self.block_summary, "block_summary")
        if self.terminal_claim is not None:
            _summary(self.terminal_claim, "terminal_claim")
        if not isinstance(self.packets, tuple):
            raise GatewayError("Gateway response packets must be a tuple")
        if len({packet.action_id for packet in self.packets}) != len(self.packets):
            raise GatewayError("Gateway response packet action ids must be unique")
        _id(self.schema_version, "schema_version")
        if self.request_digest is not None and (len(self.request_digest) != 64 or any(char not in "0123456789abcdef" for char in self.request_digest)):
            raise GatewayError("Gateway response request_digest must be SHA-256")
        object.__setattr__(self, "requested_capabilities", _public_gateway_strings(self.requested_capabilities, "requested_capabilities"))
        object.__setattr__(self, "requested_packs", _public_gateway_strings(self.requested_packs, "requested_packs"))
        object.__setattr__(self, "authority_claims", _public_gateway_strings(self.authority_claims, "authority_claims"))
        object.__setattr__(self, "telemetry", _telemetry_pairs(self.telemetry))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "request_digest": self.request_digest,
            "phase": self.phase,
            "status": self.status,
            "frame_summary": self.frame_summary,
            "packets": [packet.to_dict() for packet in self.packets],
            "block_summary": self.block_summary,
            "requested_capabilities": list(self.requested_capabilities),
            "requested_packs": list(self.requested_packs),
            "authority_claims": list(self.authority_claims),
            "terminal_claim": self.terminal_claim,
            "telemetry": dict(self.telemetry),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "GatewayResponse":
        required = {
            "schema_version", "request_digest", "phase", "status", "frame_summary", "packets",
            "block_summary", "requested_capabilities", "requested_packs", "authority_claims", "terminal_claim", "telemetry",
        }
        if set(data) != required or not isinstance(data.get("packets"), list):
            raise GatewayError("Gateway response schema keys or packet array are invalid")
        try:
            packets = tuple(ExecutionPacket.from_dict(item) for item in data["packets"])
        except (KeyError, TypeError, ValueError) as exc:
            raise GatewayError(f"Gateway response packet is invalid: {exc}") from exc
        return cls(
            schema_version=data["schema_version"], request_digest=data["request_digest"], phase=data["phase"],
            status=data["status"], frame_summary=data["frame_summary"], packets=packets,
            block_summary=data["block_summary"], requested_capabilities=tuple(data["requested_capabilities"]),
            requested_packs=tuple(data["requested_packs"]),
            authority_claims=tuple(data["authority_claims"]), terminal_claim=data["terminal_claim"],
            telemetry=data["telemetry"],
        )


class ScriptedGatewayAdapter:
    """Deterministic offline adapter returning only a typed proposal."""

    def __init__(self, packets: Sequence[ExecutionPacket], *, frame_summary: str = "bounded gateway task frame", requested_packs: Sequence[str] = (), telemetry: Mapping[str, str] | None = None) -> None:
        self.packets = tuple(packets)
        self.frame_summary = frame_summary
        self.requested_packs = tuple(requested_packs)
        self.telemetry = tuple(sorted((telemetry or {}).items()))

    def request(self, request: GatewayRequest) -> GatewayResponse:
        if request.phase == "FRAME":
            return GatewayResponse(
                schema_version=request.schema_version, request_digest=request.request_digest,
                phase="FRAME", status="CONTINUE", frame_summary=self.frame_summary, packets=(),
                telemetry=self.telemetry,
            )
        return GatewayResponse(
            schema_version=request.schema_version, request_digest=request.request_digest,
            phase="PLAN", status="CONTINUE", frame_summary=None, packets=self.packets,
            requested_capabilities=tuple(sorted({capability for packet in self.packets for capability in packet.required_capabilities})),
            requested_packs=self.requested_packs,
            telemetry=self.telemetry,
        )


class SubprocessReasonerAdapter:
    """Reference one-request/one-response subprocess adapter for the Gateway."""

    def __init__(self, argv: Sequence[str], *, timeout_seconds: float = 30.0, max_output_bytes: int = 65536, cwd: str | Path | None = None) -> None:
        if isinstance(argv, str) or not argv:
            raise GatewayError("Gateway subprocess argv must be a non-empty array")
        self.argv = tuple(str(item) for item in argv)
        if any(not item or any(char in item for char in "|;&<>`\n\r") or "$(" in item for item in self.argv):
            raise GatewayError("Gateway subprocess argv must be literal and shell-free")
        if timeout_seconds <= 0 or max_output_bytes <= 0:
            raise GatewayError("Gateway timeout and output budget must be positive")
        self.timeout_seconds = float(timeout_seconds)
        self.max_output_bytes = int(max_output_bytes)
        self.cwd = str(cwd) if cwd is not None else None

    def request(self, request: GatewayRequest) -> GatewayResponse:
        try:
            process = subprocess.Popen(
                list(self.argv), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=self.cwd, shell=False, close_fds=True,
            )
        except OSError as exc:
            raise GatewayError("GATEWAY_CRASH: subprocess could not start") from exc
        payload = (json.dumps(request.to_dict(), ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        try:
            stdout, stderr = process.communicate(payload, timeout=self.timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            process.kill()
            process.communicate()
            raise GatewayError("GATEWAY_TIMEOUT") from exc
        if process.returncode != 0:
            detail = stderr[:512].decode("utf-8", errors="replace")
            raise GatewayError(f"GATEWAY_CRASH: process exited {process.returncode}: {detail}")
        if len(stdout) > self.max_output_bytes:
            raise GatewayError("GATEWAY_OVERSIZED_OUTPUT")
        try:
            lines = [line for line in stdout.decode("utf-8", errors="strict").splitlines() if line.strip()]
        except UnicodeDecodeError as exc:
            raise GatewayError("GATEWAY_MALFORMED_OUTPUT") from exc
        if len(lines) != 1:
            raise GatewayError("GATEWAY_MALFORMED_OUTPUT")
        try:
            data = json.loads(lines[0])
        except json.JSONDecodeError as exc:
            raise GatewayError("GATEWAY_MALFORMED_OUTPUT") from exc
        if not isinstance(data, dict):
            raise GatewayError("GATEWAY_MALFORMED_OUTPUT")
        return GatewayResponse.from_dict(data)


class AdversarialGatewayAdapter:
    """Offline negative adapter for authority, completion and wire attacks."""

    def __init__(self, mode: str) -> None:
        self.mode = mode
        if mode not in {"permission_expansion", "forged_completion", "malformed_json", "oversized_output", "crash"}:
            raise GatewayError(f"unknown adversarial Gateway mode: {mode}")

    def request(self, request: GatewayRequest) -> GatewayResponse:
        if self.mode == "malformed_json":
            raise GatewayError("GATEWAY_MALFORMED_OUTPUT")
        if self.mode == "oversized_output":
            raise GatewayError("GATEWAY_OVERSIZED_OUTPUT")
        if self.mode == "crash":
            raise GatewayError("GATEWAY_CRASH")
        if self.mode == "permission_expansion":
            return GatewayResponse(
                phase=request.phase, status="CONTINUE", frame_summary="bounded adversarial proposal" if request.phase == "FRAME" else None,
                packets=(), request_digest=request.request_digest,
                requested_capabilities=("network",), authority_claims=("self-approved permission expansion",),
            )
        return GatewayResponse(
            phase=request.phase, status="STOP", frame_summary=None, packets=(), request_digest=request.request_digest,
            terminal_claim="COMPLETED_VALIDATED",
        )


class ReasonerGateway:
    """Provider-neutral validator around deterministic or subprocess adapters."""

    def __init__(self, adapter: Any, *, max_context_chars: int = 12000, supported_schema_versions: Sequence[str] = (GATEWAY_SCHEMA_VERSION,)) -> None:
        if max_context_chars <= 0:
            raise GatewayError("Gateway context budget must be positive")
        self.adapter = adapter
        self.max_context_chars = int(max_context_chars)
        self.supported_schema_versions = frozenset(str(item) for item in supported_schema_versions)
        if not self.supported_schema_versions:
            raise GatewayError("Gateway must support at least one schema version")

    def request(self, request: GatewayRequest) -> GatewayResponse:
        if request.schema_version not in self.supported_schema_versions:
            raise GatewayError(f"Gateway schema negotiation failed for {request.schema_version}")
        capsule_chars = sum(len(item) for item in (*request.context_capsule, *request.memory_summaries, *request.previous_summaries))
        if capsule_chars > self.max_context_chars:
            raise GatewayError("GATEWAY_CONTEXT_CAPSULE_EXCEEDED")
        response = self.adapter.request(request)
        if not isinstance(response, GatewayResponse):
            raise GatewayError("Gateway adapter did not return a typed response")
        if response.schema_version not in self.supported_schema_versions:
            raise GatewayError(f"Gateway response schema is unsupported: {response.schema_version}")
        if response.request_digest != request.request_digest:
            raise GatewayError("Gateway response request digest does not match request")
        if response.authority_claims:
            raise GatewayError("Gateway rejected self-approved authority claim")
        if response.terminal_claim is not None:
            raise GatewayError("Gateway rejected reasoner terminal/completion claim")
        known_capabilities = set(request.capability_catalog)
        requested = set(response.requested_capabilities)
        packet_capabilities = {capability for packet in response.packets for capability in packet.required_capabilities}
        outside = sorted((requested | packet_capabilities) - known_capabilities)
        if outside:
            raise GatewayError(f"Gateway proposal requests capability outside read-only catalog: {outside}")
        outside_packs = sorted(set(response.requested_packs) - set(request.available_packs))
        if outside_packs:
            raise GatewayError(f"Gateway proposal requests Pack outside read-only catalog: {outside_packs}")
        for packet in response.packets:
            if packet.run_id != request.run_id:
                raise GatewayError("Gateway proposal packet has a different run lineage")
        if response.packets:
            digest = action_plan_hash(response.packets)
            if any(packet.source_plan_hash != digest for packet in response.packets):
                raise GatewayError("Gateway proposal packet source_plan_hash is not bound to its complete plan")
        return response


class GatewayReasonerAdapter:
    """Bridge the stable Gateway into the legacy R1 Reasoner interface."""

    def __init__(self, gateway: ReasonerGateway, *, available_packs: Sequence[str] = (), context_capsule: Sequence[str] = ()) -> None:
        self.gateway = gateway
        self.available_packs = tuple(available_packs)
        self.context_capsule = tuple(context_capsule)

    def request(self, request: ReasonerRequest) -> ReasonerResponse:
        gateway_request = GatewayRequest(
            phase=request.phase, run_id=request.run_id, goal_summary=request.goal_summary,
            environment_summary=request.environment_summary, capability_catalog=request.capability_catalog,
            context_capsule=(*self.context_capsule, *request.memory_summaries), available_packs=self.available_packs,
            memory_summaries=request.memory_summaries, previous_summaries=request.previous_summaries,
        )
        response = self.gateway.request(gateway_request)
        return ReasonerResponse(
            phase=response.phase, frame_summary=response.frame_summary, packets=response.packets,
            status=response.status, block_summary=response.block_summary,
        )


__all__ = [
    "AdversarialGatewayAdapter",
    "GatewayError",
    "GatewayReasonerAdapter",
    "GatewayRequest",
    "GatewayResponse",
    "GATEWAY_SCHEMA_VERSION",
    "JsonlReasonerTransport",
    "ReasonerGateway",
    "ReasonerRequest",
    "ReasonerResponse",
    "ScriptedGatewayAdapter",
    "ScriptedReasoner",
    "SubprocessReasonerAdapter",
    "TransportError",
    "action_plan_hash",
]
