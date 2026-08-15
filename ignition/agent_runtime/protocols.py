"""Minimal executor/reasoner/validator interfaces for the runtime."""

from __future__ import annotations

from typing import Protocol

from .records import ActionObservation, ActionRequest, EnvironmentObservation, GoalContract, Plan, ValidationResult


class Reasoner(Protocol):
    """A provider-neutral planner; implementations may be deterministic or model-backed."""

    def frame(self, goal: GoalContract, environment: EnvironmentObservation) -> str: ...

    def plan(self, goal: GoalContract, environment: EnvironmentObservation, frame_summary: str) -> Plan: ...


class Executor(Protocol):
    executor_id: str

    def execute(self, action: ActionRequest, environment: EnvironmentObservation) -> ActionObservation: ...


class Validator(Protocol):
    def validate(self, action: ActionRequest, observation: ActionObservation) -> ValidationResult: ...
