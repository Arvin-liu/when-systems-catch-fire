from __future__ import annotations

from dataclasses import replace
import io
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout

from agent_kernel import KernelValidationError, StopState

from agent_runtime.actions import (
    ActionKind,
    ApprovalClass,
    ActionExecutionError,
    CrashInjected,
    ExecutionPacket,
    FilePreimage,
    LocalWorkspaceExecutor,
    RollbackClass,
    WorkspacePolicy,
    WorkspaceViolation,
)
from agent_runtime.cli import main as cli_main
from agent_runtime.control import (
    ApprovalConflict,
    ApprovalDecisionR1,
    ApprovalRequestR1,
    ApprovalStore,
    IdempotencyConflict,
    LeaseConflict,
    LeaseStore,
)
from agent_runtime.pilots.r1_real_local import run_pilot_a, run_pilot_b, validate_pilots
from agent_runtime.r1_runtime import AgentRuntimeR1, R1RunSpec, RuntimeR1Error
from agent_runtime.transport import JsonlReasonerTransport, ReasonerRequest, TransportError, action_plan_hash


def packet(
    *, run_id: str = "run-test", action_id: str = "action-test", kind: str = "WRITE_FILE",
    path: str = "out.txt", content: str = "out\n", approval: str = ApprovalClass.AUTO_ALLOWED_SAFE.value,
    rollback: str = RollbackClass.ROLLBACKABLE_LOCAL_FILE.value, argv: tuple[str, ...] = (),
    reads: tuple[str, ...] = (), idem: str = "idem-test", source_hash: str = "0" * 64,
) -> ExecutionPacket:
    capability = "write.files" if kind == ActionKind.WRITE_FILE.value else "run.commands"
    return ExecutionPacket(
        run_id=run_id, step_id=f"step-{action_id}", action_id=action_id, kind=kind,
        required_capabilities=(capability,), requested_reads=reads, requested_writes=(path,) if kind == "WRITE_FILE" else (),
        argv=argv, approval_class=approval, expected_side_effects=(path,) if kind == "WRITE_FILE" else (),
        validator_refs=("bounded",), timeout_seconds=1, max_output_bytes=64, idempotency_key=idem,
        rollback_class=rollback, reason_summary="test local action", source_plan_hash=source_hash,
        payload={"path": path, "content": content} if kind == "WRITE_FILE" else {}, network_requested=False,
    )


def bind(packets: tuple[ExecutionPacket, ...]) -> tuple[ExecutionPacket, ...]:
    digest = action_plan_hash(packets)
    return tuple(replace(item, source_plan_hash=digest) for item in packets)


def spec(root: Path, packets: tuple[ExecutionPacket, ...], *, faults: dict[str, str] | None = None, validator: dict | None = None) -> R1RunSpec:
    return R1RunSpec(
        run_id=packets[0].run_id, profile_ref="profile-test",
        goal={"statement": "test a bounded local action", "success_conditions": ["typed check"], "prohibited_actions": ["network"]},
        workspace=WorkspacePolicy(str(root), (".",), (".",), (sys.executable,), timeout_seconds=1, max_output_bytes=64),
        capability_scope={"scope_id": "scope-test", "allowed_capabilities": ["read.files", "write.files", "run.commands"], "network_allowed": False},
        actions=packets, reasoner={"type": "scripted"}, executor={"type": "local_workspace", "class_id": "local-workspace-executor"}, validator=validator or {"type": "command_exit"},
        lease_ttl_seconds=10, fault_injection=faults or {},
    )


