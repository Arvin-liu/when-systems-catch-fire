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
