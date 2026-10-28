"""Two offline pilots for the R1 local action plane."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from agent_kernel import StopState, sha256_json

from ..actions import ApprovalClass, CrashInjected, ExecutionPacket, RollbackClass, WorkspacePolicy
from ..control import _atomic_json
from ..r1_runtime import AgentRuntimeR1, R1RunSpec
from ..transport import action_plan_hash


def _packet(
    *, run_id: str, action_id: str, step_id: str, kind: str, reads: tuple[str, ...], writes: tuple[str, ...],
    argv: tuple[str, ...] = (), approval: str, rollback: str, payload: dict[str, Any], idem: str,
) -> ExecutionPacket:
    if kind in {"WRITE_FILE", "CREATE_FILE", "PATCH_TEXT_FILE"}:
        capability = "write.files"
    elif kind == "LIST_DIR":
        capability = "read.directories"
    elif kind in {"READ_FILE", "HASH_FILE"}:
        capability = "read.files"
    else:
        capability = "run.commands"
    return ExecutionPacket(
        run_id=run_id, step_id=step_id, action_id=action_id, kind=kind,
        required_capabilities=(capability,),
        requested_reads=reads, requested_writes=writes, argv=argv,
        approval_class=approval, expected_side_effects=writes, validator_refs=("bounded",),
        timeout_seconds=3, max_output_bytes=2048, idempotency_key=idem, rollback_class=rollback,
        reason_summary="offline pilot action", source_plan_hash="0" * 64, payload=payload, network_requested=False,
    )


def _bind(packets: tuple[ExecutionPacket, ...]) -> tuple[ExecutionPacket, ...]:
    digest = action_plan_hash(packets)
    return tuple(replace(packet, source_plan_hash=digest) for packet in packets)


def _base_spec(*, run_id: str, root: Path, packets: tuple[ExecutionPacket, ...], validator: dict[str, Any], faults: dict[str, str] | None = None) -> R1RunSpec:
    return R1RunSpec(
        run_id=run_id, profile_ref=f"profile-{run_id}",
        goal={"statement": "complete a bounded offline local task", "success_conditions": ["typed validation passes"], "prohibited_actions": ["network"]},
        workspace=WorkspacePolicy(
            workspace_root=str(root), allowed_read_roots=(".",), allowed_write_roots=(".",),
            allowed_executables=(sys.executable,), timeout_seconds=3, max_output_bytes=2048,
        ), capability_scope={
            "scope_id": f"scope-{run_id}",
            "allowed_capabilities": ["read.files", "write.files", "run.commands"],
            "network_allowed": False,
        }, actions=packets, reasoner={"type": "scripted", "frame_summary": "offline local pilot"},
        executor={"type": "local_workspace", "class_id": "local-workspace-executor"},
        validator=validator, lease_ttl_seconds=30, fault_injection=faults or {},
    )


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_pilot_a(output_dir: str | Path) -> dict[str, Any]:
    """Approve a real write, then approve an allowlisted local validator command."""

    output_dir = Path(output_dir)
    root = output_dir / "pilot-a-workspace"
    run_dir = output_dir / "pilot-a-run"
    root.mkdir(parents=True, exist_ok=True)
    (root / "input.txt").write_text("pilot-a-input\n", encoding="utf-8")
    read = _packet(
        run_id="pilot-a", action_id="action-read", step_id="step-read", kind="READ_FILE",
        reads=("input.txt",), writes=(), approval=ApprovalClass.AUTO_ALLOWED_SAFE.value,
        rollback=RollbackClass.NONE.value, payload={"path": "input.txt"}, idem="pilot-a-read-v1",
    )
    write = _packet(
        run_id="pilot-a", action_id="action-write", step_id="step-write", kind="WRITE_FILE",
        reads=("input.txt",), writes=("output.txt",), approval=ApprovalClass.BOUNDED_WRITE_REQUIRES_APPROVAL.value,
        rollback=RollbackClass.ROLLBACKABLE_LOCAL_FILE.value, payload={"path": "output.txt", "content": "pilot-a-output\n"}, idem="pilot-a-write-v1",
    )
    check = _packet(
        run_id="pilot-a", action_id="action-check", step_id="step-check", kind="RUN_COMMAND",
        reads=("output.txt",), writes=(), argv=(sys.executable, "-c", "raise SystemExit(__import__('pathlib').Path('output.txt').read_text() != 'pilot-a-output\\n')"),
        approval=ApprovalClass.COMMAND_REQUIRES_APPROVAL.value, rollback=RollbackClass.NOT_SUPPORTED_R1.value,
        payload={}, idem="pilot-a-check-v1",
    )
    packets = _bind((read, write, check))
    spec = _base_spec(run_id="pilot-a", root=root, packets=packets, validator={"type": "command_exit"})
    runtime = AgentRuntimeR1(run_dir)
    waiting_write = runtime.start(spec)
    if (root / "output.txt").exists() or waiting_write["terminal"]["state"] != StopState.WAITING_FOR_APPROVAL.value:
        raise AssertionError("pilot A wrote before approval")
    waiting_check = runtime.approve("approval-action-write", "ALLOW", authority_id="pilot-a-human", authority_type="synthetic_pilot")
    if waiting_check["terminal"]["state"] != StopState.WAITING_FOR_APPROVAL.value:
        raise AssertionError("pilot A did not request command approval")
    final = runtime.approve("approval-action-check", "ALLOW", authority_id="pilot-a-human", authority_type="synthetic_pilot")
    if final["terminal"]["state"] != StopState.COMPLETED_VALIDATED.value:
        raise AssertionError("pilot A did not complete")
    receipt = {
        "pilot": "A",
        "final_state": final["terminal"]["state"],
        "output_sha256": _hash_file(root / "output.txt"),
        "command_validation": final["validations"][-1],
        "approval_request_ids": [item["request_id"] for item in final["approval_events"]],
        "knowledge_paths_visible": False,
        "network_allowed": spec.workspace.network_allowed,
        "hidden_reasoning_persisted": False,
        "live_model_pilot": "LIVE_MODEL_PILOT_NOT_RUN",
        "remote_mutation": False,
        "executor_history": final["executor_history"],
        "state_sha256": final["state_sha256"],
    }
    _atomic_json(output_dir / "pilot-a-receipt.json", receipt)
    return receipt


def run_pilot_b(output_dir: str | Path) -> dict[str, Any]:
    """Recover a post-execute crash, then roll back a failed second write."""

    output_dir = Path(output_dir)
    root = output_dir / "pilot-b-workspace"
    run_dir = output_dir / "pilot-b-run"
    root.mkdir(parents=True, exist_ok=True)
    (root / "state.txt").write_text("pilot-b-original\n", encoding="utf-8")
    first = _packet(
        run_id="pilot-b", action_id="action-first", step_id="step-first", kind="WRITE_FILE",
        reads=("state.txt",), writes=("step1.txt",), approval=ApprovalClass.BOUNDED_WRITE_REQUIRES_APPROVAL.value,
        rollback=RollbackClass.ROLLBACKABLE_LOCAL_FILE.value, payload={"path": "step1.txt", "content": "pilot-b-first\n"}, idem="pilot-b-first-v1",
    )
    second = _packet(
        run_id="pilot-b", action_id="action-second", step_id="step-second", kind="WRITE_FILE",
        reads=("state.txt",), writes=("bad.txt",), approval=ApprovalClass.BOUNDED_WRITE_REQUIRES_APPROVAL.value,
        rollback=RollbackClass.ROLLBACKABLE_LOCAL_FILE.value, payload={"path": "bad.txt", "content": "pilot-b-invalid\n"}, idem="pilot-b-second-v1",
    )
    packets = _bind((first, second))
    spec = _base_spec(
        run_id="pilot-b", root=root, packets=packets,
        validator={"type": "scripted", "fail_action_ids": ["action-second"]},
        faults={"action-first": "post_execute_before_persist"},
    )
    runtime = AgentRuntimeR1(run_dir)
    runtime.start(spec)
    try:
        runtime.approve("approval-action-first", "ALLOW", authority_id="pilot-b-human", authority_type="synthetic_pilot")
    except CrashInjected:
        pass
    else:
        raise AssertionError("pilot B did not inject the requested crash")
    resumed = AgentRuntimeR1(run_dir, executor_class_id="local-workspace-executor-v2", executor_instance_id="instance-2")
    waiting_second = resumed.resume()
    if waiting_second["terminal"]["state"] != StopState.WAITING_FOR_APPROVAL.value:
        raise AssertionError("pilot B did not resume to the second approval")
    final = resumed.approve("approval-action-second", "ALLOW", authority_id="pilot-b-human", authority_type="synthetic_pilot")
    if final["terminal"]["state"] != StopState.FAILED_VALIDATION_ROLLED_BACK.value:
        raise AssertionError("pilot B did not enter the rolled-back validation stop")
    if not (root / "step1.txt").is_file() or (root / "bad.txt").exists() or (root / "state.txt").read_text(encoding="utf-8") != "pilot-b-original\n":
        raise AssertionError("pilot B workspace was not in the expected bounded state")
    journal = resumed.journal.records()
    receipt = {
        "pilot": "B",
        "final_state": final["terminal"]["state"],
        "first_output_sha256": _hash_file(root / "step1.txt"),
        "source_state_sha256": _hash_file(root / "state.txt"),
        "bad_output_absent": not (root / "bad.txt").exists(),
        "knowledge_paths_visible": False,
        "network_allowed": spec.workspace.network_allowed,
        "hidden_reasoning_persisted": False,
        "live_model_pilot": "LIVE_MODEL_PILOT_NOT_RUN",
        "remote_mutation": False,
        "journal": [{"action_id": item["action_id"], "status": item["status"]} for item in journal],
        "executor_history": final["executor_history"],
        "lease_records": [item.status for item in resumed.leases.list()],
        "state_sha256": final["state_sha256"],
    }
    _atomic_json(output_dir / "pilot-b-receipt.json", receipt)
    return receipt


def validate_pilots(output_dir: str | Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    a = json.loads((output_dir / "pilot-a-receipt.json").read_text(encoding="utf-8"))
    b = json.loads((output_dir / "pilot-b-receipt.json").read_text(encoding="utf-8"))
    if a["final_state"] != StopState.COMPLETED_VALIDATED.value or b["final_state"] != StopState.FAILED_VALIDATION_ROLLED_BACK.value:
        raise AssertionError("pilot terminal states do not match the R1 contract")
    return {"status": "PASS", "pilots": [a, b], "receipt_sha256": sha256_json({"a": a, "b": b})}