class AgentRuntimeR1Tests(unittest.TestCase):
    def test_real_offline_pilots(self) -> None:
        with tempfile.TemporaryDirectory(prefix="r1-pilots-test-") as temp:
            root = Path(temp)
            a = run_pilot_a(root)
            b = run_pilot_b(root)
            combined = validate_pilots(root)
            self.assertEqual(a["final_state"], StopState.COMPLETED_VALIDATED.value)
            self.assertEqual(b["final_state"], StopState.FAILED_VALIDATION_ROLLED_BACK.value)
            self.assertTrue(b["bad_output_absent"])
            self.assertEqual(combined["status"], "PASS")
            self.assertNotEqual(b["executor_history"][0], b["executor_history"][1])

    def test_workspace_path_symlink_and_command_guards(self) -> None:
        with tempfile.TemporaryDirectory(prefix="r1-boundary-") as temp:
            root = Path(temp) / "root"
            outside = Path(temp) / "outside"
            root.mkdir()
            outside.mkdir()
            (outside / "secret.txt").write_text("secret", encoding="utf-8")
            (root / "escape").symlink_to(outside, target_is_directory=True)
            policy = WorkspacePolicy(str(root), (".",), (".",), (sys.executable,))
            with self.assertRaises(WorkspaceViolation):
                policy.resolve_read("../outside/secret.txt")
            with self.assertRaises(WorkspaceViolation):
                policy.resolve_read("escape/secret.txt")
            with self.assertRaises(WorkspaceViolation):
                policy.command_argv(("/usr/bin/not-allowlisted", "--version"))
            with self.assertRaises(WorkspaceViolation):
                policy.command_argv((sys.executable, "-c", "print(1) | cat"))
            unknown_capability = replace(packet(), required_capabilities=("write.files", "write.secret"))
            with self.assertRaises(WorkspaceViolation):
                policy.validate_packet(unknown_capability)

    def test_special_file_and_unknown_packet_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="r1-special-") as temp:
            root = Path(temp)
            policy = WorkspacePolicy(str(root), (".",), (".",), ())
            with self.assertRaises(WorkspaceViolation):
                policy.resolve_read("/dev/null")
            raw = packet().to_dict()
            raw["kind"] = "DELETE_TREE"
            with self.assertRaises(KernelValidationError):
                ExecutionPacket.from_dict(raw)

    def test_timeout_and_output_truncation_are_typed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="r1-command-") as temp:
            root = Path(temp)
            policy = WorkspacePolicy(str(root), (".",), (".",), (sys.executable,), timeout_seconds=0.05, max_output_bytes=10)
            timeout_packet = ExecutionPacket(
                **{**packet(kind="RUN_COMMAND", approval=ApprovalClass.COMMAND_REQUIRES_APPROVAL.value, rollback=RollbackClass.NOT_SUPPORTED_R1.value, argv=(sys.executable, "-c", "__import__('time').sleep(1)"), source_hash="0" * 64).to_dict(), "requested_reads": [], "requested_writes": [], "expected_side_effects": []}
            )
            timeout_result = LocalWorkspaceExecutor(policy).execute(timeout_packet)
            self.assertEqual(timeout_result.status, "TIMEOUT")
            output_packet = ExecutionPacket(
                **{**packet(kind="RUN_COMMAND", action_id="action-output", approval=ApprovalClass.COMMAND_REQUIRES_APPROVAL.value, rollback=RollbackClass.NOT_SUPPORTED_R1.value, argv=(sys.executable, "-c", "print('x' * 100)"), source_hash="0" * 64).to_dict(), "requested_reads": [], "requested_writes": [], "expected_side_effects": []}
            )
            output_result = LocalWorkspaceExecutor(policy).execute(output_packet)
            self.assertTrue(output_result.stdout_truncated)

    def test_lease_and_idempotency_conflicts(self) -> None:
        clock = [100.0]
        with tempfile.TemporaryDirectory(prefix="r1-lease-") as temp:
            store = LeaseStore(Path(temp) / "leases.json", ttl_seconds=5, clock=lambda: clock[0])
            lease = store.acquire(run_id="run-1", action_id="action-1", idempotency_key="idem-1", packet_digest="a" * 64, executor_class_id="class-1", executor_instance_id="instance-1")
            with self.assertRaises(LeaseConflict):
                store.acquire(run_id="run-1", action_id="action-1", idempotency_key="idem-2", packet_digest="b" * 64, executor_class_id="class-1", executor_instance_id="instance-2")
            with self.assertRaises(IdempotencyConflict):
                store.acquire(run_id="run-1", action_id="action-other", idempotency_key="idem-1", packet_digest="b" * 64, executor_class_id="class-1", executor_instance_id="instance-2")
            clock[0] = 106.0
            expired = store.acquire(run_id="run-1", action_id="action-1", idempotency_key="idem-2", packet_digest="b" * 64, executor_class_id="class-1", executor_instance_id="instance-2")
            self.assertEqual(lease.status, "ACTIVE")
            self.assertEqual(expired.status, "ACTIVE")

    def test_approval_stale_and_digest_mismatch(self) -> None:
        clock = [10.0]
        with tempfile.TemporaryDirectory(prefix="r1-approval-") as temp:
            store = ApprovalStore(Path(temp) / "approvals.json", clock=lambda: clock[0])
            request = ApprovalRequestR1("request-1", "run-1", "action-1", "a" * 64, "write one file", "bounded", ("write.files",), ("in.txt",), ("out.txt",), 11.0, created_at="now")
            store.create(request)
            mismatch = ApprovalDecisionR1("decision-1", "request-1", "run-1", "b" * 64, "ALLOW", "human-1", "human", "now", "approve")
            with self.assertRaises(ApprovalConflict):
                store.submit(mismatch)
            clock[0] = 12.0
            expired = ApprovalDecisionR1("decision-1", "request-1", "run-1", "a" * 64, "ALLOW", "human-1", "human", "now", "approve")
            with self.assertRaises(ApprovalConflict):
                store.submit(expired)

    def test_plan_digest_rejects_packet_expansion(self) -> None:
        with tempfile.TemporaryDirectory(prefix="r1-digest-") as temp:
            root = Path(temp)
            first = packet()
            bound = bind((first,))[0]
            raw = {
                "run_id": "run-test", "profile_ref": "profile-test",
                "goal": {"statement": "test", "success_conditions": ["ok"], "prohibited_actions": []},
                "workspace": WorkspacePolicy(str(root), (".",), (".",), ()).to_dict(),
                "capability_scope": {"scope_id": "scope-test", "allowed_capabilities": ["write.files"], "network_allowed": False},
                "actions": [bound.to_dict()], "reasoner": {"type": "scripted"}, "executor": {"type": "local_workspace", "class_id": "local-workspace-executor"}, "validator": {"type": "command_exit"},
                "lease_ttl_seconds": 10, "fault_injection": {},
            }
            raw["actions"][0]["payload"]["content"] = "expanded"
            with self.assertRaises(RuntimeR1Error):
                R1RunSpec.from_dict(raw)

    def test_all_restart_fault_points_recover_without_terminal_promotion(self) -> None:
        for point in ("pre_execute", "mid_write", "post_execute_before_persist", "post_persist"):
            with self.subTest(point=point), tempfile.TemporaryDirectory(prefix=f"r1-{point}-") as temp:
                root = Path(temp)
                p = bind((packet(run_id=f"run-{point}", action_id="action-1", path="out.txt", content="ok", approval=ApprovalClass.BOUNDED_WRITE_REQUIRES_APPROVAL.value),))[0]
                run_spec = spec(root, (p,), faults={"action-1": point})
                run_dir = root / "run"
                runtime = AgentRuntimeR1(run_dir)
                runtime.start(run_spec)
                with self.assertRaises(CrashInjected):
                    runtime.approve("approval-action-1", "ALLOW", authority_id="pilot", authority_type="synthetic_pilot")
                resumed = AgentRuntimeR1(run_dir, executor_class_id="executor-v2", executor_instance_id="instance-2")
                state = resumed.resume()
                self.assertEqual(state["terminal"]["state"], StopState.COMPLETED_VALIDATED.value)
                self.assertEqual((root / "out.txt").read_text(encoding="utf-8"), "ok")
                self.assertNotIn("SUCCESS", json.dumps(state))

    def test_rollback_failure_is_not_silently_reclassified(self) -> None:
        with tempfile.TemporaryDirectory(prefix="r1-rollback-") as temp:
            root = Path(temp)
            policy = WorkspacePolicy(str(root), (".",), (".",), ())
            executor = LocalWorkspaceExecutor(policy)
            bad = FilePreimage("out.txt", True, 0o644, "a" * 64, 1, "not-base64")
            rollback = executor.rollback((bad,))
            self.assertEqual(rollback["status"], "ROLLBACK_FAILED")

    def test_jsonl_transport_rejects_multiple_lines_and_accepts_typed_frame(self) -> None:
        request = ReasonerRequest("FRAME", "run-transport", "frame this task", "bounded workspace", ("read.files",))
        script = "print(__import__('json').dumps({'phase':'FRAME','frame_summary':'typed frame','packets':[],'status':'CONTINUE','block_summary':None}))"
        response = JsonlReasonerTransport((sys.executable, "-c", script), timeout_seconds=2).request(request)
        self.assertEqual(response.frame_summary, "typed frame")
        multi_path = Path(tempfile.mkdtemp(prefix="r1-transport-") ) / "multi.py"
        multi_path.write_text("print('{}')\nprint('{}')\n", encoding="utf-8")
        multi = (sys.executable, str(multi_path))
        with self.assertRaises(TransportError):
            JsonlReasonerTransport(multi, timeout_seconds=2).request(request)

    def test_cli_run_status_pending_approve_and_resume(self) -> None:
        with tempfile.TemporaryDirectory(prefix="r1-cli-") as temp:
            root = Path(temp)
            workspace = root / "workspace"
            workspace.mkdir()
            p = bind((packet(run_id="run-cli", action_id="action-cli", path="out.txt", approval=ApprovalClass.BOUNDED_WRITE_REQUIRES_APPROVAL.value),))[0]
            data = {
                "run_id": "run-cli", "profile_ref": "profile-cli",
                "goal": {"statement": "cli run", "success_conditions": ["file"], "prohibited_actions": []},
                "workspace": WorkspacePolicy(str(workspace), (".",), (".",), ()).to_dict(),
                "capability_scope": {"scope_id": "scope-cli", "allowed_capabilities": ["write.files"], "network_allowed": False},
                "actions": [p.to_dict()], "reasoner": {"type": "scripted"}, "executor": {"type": "local_workspace", "class_id": "local-workspace-executor"}, "validator": {"type": "command_exit"},
                "lease_ttl_seconds": 10, "fault_injection": {},
            }
            spec_path = root / "spec.json"
            spec_path.write_text(json.dumps(data), encoding="utf-8")
            run_dir = root / "run"
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(cli_main(["run", "--spec", str(spec_path), "--run-dir", str(run_dir), "--json"]), 0)
            self.assertIn("WAITING_FOR_APPROVAL", output.getvalue())
            with redirect_stdout(io.StringIO()):
                self.assertEqual(cli_main(["approve", "--run-dir", str(run_dir), "--request-id", "approval-action-cli", "--decision", "allow", "--authority", "cli-human", "--json"]), 0)
            state = json.loads((run_dir / "run-state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["terminal"]["state"], StopState.COMPLETED_VALIDATED.value)


if __name__ == "__main__":
    unittest.main()
