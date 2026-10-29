from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import tempfile
import unittest

from agent_runtime.actions import ActionKind, ApprovalClass, ExecutionPacket, RollbackClass, WorkspacePolicy
from agent_runtime.r1_runtime import R1RunSpec
from agent_runtime.supervisor import EpisodeBudget, EpisodeSpec, ChildRunSpec, Supervisor, SupervisorError
from agent_runtime.transport import action_plan_hash


def packet(run_id: str, action_id: str, path: str, *, approval: str = ApprovalClass.AUTO_ALLOWED_SAFE.value) -> ExecutionPacket:
    raw = ExecutionPacket(
        run_id=run_id,
        step_id=f"step-{action_id}",
        action_id=action_id,
        kind=ActionKind.WRITE_FILE.value,
        required_capabilities=("write.files",),
        requested_reads=(),
        requested_writes=(path,),
        argv=(),
        approval_class=approval,
        expected_side_effects=(path,),
        validator_refs=("bounded",),
        timeout_seconds=1,
        max_output_bytes=64,
        idempotency_key=f"idem-{action_id}",
        rollback_class=RollbackClass.ROLLBACKABLE_LOCAL_FILE.value,
        reason_summary="bounded supervisor test write",
        source_plan_hash="0" * 64,
        payload={"path": path, "content": f"content-{action_id}\n"},
        network_requested=False,
    )
    return replace(raw, source_plan_hash=action_plan_hash((raw,)))


def run_spec(root: Path, run_id: str, action_id: str, path: str, *, approval: str = ApprovalClass.AUTO_ALLOWED_SAFE.value, fail: bool = False, fault: dict[str, str] | None = None) -> R1RunSpec:
    return R1RunSpec(
        run_id=run_id,
        profile_ref="profile-supervisor-test",
        goal={"statement": "run one bounded child", "success_conditions": ["typed validation"], "prohibited_actions": ["network"]},
        workspace=WorkspacePolicy(
            str(root), (".",), (".",), (), timeout_seconds=1, max_output_bytes=64,
            max_actions=4, max_writes=4,
        ),
        capability_scope={"scope_id": f"scope-{run_id}", "allowed_capabilities": ["write.files"], "network_allowed": False},
        actions=(packet(run_id, action_id, path, approval=approval),),
        reasoner={"type": "scripted", "frame_summary": "bounded child frame"},
        executor={"type": "local_workspace", "class_id": "local-workspace-executor"},
        validator={"type": "command_exit", "fail_action_ids": [action_id] if fail else []},
        lease_ttl_seconds=10,
        fault_injection=fault or {},
    )


def child(spec: R1RunSpec, *, depends_on: tuple[str, ...] = (), retry_limit: int = 0, executor_instance_id: str = "instance-1") -> ChildRunSpec:
    return ChildRunSpec(
        run_id=spec.run_id,
        run_spec=spec,
        depends_on=depends_on,
        retry_limit=retry_limit,
        executor_instance_id=executor_instance_id,
        executor_class_id="local-workspace-executor",
    )


def episode(children: tuple[ChildRunSpec, ...], *, policy: str = "FAIL_FAST", max_actions: int = 8) -> EpisodeSpec:
    return EpisodeSpec(
        episode_id="episode-test",
        job_id="job-test",
        created_by="test-owner",
        capability_scope_id="episode-scope",
        allowed_capabilities=("write.files",),
        budget=EpisodeBudget(max_actions=max_actions, max_seconds=30, max_output_bytes=4096),
        children=children,
        policy=policy,
    )


