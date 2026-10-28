#!/usr/bin/env python3
"""Freeze the no-inference admission gate for Task139's single live attempt."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import argparse
import hashlib
import json
from pathlib import Path
import stat
import tempfile
from typing import Any, Sequence

try:
    from agent_federation.live_admission import LiveCapabilityAdmission
    from agent_federation.live_bridge import LIVE_DISPATCH_SCHEMA, LiveCapabilityLease, LiveDispatchEnvelope
    from agent_federation.live_child_guard import CHILD_ENV_ALLOWLIST, LiveChildContext, LiveChildGuardError
    from agent_federation.live_pilot import DisposableLiveFixture, LivePilotValidator
    from agent_federation.live_transport import LiveProcessTransport, LiveTransportError, auth_source_metadata_digest
    from agent_federation.live_current_projection import validate_projection
    from agent_federation.local_executor_census import validate_path
except ImportError:  # direct execution with ignition/tools on sys.path
    from live_admission import LiveCapabilityAdmission
    from live_bridge import LIVE_DISPATCH_SCHEMA, LiveCapabilityLease, LiveDispatchEnvelope
    from live_child_guard import CHILD_ENV_ALLOWLIST, LiveChildContext, LiveChildGuardError
    from live_pilot import DisposableLiveFixture, LivePilotValidator
    from live_transport import LiveProcessTransport, LiveTransportError, auth_source_metadata_digest
    from live_current_projection import validate_projection
    from local_executor_census import validate_path


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
TASK_ID = "IGNITION-20260825-139"
FORMAL_SHA = "12205be8ad94916a39253e0eba2106bf5da9da12"
CONTROL_TIP = "e80d7c4aeb70ae44edbd340fc2f341c7a6a737d4"
CODEX = Path("/Users/zhiyuan/.local/bin/codex")
AUTH_SOURCE = Path("/Users/zhiyuan/.codex/auth.json")
CONTROL_REPO = Path("/Users/zhiyuan/Agent 工作区/1111-sync")
# The broad Documents tree contains unrelated symlinked tool environments.  A
# bounded persistent user-document root is required by the filesystem contract;
# this note root is observed by metadata only and is never read or copied.
DOCUMENT_ROOT = Path("/Users/zhiyuan/我的笔记")


class LiveAdmissionGateError(RuntimeError):
    """Raised when a no-inference admission check is not proven."""


class RecordingTransport:
    """Record public probe calls while delegating to the bounded transport."""

    supports_runtime_scratch = True
    supports_durable_capture = True

    def __init__(self, delegate: LiveProcessTransport) -> None:
        self.delegate = delegate
        self.calls: list[tuple[str, ...]] = []

    def run(self, argv: Sequence[str], **kwargs: Any) -> Any:
        self.calls.append(tuple(argv))
        return self.delegate.run(argv, **kwargs)


def _now() -> tuple[str, str]:
    current = datetime.now(timezone.utc).replace(microsecond=0)
    return current.isoformat().replace("+00:00", "Z"), (current + timedelta(minutes=15)).isoformat().replace("+00:00", "Z")


def _schema_path(fixture: DisposableLiveFixture) -> Path:
    path = fixture.root.parent / (fixture.root.name + "-output-schema.json")
    path.write_text(
        json.dumps({
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["nonce", "line_count", "field_value", "checksum_prefix"],
            "properties": {
                "nonce": {"type": "string", "pattern": "^[a-f0-9]{24}$"},
                "line_count": {"type": "integer", "minimum": 1},
                "field_value": {"type": "string", "minLength": 1},
                "checksum_prefix": {"type": "string", "pattern": "^[a-f0-9]{8}$"},
            },
        }, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    return path


def _envelope(
    lease: LiveCapabilityLease,
    fixture: DisposableLiveFixture,
    schema_path: Path,
    observed_at: str,
    expires_at: str,
    *,
    dispatch_id: str = "dispatch-139-live-01",
    attempt_id: str = "attempt-139-live-01",
    phase: str = "step10-admission-only",
) -> LiveDispatchEnvelope:
    synthetic_ref = "fixture://IGNITION-20260825-139"
    return LiveDispatchEnvelope(
        schema_version=LIVE_DISPATCH_SCHEMA,
        task_id=TASK_ID,
        dispatch_id=dispatch_id,
        attempt_id=attempt_id,
        executor_id="external.codex",
        adapter_id="codex-live-r3",
        capability_id="live.readonly.synthetic",
        capability_lease_ref=lease.lease_id,
        workspace_ref="DISPOSABLE_TASK139_SYNTHETIC_FIXTURE",
        workspace_mode="DISPOSABLE_SYNTHETIC_READ_ONLY",
        permission_ceiling=("repo.read",),
        side_effect_class="READ_ONLY_SYNTHETIC",
        network_class="INFERENCE_TRANSPORT_ONLY",
        intent_capsule_ref=None,
        synthetic_input_ref=synthetic_ref,
        synthetic_input_digest=hashlib.sha256(synthetic_ref.encode("utf-8")).hexdigest(),
        success_criteria=("return the exact public result described by the disposable synthetic fixture",),
        output_contract={
            "format": "json",
            "required_fields": ["nonce", "line_count", "field_value", "checksum_prefix"],
            "strict_output_schema": True,
            "schema_path": str(schema_path),
        },
        deadline=expires_at,
        timeout_seconds=90,
        retry_policy="NO_BLIND_RETRY",
        reconciliation_policy="REQUIRE_ON_TIMEOUT_OR_UNKNOWN_EFFECT",
        budget_authority="NO_NEW_BILLING_AUTHORITY",
        provenance={"controller": "pointfire-os", "task": TASK_ID, "phase": phase},
    )


def run_gate() -> dict[str, Any]:
    census_path = ROOT / "data/operations/iterations/139/local-executor-census-r1.json"
    census = validate_path(census_path, expected_task_id=TASK_ID, expected_step="09")
    if census["selected_executor_id"] != "external.codex" or census["selection_status"] != "SELECTED":
        raise LiveAdmissionGateError("fresh census did not select the admitted Codex candidate")
    projection = json.loads((ROOT / "data/operations/iterations/139/live-current-projection-r1.json").read_text(encoding="utf-8"))
    projection_summary = validate_projection(projection)
    if projection["obligation"]["state"] != "OPEN" or projection["counts"]["validated_completion_count"] != 0:
        raise LiveAdmissionGateError("Current live projection does not retain the open no-completion obligation")
    observed_at, expires_at = _now()
    with tempfile.TemporaryDirectory(prefix="ignition-139-admission-") as directory:
        root = Path(directory)
        workspace_parent = root / "fixture-parent"
        runtime_parent = root / "runtime-parent"
        capture_parent = root / "capture-parent"
        for path in (workspace_parent, runtime_parent, capture_parent):
            path.mkdir()
        fixture = DisposableLiveFixture.create(workspace_parent, nonce="abcdef0123456789abcdef01")
        schema_path = _schema_path(fixture)
        try:
            fixture.make_read_only()
            if not fixture.read_only_guard_observed():
                raise LiveAdmissionGateError("synthetic workspace read-only guard was not observed")
            transport = RecordingTransport(LiveProcessTransport(
                executable_allowlist=(str(CODEX),),
                env_allowlist=CHILD_ENV_ALLOWLIST,
                output_cap_bytes=128 * 1024,
                capture_output_cap_bytes=16 * 1024 * 1024,
            ))
            adapter = __import__("agent_federation.live_adapters", fromlist=["LiveCodexAdapter"]).LiveCodexAdapter(
                fixture.root,
                executable=str(CODEX),
                transport=transport,
                authentication_observed=True,
                adapter_id="codex-live-r3",
                child_context=LiveChildContext(depth=0),
                runtime_scratch_required=True,
                runtime_scratch_parent=runtime_parent,
                capture_parent=capture_parent,
                formal_repo=REPO_ROOT,
                control_repo=CONTROL_REPO,
                persistent_user_document_roots=(DOCUMENT_ROOT,),
                auth_source_path=AUTH_SOURCE,
                auth_source_ref="auth://codex-login-status",
            )
            lease = adapter.observe_lease(
                lease_id="lease-ignition-139-codex-live-01",
                observed_at=observed_at,
                expires_at=expires_at,
                ttl_seconds=900,
            )
            if lease.live_eligibility != "ELIGIBLE_FOR_LIVE_READONLY":
                raise LiveAdmissionGateError("Codex public lease was not eligible: " + ",".join(lease.eligibility_blockers))
            filesystem_probe = adapter._new_runtime_scratch("admission-139-probe")
            try:
                adapter._filesystem_domains(
                    filesystem_probe,
                    workspace_before=fixture.before_digest,
                    workspace_after=fixture.before_digest,
                    scratch_after=filesystem_probe.before_digest,
                    validate_paths=True,
                )
            finally:
                if filesystem_probe.cleanup() != "CLEANED":
                    raise LiveAdmissionGateError("filesystem admission probe did not prove scratch cleanup")
            envelope = _envelope(lease, fixture, schema_path, observed_at, expires_at)
            argv = adapter.build_argv(envelope)
            admission = LiveCapabilityAdmission().admit(
                envelope,
                lease,
                os_granted=("repo.read",),
                executor_declared=("repo.read", "structured_progress"),
                now_observed=observed_at,
                current_binary_digest=lease.binary_digest,
                current_interface_digest=lease.interface_digest,
            )
            if admission.status != "ADMITTED" or admission.effective_capabilities != ("repo.read",):
                raise LiveAdmissionGateError("strict OS capability intersection was not admitted")
            child = adapter.child_context.issue_child(fixture.root)
            child_env = child.child_environment({"PATH": "/Users/zhiyuan/.local/bin:/usr/bin", "CODEX_HOME": str(AUTH_SOURCE)})
            try:
                child.issue_child(fixture.root)
            except LiveChildGuardError:
                child_depth_guard = "PASS_ONE_LEVEL_ONLY"
            else:
                raise LiveAdmissionGateError("child depth guard allowed recursive Agent spawn")
            if child_env.get("HOME") != str(fixture.root) or child_env.get("TMPDIR") != str(fixture.root) or child_env.get("CODEX_HOME") != str(AUTH_SOURCE):
                raise LiveAdmissionGateError("child environment did not separate disposable HOME/TMP from read-only CODEX_HOME")
            required_flags = {"--json", "--ephemeral", "--ignore-user-config", "--ignore-rules", "--sandbox", "read-only", "--output-schema", "--cd"}
            if not required_flags <= set(argv):
                raise LiveAdmissionGateError("Codex argv lacks one or more required bounded flags")
            forbidden_tokens = {"--add-dir", "workspace-write", "dangerously-bypass-approvals-and-sandbox"}
            if forbidden_tokens & set(argv):
                raise LiveAdmissionGateError("unsafe Codex argv token reached admission")
            validator = LivePilotValidator(
                fixture,
                task_id=TASK_ID,
                dispatch_id=envelope.dispatch_id,
                attempt_id=envelope.attempt_id,
                executor_id=envelope.executor_id,
            )
            expected = {
                "nonce": fixture.expectation.nonce,
                "line_count": fixture.expectation.line_count,
                "field_value": fixture.expectation.field_value,
                "checksum_prefix": fixture.expectation.checksum_prefix,
            }
            validator_self_test = validator.validate(expected, before_digest=fixture.before_digest, after_digest=fixture.before_digest)
            if validator_self_test.status != "PASS":
                raise LiveAdmissionGateError("independent validator freeze self-test failed")
            auth_digest = auth_source_metadata_digest(AUTH_SOURCE)
            return {
                "schema_version": "ignition-139-step10-live-admission-r1",
                "task_id": TASK_ID,
                "status": "PASS",
                "census": census,
                "current_projection": projection_summary,
                "lease": lease.to_dict(),
                "admission": {
                    "status": admission.status,
                    "effective_capabilities": list(admission.effective_capabilities),
                    "reason": admission.reason,
                },
                "dispatch": {
                    "dispatch_id": envelope.dispatch_id,
                    "attempt_id": envelope.attempt_id,
                    "executor_id": envelope.executor_id,
                    "adapter_id": envelope.adapter_id,
                    "capability_lease_ref": envelope.capability_lease_ref,
                    "workspace_mode": envelope.workspace_mode,
                    "permission_ceiling": list(envelope.permission_ceiling),
                    "side_effect_class": envelope.side_effect_class,
                    "network_class": envelope.network_class,
                    "timeout_seconds": envelope.timeout_seconds,
                    "retry_policy": envelope.retry_policy,
                    "budget_authority": envelope.budget_authority,
                    "argv_shape": [
                        "<CODEX>" if item == str(CODEX)
                        else "<DISPOSABLE_WORKSPACE>" if item == str(fixture.root)
                        else "<OUTPUT_SCHEMA>" if item == str(schema_path)
                        else item.replace(str(fixture.root), "<DISPOSABLE_WORKSPACE>").replace(str(schema_path), "<OUTPUT_SCHEMA>")
                        if isinstance(item, str) else item
                        for item in argv
                    ],
                    "inference_started": False,
                },
                "filesystem": {
                    "task_workspace_mode": "DISPOSABLE_READ_ONLY",
                    "runtime_scratch_mode": "ATTEMPT_EPHEMERAL_WRITABLE",
                    "capture_mode": "HOST_DURABLE_SPOOL_DEFERRED_CLEANUP",
                    "runtime_parent_separate_from_capture_parent": runtime_parent.resolve() != capture_parent.resolve(),
                    "auth_source_mode": "READ_ONLY_REFERENCE",
                    "auth_source_metadata_digest": auth_digest,
                    "auth_source_content_read": False,
                    "auth_source_copied": False,
                    "config_mutation_allowed": False,
                    "workspace_read_only_guard": fixture.read_only_guard_observed(),
                    "runtime_filesystem_domains_validated": True,
                },
                "child_depth_guard": child_depth_guard,
                "durable_capture_support": transport.supports_durable_capture,
                "runtime_scratch_support": transport.supports_runtime_scratch,
                "probe_calls": len(transport.calls),
                "probe_argv": [["<CODEX>" if item == str(CODEX) else item for item in call] for call in transport.calls],
                "validator_freeze": {
                    "status": validator_self_test.status,
                    "task_id": TASK_ID,
                    "dispatch_id": envelope.dispatch_id,
                    "attempt_id": envelope.attempt_id,
                    "executor_id": envelope.executor_id,
                    "schema_fields": ["nonce", "line_count", "field_value", "checksum_prefix"],
                    "self_test_is_not_live_result": True,
                },
                "claim_ceiling": "Task139 repository-local live admission, capability lease, synthetic fixture and independent validator freeze evidence only; no external process inference, live completion, external truth, production readiness, Owner acceptance or epistemic acceptance is inferred.",
            }
        finally:
            if schema_path.exists():
                schema_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
                schema_path.unlink()
            fixture.cleanup()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    try:
        report = run_gate()
    except (LiveAdmissionGateError, LiveTransportError, OSError, ValueError) as exc:
        print(f"LIVE_ADMISSION_GATE_INVALID\n- {type(exc).__name__}: {exc}")
        return 1
    print("LIVE_ADMISSION_GATE_OK selected=external.codex probes=" + str(report["probe_calls"]) + " inference_started=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
