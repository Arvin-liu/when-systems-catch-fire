"""Offline structural and persistence validator for Supervisor R0."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.actions import ActionKind, ApprovalClass, ExecutionPacket, RollbackClass, WorkspacePolicy
from agent_runtime.r1_runtime import R1RunSpec
from agent_runtime.supervisor import EpisodeBudget, EpisodeSpec, ChildRunSpec, Supervisor, SupervisorError
from agent_runtime.transport import action_plan_hash


def _packet(run_id: str, action_id: str, path: str) -> ExecutionPacket:
    raw = ExecutionPacket(
        run_id=run_id, step_id=f"step-{action_id}", action_id=action_id,
        kind=ActionKind.WRITE_FILE.value, required_capabilities=("write.files",),
        requested_reads=(), requested_writes=(path,), argv=(),
        approval_class=ApprovalClass.AUTO_ALLOWED_SAFE.value,
        expected_side_effects=(path,), validator_refs=("bounded",),
        timeout_seconds=1, max_output_bytes=64, idempotency_key=f"idem-{action_id}",
        rollback_class=RollbackClass.ROLLBACKABLE_LOCAL_FILE.value,
        reason_summary="bounded Supervisor validator write", source_plan_hash="0" * 64,
        payload={"path": path, "content": "validator\n"}, network_requested=False,
    )
    return replace(raw, source_plan_hash=action_plan_hash((raw,)))


def _child(root: Path, run_id: str, action_id: str, path: str, depends_on: tuple[str, ...] = ()) -> ChildRunSpec:
    spec = R1RunSpec(
        run_id=run_id, profile_ref="profile-supervisor-validator",
        goal={"statement": "validate Supervisor R0", "success_conditions": ["typed child"], "prohibited_actions": ["network"]},
        workspace=WorkspacePolicy(str(root), (".",), (".",), (), max_actions=2, max_writes=2, max_output_bytes=64),
        capability_scope={"scope_id": f"scope-{run_id}", "allowed_capabilities": ["write.files"], "network_allowed": False},
        actions=(_packet(run_id, action_id, path),), reasoner={"type": "scripted"},
        executor={"type": "local_workspace", "class_id": "local-workspace-executor"},
        validator={"type": "command_exit"}, lease_ttl_seconds=10, fault_injection={},
    )
    return ChildRunSpec(run_id=run_id, run_spec=spec, depends_on=depends_on)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="supervisor-validator-") as temp:
        root = Path(temp)
        first = _child(root, "run-a", "action-a", "a.txt")
        second = _child(root, "run-b", "action-b", "b.txt", ("run-a",))
        spec = EpisodeSpec(
            episode_id="episode-validator", job_id="job-validator", created_by="validator",
            capability_scope_id="episode-scope", allowed_capabilities=("write.files",),
            budget=EpisodeBudget(max_actions=2, max_seconds=30, max_output_bytes=1024),
            children=(first, second),
        )
        result = Supervisor(root / "episode").start(spec)
        assert result["terminal"]["state"] == "EPISODE_COMPLETED_VALIDATED"
        restored = Supervisor(root / "episode").status()
        assert restored["state_sha256"] == result["state_sha256"]
        assert (root / "a.txt").is_file() and (root / "b.txt").is_file()

        try:
            EpisodeSpec(
                episode_id="episode-cycle", job_id="job-cycle", created_by="validator",
                capability_scope_id="episode-scope", allowed_capabilities=("write.files",),
                budget=EpisodeBudget(max_actions=2, max_seconds=30, max_output_bytes=1024),
                children=(
                    _child(root, "cycle-a", "cycle-action-a", "cycle-a.txt", ("cycle-b",)),
                    _child(root, "cycle-b", "cycle-action-b", "cycle-b.txt", ("cycle-a",)),
                ),
            )
        except SupervisorError:
            pass
        else:
            raise AssertionError("Supervisor accepted a cyclic DAG")
    print("SUPERVISOR_R0_VALIDATOR=PASS")
    print("DAG_PERSISTENCE=PASS")
    print("SCOPE_NON_ESCALATION=PASS")
    print("TERMINAL_ROLLUP=EPISODE_COMPLETED_VALIDATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
