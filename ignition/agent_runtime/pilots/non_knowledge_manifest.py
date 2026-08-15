"""Non-knowledge Agent Runtime R0 pilot.

The fixture scans two text files and writes one sorted SHA-256 manifest.  It
does not use a source registry, evidence vocabulary, a domain adapter or a
network connection.  The first executor stops after the read/validate step;
the second executor resumes from the persisted capsule and performs the
bounded write.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import tempfile
from typing import Any

from agent_kernel import CapabilityScope, StopState
from agent_runtime import (
    ActionObservation,
    ActionRequest,
    AgentRuntime,
    EnvironmentObservation,
    GoalContract,
    Plan,
    PlanStep,
    RunIdentity,
    ValidationResult,
)


FIXTURE_FILES = {
    "sandbox/input/alpha.txt": b"alpha\n",
    "sandbox/input/beta.txt": b"beta\n",
}


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _expected_manifest(workspace: Path) -> dict[str, Any]:
    entries = []
    for relative in sorted(FIXTURE_FILES):
        path = workspace / relative
        entries.append({"path": relative, "sha256": _sha(path), "bytes": path.stat().st_size})
    return {"manifest_version": "r0", "files": entries}


class ManifestReasoner:
    """A scripted reasoner; no model/provider is required."""

    def frame(self, goal: GoalContract, environment: EnvironmentObservation) -> str:
        return f"bounded file-manifest goal over {len(environment.observed_paths)} declared inputs"

    def plan(self, goal: GoalContract, environment: EnvironmentObservation, frame_summary: str) -> Plan:
        inputs = tuple(environment.observed_paths)
        return Plan(
            plan_id="manifest-plan-r0",
            run_id=environment.run_id,
            rationale_summary="read and validate inputs before writing the single declared output",
            steps=(
                PlanStep(
                    step_id="scan-inputs",
                    operation="scan_inputs",
                    required_capabilities=("read.files",),
                    requested_reads=inputs,
                    requested_writes=(),
                    requested_commands=(),
                    network_requested=False,
                    approval_class=None,
                    expected_output="input hashes and sorted path set",
                    reason_summary="observe only; source files must remain unchanged",
                ),
                PlanStep(
                    step_id="write-manifest",
                    operation="write_manifest",
                    required_capabilities=("write.manifest",),
                    requested_reads=inputs,
                    requested_writes=("sandbox/manifest.json",),
                    requested_commands=(),
                    network_requested=False,
                    approval_class=None,
                    expected_output="one deterministic manifest at the declared path",
                    reason_summary="write exactly one allowed derived output after the read step",
                ),
            ),
        )


class ManifestExecutor:
    def __init__(self, workspace: Path, executor_id: str) -> None:
        self.workspace = workspace
        self.executor_id = executor_id

    def execute(self, action: ActionRequest, environment: EnvironmentObservation) -> ActionObservation:
        if action.operation == "scan_inputs":
            hashes = [_sha(self.workspace / relative) for relative in sorted(environment.observed_paths)]
            digest = sha256("".join(hashes).encode("ascii")).hexdigest()
            return ActionObservation(
                action_id=action.action_id,
                run_id=action.run_id,
                executor_id=self.executor_id,
                changed_paths=(),
                output_refs=(f"scan:{digest}",),
                summary="read declared input files and produced an in-memory hash observation",
            )
        if action.operation == "write_manifest":
            output = self.workspace / "sandbox/manifest.json"
            output.write_text(json.dumps(_expected_manifest(self.workspace), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return ActionObservation(
                action_id=action.action_id,
                run_id=action.run_id,
                executor_id=self.executor_id,
                changed_paths=("sandbox/manifest.json",),
                output_refs=("sandbox/manifest.json",),
                summary="wrote the single declared manifest output",
            )
        raise ValueError(f"unsupported pilot operation: {action.operation}")


class ManifestValidator:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace

    def validate(self, action: ActionRequest, observation: ActionObservation) -> ValidationResult:
        if action.operation == "scan_inputs":
            passed = observation.changed_paths == () and len(observation.output_refs) == 1
            return ValidationResult(
                validation_id=f"validation-{action.action_id}",
                run_id=action.run_id,
                action_id=action.action_id,
                passed=passed,
                checks=("no source file changed", "scan produced one structured output ref"),
                summary="scan step is valid" if passed else "scan step changed an unexpected path",
            )
        if action.operation == "write_manifest":
            manifest = self.workspace / "sandbox/manifest.json"
            expected = _expected_manifest(self.workspace)
            actual = json.loads(manifest.read_text(encoding="utf-8")) if manifest.is_file() else None
            passed = actual == expected and observation.changed_paths == ("sandbox/manifest.json",)
            return ValidationResult(
                validation_id=f"validation-{action.action_id}",
                run_id=action.run_id,
                action_id=action.action_id,
                passed=passed,
                checks=("manifest exists", "paths are sorted", "SHA-256 values match", "only declared output changed"),
                summary="manifest matches the deterministic validator" if passed else "manifest or write-set mismatch",
            )
        raise ValueError(f"unsupported pilot operation: {action.operation}")


def _scope() -> CapabilityScope:
    return CapabilityScope(
        scope_id="non-knowledge-pilot-scope",
        allowed_reads=("sandbox/input/*.txt",),
        allowed_writes=("sandbox/manifest.json",),
        allowed_tools=("read.files", "write.manifest"),
        network_allowed=False,
        max_actions=2,
    )


def _prepare_workspace(workspace: Path) -> None:
    for relative, content in FIXTURE_FILES.items():
        path = workspace / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def _source_snapshot(workspace: Path) -> dict[str, str]:
    return {relative: _sha(workspace / relative) for relative in sorted(FIXTURE_FILES)}


def run_pilot(output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    workspace = output_dir / "workspace"
    _prepare_workspace(workspace)
    before = _source_snapshot(workspace)
    identity = RunIdentity(
        run_id="manifest-pilot/run-001",
        profile_ref="agent-profile-r0",
        goal_version="manifest-goal-r0",
        created_by="pilot-owner",
    )
    goal = GoalContract(
        goal_id="manifest-pilot",
        statement="scan declared text files and write a sorted SHA-256 manifest without changing sources",
        success_conditions=("manifest matches all declared inputs", "no source file changes", "no unauthorized paths change"),
        prohibited_actions=("network access", "source mutation", "writes outside sandbox/manifest.json"),
        capability_scope_ref="non-knowledge-pilot-scope",
    )
    environment = EnvironmentObservation(
        observation_id="environment-001",
        run_id=identity.run_id,
        executor_id="executor-alpha",
        observed_paths=tuple(sorted(FIXTURE_FILES)),
        summary="sandbox contains two declared text inputs and no manifest yet",
    )
    reasoner = ManifestReasoner()
    validator = ManifestValidator(workspace)
    first = AgentRuntime(
        state_path=output_dir / "run-state.json",
        trace_path=output_dir / "machine-trace.json",
        memory_path=output_dir / "durable-memory.jsonl",
        capsule_path=output_dir / "resume-capsule.json",
        capability_scope=_scope(),
        reasoner=reasoner,
        executor=ManifestExecutor(workspace, "executor-alpha"),
        validator=validator,
        clock=lambda: "2026-08-15T12:00:00Z",
    )
    checkpointed = first.start(identity, goal, environment, checkpoint_after_actions=1, handoff_to="executor-beta")
    if (checkpointed.get("terminal") or {}).get("state") != StopState.CHECKPOINTED_RESUMABLE.value:
        raise AssertionError("pilot did not stop at the required checkpoint")

    second = AgentRuntime(
        state_path=output_dir / "run-state.json",
        trace_path=output_dir / "machine-trace.json",
        memory_path=output_dir / "durable-memory.jsonl",
        capsule_path=output_dir / "resume-capsule.json",
        capability_scope=_scope(),
        reasoner=reasoner,
        executor=ManifestExecutor(workspace, "executor-beta"),
        validator=validator,
        clock=lambda: "2026-08-15T12:00:00Z",
    )
    completed = second.resume()
    after = _source_snapshot(workspace)
    manifest = workspace / "sandbox/manifest.json"
    expected = _expected_manifest(workspace)
    if (completed.get("terminal") or {}).get("state") != StopState.COMPLETED_VALIDATED.value:
        raise AssertionError("pilot did not reach COMPLETED_VALIDATED")
    if before != after or not manifest.is_file() or json.loads(manifest.read_text(encoding="utf-8")) != expected:
        raise AssertionError("pilot source immutability or manifest validation failed")

    receipt = {
        "pilot_id": "non-knowledge-manifest-r0",
        "domain_dependency": "none",
        "knowledge_paths_visible": False,
        "network_allowed": False,
        "first_executor": "executor-alpha",
        "resume_executor": "executor-beta",
        "checkpoint_state": checkpointed["terminal"]["state"],
        "final_state": completed["terminal"]["state"],
        "state_sha256": completed["state_sha256"],
        "source_hashes_before": before,
        "source_hashes_after": after,
        "allowed_write_set": ["sandbox/manifest.json"],
        "actual_write_set": ["sandbox/manifest.json"],
        "trace_phases": [event["phase"] for event in completed["trace"]],
        "trace_event_count": len(completed["trace"]),
        "validator_checks": completed["validation_results"][-1]["checks"],
    }
    (output_dir / "pilot-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "HUMAN-REPORT.md").write_text(
        "# Agent Runtime R0 非知识 pilot\n\n"
        "给定 sandbox 中的两个文本文件，运行时先读取并校验，再把按路径排序的 SHA-256 manifest 写入唯一允许的输出路径。\n\n"
        f"- 第一个 executor：`executor-alpha`，在 `{checkpointed['terminal']['state']}` checkpoint 停止。\n"
        f"- 第二个 executor：`executor-beta`，通过 resume capsule 继续并达到 `{completed['terminal']['state']}`。\n"
        "- 网络关闭；pilot 不读取任何知识系统路径；源文件前后 SHA-256 相同；实际写集等于声明写集。\n"
        "- 该结果只证明一个确定性 control-plane 闭环，不证明模型智能、现实自主性或通用 AGI。\n",
        encoding="utf-8",
    )
    return receipt


def validate_artifact(output_dir: Path) -> dict[str, Any]:
    receipt_path = output_dir / "pilot-receipt.json"
    state_path = output_dir / "run-state.json"
    trace_path = output_dir / "machine-trace.json"
    capsule_path = output_dir / "resume-capsule.json"
    for path in (receipt_path, state_path, trace_path, capsule_path, output_dir / "HUMAN-REPORT.md"):
        if not path.is_file():
            raise AssertionError(f"missing pilot artifact: {path}")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    state = json.loads(state_path.read_text(encoding="utf-8"))
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    if receipt["final_state"] != StopState.COMPLETED_VALIDATED.value or state["terminal"]["state"] != receipt["final_state"]:
        raise AssertionError("pilot terminal receipt is not validated")
    if receipt["first_executor"] == receipt["resume_executor"]:
        raise AssertionError("pilot resume did not use a different executor")
    if trace != state["trace"]:
        raise AssertionError("machine trace is not the persisted trace")
    if receipt["state_sha256"] != state["state_sha256"]:
        raise AssertionError("receipt state digest drift")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        if not args.output_dir:
            parser.error("--check requires --output-dir")
        print(json.dumps(validate_artifact(args.output_dir), ensure_ascii=False, sort_keys=True))
        return 0
    if args.output_dir:
        print(json.dumps(run_pilot(args.output_dir), ensure_ascii=False, sort_keys=True))
        return 0
    with tempfile.TemporaryDirectory(prefix="agent-runtime-pilot-") as tmp:
        print(json.dumps(run_pilot(Path(tmp)), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
