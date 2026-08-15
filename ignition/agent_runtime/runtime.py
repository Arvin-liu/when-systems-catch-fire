"""Deterministic Agent Runtime R0 control loop.

The runtime owns sequencing, authorization-before-action, persistence,
validation, memory events and resumable handoff.  It delegates framing and
planning to a Reasoner, execution to an Executor, and outcome checks to a
Validator.  None of those interfaces require a model or provider name.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Callable

from agent_kernel import (
    AuthorizationRequest,
    AuthorizationStatus,
    CapabilityScope,
    Checkpoint,
    Handoff,
    MemoryEvent,
    Phase,
    ResumeCapsule,
    StopState,
    authorize_action,
    sha256_json,
    validate_resume_lineage,
)
from agent_kernel.contracts import KernelValidationError, _id, _summary

from .records import (
    ActionObservation,
    ActionRequest,
    EnvironmentObservation,
    GoalContract,
    Plan,
    PlanStep,
    RunIdentity,
    RunTerminalState,
    ValidationResult,
)


class RuntimeErrorState(ValueError):
    """Raised when a persisted run cannot be safely continued."""


Clock = Callable[[], str]


def _default_clock() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class AgentRuntime:
    """Run a bounded, auditable and resumable generic control loop."""

    def __init__(
        self,
        *,
        state_path: str | Path,
        trace_path: str | Path,
        memory_path: str | Path,
        capsule_path: str | Path,
        capability_scope: CapabilityScope,
        reasoner: Any,
        executor: Any,
        validator: Any,
        clock: Clock | None = None,
        state_ref: str = "run-state.json",
    ) -> None:
        self.state_path = Path(state_path)
        self.trace_path = Path(trace_path)
        self.memory_path = Path(memory_path)
        self.capsule_path = Path(capsule_path)
        self.capability_scope = capability_scope
        self.reasoner = reasoner
        self.executor = executor
        self.validator = validator
        self.clock = clock or _default_clock
        self.state_ref = state_ref
        self._state: dict[str, Any] | None = None

        executor_id = getattr(executor, "executor_id", None)
        if not isinstance(executor_id, str) or not executor_id.strip():
            raise RuntimeErrorState("executor must expose a stable executor_id")
        _id(executor_id, "executor_id")

    @property
    def state(self) -> dict[str, Any]:
        if self._state is None:
            raise RuntimeErrorState("runtime has not been started or resumed")
        return self._state

    @property
    def trace(self) -> list[dict[str, Any]]:
        return self.state["trace"]

    def start(
        self,
        run_identity: RunIdentity,
        goal: GoalContract,
        environment: EnvironmentObservation,
        *,
        checkpoint_after_actions: int = 0,
        handoff_to: str | None = None,
    ) -> dict[str, Any]:
        """Start a fresh run and drive it until a stop state or checkpoint."""

        if self.state_path.exists() or self.trace_path.exists() or self.memory_path.exists() or self.capsule_path.exists():
            raise RuntimeErrorState("run output paths already exist; refusing to overwrite a prior run")
        if run_identity.run_id != goal.goal_id and not run_identity.run_id.startswith(goal.goal_id + "/"):
            raise RuntimeErrorState("run identity and goal identity are not linked")
        if environment.run_id != run_identity.run_id:
            raise RuntimeErrorState("environment observation belongs to another run")
        if not isinstance(checkpoint_after_actions, int) or checkpoint_after_actions < 0:
            raise RuntimeErrorState("checkpoint_after_actions must be a non-negative integer")
        if checkpoint_after_actions and not handoff_to:
            raise RuntimeErrorState("a checkpoint requires an explicit different handoff executor")
        if handoff_to is not None and handoff_to == self.executor.executor_id:
            raise RuntimeErrorState("handoff executor must be different from the current executor")
        if handoff_to is not None:
            _id(handoff_to, "handoff_to")

        self._state = {
            "runtime_version": "agent-runtime-r0",
            "run_identity": run_identity.to_dict(),
            "goal": goal.to_dict(),
            "environment": environment.to_dict(),
            "frame_summary": None,
            "plan": None,
            "next_step_index": 0,
            "action_count": 0,
            "checkpoint_after_actions": checkpoint_after_actions,
            "handoff_to": handoff_to,
            "phase": Phase.OBSERVE.value,
            "trace": [],
            "memory_events": [],
            "checkpoints": [],
            "resume_capsule": None,
            "terminal": None,
            "executors": [self.executor.executor_id],
            "created_at": self.clock(),
        }
        self._event(Phase.OBSERVE.value, "observe", self.executor.executor_id, "captured the declared environment observation", [environment.observation_id])

        self._set_phase(Phase.FRAME.value)
        frame_summary = self.reasoner.frame(goal, environment)
        _summary(frame_summary, "frame_summary")
        self.state["frame_summary"] = frame_summary
        self._event(Phase.FRAME.value, "frame", self.executor.executor_id, "recorded a bounded goal frame", [goal.goal_id])

        self._set_phase(Phase.PLAN.value)
        plan = self.reasoner.plan(goal, environment, frame_summary)
        if not isinstance(plan, Plan) or plan.run_id != run_identity.run_id:
            raise RuntimeErrorState("reasoner returned an invalid plan or wrong run_id")
        self.state["plan"] = plan.to_dict()
        self._event(Phase.PLAN.value, "plan", self.executor.executor_id, "created a deterministic action plan", [plan.plan_id])
        self._persist()
        return self._drive()

    def resume(self, executor: Any | None = None) -> dict[str, Any]:
        """Resume from the persisted capsule using the capsule's executor."""

        self._load()
        if executor is not None:
            self.executor = executor
        executor_id = getattr(self.executor, "executor_id", None)
        if not isinstance(executor_id, str):
            raise RuntimeErrorState("resume executor must expose executor_id")
        _id(executor_id, "executor_id")
        terminal = self.state.get("terminal") or {}
        if terminal.get("state") != StopState.CHECKPOINTED_RESUMABLE.value:
            raise RuntimeErrorState("run is not waiting at a resumable checkpoint")
        checkpoint_data = self.state.get("checkpoints", [])[-1] if self.state.get("checkpoints") else None
        capsule_data = self.state.get("resume_capsule")
        if not checkpoint_data or not capsule_data:
            raise RuntimeErrorState("resumable run lacks checkpoint or capsule")
        checkpoint = Checkpoint(**checkpoint_data)
        handoff_data = capsule_data.get("handoff") or {}
        handoff = Handoff(**handoff_data)
        capsule = ResumeCapsule(
            capsule_id=capsule_data["capsule_id"],
            run_id=capsule_data["run_id"],
            checkpoint_id=capsule_data["checkpoint_id"],
            state_ref=capsule_data["state_ref"],
            state_sha256=capsule_data["state_sha256"],
            pending_action_ids=tuple(capsule_data["pending_action_ids"]),
            required_capabilities=tuple(capsule_data["required_capabilities"]),
            created_by=capsule_data["created_by"],
            handoff=handoff,
        )
        validate_resume_lineage(checkpoint, capsule, self.state["state_sha256"], executor_id=executor_id)
        if executor_id in self.state.get("executors", []):
            raise RuntimeErrorState("resume executor must be different from every prior executor")
        self.state["executors"].append(executor_id)
        self.state["checkpoint_after_actions"] = 0
        self.state["terminal"] = None
        self._set_phase(Phase.CONTINUE.value)
        self._event(Phase.CONTINUE.value, "resume", executor_id, "resumed from a verified capsule with a different executor", [capsule.capsule_id, checkpoint.checkpoint_id])
        self._persist()
        return self._drive()

    def load_state(self) -> dict[str, Any]:
        self._load()
        return deepcopy(self.state)

    def _drive(self) -> dict[str, Any]:
        plan = Plan.from_dict(self.state["plan"])
        while self.state["next_step_index"] < len(plan.steps):
            if self.capability_scope.max_actions and self.state["action_count"] >= self.capability_scope.max_actions:
                return self._stop(StopState.BUDGET_EXHAUSTED.value, "declared action budget is exhausted")

            step = plan.steps[self.state["next_step_index"]]
            action = ActionRequest.from_step(plan.run_id, step)
            self._set_phase(Phase.AUTHORIZE.value)
            auth_request = AuthorizationRequest(
                action_id=action.action_id,
                run_id=action.run_id,
                required_capabilities=action.required_capabilities,
                requested_reads=action.requested_reads,
                requested_writes=action.requested_writes,
                requested_commands=action.requested_commands,
                network_requested=action.network_requested,
                approval_class=action.approval_class,
                reason_summary=action.reason_summary,
            )
            decision = authorize_action(self.capability_scope, auth_request)
            self.state.setdefault("authorization_decisions", []).append(decision.to_dict())
            self._event(Phase.AUTHORIZE.value, "authorize", "kernel", f"authorization decision: {decision.status}", [action.action_id, decision.decision_id])
            if decision.status != AuthorizationStatus.ALLOW.value:
                stop_state = StopState.WAITING_FOR_APPROVAL.value if decision.status == AuthorizationStatus.REQUIRE_HUMAN_APPROVAL.value else StopState.CAPABILITY_UNAVAILABLE.value
                return self._stop(stop_state, decision.reason_summary)

            self._set_phase(Phase.ACT.value)
            observation = self.executor.execute(action, EnvironmentObservation.from_dict(self.state["environment"]))
            if not isinstance(observation, ActionObservation):
                return self._stop(StopState.FAILED_VALIDATION.value, "executor returned a non-typed action observation")
            if observation.action_id != action.action_id or observation.run_id != action.run_id or observation.executor_id != self.executor.executor_id:
                return self._stop(StopState.FAILED_VALIDATION.value, "executor observation lineage does not match the action")
            self.state.setdefault("action_observations", []).append(observation.to_dict())
            self._event(Phase.ACT.value, "act", observation.executor_id, "executor returned a typed action observation", [action.action_id])

            self._set_phase(Phase.VALIDATE.value)
            result = self.validator.validate(action, observation)
            if not isinstance(result, ValidationResult):
                return self._stop(StopState.FAILED_VALIDATION.value, "validator returned a non-typed validation result")
            if result.action_id != action.action_id or result.run_id != action.run_id:
                return self._stop(StopState.FAILED_VALIDATION.value, "validation result lineage does not match the action")
            self.state.setdefault("validation_results", []).append(result.to_dict())
            self._event(Phase.VALIDATE.value, "validate", "validator", "recorded the action validation result", [result.validation_id])

            self._set_phase(Phase.REMEMBER.value)
            memory = MemoryEvent(
                event_id=f"memory-{self.state['action_count']:04d}",
                run_id=action.run_id,
                event_type="action_validation",
                source_refs=(action.action_id, result.validation_id),
                public_summary="recorded a structured action outcome for this run",
                created_by=self.executor.executor_id,
                retention="run_and_resume",
            )
            self.state["memory_events"].append(memory.to_dict())
            self._event(Phase.REMEMBER.value, "remember", self.executor.executor_id, "persisted a structured durable memory event", [memory.event_id])

            self.state["action_count"] += 1
            self.state["next_step_index"] += 1
            if not result.passed:
                return self._stop(StopState.FAILED_VALIDATION.value, result.summary)
            if self.state["checkpoint_after_actions"] and self.state["action_count"] >= self.state["checkpoint_after_actions"] and self.state["next_step_index"] < len(plan.steps):
                return self._checkpoint(plan)
            self._set_phase(Phase.CONTINUE.value)
            self._event(Phase.CONTINUE.value, "continue", self.executor.executor_id, "validation passed; continuing with the next bounded step", [action.action_id])
            self._persist()

        return self._stop(StopState.COMPLETED_VALIDATED.value, "all planned actions passed their declared validators")

    def _checkpoint(self, plan: Plan) -> dict[str, Any]:
        handoff_to = self.state.get("handoff_to")
        if not handoff_to or handoff_to == self.executor.executor_id:
            return self._stop(StopState.CAPABILITY_UNAVAILABLE.value, "checkpoint handoff is missing or not independent")
        self._set_phase(Phase.CONTINUE.value)
        self._event(Phase.CONTINUE.value, "checkpoint_prepare", self.executor.executor_id, "prepared a resumable handoff after a validated step", [plan.plan_id])
        self._set_phase(Phase.STOP.value)
        self._event(Phase.STOP.value, "checkpoint_stop", self.executor.executor_id, "stopped at an explicit resumable checkpoint", [])
        self.state["terminal"] = RunTerminalState(
            state=StopState.CHECKPOINTED_RESUMABLE.value,
            summary="run is paused with a verified checkpoint and resume capsule",
            executor_id=self.executor.executor_id,
            event_count=len(self.trace),
        ).to_dict()
        self._persist()
        digest = self.state["state_sha256"]
        checkpoint = Checkpoint(
            checkpoint_id=f"checkpoint-{self.state['action_count']:04d}",
            run_id=self.state["run_identity"]["run_id"],
            phase=Phase.STOP.value,
            state_ref=self.state_ref,
            state_sha256=digest,
            event_count=len(self.trace),
            created_by=self.executor.executor_id,
            reason_summary="validated step complete; next step is handed off",
        )
        pending = tuple(f"action-{step.step_id}" for step in plan.steps[self.state["next_step_index"] :])
        required = tuple(sorted({capability for step in plan.steps[self.state["next_step_index"] :] for capability in step.required_capabilities}))
        capsule = ResumeCapsule(
            capsule_id=f"capsule-{self.state['action_count']:04d}",
            run_id=self.state["run_identity"]["run_id"],
            checkpoint_id=checkpoint.checkpoint_id,
            state_ref=self.state_ref,
            state_sha256=digest,
            pending_action_ids=pending,
            required_capabilities=required,
            created_by=self.executor.executor_id,
            handoff=Handoff(
                from_executor_id=self.executor.executor_id,
                to_executor_id=handoff_to,
                reason_summary="continue the bounded plan after verifying the persisted state digest",
                resume_ref=self.state_ref,
            ),
        )
        self.state["checkpoints"].append(checkpoint.to_dict())
        self.state["resume_capsule"] = capsule.to_dict()
        self._persist()
        return deepcopy(self.state)

    def _stop(self, state: str, summary: str) -> dict[str, Any]:
        _summary(summary)
        self._set_phase(Phase.STOP.value)
        self._event(Phase.STOP.value, "stop", self.executor.executor_id, summary, [])
        self.state["terminal"] = RunTerminalState(state=state, summary=summary, executor_id=self.executor.executor_id, event_count=len(self.trace)).to_dict()
        self._persist()
        return deepcopy(self.state)

    def _set_phase(self, phase: str) -> None:
        if phase not in {item.value for item in Phase}:
            raise RuntimeErrorState(f"unknown runtime phase: {phase}")
        self.state["phase"] = phase

    def _event(self, phase: str, event_type: str, actor_id: str, summary: str, refs: list[str]) -> None:
        _summary(summary)
        _id(actor_id, "actor_id")
        sequence = len(self.state["trace"])
        event = {
            "event_id": f"trace-{sequence:04d}",
            "run_id": self.state["run_identity"]["run_id"],
            "sequence": sequence,
            "phase": phase,
            "event_type": event_type,
            "actor_id": actor_id,
            "summary": summary,
            "refs": list(refs),
        }
        self.state["trace"].append(event)

    def _digest_payload(self) -> dict[str, Any]:
        return {key: value for key, value in self.state.items() if key not in {"state_sha256", "checkpoints", "resume_capsule", "terminal"}}

    def _persist(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.trace_path.parent.mkdir(parents=True, exist_ok=True)
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        self.capsule_path.parent.mkdir(parents=True, exist_ok=True)
        self.state["state_sha256"] = sha256_json(self._digest_payload())
        self.state_path.write_text(json.dumps(self.state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.trace_path.write_text(json.dumps(self.state["trace"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        memory_lines = "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in self.state["memory_events"])
        self.memory_path.write_text(memory_lines, encoding="utf-8")
        if self.state.get("resume_capsule") is not None:
            self.capsule_path.write_text(json.dumps(self.state["resume_capsule"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _load(self) -> None:
        if not self.state_path.is_file():
            raise RuntimeErrorState("persisted run state is missing")
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeErrorState(f"persisted run state is unreadable: {exc}") from exc
        if not isinstance(data, dict) or not data.get("state_sha256"):
            raise RuntimeErrorState("persisted run state lacks a state_sha256")
        expected = sha256_json({key: value for key, value in data.items() if key not in {"state_sha256", "checkpoints", "resume_capsule", "terminal"}})
        if data["state_sha256"] != expected:
            raise RuntimeErrorState("persisted run state digest does not verify")
        if not isinstance(data.get("trace"), list) or not isinstance(data.get("memory_events"), list):
            raise RuntimeErrorState("persisted run state has malformed trace or memory")
        self._state = data