class SupervisorTests(unittest.TestCase):
    def test_dependency_order_and_persisted_rollup(self) -> None:
        with tempfile.TemporaryDirectory(prefix="supervisor-dag-") as temp:
            root = Path(temp)
            first = run_spec(root, "run-a", "action-a", "a.txt")
            second = run_spec(root, "run-b", "action-b", "b.txt")
            result = Supervisor(root / "episode").start(episode((child(first), child(second, depends_on=("run-a",)))))
            self.assertEqual(result["terminal"]["state"], "EPISODE_COMPLETED_VALIDATED")
            self.assertEqual([item["status"] for item in result["children"]], ["COMPLETED_VALIDATED", "COMPLETED_VALIDATED"])
            self.assertEqual((root / "a.txt").read_text(encoding="utf-8"), "content-action-a\n")
            self.assertEqual((root / "b.txt").read_text(encoding="utf-8"), "content-action-b\n")
            restored = Supervisor(root / "episode").status()
            self.assertEqual(restored["terminal"]["state"], "EPISODE_COMPLETED_VALIDATED")
            self.assertNotIn("SUCCESS", str(restored))

    def test_scope_cycle_and_network_escalation_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="supervisor-contract-") as temp:
            root = Path(temp)
            a = run_spec(root, "run-a", "action-a", "a.txt")
            b = run_spec(root, "run-b", "action-b", "b.txt")
            with self.assertRaises(SupervisorError):
                episode((child(a, depends_on=("run-b",)), child(b, depends_on=("run-a",))))
            expanded = replace(a, capability_scope={"scope_id": "scope-expanded", "allowed_capabilities": ["write.files", "run.commands"], "network_allowed": False})
            with self.assertRaises(SupervisorError):
                episode((child(expanded),))
            with self.assertRaises(Exception):
                network = replace(a, capability_scope={"scope_id": "scope-network", "allowed_capabilities": ["write.files"], "network_allowed": True})
                episode((child(network),))

    def test_continue_independent_policy_blocks_dependents_but_runs_sibling(self) -> None:
        with tempfile.TemporaryDirectory(prefix="supervisor-independent-") as temp:
            root = Path(temp)
            failed = run_spec(root, "run-fail", "action-fail", "fail.txt", fail=True)
            sibling = run_spec(root, "run-sibling", "action-sibling", "sibling.txt")
            dependent = run_spec(root, "run-dependent", "action-dependent", "dependent.txt")
            result = Supervisor(root / "episode").start(episode((child(failed), child(sibling), child(dependent, depends_on=("run-fail",))), policy="CONTINUE_INDEPENDENT"))
            self.assertEqual(result["terminal"]["state"], "EPISODE_COMPLETED_WITH_DEPENDENCY_BLOCKS")
            statuses = {item["run_id"]: item["status"] for item in result["children"]}
            self.assertEqual(statuses, {"run-fail": "FAILED", "run-sibling": "COMPLETED_VALIDATED", "run-dependent": "BLOCKED_DEPENDENCY"})
            self.assertTrue((root / "sibling.txt").exists())
            self.assertFalse((root / "dependent.txt").exists())

    def test_approval_aggregation_and_handoff(self) -> None:
        with tempfile.TemporaryDirectory(prefix="supervisor-approval-") as temp:
            root = Path(temp)
            waiting = run_spec(root, "run-approval", "action-approval", "approval.txt", approval=ApprovalClass.BOUNDED_WRITE_REQUIRES_APPROVAL.value)
            result = Supervisor(root / "episode").start(episode((child(waiting),)))
            self.assertEqual(result["terminal"]["state"], "EPISODE_WAITING_FOR_APPROVAL")
            pending = Supervisor(root / "episode").pending_approvals()
            self.assertEqual(len(pending), 1)
            self.assertEqual(pending[0]["run_id"], "run-approval")
            handed = Supervisor(root / "episode").handoff("run-approval", "instance-2")
            self.assertEqual(handed["handoffs"][-1]["to_executor_instance_id"], "instance-2")
            result = Supervisor(root / "episode").approve("run-approval", pending[0]["request_id"], "allow", authority_id="owner-1")
            self.assertEqual(result["terminal"]["state"], "EPISODE_COMPLETED_VALIDATED")
            self.assertEqual(result["approval_events"][-1]["decision"], "ALLOW")

    def test_crash_checkpoint_resume_and_bounded_retry(self) -> None:
        with tempfile.TemporaryDirectory(prefix="supervisor-recovery-") as temp:
            root = Path(temp)
            checkpointed = run_spec(root, "run-crash", "action-crash", "crash.txt", fault={"action-crash": "post_execute_before_persist"})
            result = Supervisor(root / "episode").start(episode((child(checkpointed),)))
            self.assertEqual(result["terminal"]["state"], "EPISODE_CHECKPOINTED_RESUMABLE")
            result = Supervisor(root / "episode").handoff("run-crash", "instance-2")
            self.assertEqual(result["handoffs"][-1]["to_executor_instance_id"], "instance-2")
            result = Supervisor(root / "episode").resume()
            self.assertEqual(result["terminal"]["state"], "EPISODE_COMPLETED_VALIDATED")
            self.assertEqual((root / "crash.txt").read_text(encoding="utf-8"), "content-action-crash\n")

            retry = run_spec(root, "run-retry", "action-retry", "retry.txt", fail=True)
            result = Supervisor(root / "retry-episode").start(episode((child(retry, retry_limit=1),)))
            self.assertEqual(result["terminal"]["state"], "EPISODE_FAILED_FAST")
            self.assertEqual(result["children"][0]["retry_count"], 1)
            self.assertEqual(len(result["children"][0]["history"]), 2)

    def test_global_action_budget_is_not_overrun(self) -> None:
        with tempfile.TemporaryDirectory(prefix="supervisor-budget-") as temp:
            root = Path(temp)
            first = run_spec(root, "run-a", "action-a", "a.txt")
            second = run_spec(root, "run-b", "action-b", "b.txt")
            result = Supervisor(root / "episode").start(episode((child(first), child(second)), max_actions=1))
            self.assertEqual(result["terminal"]["state"], "EPISODE_BUDGET_EXHAUSTED")
            self.assertEqual(result["budget_usage"]["actions"], 1)
            self.assertEqual(result["children"][1]["status"], "PENDING")
            self.assertFalse((root / "b.txt").exists())


if __name__ == "__main__":
    unittest.main()
