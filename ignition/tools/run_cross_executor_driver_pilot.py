"""Run the bounded Cross-Executor Driver Pilot for IGNITION-20260816-123.

The pilot deliberately consumes the public Step 09 probe/smoke receipt instead
of invoking a vendor a second time.  It exercises Ignition-owned routing,
failover, validation, handoff and bounded operational-memory absorption in a
temporary disposable fixture.  No formal repository or external executor
session is used as a live target.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Mapping

from agent_federation.approval_handoff import (
    ApprovalBridge,
    ExternalApprovalObservation,
    FailoverContext,
    accept_handoff,
    build_handoff_bundle,
    decide_failover,
)
from agent_federation.contracts import (
    ExecutorDescriptor,
    ExecutorHealth,
    FederatedResultReceipt,
    HandoffEligibility,
    canonical_digest,
)
from agent_federation.convergence import FederationConvergence, project_approval, project_recovery
from agent_federation.pilots import (
    ReferenceExecutorAdapter,
    _fixture_audit,
    _pilot_envelope,
    _validated_receipt,
    _write_fixture,
)
from agent_federation.router import FederationRouter, RoutingRequest, load_routing_policy
from agent_runtime.memory import OperationalMemoryStore


TASK_ID = "IGNITION-20260816-123"
STEP = "10"
SMOKE_RELATIVE_PATH = "data/operations/iterations/123/external-conformance-smoke-r1.json"
POLICY_RELATIVE_PATH = "data/agent-federation/federation-routing-policy-r1.json"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _probe_descriptor(
    smoke: Mapping[str, Any],
    executor_id: str,
    *,
    capability_tokens: tuple[str, ...],
    granularities: tuple[str, ...],
    workspace_semantics: str,
    structured_output_support: bool,
    progress_support: bool,
    limitations: tuple[str, ...],
) -> ExecutorDescriptor:
    """Project Step 09's public probe into the router descriptor contract."""

    rows = smoke.get("executors")
    if not isinstance(rows, list):
        raise ValueError("Step 09 smoke receipt has no executor rows")
    row = next((item for item in rows if item.get("executor_id") == executor_id), None)
    if not isinstance(row, Mapping) or not isinstance(row.get("probe"), Mapping):
        raise ValueError(f"Step 09 smoke receipt lacks probe for {executor_id}")
    probe = row["probe"]
    return ExecutorDescriptor(
        executor_id=executor_id,
        family=str(probe["family"]),
        version=str(probe["observed_version"]),
        transport_kind=tuple(probe["transport_kind"]),
        availability="AVAILABLE",
        health=ExecutorHealth(
            "HEALTHY",
            str(smoke["recorded_at"]),
            "Step 09 public CLI probe; no Step 10 live retry",
        ),
        capability_tokens=capability_tokens,
        supported_task_granularities=granularities,
        workspace_semantics=workspace_semantics,
        permission_control_semantics="OBSERVED_PUBLIC_BOUNDARY_ONLY",
        structured_output_support=structured_output_support,
        progress_support=progress_support,
        cancel_support=False,
        native_resume_support=False,
        external_session_refs=(),
        network_semantics="NOT_USED_BY_STEP10_ROUTING",
        max_task_duration_seconds=5,
        adapter_version="step09-probe-projection-r1",
        limitations=limitations,
    )


def _receipt_summary(receipt: Any) -> dict[str, Any]:
    return {
        "executor_id": receipt.executor_id,
        "federation_task_id": receipt.federation_task_id,
        "terminal_state": receipt.terminal_state,
        "receipt_digest": receipt.receipt_digest,
        "validation_refs": list(receipt.validation_refs),
        "artifact_refs": [item.ref for item in receipt.artifact_refs],
        "handoff_eligible": receipt.handoff_eligibility.eligible,
    }


