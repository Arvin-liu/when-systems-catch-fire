"""R2 offline multi-Run repository-maintenance episode.

The pilot prepares a disposable local source repository and a fresh local
clone before the Supervisor starts. The child runs themselves have
``network_allowed=False`` and no remote-mutation capability. Their receipts
are intentionally sanitized: temporary paths and private clone URLs never
enter the committed evidence.
"""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Mapping

from ..actions import ApprovalClass, ExecutionPacket, RollbackClass, WorkspacePolicy
from ..control import _atomic_json
from ..memory import MemoryEntry, OperationalMemoryStore
from ..profile import load_profile_registry
from ..supervisor import ChildRunSpec, EpisodeBudget, EpisodeSpec, Supervisor
from ..transport import AdversarialGatewayAdapter, GatewayError, GatewayRequest, ReasonerGateway, action_plan_hash
from ..r1_runtime import R1RunSpec


PILOT_ID = "r2-offline-repository-maintenance"
EXECUTOR_CLASS = "local-workspace-executor"
ROOT = Path(__file__).resolve().parents[2]


def _packet(
    *, run_id: str, action_id: str, step_id: str, kind: str,
    reads: tuple[str, ...], writes: tuple[str, ...], argv: tuple[str, ...] = (),
    approval: str, rollback: str, payload: dict[str, Any], idem: str,
    network_requested: bool = False,
) -> ExecutionPacket:
    capability = {
        "READ_FILE": "read.files",
        "PATCH_TEXT_FILE": "write.files",
        "WRITE_FILE": "write.files",
        "RUN_COMMAND": "run.commands",
    }[kind]
    return ExecutionPacket(
        run_id=run_id, step_id=step_id, action_id=action_id, kind=kind,
        required_capabilities=(capability,), requested_reads=reads,
        requested_writes=writes, argv=argv, approval_class=approval,
        expected_side_effects=writes, validator_refs=("bounded",),
        timeout_seconds=5, max_output_bytes=8192, idempotency_key=idem,
        rollback_class=rollback, reason_summary="R2 offline repository maintenance pilot action",
        source_plan_hash="0" * 64, payload=payload, network_requested=network_requested,
    )


def _bind(packets: tuple[ExecutionPacket, ...]) -> tuple[ExecutionPacket, ...]:
    digest = action_plan_hash(packets)
    return tuple(replace(packet, source_plan_hash=digest) for packet in packets)


def _workspace_spec(
    *, run_id: str, root: Path, packets: tuple[ExecutionPacket, ...], faults: Mapping[str, str] | None = None,
    reasoner: Mapping[str, Any] | None = None, allowed_capabilities: tuple[str, ...] = ("read.files", "write.files", "run.commands"),
) -> R1RunSpec:
    return R1RunSpec(
        run_id=run_id,
        profile_ref="repository-maintainer",
        goal={
            "statement": "maintain one disposable local repository under a bounded offline contract",
            "success_conditions": ["typed audit, repair and validation receipts are present"],
            "prohibited_actions": ["network", "remote Git mutation", "deletion", "self-approved authority"],
        },
        workspace=WorkspacePolicy(
            workspace_root=str(root), allowed_read_roots=(".",), allowed_write_roots=(".",),
            allowed_executables=(sys.executable,), timeout_seconds=5, max_output_bytes=8192,
            max_actions=8, max_writes=8, network_allowed=False,
        ),
        capability_scope={
            "scope_id": f"scope-{run_id}",
            "allowed_capabilities": list(allowed_capabilities),
            "network_allowed": False,
        },
        actions=packets,
        reasoner=reasoner or {
            "type": "gateway-scripted",
            "available_packs": ["maintenance.repository"],
            "context_capsule": ["offline disposable repository maintenance"],
        },
        executor={"type": "local_workspace", "class_id": EXECUTOR_CLASS},
        validator={"type": "command_exit"},
        lease_ttl_seconds=30,
        fault_injection=dict(faults or {}),
    )


def _child(run_id: str, spec: R1RunSpec, *, depends_on: tuple[str, ...] = (), executor_instance_id: str = "instance-1") -> ChildRunSpec:
    return ChildRunSpec(
        run_id=run_id, run_spec=spec, depends_on=depends_on,
        retry_limit=0, executor_instance_id=executor_instance_id,
        executor_class_id=EXECUTOR_CLASS,
    )


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)
    return completed.stdout.strip()


