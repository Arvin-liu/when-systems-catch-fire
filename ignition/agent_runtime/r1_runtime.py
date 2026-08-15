"""Durable local execution runtime for Agent Runtime R1."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import time
from typing import Any, Mapping, Sequence

from agent_kernel import Phase, StopState, sha256_json
from agent_kernel.contracts import _id, _summary

from .actions import (
    ActionExecutionResult,
    ActionKind,
    ApprovalClass,
    CrashInjected,
    ExecutionPacket,
    FilePreimage,
    LocalWorkspaceExecutor,
    RollbackClass,
    WorkspacePolicy,
    WorkspaceViolation,
)
from .control import (
    ActionJournal,
    ApprovalDecisionR1,
    ApprovalRequestR1,
    ApprovalStore,
    ControlConflict,
    LeaseStore,
    _atomic_json,
    utc_now,
)
from .transport import (
    GatewayReasonerAdapter,
    ReasonerGateway,
    JsonlReasonerTransport,
    ReasonerRequest,
    ReasonerResponse,
    ScriptedGatewayAdapter,
    ScriptedReasoner,
    SubprocessReasonerAdapter,
    TransportError,
    action_plan_hash,
)
from .records import RunTerminalState


class RuntimeR1Error(RuntimeError):
    """Raised when a run cannot be continued without guessing."""


def _tuple(value: Any, field: str) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise RuntimeR1Error(f"{field} must be an array")
    result = tuple(str(item) for item in value)
    if any(not item.strip() for item in result):
        raise RuntimeR1Error(f"{field} contains an empty item")
    return result


@dataclass(frozen=True)
class R1RunSpec:
    run_id: str
    profile_ref: str
    goal: Mapping[str, Any]
    workspace: WorkspacePolicy
    capability_scope: Mapping[str, Any]
    actions: tuple[ExecutionPacket, ...]
    reasoner: Mapping[str, Any]
    executor: Mapping[str, Any]
    validator: Mapping[str, Any]
    lease_ttl_seconds: float = 60.0
    fault_injection: Mapping[str, str] = None

    def __post_init__(self) -> None:
        _id(self.run_id, "run_id")
        _id(self.profile_ref, "profile_ref")
        if not isinstance(self.goal, Mapping):
            raise RuntimeR1Error("goal must be an object")
        required_goal = {"statement", "success_conditions", "prohibited_actions"}
        if set(self.goal) != required_goal:
            raise RuntimeR1Error("goal must contain exactly statement, success_conditions and prohibited_actions")
        _summary(self.goal["statement"], "goal.statement")
        _tuple(self.goal["success_conditions"], "goal.success_conditions")
        _tuple(self.goal["prohibited_actions"], "goal.prohibited_actions")
        if not isinstance(self.capability_scope, Mapping):
            raise RuntimeR1Error("capability_scope must be an object")
        if set(self.capability_scope) != {"scope_id", "allowed_capabilities", "network_allowed"}:
            raise RuntimeR1Error("capability_scope must contain exactly scope_id, allowed_capabilities and network_allowed")
        _id(self.capability_scope["scope_id"], "capability_scope.scope_id")
        allowed_capabilities = _tuple(self.capability_scope["allowed_capabilities"], "capability_scope.allowed_capabilities")
        if not allowed_capabilities:
            raise RuntimeR1Error("capability_scope.allowed_capabilities must not be empty")
        known_capabilities = {"read.files", "read.directories", "write.files", "run.commands", "git.read"}
        unknown_capabilities = sorted(set(allowed_capabilities) - known_capabilities)
        if unknown_capabilities:
            raise RuntimeR1Error(f"capability_scope contains unknown capabilities: {unknown_capabilities}")
        if self.capability_scope["network_allowed"] is not False:
            raise RuntimeR1Error("R1 capability_scope.network_allowed must be false")
        if not isinstance(self.actions, tuple):
            raise RuntimeR1Error("actions must be a tuple")
        if len(self.actions) > self.workspace.max_actions:
            raise RuntimeR1Error("action count exceeds workspace policy")
        if sum(packet.kind in {item.value for item in (ActionKind.WRITE_FILE, ActionKind.CREATE_FILE, ActionKind.PATCH_TEXT_FILE)} for packet in self.actions) > self.workspace.max_writes:
            raise RuntimeR1Error("write count exceeds workspace policy")
        if not isinstance(self.reasoner, Mapping) or not isinstance(self.executor, Mapping) or not isinstance(self.validator, Mapping):
            raise RuntimeR1Error("reasoner, executor and validator must be objects")
        if self.reasoner.get("type", "scripted") not in {"scripted", "jsonl", "gateway-scripted", "gateway-jsonl"}:
            raise RuntimeR1Error("reasoner.type must be scripted, jsonl, gateway-scripted or gateway-jsonl")
        if set(self.executor) != {"type", "class_id"} or self.executor.get("type") != "local_workspace":
            raise RuntimeR1Error("executor must be the declared local_workspace adapter")
        _id(self.executor["class_id"], "executor.class_id")
        if self.validator.get("type", "command_exit") not in {"command_exit", "scripted"}:
            raise RuntimeR1Error("validator.type is not available in R1")
        if self.lease_ttl_seconds <= 0:
            raise RuntimeR1Error("lease_ttl_seconds must be positive")
        faults = dict(self.fault_injection or {})
        allowed_faults = {"pre_execute", "mid_write", "post_execute_before_persist", "post_persist"}
        for action_id, point in faults.items():
            _id(action_id, "fault_injection action_id")
            if point not in allowed_faults:
                raise RuntimeR1Error(f"unknown fault injection point: {point}")
        object.__setattr__(self, "fault_injection", faults)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "R1RunSpec":
        required = {"run_id", "profile_ref", "goal", "workspace", "capability_scope", "actions", "reasoner", "executor", "validator", "lease_ttl_seconds", "fault_injection"}
        if set(data) != required:
            raise RuntimeR1Error(f"run spec keys mismatch: missing={sorted(required-set(data))} unknown={sorted(set(data)-required)}")
        if not isinstance(data["actions"], list):
            raise RuntimeR1Error("actions must be an array")
        try:
            actions = tuple(ExecutionPacket.from_dict(item) for item in data["actions"])
            workspace = WorkspacePolicy.from_dict(data["workspace"])
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeR1Error(f"run spec action or workspace is invalid: {exc}") from exc
        if actions:
            plan_digest = action_plan_hash(actions)
            if any(packet.source_plan_hash != plan_digest for packet in actions):
                raise RuntimeR1Error("each action source_plan_hash must match the complete action plan")
        return cls(
            run_id=data["run_id"], profile_ref=data["profile_ref"], goal=dict(data["goal"]), workspace=workspace,
            capability_scope=dict(data["capability_scope"]),
            actions=actions, reasoner=dict(data["reasoner"]), executor=dict(data["executor"]), validator=dict(data["validator"]),
            lease_ttl_seconds=data["lease_ttl_seconds"], fault_injection=dict(data["fault_injection"] or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "profile_ref": self.profile_ref,
            "goal": dict(self.goal),
            "workspace": self.workspace.to_dict(),
            "capability_scope": dict(self.capability_scope),
            "actions": [packet.to_dict() for packet in self.actions],
            "reasoner": dict(self.reasoner),
            "executor": dict(self.executor),
            "validator": dict(self.validator),
            "lease_ttl_seconds": self.lease_ttl_seconds,
            "fault_injection": dict(self.fault_injection or {}),
        }


class AgentRuntimeR1:
    """A persisted one-process runtime with explicit local action boundaries."""

    def __init__(
        self,
        run_dir: str | Path,
        *,
        executor_instance_id: str = "instance-1",
        executor_class_id: str = "local-workspace-executor",
    ) -> None:
        self.run_dir = Path(run_dir)
        self.state_path = self.run_dir / "run-state.json"
        self.spec_path = self.run_dir / "run-spec.json"
        self.trace_path = self.run_dir / "trace.jsonl"
        self.journal = ActionJournal(self.run_dir / "action-journal.json")
        self.leases = LeaseStore(self.run_dir / "leases.json")
        self.approvals = ApprovalStore(self.run_dir / "approvals.json")
        self.executor_instance_id = executor_instance_id
        self.executor_class_id = executor_class_id
        _id(executor_instance_id, "executor_instance_id")
        _id(executor_class_id, "executor_class_id")
        self._state: dict[str, Any] | None = None
        self._spec: R1RunSpec | None = None
        self.executor: LocalWorkspaceExecutor | None = None

    @property
    def state(self) -> dict[str, Any]:
        if self._state is None:
            raise RuntimeR1Error("run is not loaded")
        return self._state

    @property
    def spec(self) -> R1RunSpec:
        if self._spec is None:
            raise RuntimeR1Error("run spec is not loaded")
        return self._spec

    def start(self, spec: R1RunSpec) -> dict[str, Any]:
        if self.state_path.exists() or self.spec_path.exists():
            raise RuntimeR1Error("run directory already contains a state or spec")
        if self.executor_class_id != spec.executor["class_id"]:
            raise RuntimeR1Error("initial executor class does not match the declared executor adapter")
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self._spec = spec
        self.executor = LocalWorkspaceExecutor(
            spec.workspace, executor_class_id=self.executor_class_id, executor_instance_id=self.executor_instance_id,
        )
        _atomic_json(self.spec_path, spec.to_dict())
        self._state = {
            "runtime_version": "agent-runtime-r1",
            "run_id": spec.run_id,
            "profile_ref": spec.profile_ref,
            "goal": dict(spec.goal),
            "phase": Phase.OBSERVE.value,
            "frame_summary": None,
            "packets": [],
            "plan_digest": None,
            "next_action_index": 0,
            "action_count": 0,
            "terminal": None,
            "pending_approval": None,
            "approval_events": [],
            "executions": [],
            "validations": [],
            "rollback_events": [],
            "memories": [],
            "trace": [],
            "executor_history": [self.executor.executor_id],
            "fault_injection": dict(spec.fault_injection or {}),
            "fault_injection_consumed": {},
            "created_at": utc_now(),
        }
        self._event(Phase.OBSERVE.value, "observe", "runtime-r1", "captured the declared workspace boundary", [spec.profile_ref])
        try:
            reasoner = self._reasoner(spec.actions)
            frame = reasoner.request(self._reasoner_request("FRAME"))
        except (RuntimeR1Error, TransportError) as exc:
            return self._stop(StopState.BLOCKED_WITH_EVIDENCE.value, f"reasoner transport failed closed: {exc}")
        if frame.phase != "FRAME" or frame.frame_summary is None or frame.packets:
            return self._stop(StopState.BLOCKED_WITH_EVIDENCE.value, "reasoner frame response was not a bounded frame")
        self.state["frame_summary"] = frame.frame_summary
        self._set_phase(Phase.FRAME.value)
        self._event(Phase.FRAME.value, "frame", "reasoner", "recorded a bounded task frame", [spec.run_id])
        try:
            plan = reasoner.request(self._reasoner_request("PLAN"))
        except (RuntimeR1Error, TransportError) as exc:
            return self._stop(StopState.BLOCKED_WITH_EVIDENCE.value, f"reasoner transport failed closed: {exc}")
        if plan.phase != "PLAN":
            return self._stop(StopState.BLOCKED_WITH_EVIDENCE.value, "reasoner plan response had the wrong phase")
        if plan.status != "CONTINUE":
            return self._stop(StopState.BLOCKED_WITH_EVIDENCE.value, plan.block_summary or "reasoner did not provide an executable plan")
        try:
            self._install_plan(plan.packets)
        except (RuntimeR1Error, WorkspaceViolation) as exc:
            return self._stop(StopState.CAPABILITY_UNAVAILABLE.value, str(exc))
        self._persist()
        return self._drive()

    def resume(self, *, executor_instance_id: str | None = None) -> dict[str, Any]:
        self._load()
        if executor_instance_id is not None:
            _id(executor_instance_id, "executor_instance_id")
            self.executor_instance_id = executor_instance_id
        self.executor = LocalWorkspaceExecutor(
            self.spec.workspace, executor_class_id=self.executor_class_id, executor_instance_id=self.executor_instance_id,
        )
        if self.executor.executor_id not in self.state["executor_history"]:
            self.state["executor_history"].append(self.executor.executor_id)
        terminal = self.state.get("terminal")
        if terminal and terminal.get("state") not in {StopState.WAITING_FOR_APPROVAL.value}:
            return dict(self.state)
        if terminal and terminal.get("state") == StopState.WAITING_FOR_APPROVAL.value:
            pending = self.state.get("pending_approval")
            if pending:
                request = self.approvals.get(pending["request_id"])
                if request is None or request.status == "PENDING":
                    return dict(self.state)
                if request.status == "DENIED":
                    return self._stop(StopState.BLOCKED_WITH_EVIDENCE.value, "the typed approval decision denied the action")
                if request.status != "ALLOWED":
                    return self._stop(StopState.BLOCKED_WITH_EVIDENCE.value, "the typed approval request is no longer actionable")
                self.state["approval_events"].append({"request_id": request.request_id, "status": request.status})
                self.state["pending_approval"] = None
                self.state["terminal"] = None
                self._persist()
        self._set_phase(Phase.CONTINUE.value)
        self._event(Phase.CONTINUE.value, "resume", self.executor.executor_id, "resumed from durable action and approval state", [])
        self._persist()
        return self._drive()

    def approve(
        self,
        request_id: str,
        decision: str,
        *,
        authority_id: str,
        authority_type: str = "human",
        reason_summary: str = "explicit typed approval decision",
    ) -> dict[str, Any]:
        self._load()
        pending = self.state.get("pending_approval")
        if not pending or pending.get("request_id") != request_id:
            raise RuntimeR1Error("request is not the pending approval for this run")
        request = self.approvals.get(request_id)
        if request is None:
            raise RuntimeR1Error("approval request is missing")
        approval = ApprovalDecisionR1(
            decision_id=f"decision-{request_id}", request_id=request_id, run_id=self.spec.run_id,
            action_digest=request.action_digest, decision=decision.upper(), authority_id=authority_id,
            authority_type=authority_type, decided_at=utc_now(), reason_summary=reason_summary,
        )
        self.approvals.submit(approval)
        return self.resume()

    def status(self) -> dict[str, Any]:
        self._load()
        return dict(self.state)

    def pending_approval(self) -> list[dict[str, Any]]:
        self._load()
        return [item.to_dict() for item in self.approvals.pending(run_id=self.spec.run_id)]

    def trace(self) -> list[dict[str, Any]]:
        self._load()
        return list(self.state["trace"])

    def _reasoner(self, configured: Sequence[ExecutionPacket]) -> Any:
        reasoner_type = self.spec.reasoner.get("type", "scripted")
        if reasoner_type == "scripted":
            return ScriptedReasoner(configured, frame_summary=self.spec.reasoner.get("frame_summary", "bounded local task frame"))
        if reasoner_type == "gateway-scripted":
            gateway = ReasonerGateway(
                ScriptedGatewayAdapter(configured, frame_summary=self.spec.reasoner.get("frame_summary", "bounded gateway task frame")),
                max_context_chars=int(self.spec.reasoner.get("max_context_chars", 12000)),
            )
            return GatewayReasonerAdapter(
                gateway,
                available_packs=tuple(self.spec.reasoner.get("available_packs", ())),
                context_capsule=tuple(self.spec.reasoner.get("context_capsule", ())),
            )
        if reasoner_type == "gateway-jsonl":
            argv = self.spec.reasoner.get("argv")
            if not isinstance(argv, list):
                raise RuntimeR1Error("gateway-jsonl reasoner requires a literal argv array")
            gateway = ReasonerGateway(
                SubprocessReasonerAdapter(
                    argv,
                    timeout_seconds=float(self.spec.reasoner.get("timeout_seconds", 30.0)),
                    max_output_bytes=int(self.spec.reasoner.get("max_output_bytes", 65536)),
                    cwd=self.spec.reasoner.get("cwd"),
                ),
                max_context_chars=int(self.spec.reasoner.get("max_context_chars", 12000)),
            )
            return GatewayReasonerAdapter(
                gateway,
                available_packs=tuple(self.spec.reasoner.get("available_packs", ())),
                context_capsule=tuple(self.spec.reasoner.get("context_capsule", ())),
            )
        argv = self.spec.reasoner.get("argv")
        if not isinstance(argv, list):
            raise RuntimeR1Error("jsonl reasoner requires a literal argv array")
        return JsonlReasonerTransport(argv, timeout_seconds=float(self.spec.reasoner.get("timeout_seconds", 30.0)), cwd=self.spec.reasoner.get("cwd"))

    def _reasoner_request(self, phase: str) -> ReasonerRequest:
        capabilities = tuple(sorted(_tuple(self.spec.capability_scope["allowed_capabilities"], "capability_scope.allowed_capabilities")))
        return ReasonerRequest(
            phase=phase, run_id=self.spec.run_id, goal_summary=str(self.spec.goal["statement"]),
            environment_summary="bounded local workspace with declared read/write roots",
            capability_catalog=capabilities, memory_summaries=tuple(self.state.get("memories", [])),
            previous_summaries=tuple(item["summary"] for item in self.state.get("trace", [])[-8:]),
        )

    def _install_plan(self, packets: Sequence[ExecutionPacket]) -> None:
        packets = tuple(packets)
        if not packets:
            raise RuntimeR1Error("plan must contain at least one action")
        if len(packets) > self.spec.workspace.max_actions:
            raise RuntimeR1Error("plan exceeds action budget")
        if len({packet.action_id for packet in packets}) != len(packets):
            raise RuntimeR1Error("plan action ids must be unique")
        digest = action_plan_hash(packets)
        allowed_capabilities = set(_tuple(self.spec.capability_scope["allowed_capabilities"], "capability_scope.allowed_capabilities"))
        for packet in packets:
            if packet.run_id != self.spec.run_id or packet.source_plan_hash != digest:
                raise RuntimeR1Error("packet lineage or source plan hash does not match the complete plan")
            missing_capabilities = sorted(set(packet.required_capabilities) - allowed_capabilities)
            if missing_capabilities:
                raise RuntimeR1Error(f"packet requests capability outside capability_scope: {missing_capabilities}")
            self.spec.workspace.validate_packet(packet, allow_declared_read_missing=True)
            if packet.kind in {item.value for item in (ActionKind.WRITE_FILE, ActionKind.CREATE_FILE, ActionKind.PATCH_TEXT_FILE)}:
                if packet.payload.get("path") not in packet.requested_writes:
                    raise RuntimeR1Error("write target must be included in requested_writes")
            if packet.kind in {ActionKind.READ_FILE.value, ActionKind.HASH_FILE.value} and packet.payload.get("path") not in packet.requested_reads:
                raise RuntimeR1Error("read target must be included in requested_reads")
        self.state["packets"] = [packet.to_dict() for packet in packets]
        self.state["plan_digest"] = digest
        self._set_phase(Phase.PLAN.value)
        self._event(Phase.PLAN.value, "plan", "reasoner", "installed a digest-bound execution plan", [digest])

    def _drive(self) -> dict[str, Any]:
        if self.executor is None:
            raise RuntimeR1Error("executor is not initialized")
        packets = tuple(ExecutionPacket.from_dict(item) for item in self.state["packets"])
        while self.state["next_action_index"] < len(packets):
            if self.state["action_count"] >= self.spec.workspace.max_actions:
                return self._stop(StopState.BUDGET_EXHAUSTED.value, "declared action budget is exhausted")
            packet = packets[self.state["next_action_index"]]
            try:
                result = self._drive_one(packet)
            except CrashInjected:
                self._event(Phase.STOP.value, "crash", self.executor.executor_id, "deterministic crash left durable journal state for restart", [packet.action_id])
                self._persist()
                raise
            if result == "WAITING":
                return dict(self.state)
            if result == "STOPPED":
                return dict(self.state)
            self._set_phase(Phase.CONTINUE.value)
            self._persist()
        return self._stop(StopState.COMPLETED_VALIDATED.value, "all declared local actions passed validation")

    def _drive_one(self, packet: ExecutionPacket) -> str:
        if self.state.get("pending_approval"):
            return "WAITING"
        try:
            self.spec.workspace.validate_packet(packet)
        except WorkspaceViolation as exc:
            self._stop(StopState.CAPABILITY_UNAVAILABLE.value, str(exc))
            return "STOPPED"
        if packet.approval_class != ApprovalClass.AUTO_ALLOWED_SAFE.value:
            request = self._ensure_approval(packet)
            if request.status == "PENDING":
                return "WAITING"
            if request.status != "ALLOWED":
                if not self.state.get("terminal"):
                    self._stop(StopState.BLOCKED_WITH_EVIDENCE.value, "the typed approval request is expired or denied")
                return "STOPPED"
        latest = self.journal.latest(packet.action_id)
        if latest is not None:
            if latest.get("status") in {"COMPLETED", "RECONCILED"}:
                return self._finish_journaled(packet, latest, reconcile=latest.get("status") != "RECONCILED")
            if latest.get("status") in {"EXECUTING", "AMBIGUOUS"}:
                recovery = self._recover_journaled(packet, latest)
                if recovery == "RECONCILED":
                    return "CONTINUE" if self._finish_journaled(packet, self.journal.latest(packet.action_id) or latest, reconcile=False) == "CONTINUE" else "STOPPED"
                if recovery == "STOPPED":
                    return "STOPPED"
            if latest.get("status") in {"FAILED", "ROLLBACK_SUCCEEDED", "ROLLBACK_FAILED"}:
                self._stop(StopState.FAILED_VALIDATION.value, "durable journal records a prior failed action")
                return "STOPPED"
        preimages = self.executor.prepare(packet)
        expected_postimages = self.executor.expected_postimages(packet, preimages)
        record = self.journal.append({
            "action_id": packet.action_id, "run_id": packet.run_id, "packet": packet.to_dict(),
            "packet_digest": packet.action_digest, "idempotency_key": packet.idempotency_key,
            "status": "PREPARED", "preimages": [item.to_dict() for item in preimages],
            "expected_postimages": [item.to_dict() for item in expected_postimages], "result": None,
            "crash_marker": None,
        })
        lease = self.leases.find(action_id=packet.action_id, idempotency_key=packet.idempotency_key)
        if lease is None:
            lease = self.leases.acquire(
                run_id=packet.run_id, action_id=packet.action_id, idempotency_key=packet.idempotency_key,
                packet_digest=packet.action_digest, executor_class_id=self.executor.executor_class_id,
                executor_instance_id=self.executor.executor_instance_id,
            )
        elif lease.status == "COMPLETED":
            self._stop(StopState.REQUIRES_RECONCILIATION.value, "lease is completed but the action journal is not complete")
            return "STOPPED"
        elif lease.status != "ACTIVE":
            lease = self.leases.reactivate(lease.lease_id)
        self.journal.update(packet.action_id, lease_id=lease.lease_id)
        self.journal.update(packet.action_id, status="EXECUTING")
        self._set_phase(Phase.ACT.value)
        self._event(Phase.ACT.value, "execute_prepare", self.executor.executor_id, "prepared a bounded action and acquired an execution lease", [packet.action_id, lease.lease_id])
        self._persist()
        fault = self._fault_for(packet.action_id)
        if fault == "pre_execute":
            self._consume_fault(packet.action_id, fault)
            raise CrashInjected("fault injection: pre_execute")
        if fault == "mid_write":
            self._consume_fault(packet.action_id, fault)
            self.executor.fault_injection = "mid_write"
        try:
            result = self.executor.execute(packet, preimages)
        finally:
            self.executor.fault_injection = None
        if fault == "post_execute_before_persist":
            self._consume_fault(packet.action_id, fault)
            raise CrashInjected("fault injection: post_execute_before_persist")
        declared_paths = set(packet.requested_writes)
        observed_paths = set(result.changed_paths) | {item.path for item in result.postimages}
        if not observed_paths.issubset(declared_paths):
            self.journal.update(packet.action_id, status="AMBIGUOUS", result=result.to_dict(), crash_marker="executor reported an undeclared side effect")
            self._stop(StopState.REQUIRES_RECONCILIATION.value, "executor reported a side effect outside the authorized packet")
            return "STOPPED"
        self.journal.update(packet.action_id, status="COMPLETED", result=result.to_dict(), postimages=[item.to_dict() for item in result.postimages])
        self.state["executions"].append(result.to_dict())
        self._persist()
        if fault == "post_persist":
            self._consume_fault(packet.action_id, fault)
            self._persist()
            raise CrashInjected("fault injection: post_persist")
        return self._validate_and_advance(packet, result.to_dict(), lease.lease_id)

    def _ensure_approval(self, packet: ExecutionPacket) -> ApprovalRequestR1:
        request_id = f"approval-{packet.action_id}"
        existing = self.approvals.get(request_id)
        if existing is not None:
            self.state["pending_approval"] = existing.to_dict() if existing.status == "PENDING" else None
            if existing.status == "PENDING":
                self._set_phase(Phase.AUTHORIZE.value)
                self._stop(StopState.WAITING_FOR_APPROVAL.value, "a typed external approval is required before this action")
            elif existing.status not in {"ALLOWED"}:
                self._stop(StopState.BLOCKED_WITH_EVIDENCE.value, "the typed approval request is expired or denied")
            return existing
        request = ApprovalRequestR1(
            request_id=request_id, run_id=packet.run_id, action_id=packet.action_id, action_digest=packet.action_digest,
            impact_summary=f"bounded action {packet.kind} may affect {', '.join(packet.requested_writes) or 'no declared files'}",
            risk_class=packet.approval_class, requested_capabilities=packet.required_capabilities,
            requested_reads=packet.requested_reads, requested_writes=packet.requested_writes,
            expires_at=time.time() + 300.0, created_at=utc_now(),
        )
        self.approvals.create(request)
        self.state["pending_approval"] = request.to_dict()
        self._set_phase(Phase.AUTHORIZE.value)
        self._stop(StopState.WAITING_FOR_APPROVAL.value, "a typed external approval is required before this action")
        return request

    def _recover_journaled(self, packet: ExecutionPacket, record: Mapping[str, Any]) -> str:
        result = record.get("result") or {}
        postimages = result.get("postimages") or record.get("postimages") or record.get("expected_postimages") or []
        if postimages and self.executor.postimages_match(postimages):
            if not result:
                result = {
                    "action_id": packet.action_id, "run_id": packet.run_id, "step_id": packet.step_id,
                    "kind": packet.kind, "packet_digest": packet.action_digest,
                    "idempotency_key": packet.idempotency_key, "status": "RECONCILED",
                    "changed_paths": list(packet.requested_writes), "stdout": "", "stderr": "",
                    "stdout_truncated": False, "stderr_truncated": False, "return_code": None,
                    "duration_ms": 0, "argv_digest": sha256_json(list(packet.argv)), "cwd": ".",
                    "preimages": list(record.get("preimages") or []), "postimages": list(postimages),
                    "error_code": None,
                }
            self.journal.update(packet.action_id, status="RECONCILED", result=result, postimages=list(postimages), crash_marker="postimage matched after restart")
            return "RECONCILED"
        preimages = record.get("preimages") or result.get("preimages") or []
        if packet.kind in {item.value for item in (ActionKind.WRITE_FILE, ActionKind.CREATE_FILE, ActionKind.PATCH_TEXT_FILE)} and preimages and self.executor.preimages_match(preimages):
            lease = self.leases.find(action_id=packet.action_id, idempotency_key=packet.idempotency_key)
            if lease is not None and lease.status != "ACTIVE":
                self.leases.reactivate(lease.lease_id)
            return "RETRY"
        if packet.side_effecting:
            self.journal.update(packet.action_id, status="AMBIGUOUS", crash_marker="postimage and preimage did not establish a safe outcome")
            self._stop(StopState.REQUIRES_RECONCILIATION.value, "a crashed side effect cannot be safely classified")
            return "STOPPED"
        return "RETRY"

    def _finish_journaled(self, packet: ExecutionPacket, record: Mapping[str, Any], *, reconcile: bool) -> str:
        result = record.get("result") or {}
        postimages = result.get("postimages") or record.get("postimages") or []
        if postimages and not self.executor.postimages_match(postimages):
            self._stop(StopState.REQUIRES_RECONCILIATION.value, "durable action postimage no longer matches the recorded outcome")
            return "STOPPED"
        if reconcile:
            self.journal.update(packet.action_id, status="RECONCILED", crash_marker="durable completion reused without re-execution")
        lease_id = record.get("lease_id")
        return self._validate_and_advance(packet, result, lease_id, reused=True)

    def _validate_and_advance(self, packet: ExecutionPacket, result: Mapping[str, Any], lease_id: str | None, *, reused: bool = False) -> str:
        self._set_phase(Phase.VALIDATE.value)
        passed, checks, summary = self._validate_result(packet, result)
        validation = {
            "validation_id": f"validation-{packet.action_id}", "run_id": packet.run_id, "action_id": packet.action_id,
            "passed": passed, "checks": checks, "summary": summary,
        }
        if not any(item.get("action_id") == packet.action_id for item in self.state["validations"]):
            self.state["validations"].append(validation)
        self._event(Phase.VALIDATE.value, "validate", "validator-r1", summary, [packet.action_id])
        if not passed:
            preimages = result.get("preimages") or []
            if packet.rollback_class == RollbackClass.ROLLBACKABLE_LOCAL_FILE.value and preimages:
                rollback = self.executor.rollback(tuple(FilePreimage.from_dict(item) for item in preimages))
                self.state["rollback_events"].append({"action_id": packet.action_id, **rollback})
                if rollback.get("status") == "RESTORED":
                    self.journal.update(packet.action_id, status="ROLLBACK_SUCCEEDED", rollback=rollback)
                    if lease_id:
                        self.leases.set_status(lease_id, "COMPLETED")
                    self._persist()
                    self._stop(StopState.FAILED_VALIDATION_ROLLED_BACK.value, "validation failed and bounded local preimages were restored")
                else:
                    self.journal.update(packet.action_id, status="ROLLBACK_FAILED", rollback=rollback)
                    if lease_id:
                        self.leases.set_status(lease_id, "COMPLETED")
                    self._persist()
                    self._stop(StopState.ROLLBACK_FAILED.value, "validation failed and bounded rollback did not verify")
                return "STOPPED"
            if lease_id:
                self.leases.set_status(lease_id, "COMPLETED")
            self.journal.update(packet.action_id, status="FAILED", validation=validation)
            self._persist()
            self._stop(StopState.FAILED_VALIDATION.value, summary)
            return "STOPPED"
        if lease_id:
            self.leases.set_status(lease_id, "COMPLETED")
        self.state["memories"].append(f"validated {packet.action_id}: {summary}")
        self.state["action_count"] += 1
        self.state["next_action_index"] += 1
        self._event(Phase.REMEMBER.value, "remember", "runtime-r1", "recorded the bounded action outcome", [packet.action_id])
        self._persist()
        return "CONTINUE"

    def _validate_result(self, packet: ExecutionPacket, result: Mapping[str, Any]) -> tuple[bool, list[str], str]:
        checks: list[str] = []
        passed = True
        status = result.get("status")
        if status not in {"EXECUTED", "IDEMPOTENT_REPLAY", "RECONCILED"}:
            passed = False
            checks.append("execution_status_failed")
        else:
            checks.append("execution_status_recorded")
        if packet.kind in {ActionKind.RUN_COMMAND.value, ActionKind.GIT_STATUS.value, ActionKind.GIT_DIFF.value}:
            if result.get("return_code") != 0:
                passed = False
                checks.append("command_exit_nonzero")
            else:
                checks.append("command_exit_zero")
        if packet.kind in {ActionKind.WRITE_FILE.value, ActionKind.CREATE_FILE.value, ActionKind.PATCH_TEXT_FILE.value}:
            if not result.get("postimages") or not self.executor.postimages_match(result["postimages"]):
                passed = False
                checks.append("postimage_mismatch")
            else:
                checks.append("postimage_matches")
        expected = packet.payload.get("expected_stdout_sha256")
        if expected is not None:
            actual = sha256_json(result.get("stdout", ""))
            if actual != expected:
                passed = False
                checks.append("stdout_digest_mismatch")
            else:
                checks.append("stdout_digest_matches")
        fail_actions = set(self.spec.validator.get("fail_action_ids", []))
        if packet.action_id in fail_actions:
            passed = False
            checks.append("declared_validator_failure")
        summary = "action passed bounded validator checks" if passed else "action failed one or more bounded validator checks"
        return passed, checks, summary

    def _fault_for(self, action_id: str) -> str | None:
        point = self.state.get("fault_injection", {}).get(action_id)
        if point and self.state.get("fault_injection_consumed", {}).get(action_id) == point:
            return None
        return point

    def _consume_fault(self, action_id: str, point: str) -> None:
        self.state["fault_injection_consumed"][action_id] = point
        self._persist()

    def _stop(self, state: str, summary: str) -> dict[str, Any]:
        _summary(summary)
        self._set_phase(Phase.STOP.value)
        actor = self.executor.executor_id if self.executor is not None else "runtime-r1"
        self._event(Phase.STOP.value, "stop", actor, summary, [])
        self.state["terminal"] = RunTerminalState(state=state, summary=summary, executor_id=actor, event_count=len(self.state["trace"])).to_dict()
        self._persist()
        return dict(self.state)

    def _set_phase(self, phase: str) -> None:
        if phase not in {item.value for item in Phase}:
            raise RuntimeR1Error(f"unknown phase: {phase}")
        self.state["phase"] = phase

    def _event(self, phase: str, event_type: str, actor_id: str, summary: str, refs: list[str]) -> None:
        _summary(summary)
        _id(actor_id, "actor_id")
        self.state["trace"].append({
            "event_id": f"trace-{len(self.state['trace']):04d}", "run_id": self.spec.run_id,
            "sequence": len(self.state["trace"]), "phase": phase, "event_type": event_type,
            "actor_id": actor_id, "summary": summary, "refs": list(refs),
        })

    def _persist(self) -> None:
        digest_payload = {key: value for key, value in self.state.items() if key != "state_sha256"}
        self.state["state_sha256"] = sha256_json(digest_payload)
        _atomic_json(self.state_path, self.state)
        self.trace_path.parent.mkdir(parents=True, exist_ok=True)
        self.trace_path.write_text("".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in self.state["trace"]), encoding="utf-8")

    def _load(self) -> None:
        if not self.state_path.is_file() or not self.spec_path.is_file():
            raise RuntimeR1Error("run state or run spec is missing")
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            spec_data = json.loads(self.spec_path.read_text(encoding="utf-8"))
            spec = R1RunSpec.from_dict(spec_data)
        except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
            raise RuntimeR1Error(f"persisted run is unreadable: {exc}") from exc
        if not isinstance(data, dict) or data.get("run_id") != spec.run_id or not data.get("state_sha256"):
            raise RuntimeR1Error("persisted run lineage is invalid")
        expected = sha256_json({key: value for key, value in data.items() if key != "state_sha256"})
        if data["state_sha256"] != expected:
            raise RuntimeR1Error("persisted run state digest does not verify")
        self._spec = spec
        self._state = data


__all__ = ["AgentRuntimeR1", "R1RunSpec", "RuntimeR1Error", "CrashInjected"]