def build_pilot(*, recorded_at: str | None = None) -> dict[str, Any]:
    """Build one disposable, vendor-neutral driver episode and its receipt."""

    root = Path(__file__).resolve().parents[1]
    smoke = _load_json(root / SMOKE_RELATIVE_PATH)
    policy = load_routing_policy(root / POLICY_RELATIVE_PATH)
    recorded_at = recorded_at or _now()
    external_rows = []
    for row in smoke["executors"]:
        external_rows.append(
            {
                "executor_id": row["executor_id"],
                "observed_version": row["probe"]["observed_version"],
                "live_invocation": row["live_invocation"],
                "outcome": row["outcome"],
                "classification": row["classification"],
                "attempted_bounded_smoke": row["attempted_bounded_smoke"],
                "skip_reason": row.get("skip_reason", ""),
                "source_receipt": "ignition/data/operations/iterations/123/external-conformance-smoke-r1.json",
            }
        )

    hermes = _probe_descriptor(
        smoke,
        "external.hermes",
        capability_tokens=("repo.read",),
        granularities=("ACTION", "SUBTASK"),
        workspace_semantics="INHERITS_CWD_WITHOUT_HERMES_WORKTREE",
        structured_output_support=False,
        progress_support=False,
        limitations=("Step 09 bounded smoke timed out; not retried in Step 10.",),
    )
    codex = _probe_descriptor(
        smoke,
        "external.codex",
        capability_tokens=("repo.read", "structured_progress"),
        granularities=("ACTION", "SUBTASK"),
        workspace_semantics="EXPLICIT_CD_SCOPE_ONLY",
        structured_output_support=True,
        progress_support=True,
        limitations=("Step 09 bounded smoke timed out; not retried in Step 10.",),
    )
    openclaw = _probe_descriptor(
        smoke,
        "external.openclaw",
        capability_tokens=("long_task",),
        granularities=("ACTION", "SUBTASK", "EPISODE"),
        workspace_semantics="UNKNOWN_UNPROBED",
        structured_output_support=True,
        progress_support=False,
        limitations=("Step 09 unsafe-surface skip; no disposable workspace binding.",),
    )

    with TemporaryDirectory(prefix="ignition-123-step10-") as temporary_root:
        temporary_root = Path(temporary_root)
        fixture = temporary_root / "disposable-fixture"
        _write_fixture(fixture)
        source = ReferenceExecutorAdapter(fixture)
        descriptors = (hermes, codex, openclaw, source.describe())
        envelope = _pilot_envelope("step10-driver-001", idempotency_key="step10-driver-001")
        request = RoutingRequest(
            federation_task_id=envelope.federation_task_id,
            owner_ref=envelope.owner_ref,
            profile_ref=envelope.profile_ref,
            task_type="read_only",
            required_capabilities=("repo.read",),
            required_effects=("read",),
            task_granularity="ACTION",
            privacy_class="LOCAL_FIXTURE",
            workspace_locality="LOCAL",
            approval_policy=envelope.approval_policy,
        )
        initial_route = FederationRouter(policy, descriptors).route(request)
        if initial_route.selected_executor_id != "external.hermes":
            raise AssertionError("Step 10 initial route must select the compatible Hermes candidate")

        unavailable_descriptors = tuple(
            replace(
                descriptor,
                availability="UNAVAILABLE",
                health=replace(
                    descriptor.health,
                    status="UNAVAILABLE",
                    reason="Step 09 bounded live result was skipped or timed out; Step 10 does not retry.",
                ),
            )
            if descriptor.executor_id.startswith("external.")
            else descriptor
            for descriptor in descriptors
        )
        fallback_route = FederationRouter(policy, unavailable_descriptors).route(request)
        if fallback_route.selected_executor_id != source.executor_id:
            raise AssertionError("Step 10 fallback route must select the bounded Reference Executor")

        approval = ApprovalBridge().evaluate(
            envelope.approval_policy,
            envelope.required_capabilities,
            external_observation=ExternalApprovalObservation("NOT_REQUESTED"),
            external_approval_required=False,
        )
        failover = decide_failover(
            FailoverContext(
                "external.hermes",
                source.executor_id,
                "EXECUTOR_TIMEOUT",
                ("repo.read",),
                True,
                True,
                True,
                True,
            ),
            target_capabilities=source.describe().capability_tokens,
        )
        if failover.status != "AUTO_FAILOVER_ELIGIBLE":
            raise AssertionError("read-only timeout must be eligible for bounded automatic failover")

        source_event = source.dispatch(envelope)
        source_validation = _fixture_audit(fixture)
        source_receipt = _validated_receipt(source.executor_id, envelope.federation_task_id, fixture)
        bundle = build_handoff_bundle(
            handoff_id="step10-handoff-001",
            source_receipt=source_receipt,
            goal=envelope.goal,
            pending_work=("re-observe the disposable fixture and preserve the OS-owned acceptance record",),
            allowed_capabilities=("repo.read",),
            workspace_refs=("disposable-fixture/",),
            acceptance_criteria=("source files remain unchanged", "validator finds the same two issues"),
            operational_memory_capsule_refs=("step10-public-operational-capsule",),
        )
        recovery = ReferenceExecutorAdapter(fixture)
        recovery.executor_id = "reference.executor.recovery"
        takeover = accept_handoff(
            bundle,
            recovery.executor_id,
            recovery.describe().capability_tokens,
            workspace_reobserved=True,
            source_receipt_verified=True,
            observed_artifact_refs=tuple(item.ref for item in bundle.artifact_refs),
        )
        if takeover.status != "ACCEPTED":
            raise AssertionError("Reference recovery must accept the verified public handoff")
        recovery_event = recovery.dispatch(envelope)
        recovery_validation = _fixture_audit(fixture)
        recovery_receipt = _validated_receipt(recovery.executor_id, envelope.federation_task_id, fixture)
        if recovery_validation != source_validation:
            raise AssertionError("handoff recovery changed the deterministic fixture observation")

        memory = OperationalMemoryStore(temporary_root / "operational-memory.json")
        convergence = FederationConvergence(memory_store=memory)
        source_progress = convergence.ingest_progress(
            source_event,
            source_run_id="step10-driver-001",
            memory_id="step10-source-progress",
            event_key="step10-progress-source-001",
        )
        recovery_progress = convergence.ingest_progress(
            recovery_event,
            source_run_id="step10-driver-001",
            memory_id="step10-recovery-progress",
            event_key="step10-progress-recovery-001",
        )
        source_receipt_ingest = convergence.ingest_receipt(
            source_receipt,
            source_run_id="step10-driver-001",
            memory_id="step10-source-receipt",
        )
        recovery_receipt_ingest = convergence.ingest_receipt(
            recovery_receipt,
            source_run_id="step10-driver-001",
            memory_id="step10-recovery-receipt",
        )
        if source_receipt_ingest.status != "VERIFIED" or recovery_receipt_ingest.status != "VERIFIED":
            raise AssertionError("OS-validated receipts must enter convergence as VERIFIED")
        if convergence.memory is None:
            raise AssertionError("Step 10 requires a bounded operational-memory sink")
        convergence.memory.absorb(
            "step10-failover-001",
            project_recovery(failover, memory_id="step10-failover", source_run_id="step10-driver-001"),
        )
        convergence.memory.absorb(
            "step10-approval-001",
            project_approval(approval, memory_id="step10-approval", source_run_id="step10-driver-001"),
        )

        actual_issue_count = recovery_validation["issue_count"]
        claimed_issue_count = 0
        adversarial_validator = (
            "REJECTED_FAILED_VALIDATION"
            if claimed_issue_count != actual_issue_count
            else "ACCEPTED_UNEXPECTEDLY"
        )
        forged = FederatedResultReceipt.build(
            federation_task_id="step10-adversarial-001",
            executor_id="external.codex",
            terminal_state="REQUIRES_RECONCILIATION",
            claimed_actions=(),
            artifact_refs=(),
            validation_refs=(),
            external_session_ref=None,
            executor_telemetry={"pilot_mode": "adversarial_claim_only"},
            unresolveds=("OS_VALIDATION_NOT_PERFORMED",),
            handoff_eligibility=HandoffEligibility(False, "external completion is not OS validation"),
        )
        adversarial_ingest = convergence.ingest_receipt(
            forged,
            source_run_id="step10-adversarial-001",
            memory_id="step10-adversarial-receipt",
        )
        if adversarial_validator != "REJECTED_FAILED_VALIDATION" or adversarial_ingest.status != "UNVERIFIED":
            raise AssertionError("adversarial completion must remain rejected and unverified")

        return {
            "schema_version": "cross-executor-driver-pilot-r1",
            "task_id": TASK_ID,
            "step": STEP,
            "recorded_at": recorded_at,
            "workspace_policy": "disposable_temp_workspace_only",
            "formal_repository_used_as_live_target": False,
            "external_observations": external_rows,
            "driver": {
                "canonical_state_owner": "ignition",
                "task_envelope_digest": canonical_digest(envelope.to_dict()),
                "required_capabilities": list(envelope.required_capabilities),
                "allowed_effects": list(envelope.allowed_effects),
                "initial_route": initial_route.to_dict(),
                "fallback_route": fallback_route.to_dict(),
                "external_dispatch_policy": "NOT_REPEATED_AFTER_STEP09",
                "approval": approval.to_dict(),
                "failover": failover.to_dict(),
                "failover_safety_evidence": "read-only envelope; Step 09 timeout/skip boundary verified; no accepted vendor completion",
            },
            "episode": {
                "task_id": envelope.federation_task_id,
                "source_executor": source.executor_id,
                "source_event": source_event.to_dict(),
                "source_os_validator": source_validation,
                "source_receipt": _receipt_summary(source_receipt),
                "handoff": {
                    "handoff_id": bundle.handoff_id,
                    "source_executor_id": bundle.source_executor_id,
                    "target_executor_id": recovery.executor_id,
                    "pending_work": list(bundle.pending_work),
                    "allowed_capabilities": list(bundle.allowed_capabilities),
                    "workspace_refs": list(bundle.workspace_refs),
                    "takeover": takeover.to_dict(),
                },
                "recovery_executor": recovery.executor_id,
                "recovery_event": recovery_event.to_dict(),
                "recovery_os_validator": recovery_validation,
                "recovery_receipt": _receipt_summary(recovery_receipt),
                "os_acceptance": "COMPLETED_VALIDATED_AFTER_INDEPENDENT_OS_VALIDATION",
            },
            "convergence": {
                "canonical_state_owner": "ignition",
                "progress_ingest": [source_progress.to_dict(), recovery_progress.to_dict()],
                "receipt_ingest": [
                    source_receipt_ingest.to_dict(),
                    recovery_receipt_ingest.to_dict(),
                    adversarial_ingest.to_dict(),
                ],
                "coordinator_audit": convergence.audit(),
                "bounded_memory_audit": memory.audit(),
                "private_vendor_history_absorbed": False,
            },
            "adversarial": {
                "external_claim": {
                    "executor_id": "external.codex",
                    "terminal_state": "REQUIRES_RECONCILIATION",
                    "claimed_issue_count": claimed_issue_count,
                    "validation_refs": [],
                },
                "actual_issue_count": actual_issue_count,
                "validator_outcome": adversarial_validator,
                "os_acceptance": "REJECTED",
                "receipt_ingest": adversarial_ingest.to_dict(),
            },
            "claim_ceiling": "Bounded Ignition routing, failover, handoff, independent fixture validation and public operational-memory evidence only; no live provider success, general Agent capability, production reliability, external validity, Owner acceptance or epistemic acceptance is inferred.",
        }


def write_pilot(output_path: str | Path, *, recorded_at: str | None = None) -> dict[str, Any]:
    result = build_pilot(recorded_at=recorded_at)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--recorded-at", default=None)
    args = parser.parse_args()
    write_pilot(args.output, recorded_at=args.recorded_at)
    print(f"CROSS_EXECUTOR_DRIVER_PILOT=PASS output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
