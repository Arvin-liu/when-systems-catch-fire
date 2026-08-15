"""Typed Agent Runtime R0 records.

These records describe a run without assuming a research, publication or
knowledge domain.  Domain-specific metadata can only travel through opaque
refs or a Domain Pack adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from agent_kernel.contracts import KernelValidationError, _id, _strict_keys, _string, _summary, _tuple_strings, normalize_relative_paths


@dataclass(frozen=True)
class RunIdentity:
    run_id: str
    profile_ref: str
    goal_version: str
    created_by: str
    runtime_version: str = "agent-runtime-r0"

    def __post_init__(self) -> None:
        _id(self.run_id, "run_id")
        _string(self.profile_ref, "profile_ref")
        _string(self.goal_version, "goal_version")
        _id(self.created_by, "created_by")
        _string(self.runtime_version, "runtime_version")

    def to_dict(self) -> dict[str, str]:
        return {
            "run_id": self.run_id,
            "profile_ref": self.profile_ref,
            "goal_version": self.goal_version,
            "created_by": self.created_by,
            "runtime_version": self.runtime_version,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RunIdentity":
        _strict_keys(data, {"run_id", "profile_ref", "goal_version", "created_by", "runtime_version"}, "RunIdentity")
        return cls(**data)


@dataclass(frozen=True)
class GoalContract:
    goal_id: str
    statement: str
    success_conditions: tuple[str, ...]
    prohibited_actions: tuple[str, ...]
    capability_scope_ref: str
    version: str = "r0"

    def __post_init__(self) -> None:
        _id(self.goal_id, "goal_id")
        _summary(self.statement, "statement")
        object.__setattr__(self, "success_conditions", _tuple_strings(self.success_conditions, "success_conditions"))
        if not self.success_conditions:
            raise KernelValidationError("success_conditions must not be empty")
        object.__setattr__(self, "prohibited_actions", _tuple_strings(self.prohibited_actions, "prohibited_actions"))
        _id(self.capability_scope_ref, "capability_scope_ref")
        _string(self.version, "version")

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "statement": self.statement,
            "success_conditions": list(self.success_conditions),
            "prohibited_actions": list(self.prohibited_actions),
            "capability_scope_ref": self.capability_scope_ref,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "GoalContract":
        _strict_keys(data, {"goal_id", "statement", "success_conditions", "prohibited_actions", "capability_scope_ref", "version"}, "GoalContract")
        return cls(**data)


@dataclass(frozen=True)
class EnvironmentObservation:
    observation_id: str
    run_id: str
    executor_id: str
    observed_paths: tuple[str, ...]
    summary: str
    provenance_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _id(self.observation_id, "observation_id")
        _id(self.run_id, "run_id")
        _id(self.executor_id, "executor_id")
        object.__setattr__(self, "observed_paths", normalize_relative_paths(self.observed_paths, "observed_paths"))
        _summary(self.summary)
        object.__setattr__(self, "provenance_refs", _tuple_strings(self.provenance_refs, "provenance_refs"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "run_id": self.run_id,
            "executor_id": self.executor_id,
            "observed_paths": list(self.observed_paths),
            "summary": self.summary,
            "provenance_refs": list(self.provenance_refs),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "EnvironmentObservation":
        _strict_keys(data, {"observation_id", "run_id", "executor_id", "observed_paths", "summary", "provenance_refs"}, "EnvironmentObservation")
        return cls(**data)


@dataclass(frozen=True)
class PlanStep:
    step_id: str
    operation: str
    required_capabilities: tuple[str, ...]
    requested_reads: tuple[str, ...]
    requested_writes: tuple[str, ...]
    requested_commands: tuple[str, ...]
    network_requested: bool
    approval_class: str | None
    expected_output: str
    reason_summary: str

    def __post_init__(self) -> None:
        _id(self.step_id, "step_id")
        _string(self.operation, "operation")
        object.__setattr__(self, "required_capabilities", _tuple_strings(self.required_capabilities, "required_capabilities"))
        if not self.required_capabilities:
            raise KernelValidationError("plan step must request at least one capability")
        object.__setattr__(self, "requested_reads", normalize_relative_paths(self.requested_reads, "requested_reads"))
        object.__setattr__(self, "requested_writes", normalize_relative_paths(self.requested_writes, "requested_writes"))
        object.__setattr__(self, "requested_commands", _tuple_strings(self.requested_commands, "requested_commands"))
        if not isinstance(self.network_requested, bool):
            raise KernelValidationError("network_requested must be boolean")
        if self.approval_class is not None:
            _string(self.approval_class, "approval_class")
        _string(self.expected_output, "expected_output")
        _summary(self.reason_summary, "reason_summary")

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "operation": self.operation,
            "required_capabilities": list(self.required_capabilities),
            "requested_reads": list(self.requested_reads),
            "requested_writes": list(self.requested_writes),
            "requested_commands": list(self.requested_commands),
            "network_requested": self.network_requested,
            "approval_class": self.approval_class,
            "expected_output": self.expected_output,
            "reason_summary": self.reason_summary,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PlanStep":
        _strict_keys(data, {"step_id", "operation", "required_capabilities", "requested_reads", "requested_writes", "requested_commands", "network_requested", "approval_class", "expected_output", "reason_summary"}, "PlanStep")
        return cls(**data)


@dataclass(frozen=True)
class Plan:
    plan_id: str
    run_id: str
    steps: tuple[PlanStep, ...]
    rationale_summary: str

    def __post_init__(self) -> None:
        _id(self.plan_id, "plan_id")
        _id(self.run_id, "run_id")
        if not self.steps:
            raise KernelValidationError("plan must contain at least one step")
        ids = [step.step_id for step in self.steps]
        if len(ids) != len(set(ids)):
            raise KernelValidationError("plan step ids must be unique")
        _summary(self.rationale_summary, "rationale_summary")

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "run_id": self.run_id,
            "steps": [step.to_dict() for step in self.steps],
            "rationale_summary": self.rationale_summary,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Plan":
        _strict_keys(data, {"plan_id", "run_id", "steps", "rationale_summary"}, "Plan")
        if not isinstance(data.get("steps"), list):
            raise KernelValidationError("Plan.steps must be an array")
        return cls(plan_id=data["plan_id"], run_id=data["run_id"], steps=tuple(PlanStep.from_dict(item) for item in data["steps"]), rationale_summary=data["rationale_summary"])


@dataclass(frozen=True)
class ActionRequest:
    action_id: str
    run_id: str
    step_id: str
    operation: str
    required_capabilities: tuple[str, ...]
    requested_reads: tuple[str, ...]
    requested_writes: tuple[str, ...]
    requested_commands: tuple[str, ...]
    network_requested: bool
    approval_class: str | None
    reason_summary: str

    @classmethod
    def from_step(cls, run_id: str, step: PlanStep) -> "ActionRequest":
        return cls(
            action_id=f"action-{step.step_id}",
            run_id=run_id,
            step_id=step.step_id,
            operation=step.operation,
            required_capabilities=step.required_capabilities,
            requested_reads=step.requested_reads,
            requested_writes=step.requested_writes,
            requested_commands=step.requested_commands,
            network_requested=step.network_requested,
            approval_class=step.approval_class,
            reason_summary=step.reason_summary,
        )

    def __post_init__(self) -> None:
        _id(self.action_id, "action_id")
        _id(self.run_id, "run_id")
        _id(self.step_id, "step_id")
        _string(self.operation, "operation")
        object.__setattr__(self, "required_capabilities", _tuple_strings(self.required_capabilities, "required_capabilities"))
        if not self.required_capabilities:
            raise KernelValidationError("action must request at least one capability")
        object.__setattr__(self, "requested_reads", normalize_relative_paths(self.requested_reads, "requested_reads"))
        object.__setattr__(self, "requested_writes", normalize_relative_paths(self.requested_writes, "requested_writes"))
        object.__setattr__(self, "requested_commands", _tuple_strings(self.requested_commands, "requested_commands"))
        if not isinstance(self.network_requested, bool):
            raise KernelValidationError("network_requested must be boolean")
        if self.approval_class is not None:
            _string(self.approval_class, "approval_class")
        _summary(self.reason_summary, "reason_summary")

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "run_id": self.run_id,
            "step_id": self.step_id,
            "operation": self.operation,
            "required_capabilities": list(self.required_capabilities),
            "requested_reads": list(self.requested_reads),
            "requested_writes": list(self.requested_writes),
            "requested_commands": list(self.requested_commands),
            "network_requested": self.network_requested,
            "approval_class": self.approval_class,
            "reason_summary": self.reason_summary,
        }


@dataclass(frozen=True)
class ActionObservation:
    action_id: str
    run_id: str
    executor_id: str
    changed_paths: tuple[str, ...]
    output_refs: tuple[str, ...]
    summary: str
    error_code: str | None = None

    def __post_init__(self) -> None:
        _id(self.action_id, "action_id")
        _id(self.run_id, "run_id")
        _id(self.executor_id, "executor_id")
        object.__setattr__(self, "changed_paths", normalize_relative_paths(self.changed_paths, "changed_paths"))
        object.__setattr__(self, "output_refs", _tuple_strings(self.output_refs, "output_refs"))
        _summary(self.summary)
        if self.error_code is not None:
            _string(self.error_code, "error_code")

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "run_id": self.run_id,
            "executor_id": self.executor_id,
            "changed_paths": list(self.changed_paths),
            "output_refs": list(self.output_refs),
            "summary": self.summary,
            "error_code": self.error_code,
        }


@dataclass(frozen=True)
class ValidationResult:
    validation_id: str
    run_id: str
    action_id: str
    passed: bool
    checks: tuple[str, ...]
    summary: str

    def __post_init__(self) -> None:
        _id(self.validation_id, "validation_id")
        _id(self.run_id, "run_id")
        _id(self.action_id, "action_id")
        if not isinstance(self.passed, bool):
            raise KernelValidationError("passed must be boolean")
        object.__setattr__(self, "checks", _tuple_strings(self.checks, "checks"))
        if not self.checks:
            raise KernelValidationError("validation must record at least one check")
        _summary(self.summary)

    def to_dict(self) -> dict[str, Any]:
        return {
            "validation_id": self.validation_id,
            "run_id": self.run_id,
            "action_id": self.action_id,
            "passed": self.passed,
            "checks": list(self.checks),
            "summary": self.summary,
        }


@dataclass(frozen=True)
class RunTerminalState:
    state: str
    summary: str
    executor_id: str
    event_count: int

    def __post_init__(self) -> None:
        from agent_kernel import ALLOWED_STOP_STATES

        if self.state not in ALLOWED_STOP_STATES:
            raise KernelValidationError(f"unknown terminal state: {self.state}")
        _summary(self.summary)
        _id(self.executor_id, "executor_id")
        if not isinstance(self.event_count, int) or self.event_count < 0:
            raise KernelValidationError("event_count must be a non-negative integer")

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "summary": self.summary,
            "executor_id": self.executor_id,
            "event_count": self.event_count,
        }
