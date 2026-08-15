"""Durable sequential Supervisor R0 for bounded multi-run episodes.

The Supervisor owns episode coordination only.  It does not replace the
Kernel, widen a child capability scope, or decide domain truth.  Each child
continues to execute through :class:`AgentRuntimeR1` in its own durable run
directory; the episode state records dependency, budget, approval, retry and
handoff facts around those runs.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import time
from typing import Any, Mapping, Sequence

from agent_kernel import StopState, sha256_json
from agent_kernel.contracts import KernelValidationError, _id, _summary, _tuple_strings

from .actions import CrashInjected
from .control import _atomic_json, utc_now
from .r1_runtime import AgentRuntimeR1, R1RunSpec, RuntimeR1Error


SUPERVISOR_SCHEMA = "supervisor-r0"
EPISODE_POLICIES = frozenset({"FAIL_FAST", "CONTINUE_INDEPENDENT"})
CHILD_TERMINAL_STATES = frozenset({
    "COMPLETED_VALIDATED",
    "FAILED",
    "BLOCKED_DEPENDENCY",
})
EPISODE_TERMINAL_STATES = frozenset({
    "EPISODE_COMPLETED_VALIDATED",
    "EPISODE_COMPLETED_WITH_INDEPENDENT_FAILURES",
    "EPISODE_COMPLETED_WITH_DEPENDENCY_BLOCKS",
    "EPISODE_FAILED_FAST",
    "EPISODE_WAITING_FOR_APPROVAL",
    "EPISODE_CHECKPOINTED_RESUMABLE",
    "EPISODE_BUDGET_EXHAUSTED",
    "EPISODE_BLOCKED_DEPENDENCY",
})
_SAFE_DIR = re.compile(r"[^A-Za-z0-9_.-]+")


class SupervisorError(RuntimeError):
    """Raised when an episode cannot continue without guessing."""


def _positive_int(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise KernelValidationError(f"{field} must be a positive integer")
    return value


def _relative_child_name(run_id: str) -> str:
    readable = _SAFE_DIR.sub("-", run_id).strip("-") or "child"
    return f"{readable}-{sha256_json(run_id)[:12]}"


@dataclass(frozen=True)
class EpisodeBudget:
    """Global episode budgets, enforced before the next child is driven."""

    max_actions: int
    max_seconds: float
    max_output_bytes: int

    def __post_init__(self) -> None:
        _positive_int(self.max_actions, "budget.max_actions")
        if not isinstance(self.max_seconds, (int, float)) or isinstance(self.max_seconds, bool) or self.max_seconds <= 0:
            raise KernelValidationError("budget.max_seconds must be positive")
        _positive_int(self.max_output_bytes, "budget.max_output_bytes")

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_actions": self.max_actions,
            "max_seconds": self.max_seconds,
            "max_output_bytes": self.max_output_bytes,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "EpisodeBudget":
        required = {"max_actions", "max_seconds", "max_output_bytes"}
        if set(data) != required:
            raise SupervisorError("episode budget keys must be max_actions, max_seconds and max_output_bytes")
        return cls(
            max_actions=data["max_actions"],
            max_seconds=data["max_seconds"],
            max_output_bytes=data["max_output_bytes"],
        )


@dataclass(frozen=True)
class ChildRunSpec:
    """One R1 child and its bounded scheduling policy."""

    run_id: str
    run_spec: R1RunSpec
    depends_on: tuple[str, ...] = ()
    retry_limit: int = 0
    executor_instance_id: str = "instance-1"
    executor_class_id: str = "local-workspace-executor"

    def __post_init__(self) -> None:
        _id(self.run_id, "child.run_id")
        if self.run_spec.run_id != self.run_id:
            raise SupervisorError("child run_id must match the nested R1 run spec")
        object.__setattr__(self, "depends_on", _tuple_strings(self.depends_on, "child.depends_on"))
        if self.run_id in self.depends_on:
            raise SupervisorError("a child cannot depend on itself")
        if not isinstance(self.retry_limit, int) or isinstance(self.retry_limit, bool) or not 0 <= self.retry_limit <= 3:
            raise SupervisorError("child.retry_limit must be an integer between 0 and 3")
        _id(self.executor_instance_id, "child.executor_instance_id")
        _id(self.executor_class_id, "child.executor_class_id")
        declared_class = self.run_spec.executor.get("class_id")
        if declared_class != self.executor_class_id:
            raise SupervisorError("child executor class cannot differ from its declared R1 adapter")

    @property
    def allowed_capabilities(self) -> tuple[str, ...]:
        return tuple(str(item) for item in self.run_spec.capability_scope["allowed_capabilities"])

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "depends_on": list(self.depends_on),
            "retry_limit": self.retry_limit,
            "executor_instance_id": self.executor_instance_id,
            "executor_class_id": self.executor_class_id,
            "spec": self.run_spec.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ChildRunSpec":
        if not isinstance(data, Mapping) or "spec" not in data:
            raise SupervisorError("child must contain a nested R1 spec")
        spec_data = data["spec"]
        if not isinstance(spec_data, Mapping):
            raise SupervisorError("child.spec must be an object")
        run_id = data.get("run_id", spec_data.get("run_id"))
        executor_class_id = data.get("executor_class_id", spec_data.get("executor", {}).get("class_id"))
        return cls(
            run_id=run_id,
            run_spec=R1RunSpec.from_dict(spec_data),
            depends_on=tuple(data.get("depends_on", ())),
            retry_limit=data.get("retry_limit", 0),
            executor_instance_id=data.get("executor_instance_id", "instance-1"),
            executor_class_id=executor_class_id,
        )


@dataclass(frozen=True)
class EpisodeSpec:
    """Durable DAG and global scope contract for one episode."""

    episode_id: str
    job_id: str
    created_by: str
    capability_scope_id: str
    allowed_capabilities: tuple[str, ...]
    budget: EpisodeBudget
    children: tuple[ChildRunSpec, ...]
    policy: str = "FAIL_FAST"
    network_allowed: bool = False

    def __post_init__(self) -> None:
        _id(self.episode_id, "episode_id")
        _id(self.job_id, "job_id")
        _id(self.created_by, "created_by")
        _id(self.capability_scope_id, "capability_scope_id")
        object.__setattr__(self, "allowed_capabilities", _tuple_strings(self.allowed_capabilities, "capability_scope.allowed_capabilities"))
        if not self.allowed_capabilities:
            raise SupervisorError("episode capability scope must not be empty")
        if self.network_allowed is not False:
            raise SupervisorError("Supervisor R0 is offline and cannot enable network")
        if self.policy not in EPISODE_POLICIES:
            raise SupervisorError(f"unknown episode policy: {self.policy}")
        if not self.children:
            raise SupervisorError("episode must contain at least one child")
        ids = [child.run_id for child in self.children]
        if len(ids) != len(set(ids)):
            raise SupervisorError("child run ids must be unique")
        known = set(ids)
        for child in self.children:
            unknown = sorted(set(child.depends_on) - known)
            if unknown:
                raise SupervisorError(f"child {child.run_id} depends on unknown runs: {unknown}")
            outside = sorted(set(child.allowed_capabilities) - set(self.allowed_capabilities))
            if outside:
                raise SupervisorError(f"child {child.run_id} expands episode capability scope: {outside}")
            if child.run_spec.capability_scope.get("network_allowed") is not False:
                raise SupervisorError("child network scope must remain false")
        self._topological_order()

    def _topological_order(self) -> tuple[str, ...]:
        children = {child.run_id: child for child in self.children}
        visiting: set[str] = set()
        visited: set[str] = set()
        order: list[str] = []

        def visit(run_id: str) -> None:
            if run_id in visiting:
                raise SupervisorError("episode child dependency graph contains a cycle")
            if run_id in visited:
                return
            visiting.add(run_id)
            for dependency in children[run_id].depends_on:
                visit(dependency)
            visiting.remove(run_id)
            visited.add(run_id)
            order.append(run_id)

        for child in self.children:
            visit(child.run_id)
        return tuple(order)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SUPERVISOR_SCHEMA,
            "episode_id": self.episode_id,
            "job_id": self.job_id,
            "created_by": self.created_by,
            "policy": self.policy,
            "capability_scope": {
                "scope_id": self.capability_scope_id,
                "allowed_capabilities": list(self.allowed_capabilities),
                "network_allowed": self.network_allowed,
            },
            "budget": self.budget.to_dict(),
            "children": [child.to_dict() for child in self.children],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "EpisodeSpec":
        if not isinstance(data, Mapping):
            raise SupervisorError("episode spec must be an object")
        if data.get("schema", SUPERVISOR_SCHEMA) != SUPERVISOR_SCHEMA:
            raise SupervisorError("episode spec schema is not supervisor-r0")
        scope = data.get("capability_scope")
        if not isinstance(scope, Mapping) or set(scope) != {"scope_id", "allowed_capabilities", "network_allowed"}:
            raise SupervisorError("episode capability_scope has an invalid shape")
        children = data.get("children")
        if not isinstance(children, list):
            raise SupervisorError("episode children must be an array")
        return cls(
            episode_id=data["episode_id"],
            job_id=data["job_id"],
            created_by=data.get("created_by", "supervisor-cli"),
            capability_scope_id=scope["scope_id"],
            allowed_capabilities=tuple(scope["allowed_capabilities"]),
            network_allowed=scope["network_allowed"],
            budget=EpisodeBudget.from_dict(data["budget"]),
            children=tuple(ChildRunSpec.from_dict(item) for item in children),
            policy=data.get("policy", "FAIL_FAST"),
        )


class Supervisor:
    """A persisted, sequential DAG supervisor for R1 child runs."""

    def __init__(self, episode_dir: str | Path) -> None:
        self.episode_dir = Path(episode_dir)
        self.spec_path = self.episode_dir / "episode-spec.json"
        self.state_path = self.episode_dir / "episode-state.json"
        self.trace_path = self.episode_dir / "episode-trace.jsonl"
        self.lock_path = self.episode_dir / ".supervisor.lock"
        self._spec: EpisodeSpec | None = None
        self._state: dict[str, Any] | None = None

    @property
    def spec(self) -> EpisodeSpec:
        if self._spec is None:
            raise SupervisorError("episode is not loaded")
        return self._spec

    @property
    def state(self) -> dict[str, Any]:
        if self._state is None:
            raise SupervisorError("episode is not loaded")
        return self._state

    def start(self, spec: EpisodeSpec) -> dict[str, Any]:
        if self.spec_path.exists() or self.state_path.exists():
            raise SupervisorError("episode directory already contains a spec or state")
        self.episode_dir.mkdir(parents=True, exist_ok=True)
        self._spec = spec
        _atomic_json(self.spec_path, spec.to_dict())
        self._state = {
            "schema": SUPERVISOR_SCHEMA,
            "episode_id": spec.episode_id,
            "job_id": spec.job_id,
            "policy": spec.policy,
            "phase": "SUPERVISE",
            "terminal": None,
            "started_at": utc_now(),
            "started_at_epoch": time.time(),
            "checkpoint_count": 0,
            "budget_usage": {"actions": 0, "elapsed_seconds": 0.0, "output_bytes": 0},
            "approval_events": [],
            "handoffs": [],
            "trace": [],
            "children": [self._new_child_state(child) for child in spec.children],
        }
        self._event("episode_start", "created the bounded episode DAG and global capability scope", [spec.episode_id, spec.job_id])
        self._persist()
        return self._drive()

    def resume(self) -> dict[str, Any]:
        self._load()
        terminal = self.state.get("terminal")
        if terminal and terminal.get("state") not in {"EPISODE_WAITING_FOR_APPROVAL", "EPISODE_CHECKPOINTED_RESUMABLE"}:
            return dict(self.state)
        if terminal:
            self.state["terminal"] = None
            self._event("episode_resume", "resumed persisted child checkpoints and approval state", [self.spec.episode_id])
            self._persist()
        return self._drive()

    def status(self) -> dict[str, Any]:
        self._load()
        return dict(self.state)

    def trace(self) -> list[dict[str, Any]]:
        self._load()
        return list(self.state["trace"])

    def pending_approvals(self) -> list[dict[str, Any]]:
        self._load()
        approvals: list[dict[str, Any]] = []
        for child in self.state["children"]:
            if child["status"] != "WAITING_FOR_APPROVAL":
                continue
            runtime = self._runtime(child)
            try:
                for request in runtime.pending_approval():
                    approvals.append({"run_id": child["run_id"], **request})
            except RuntimeError:
                continue
        return approvals

    def approve(
        self,
        run_id: str,
        request_id: str,
        decision: str,
        *,
        authority_id: str,
        authority_type: str = "human",
        reason_summary: str = "explicit typed episode approval decision",
    ) -> dict[str, Any]:
        self._load()
        child = self._child_state(run_id)
        if child["status"] != "WAITING_FOR_APPROVAL":
            raise SupervisorError("child run is not waiting for approval")
        runtime = self._runtime(child)
        result = runtime.approve(
            request_id,
            decision,
            authority_id=authority_id,
            authority_type=authority_type,
            reason_summary=reason_summary,
        )
        self._sync_child(child, result)
        self.state["approval_events"].append({
            "run_id": run_id,
            "request_id": request_id,
            "decision": decision.upper(),
            "authority_type": authority_type,
            "recorded_at": utc_now(),
        })
        self._event("approval_aggregated", "recorded a typed child approval without widening episode scope", [run_id, request_id])
        self.state["terminal"] = None
        self._persist()
        return self._drive()

    def handoff(
        self,
        run_id: str,
        executor_instance_id: str,
        *,
        executor_class_id: str | None = None,
    ) -> dict[str, Any]:
        self._load()
        child = self._child_state(run_id)
        _id(executor_instance_id, "executor_instance_id")
        requested_class = executor_class_id or child["executor_class_id"]
        _id(requested_class, "executor_class_id")
        declared_class = self._child_spec(run_id).run_spec.executor["class_id"]
        if requested_class != declared_class:
            raise SupervisorError("handoff cannot replace the declared executor adapter")
        if child["status"] in CHILD_TERMINAL_STATES:
            raise SupervisorError("a terminal child cannot be handed off")
        previous = child["executor_instance_id"]
        child["executor_instance_id"] = executor_instance_id
        child["executor_class_id"] = requested_class
        handoff = {
            "run_id": run_id,
            "from_executor_instance_id": previous,
            "to_executor_instance_id": executor_instance_id,
            "executor_class_id": requested_class,
            "recorded_at": utc_now(),
        }
        self.state["handoffs"].append(handoff)
        self._event("handoff", "recorded a bounded executor-instance handoff without changing child permissions", [run_id, executor_instance_id])
        self._persist()
        return dict(self.state)

    def _new_child_state(self, child: ChildRunSpec) -> dict[str, Any]:
        relative = self._relative_run_dir(child.run_id, 0)
        return {
            "run_id": child.run_id,
            "depends_on": list(child.depends_on),
            "status": "PENDING",
            "terminal_state": None,
            "terminal_summary": None,
            "attempt": 0,
            "retry_count": 0,
            "retry_limit": child.retry_limit,
            "run_dir": relative,
            "attempt_dirs": [relative],
            "executor_instance_id": child.executor_instance_id,
            "executor_class_id": child.executor_class_id,
            "approval_request_ids": [],
            "history": [],
            "last_state_sha256": None,
        }

    def _relative_run_dir(self, run_id: str, attempt: int) -> str:
        return f"children/{_relative_child_name(run_id)}/attempt-{attempt}"

    def _child_spec(self, run_id: str) -> ChildRunSpec:
        for child in self.spec.children:
            if child.run_id == run_id:
                return child
        raise SupervisorError(f"unknown child run: {run_id}")

    def _child_state(self, run_id: str) -> dict[str, Any]:
        _id(run_id, "run_id")
        for child in self.state["children"]:
            if child["run_id"] == run_id:
                return child
        raise SupervisorError(f"unknown child run: {run_id}")

    def _runtime(self, child: Mapping[str, Any]) -> AgentRuntimeR1:
        run_dir = self.episode_dir / child["run_dir"]
        try:
            run_dir.resolve().relative_to(self.episode_dir.resolve())
        except ValueError as exc:
            raise SupervisorError("child run directory escaped episode directory") from exc
        return AgentRuntimeR1(
            run_dir,
            executor_instance_id=child["executor_instance_id"],
            executor_class_id=child["executor_class_id"],
        )

    def _drive(self) -> dict[str, Any]:
        while True:
            terminal = self.state.get("terminal")
            if terminal:
                return dict(self.state)
            self._update_usage()
            if self._all_children_terminal():
                return self._roll_up()
            if self._budget_exceeded():
                return self._stop_episode(
                    "EPISODE_BUDGET_EXHAUSTED",
                    "global episode budget prevents another child run",
                )
            self._mark_dependency_blocks()
            if self.state.get("terminal"):
                return dict(self.state)
            ready = [
                child for child in self.state["children"]
                if child["status"] in {"PENDING", "CHECKPOINTED_RESUMABLE"} and self._dependencies_completed(child)
            ]
            if not ready:
                return self._roll_up()
            child = ready[0]
            if not self._child_fits_action_budget(child):
                return self._stop_episode(
                    "EPISODE_BUDGET_EXHAUSTED",
                    f"child {child['run_id']} cannot fit its remaining declared actions in the global budget",
                )
            self._run_child(child)
            self._persist()

    def _run_child(self, child: dict[str, Any]) -> None:
        run_id = child["run_id"]
        child["status"] = "RUNNING"
        self._event("child_start", "started one dependency-ready child through AgentRuntimeR1", [run_id, child["run_dir"]])
        self._persist()
        runtime = self._runtime(child)
        run_dir = self.episode_dir / child["run_dir"]
        try:
            if (run_dir / "run-state.json").exists():
                result = runtime.resume()
            else:
                result = runtime.start(self._child_spec(run_id).run_spec)
        except CrashInjected:
            child["status"] = "CHECKPOINTED_RESUMABLE"
            child["terminal_state"] = "CHECKPOINTED_RESUMABLE"
            child["terminal_summary"] = "child runtime crash left a durable checkpoint for Supervisor resume"
            self.state["checkpoint_count"] += 1
            self._record_child_history(child)
            self._event("child_checkpoint", "captured a restartable child crash without promoting it to completion", [run_id])
            self._stop_episode("EPISODE_CHECKPOINTED_RESUMABLE", "one or more child runs have restartable durable checkpoints")
            return
        except (RuntimeR1Error, ValueError, OSError) as exc:
            child["status"] = "FAILED"
            child["terminal_state"] = "CHILD_RUNTIME_ERROR"
            child["terminal_summary"] = f"child runtime failed closed: {type(exc).__name__}: {exc}"
            self._record_child_history(child)
            self._event("child_failure", "recorded a typed child runtime failure", [run_id])
            self._maybe_retry(child)
            return
        self._sync_child(child, result)
        self._record_child_history(child)
        if child["status"] == "CHECKPOINTED_RESUMABLE":
            self.state["checkpoint_count"] += 1
            self._event("child_checkpoint", "captured a restartable child checkpoint without promoting it to completion", [run_id])
            self._stop_episode("EPISODE_CHECKPOINTED_RESUMABLE", "one or more child runs have restartable durable checkpoints")
            return
        if child["status"] == "FAILED":
            self._maybe_retry(child)
            if child["status"] == "FAILED" and self.spec.policy == "FAIL_FAST":
                self._stop_episode("EPISODE_FAILED_FAST", f"child {run_id} reached {child['terminal_state']}")
        elif child["status"] == "COMPLETED_VALIDATED":
            self._event("child_completed", "child reached explicit COMPLETED_VALIDATED", [run_id])

    def _sync_child(self, child: dict[str, Any], result: Mapping[str, Any]) -> None:
        terminal = result.get("terminal") if isinstance(result, Mapping) else None
        state = terminal.get("state") if isinstance(terminal, Mapping) else None
        child["last_state_sha256"] = result.get("state_sha256") if isinstance(result, Mapping) else None
        if state == StopState.COMPLETED_VALIDATED.value:
            child["status"] = "COMPLETED_VALIDATED"
        elif state == StopState.WAITING_FOR_APPROVAL.value:
            child["status"] = "WAITING_FOR_APPROVAL"
            for request_id in self._pending_request_ids(child):
                if request_id not in child["approval_request_ids"]:
                    child["approval_request_ids"].append(request_id)
                    self.state["approval_events"].append({
                        "run_id": child["run_id"],
                        "request_id": request_id,
                        "status": "PENDING",
                        "recorded_at": utc_now(),
                    })
        elif state in {None, StopState.CHECKPOINTED_RESUMABLE.value}:
            child["status"] = "CHECKPOINTED_RESUMABLE"
            child["terminal_state"] = "CHECKPOINTED_RESUMABLE"
            child["terminal_summary"] = "child has persisted state but no terminal promotion"
        else:
            child["status"] = "FAILED"
            child["terminal_state"] = state or "CHILD_RUNTIME_ERROR"
            child["terminal_summary"] = terminal.get("summary") if isinstance(terminal, Mapping) else "child returned no terminal summary"
        if isinstance(terminal, Mapping):
            child["terminal_state"] = state
            child["terminal_summary"] = terminal.get("summary")

    def _pending_request_ids(self, child: Mapping[str, Any]) -> list[str]:
        try:
            return [item["request_id"] for item in self._runtime(child).pending_approval()]
        except (RuntimeError, OSError, ValueError):
            return []

    def _record_child_history(self, child: dict[str, Any]) -> None:
        child["history"].append({
            "attempt": child["attempt"],
            "status": child["status"],
            "terminal_state": child.get("terminal_state"),
            "summary": child.get("terminal_summary"),
            "run_dir": child["run_dir"],
            "state_sha256": child.get("last_state_sha256"),
            "recorded_at": utc_now(),
        })

    def _maybe_retry(self, child: dict[str, Any]) -> None:
        if child["status"] != "FAILED" or child["retry_count"] >= child["retry_limit"]:
            return
        child["retry_count"] += 1
        child["attempt"] += 1
        child["run_dir"] = self._relative_run_dir(child["run_id"], child["attempt"])
        child["attempt_dirs"].append(child["run_dir"])
        child["status"] = "PENDING"
        child["terminal_state"] = None
        child["terminal_summary"] = None
        self._event("child_retry", "scheduled one bounded child retry within the declared retry limit", [child["run_id"]])

    def _dependencies_completed(self, child: Mapping[str, Any]) -> bool:
        by_id = {item["run_id"]: item for item in self.state["children"]}
        return all(by_id[dependency]["status"] == "COMPLETED_VALIDATED" for dependency in child["depends_on"])

    def _mark_dependency_blocks(self) -> None:
        by_id = {item["run_id"]: item for item in self.state["children"]}
        for child in self.state["children"]:
            if child["status"] != "PENDING":
                continue
            failed = [dependency for dependency in child["depends_on"] if by_id[dependency]["status"] in {"FAILED", "BLOCKED_DEPENDENCY"}]
            if not failed:
                continue
            if self.spec.policy == "FAIL_FAST":
                self._stop_episode("EPISODE_FAILED_FAST", f"dependency failure prevents child {child['run_id']}: {failed}")
                return
            child["status"] = "BLOCKED_DEPENDENCY"
            child["terminal_state"] = "BLOCKED_DEPENDENCY"
            child["terminal_summary"] = f"dependency did not reach COMPLETED_VALIDATED: {', '.join(failed)}"
            self._record_child_history(child)
            self._event("child_blocked", "blocked a dependent child without running it", [child["run_id"], *failed])

    def _all_children_terminal(self) -> bool:
        return all(child["status"] in CHILD_TERMINAL_STATES for child in self.state["children"])

    def _child_fits_action_budget(self, child: Mapping[str, Any]) -> bool:
        remaining = self.spec.budget.max_actions - int(self.state["budget_usage"]["actions"])
        run_dir = self.episode_dir / child["run_dir"]
        if (run_dir / "run-state.json").exists():
            try:
                data = json.loads((run_dir / "run-state.json").read_text(encoding="utf-8"))
                planned = max(0, len(data.get("packets", [])) - int(data.get("next_action_index", 0)))
            except (OSError, json.JSONDecodeError, TypeError, ValueError):
                planned = len(self._child_spec(child["run_id"]).run_spec.actions)
        else:
            planned = len(self._child_spec(child["run_id"]).run_spec.actions)
        return planned <= remaining

    def _update_usage(self) -> None:
        actions = 0
        output_bytes = 0
        for child in self.state["children"]:
            for relative in child.get("attempt_dirs", []):
                path = self.episode_dir / relative / "run-state.json"
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                executions = data.get("executions", [])
                if not isinstance(executions, list):
                    continue
                actions += len(executions)
                for execution in executions:
                    if isinstance(execution, Mapping):
                        output_bytes += len(str(execution.get("stdout", "")).encode("utf-8"))
                        output_bytes += len(str(execution.get("stderr", "")).encode("utf-8"))
        elapsed = max(0.0, time.time() - float(self.state["started_at_epoch"]))
        self.state["budget_usage"] = {
            "actions": actions,
            "elapsed_seconds": round(elapsed, 6),
            "output_bytes": output_bytes,
        }

    def _budget_exceeded(self) -> bool:
        usage = self.state["budget_usage"]
        return (
            usage["actions"] > self.spec.budget.max_actions
            or usage["elapsed_seconds"] > self.spec.budget.max_seconds
            or usage["output_bytes"] > self.spec.budget.max_output_bytes
        )

    def _roll_up(self) -> dict[str, Any]:
        statuses = [child["status"] for child in self.state["children"]]
        if "WAITING_FOR_APPROVAL" in statuses:
            return self._stop_episode("EPISODE_WAITING_FOR_APPROVAL", "one or more child runs require aggregated approval")
        if "CHECKPOINTED_RESUMABLE" in statuses:
            return self._stop_episode("EPISODE_CHECKPOINTED_RESUMABLE", "one or more child runs have restartable durable checkpoints")
        if any(status == "BLOCKED_DEPENDENCY" for status in statuses):
            return self._stop_episode("EPISODE_COMPLETED_WITH_DEPENDENCY_BLOCKS", "some children were not run because dependencies failed")
        if any(status == "FAILED" for status in statuses):
            if self.spec.policy == "FAIL_FAST":
                return self._stop_episode("EPISODE_FAILED_FAST", "a child failed and fail-fast policy stopped the episode")
            return self._stop_episode("EPISODE_COMPLETED_WITH_INDEPENDENT_FAILURES", "independent children were evaluated while one or more children failed")
        if all(status == "COMPLETED_VALIDATED" for status in statuses):
            return self._stop_episode("EPISODE_COMPLETED_VALIDATED", "all dependency-ordered child runs reached COMPLETED_VALIDATED")
        return self._stop_episode("EPISODE_BLOCKED_DEPENDENCY", "the episode has no dependency-ready child and no terminal roll-up")

    def _stop_episode(self, state: str, summary: str) -> dict[str, Any]:
        if state not in EPISODE_TERMINAL_STATES:
            raise SupervisorError(f"unknown episode terminal state: {state}")
        _summary(summary)
        self.state["phase"] = "STOP"
        self.state["terminal"] = {
            "state": state,
            "summary": summary,
            "episode_id": self.spec.episode_id,
            "child_states": {child["run_id"]: child["status"] for child in self.state["children"]},
            "event_count": len(self.state["trace"]),
            "recorded_at": utc_now(),
        }
        self._event("episode_stop", summary, [state])
        self._persist()
        return dict(self.state)

    def _event(self, event_type: str, summary: str, refs: Sequence[str]) -> None:
        _summary(summary)
        self.state["trace"].append({
            "event_id": f"episode-trace-{len(self.state['trace']):04d}",
            "episode_id": self.spec.episode_id,
            "sequence": len(self.state["trace"]),
            "event_type": event_type,
            "actor_id": "supervisor-r0",
            "summary": summary,
            "refs": list(refs),
        })

    def _persist(self) -> None:
        digest_payload = {key: value for key, value in self.state.items() if key != "state_sha256"}
        self.state["state_sha256"] = sha256_json(digest_payload)
        _atomic_json(self.state_path, self.state)
        self.trace_path.write_text(
            "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in self.state["trace"]),
            encoding="utf-8",
        )

    def _load(self) -> None:
        if not self.spec_path.is_file() or not self.state_path.is_file():
            raise SupervisorError("episode spec or state is missing")
        try:
            spec_data = json.loads(self.spec_path.read_text(encoding="utf-8"))
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            spec = EpisodeSpec.from_dict(spec_data)
        except (OSError, json.JSONDecodeError, TypeError, ValueError, KeyError) as exc:
            raise SupervisorError(f"persisted episode is unreadable: {exc}") from exc
        if not isinstance(data, dict) or data.get("schema") != SUPERVISOR_SCHEMA or data.get("episode_id") != spec.episode_id:
            raise SupervisorError("persisted episode lineage is invalid")
        if not data.get("state_sha256"):
            raise SupervisorError("persisted episode state has no integrity digest")
        expected = sha256_json({key: value for key, value in data.items() if key != "state_sha256"})
        if data["state_sha256"] != expected:
            raise SupervisorError("persisted episode state digest does not verify")
        self._spec = spec
        self._state = data


__all__ = [
    "CHILD_TERMINAL_STATES",
    "EPISODE_POLICIES",
    "EPISODE_TERMINAL_STATES",
    "EpisodeBudget",
    "EpisodeSpec",
    "ChildRunSpec",
    "Supervisor",
    "SupervisorError",
]