def _prepare_fresh_clone(root: Path) -> tuple[Path, str, str]:
    source = root / "source-repository"
    clone = root / "fresh-clone"
    source.mkdir(parents=True)
    _git(source, "init", "-q")
    _git(source, "config", "user.email", "r2-pilot@example.invalid")
    _git(source, "config", "user.name", "R2 Offline Pilot")
    (source / "README.md").write_text("bounded offline maintenance fixture\n", encoding="utf-8")
    manifest = {"entries": [{"id": "readme", "target": "README.md"}]}
    (source / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    _git(source, "add", "README.md", "manifest.json")
    _git(source, "commit", "-qm", "fixture baseline")
    source_head = _git(source, "rev-parse", "HEAD")
    subprocess.run(["git", "clone", "--no-local", str(source), str(clone)], check=True, capture_output=True, text=True)
    clone_head = _git(clone, "rev-parse", "HEAD")
    if clone_head != source_head:
        raise AssertionError("fresh clone did not preserve the prepared baseline commit")
    return clone, source_head, clone_head


def _build_episode(clone: Path, episode_dir: Path) -> tuple[EpisodeSpec, dict[str, str]]:
    readme_hash = hashlib.sha256((clone / "README.md").read_bytes()).hexdigest()
    audit_code = """
import hashlib
import json
from pathlib import Path
manifest_path = Path('manifest.json')
manifest = json.loads(manifest_path.read_text())
issues = []
for entry in manifest.get('entries', []):
    target = entry.get('target')
    if not Path(target).is_file():
        issues.append({'type': 'MISSING_TARGET', 'target': target})
    elif 'sha256' not in entry:
        issues.append({'type': 'MISSING_HASH', 'target': target})
findings = {'issues': issues, 'repair_allowed': ['add_hash'], 'manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest()}
Path('audit-findings.json').write_text(json.dumps(findings, sort_keys=True) + '\\n')
raise SystemExit(0 if issues else 1)
""".strip()
    validate_code = """
import hashlib
import json
from pathlib import Path
manifest = json.loads(Path('manifest.json').read_text())
findings = json.loads(Path('audit-findings.json').read_text())
valid = len(findings.get('issues', [])) == 1 and findings['issues'][0] == {'target': 'README.md', 'type': 'MISSING_HASH'}
valid = valid and manifest['entries'][0].get('sha256') == hashlib.sha256(Path('README.md').read_bytes()).hexdigest()
report = {'status': 'PASS' if valid else 'FAIL', 'manifest_sha256': hashlib.sha256(Path('manifest.json').read_bytes()).hexdigest(), 'network': False, 'remote_mutation': False}
Path('validation-report.json').write_text(json.dumps(report, sort_keys=True) + '\\n')
raise SystemExit(0 if valid else 1)
""".strip()
    audit = _bind((
        _packet(
            run_id="audit", action_id="audit-findings", step_id="audit",
            kind="RUN_COMMAND", reads=("manifest.json", "README.md"), writes=("audit-findings.json",),
            argv=(sys.executable, "-c", f"exec({audit_code!r})"),
            approval=ApprovalClass.COMMAND_REQUIRES_APPROVAL.value,
            rollback=RollbackClass.NOT_SUPPORTED_R1.value, payload={}, idem="audit-findings-v1",
        ),
    ))
    repair_read = _packet(
        run_id="repair", action_id="repair-read-findings", step_id="repair-read",
        kind="READ_FILE", reads=("audit-findings.json",), writes=(),
        approval=ApprovalClass.AUTO_ALLOWED_SAFE.value, rollback=RollbackClass.NONE.value,
        payload={"path": "audit-findings.json"}, idem="repair-read-findings-v1",
    )
    repair_patch = _packet(
        run_id="repair", action_id="repair-manifest", step_id="repair-patch",
        kind="PATCH_TEXT_FILE", reads=("manifest.json", "audit-findings.json", "README.md"), writes=("manifest.json",),
        approval=ApprovalClass.BOUNDED_WRITE_REQUIRES_APPROVAL.value,
        rollback=RollbackClass.ROLLBACKABLE_LOCAL_FILE.value,
        payload={
            "path": "manifest.json",
            "find": '"target": "README.md"',
            "replace": f'"target": "README.md", "sha256": "{readme_hash}"',
            "expected_sha256": hashlib.sha256((clone / "manifest.json").read_bytes()).hexdigest(),
        },
        idem="repair-manifest-v1",
    )
    repair_receipt = _packet(
        run_id="repair", action_id="repair-receipt", step_id="repair-receipt",
        kind="WRITE_FILE", reads=("audit-findings.json", "manifest.json"), writes=("repair-receipt.json",),
        approval=ApprovalClass.BOUNDED_WRITE_REQUIRES_APPROVAL.value,
        rollback=RollbackClass.ROLLBACKABLE_LOCAL_FILE.value,
        payload={"path": "repair-receipt.json", "content": json.dumps({"approved_finding": "MISSING_HASH", "repair": "add README sha256", "remote_mutation": False}, sort_keys=True) + "\n"},
        idem="repair-receipt-v1",
    )
    repair = _bind((repair_read, repair_patch, repair_receipt))
    validate = _bind((
        _packet(
            run_id="validate", action_id="validate-repository", step_id="validate",
            kind="RUN_COMMAND", reads=("manifest.json", "audit-findings.json", "repair-receipt.json", "README.md"),
            writes=("validation-report.json",), argv=(sys.executable, "-c", f"exec({validate_code!r})"),
            approval=ApprovalClass.COMMAND_REQUIRES_APPROVAL.value,
            rollback=RollbackClass.NOT_SUPPORTED_R1.value, payload={}, idem="validate-repository-v1",
        ),
    ))
    specs = {
        "audit": _workspace_spec(run_id="audit", root=clone, packets=audit),
        "repair": _workspace_spec(run_id="repair", root=clone, packets=repair, faults={"repair-manifest": "post_execute_before_persist"}),
        "validate": _workspace_spec(run_id="validate", root=clone, packets=validate),
    }
    episode = EpisodeSpec(
        episode_id=PILOT_ID,
        job_id="job-r2-repository-maintenance",
        created_by="owner:human",
        capability_scope_id="episode-r2-offline-maintenance",
        allowed_capabilities=("read.files", "write.files", "run.commands"),
        budget=EpisodeBudget(max_actions=8, max_seconds=120, max_output_bytes=30000),
        children=(
            _child("audit", specs["audit"]),
            _child("repair", specs["repair"], depends_on=("audit",)),
            _child("validate", specs["validate"], depends_on=("repair",)),
        ),
        policy="FAIL_FAST", network_allowed=False,
    )
    return episode, {"audit": "approval-audit-findings", "repair_patch": "approval-repair-manifest", "repair_receipt": "approval-repair-receipt", "validate": "approval-validate-repository"}


def _approve(supervisor: Supervisor, run_id: str, request_id: str, *, reason: str) -> dict[str, Any]:
    return supervisor.approve(
        run_id, request_id, "ALLOW", authority_id="owner:human",
        authority_type="synthetic_pilot", reason_summary=reason,
    )


def _sanitized_episode_state(state: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "terminal": state.get("terminal"),
        "checkpoint_count": state.get("checkpoint_count"),
        "approval_events": state.get("approval_events", []),
        "handoffs": state.get("handoffs", []),
        "budget_usage": state.get("budget_usage"),
        "children": [
            {
                "run_id": child["run_id"], "status": child["status"],
                "terminal_state": child.get("terminal_state"),
                "attempt": child.get("attempt"), "retry_count": child.get("retry_count"),
                "executor_instance_id": child.get("executor_instance_id"),
                "executor_class_id": child.get("executor_class_id"),
                "history": child.get("history", []),
            }
            for child in state.get("children", [])
        ],
        "trace_event_types": [item.get("event_type") for item in state.get("trace", [])],
    }


def _adversarial_episode(root: Path) -> dict[str, Any]:
    workspace = root / "adversarial-workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "tracked.txt").write_text("must survive adversarial proposals\n", encoding="utf-8")
    network = _bind((
        _packet(
            run_id="adversarial-network", action_id="request-network", step_id="network",
            kind="RUN_COMMAND", reads=("tracked.txt",), writes=(),
            argv=(sys.executable, "-c", "print('network proposal denied')"),
            approval=ApprovalClass.AUTO_ALLOWED_SAFE.value, rollback=RollbackClass.NONE.value,
            payload={}, idem="adversarial-network-v1", network_requested=True,
        ),
    ))
    remote_delete = _bind((
        _packet(
            run_id="adversarial-remote-delete", action_id="request-remote-delete", step_id="remote-delete",
            kind="RUN_COMMAND", reads=("tracked.txt",), writes=(),
            argv=("git", "push", "origin", "main"),
            approval=ApprovalClass.AUTO_ALLOWED_SAFE.value, rollback=RollbackClass.NONE.value,
            payload={}, idem="adversarial-remote-delete-v1",
        ),
    ))
    episode = EpisodeSpec(
        episode_id="r2-adversarial-episode", job_id="job-r2-adversarial",
        created_by="owner:human", capability_scope_id="episode-r2-adversarial",
        allowed_capabilities=("read.files", "run.commands"),
        budget=EpisodeBudget(max_actions=4, max_seconds=60, max_output_bytes=10000),
        children=(
            _child("adversarial-network", _workspace_spec(
                run_id="adversarial-network", root=workspace, packets=network,
                allowed_capabilities=("read.files", "run.commands"),
            )),
            _child("adversarial-remote-delete", _workspace_spec(
                run_id="adversarial-remote-delete", root=workspace, packets=remote_delete,
                allowed_capabilities=("read.files", "run.commands"),
            )),
        ),
        policy="CONTINUE_INDEPENDENT", network_allowed=False,
    )
    episode_dir = root / "adversarial-episode"
    state = Supervisor(episode_dir).start(episode)
    gateway_request = GatewayRequest(
        phase="PLAN", run_id="adversarial-reasoner", goal_summary="bounded adversarial proposal",
        environment_summary="offline local workspace", capability_catalog=("read.files", "run.commands"),
        context_capsule=("offline adversarial probe",), available_packs=("maintenance.repository",),
    )
    gateway_denials: dict[str, str] = {}
    for mode in ("permission_expansion", "forged_completion"):
        try:
            ReasonerGateway(AdversarialGatewayAdapter(mode)).request(gateway_request)
        except GatewayError as exc:
            gateway_denials[mode] = str(exc)
    if set(gateway_denials) != {"permission_expansion", "forged_completion"}:
        raise AssertionError("Gateway adversarial reasoner did not fail closed")
    if state["terminal"]["state"] != "EPISODE_COMPLETED_WITH_INDEPENDENT_FAILURES":
        raise AssertionError("adversarial episode did not preserve independent failures")
    if (workspace / "tracked.txt").read_text(encoding="utf-8") != "must survive adversarial proposals\n":
        raise AssertionError("adversarial episode changed the protected file")
    return {
        "episode_id": episode.episode_id,
        "terminal_state": state["terminal"]["state"],
        "child_terminal_states": {child["run_id"]: child.get("terminal_state") for child in state["children"]},
        "gateway_denials": gateway_denials,
        "network_allowed": False,
        "remote_mutation": False,
        "delete_capability": "NOT_DECLARED",
        "protected_file_preserved": True,
    }


def run_pilot(output_dir: str | Path) -> dict[str, Any]:
    """Run the full A/B/C episode and adversarial episode into ``output_dir``."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    memory_store = OperationalMemoryStore(output_dir / "durable-memory.jsonl")
    with tempfile.TemporaryDirectory(prefix="ignition-r2-pilot-") as temporary:
        temp_root = Path(temporary)
        clone, source_head, clone_head = _prepare_fresh_clone(temp_root)
        episode_dir = temp_root / "episode"
        episode, request_ids = _build_episode(clone, episode_dir)
        profiles = load_profile_registry(ROOT / "data/agent-runtime/agent-profiles-r1.json")
        supervisor = Supervisor(episode_dir)
        first = supervisor.start(episode, profiles=profiles)
        if first["terminal"]["state"] != "EPISODE_WAITING_FOR_APPROVAL":
            raise AssertionError("audit child did not stop for typed approval")
        after_audit = _approve(supervisor, "audit", request_ids["audit"], reason="approve the typed audit command only")
        if after_audit["terminal"]["state"] != "EPISODE_WAITING_FOR_APPROVAL":
            raise AssertionError("repair child did not stop for typed approval")
        after_repair_patch = _approve(
            supervisor, "repair", request_ids["repair_patch"],
            reason="approve only the declared reversible manifest hash repair",
        )
        if after_repair_patch["terminal"]["state"] != "EPISODE_CHECKPOINTED_RESUMABLE":
            raise AssertionError("repair crash injection did not produce a Supervisor checkpoint")
        memory_store.append(MemoryEntry.create(
            memory_id="r2-episode-failure-repair-crash",
            memory_type="FAILURE", source_run_id="repair",
            summary="repair child crashed after a declared patch execute and before journal persistence",
            provenance_refs=("pilot-receipt.json",), tags=("r2", "checkpoint", "offline"),
        ))
        checkpoint = Supervisor(episode_dir)
        checkpoint_state = checkpoint.status()
        if checkpoint_state["terminal"]["state"] != "EPISODE_CHECKPOINTED_RESUMABLE":
            raise AssertionError("Supervisor did not persist a resumable checkpoint")
        checkpoint.handoff("repair", "repair-executor-instance-2")
        resumed = checkpoint.resume()
        if resumed["terminal"]["state"] != "EPISODE_WAITING_FOR_APPROVAL":
            raise AssertionError("resume did not reach the second repair approval")
        after_receipt = _approve(checkpoint, "repair", request_ids["repair_receipt"], reason="approve the bounded repair receipt after postimage reconciliation")
        if after_receipt["terminal"]["state"] != "EPISODE_WAITING_FOR_APPROVAL":
            raise AssertionError("validate child did not stop for typed approval")
        final = _approve(checkpoint, "validate", request_ids["validate"], reason="approve the allowlisted offline validation command")
        if final["terminal"]["state"] != "EPISODE_COMPLETED_VALIDATED":
            raise AssertionError("A/B/C episode did not complete validated")
        if json.loads((clone / "validation-report.json").read_text(encoding="utf-8"))["status"] != "PASS":
            raise AssertionError("validation report did not pass")
        if _git(clone, "remote", "get-url", "origin") == "":
            raise AssertionError("fresh clone lost its read-only origin metadata")
        if _git(clone, "status", "--short") == "":
            raise AssertionError("pilot did not leave a local maintenance diff")
        adversarial = _adversarial_episode(temp_root)
        final_sanitized = _sanitized_episode_state(final)
        memory_store.append(MemoryEntry.create(
            memory_id="r2-episode-completed",
            memory_type="EPISODIC", source_run_id=PILOT_ID,
            summary="A/B/C offline repository maintenance episode completed after approval, crash recovery and executor-instance handoff",
            provenance_refs=("pilot-receipt.json", "adversarial-receipt.json"), tags=("r2", "episode", "offline"),
        ))
        capsule = memory_store.export_capsule(max_entries=8, max_chars=2400, tags=("r2",))
        _atomic_json(output_dir / "memory-capsule.json", capsule)
        receipt = {
            "pilot_id": PILOT_ID,
            "episode": final_sanitized,
            "fresh_clone": {
                "prepared_before_supervisor": True,
                "source_head": source_head,
                "clone_head": clone_head,
                "head_match": source_head == clone_head,
                "network_allowed": False,
                "remote_mutation": False,
                "git_push_invoked": False,
                "post_episode_worktree_dirty": True,
                "private_paths_in_receipt": False,
            },
            "memory": {"store": "durable-memory.jsonl", "capsule": "memory-capsule.json", "failure_and_recovery_recorded": True},
            "adversarial_receipt": "adversarial-receipt.json",
            "claim_ceiling": "OFFLINE_REPOSITORY_PILOT_OBSERVED_ONLY_NOT_GENERAL_INTELLIGENCE",
        }
        _atomic_json(output_dir / "pilot-receipt.json", receipt)
        _atomic_json(output_dir / "adversarial-receipt.json", adversarial)
        return receipt


def validate_receipts(output_dir: str | Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    receipt = json.loads((output_dir / "pilot-receipt.json").read_text(encoding="utf-8"))
    adversarial = json.loads((output_dir / "adversarial-receipt.json").read_text(encoding="utf-8"))
    if receipt["episode"]["terminal"]["state"] != "EPISODE_COMPLETED_VALIDATED":
        raise AssertionError("main pilot receipt is not terminal validated")
    if receipt["episode"]["checkpoint_count"] < 1:
        raise AssertionError("main pilot receipt lacks a checkpoint")
    if not any(item["from_executor_instance_id"] != item["to_executor_instance_id"] for item in receipt["episode"]["handoffs"]):
        raise AssertionError("main pilot receipt lacks an executor-instance handoff")
    if adversarial["terminal_state"] != "EPISODE_COMPLETED_WITH_INDEPENDENT_FAILURES":
        raise AssertionError("adversarial pilot receipt lacks independent failure rollup")
    return {"status": "PASS", "main_episode": receipt["episode"]["terminal"]["state"], "adversarial_episode": adversarial["terminal_state"]}


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    if args.validate:
        print(json.dumps(validate_receipts(args.output), ensure_ascii=False, sort_keys=True))
    else:
        print(json.dumps(run_pilot(args.output), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
