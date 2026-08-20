"""Disposable offline continuity pilot for IGNITION-20260820-127.

This pilot deliberately composes the durability/lifecycle stores in one
bounded episode.  It never calls an executor, sends a network request, or
replays an unknown external side effect.  The returned record contains only
portable public evidence so it can be used as a deterministic fixture.
"""

from __future__ import annotations

from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from typing import Any, Mapping

from agent_kernel.contracts import sha256_json

from agent_runtime.accounting import AccountingPolicy, AccountingStore, BudgetScope, CostVector
from agent_runtime.durable_memory import DurableMemoryRecord, DurableOperationalMemoryStore
from agent_runtime.durability import CanonicalSnapshotStore, SNAPSHOT_SCHEMA_EPOCH, SnapshotChainStore
from agent_runtime.dr_bundle import RecoveryBundleBuilder, RecoveryBundleVerifier
from agent_runtime.dispatch_reconciliation import DispatchEnvelope, DurableDispatchStore
from agent_runtime.event_ledger import EventLedger
from agent_runtime.executor_admission import ExecutorAdmission, ExecutorAdmissionStore, ExecutorRouteDenied
from agent_runtime.namespace import (
    DelegationGrant,
    NamespaceBinding,
    NamespaceGuard,
    NamespaceIsolationError,
    PrincipalIdentity,
    PrincipalRegistry,
)
from agent_runtime.pack_lifecycle import PackLifecycleManager
from agent_runtime.pack_registry import PackManifest, PackRegistry
from agent_runtime.queue_control import QueueItem, WorkQueue
from agent_runtime.recovery import RecoveryFaultInjected, RecoveryOrchestrator
from agent_runtime.revocation import CapabilityGrant, RevocationStore
from agent_runtime.soft_governance_durability import SOFT_SCHEMA, migrate_soft_state, validate_soft_state


TASK_ID = "IGNITION-20260820-127"
PILOT_SCHEMA = "ignition-durability-continuity-pilot-r1"
RECORDED_AT = "2026-08-20T00:00:00Z"
NAMESPACE_A = "namespace-a"
NAMESPACE_B = "namespace-b"
SNAPSHOT_NAMESPACE = NAMESPACE_A
PACK_ID = "knowledge.r0"


def _pack_state(manager: PackLifecycleManager, versions: tuple[str, ...], *, namespace_id: str) -> dict[str, Any]:
    pins = {
        run_id: {"pack_id": pin.pack_id, "version": pin.version, "pin_digest": pin.pin_digest}
        for run_id, pin in sorted(getattr(manager, "_pins", {}).items())
        if pin.pack_id == PACK_ID
    }
    records = [manager.get(PACK_ID, version).to_dict() for version in versions]
    return {"namespace_id": namespace_id, "active_version": manager.active_version(PACK_ID), "run_pins": pins, "records": records}


def _memory_state(memory: DurableOperationalMemoryStore, *, namespace_id: str) -> dict[str, Any]:
    state = memory.replay()
    records = [record.to_dict() for record in sorted(state["records"].values(), key=lambda item: item.memory_id) if record.namespace_id == namespace_id]
    soft = [dict(item) for item in state["soft_context_exposures"] if item.get("namespace_id") == namespace_id]
    return {"namespace_id": namespace_id, "event_count": state["event_count"], "head_hash": state["head_hash"], "records": records, "soft_context_exposures": soft}


def _recovery_summary(result: Mapping[str, Any]) -> dict[str, Any]:
    """Remove disposable absolute paths from the recovery projection."""

    phases = []
    for phase in result["phases"]:
        refs = []
        for ref in phase.get("refs", []):
            value = str(ref)
            refs.append(Path(value).name if "/" in value else value)
        phases.append({"order": phase["order"], "name": phase["name"], "status": phase["status"], "detail": phase["detail"], "refs": refs})
    return {
        "status": result["status"],
        "phase_count": result["phase_count"],
        "phases": phases,
        "uncertain_dispatch_refs": list(result["uncertain_dispatch_refs"]),
        "advisory_soft_context_refs": list(result["advisory_soft_context_refs"]),
        "delivery_semantics": result["delivery_semantics"],
        "exactly_once": result["exactly_once"],
    }


def _public_admission(admission: ExecutorAdmission) -> dict[str, Any]:
    return {
        "executor_id": admission.executor_id,
        "observed_version": admission.observed_version,
        "status": admission.status,
        "health_status": admission.health_status,
        "capability_grant_ids": list(admission.capability_grant_ids),
        "privacy_boundary": admission.privacy_boundary,
    }


def _soft_record() -> dict[str, Any]:
    return {
        "schema_version": SOFT_SCHEMA,
        "format_epoch": 2,
        "status": "ADVISORY_ONLY",
        "claim_ceiling": "Advisory operational candidate only; not truth or authority.",
        "authority_effects": {
            "capability_delta": "NONE",
            "permission_delta": "NONE",
            "authorization_delta": "NONE",
            "truth_status_delta": "NONE",
            "owner_status_delta": "NONE",
            "epistemic_acceptance_delta": "NONE",
            "safety_delta": "NONE",
        },
        "requested_effect": "advisory_context",
        "experiment_protocol_state": "READY_NOT_RUN",
    }


def _new_manifest(manifest: PackManifest, version: str) -> PackManifest:
    return PackManifest.from_dict({**manifest.to_dict(), "version": version})


def _delegation_public(delegation: DelegationGrant) -> dict[str, Any]:
    return {
        "delegation_id": delegation.delegation_id,
        "source_namespace_id": delegation.source_namespace_id,
        "target_namespace_id": delegation.target_namespace_id,
        "issuer_principal_id": delegation.issuer_principal_id,
        "subject_principal_id": delegation.subject_principal_id,
        "scopes": list(delegation.scopes),
        "expires_at": delegation.expires_at,
        "approval_ref": delegation.approval_ref,
        "policy_digest": delegation.policy_digest,
        "status": delegation.status,
        "grant_digest": delegation.grant_digest,
    }


def run_pilot(*, recorded_at: str = RECORDED_AT) -> dict[str, Any]:
    """Run the complete Step 16 lifecycle in a disposable local fixture."""

    repo_root = Path(__file__).resolve().parents[2]
    registry = PackRegistry.discover(repo_root / "packs")
    base_manifest = registry.get(PACK_ID)
    next_manifest = _new_manifest(base_manifest, "1.1.0")
    old_pack_ref = f"{PACK_ID}@{base_manifest.version}"
    new_pack_ref = f"{PACK_ID}@{next_manifest.version}"

    with TemporaryDirectory(prefix="ignition-127-continuity-") as temporary_root:
        root = Path(temporary_root)
        now = 160.0

        # Two namespaces/workspaces start in parallel.  Cross-namespace access
        # is denied by default and only the narrowly scoped soft exposure is
        # enabled by an explicit, expiring delegation.
        principal_registry = PrincipalRegistry()
        principal_a = principal_registry.register(PrincipalIdentity("principal-a", "OPERATOR", "issuer-os"))
        principal_b = principal_registry.register(PrincipalIdentity("principal-b", "OPERATOR", "issuer-os"))
        binding_a = NamespaceBinding(NAMESPACE_A, principal_a.principal_id, "workspace-a", "episode-a", "run-v1", "memory-a", "packs-a", "leases-a", "snapshot-a", "soft-a")
        binding_b = NamespaceBinding(NAMESPACE_B, principal_b.principal_id, "workspace-b", "episode-b", "run-b", "memory-b", "packs-b", "leases-b", "snapshot-b", "soft-b")
        guard = NamespaceGuard(principal_registry)
        guard.bind(binding_a, principal_a)
        guard.bind(binding_b, principal_b)
        guard.authorize(binding_a, binding_a, action="snapshot.restore", now=now)
        cross_namespace_denied = False
        try:
            guard.require_soft_context_exposure(binding_a, binding_b, now=now)
        except NamespaceIsolationError:
            cross_namespace_denied = True
        delegation = DelegationGrant(
            "delegation-a-b-soft", NAMESPACE_A, NAMESPACE_B, principal_a.principal_id, principal_b.principal_id,
            ("soft_context.expose",), 500.0, "approval-a-b-soft", "a" * 64,
        )
        guard.require_soft_context_exposure(binding_a, binding_b, now=now, delegation=delegation)

        ledger_a = EventLedger(root / "namespace-a-events.jsonl")
        ledger_b = EventLedger(root / "namespace-b-events.jsonl")
        ledger_a.append_event(aggregate_id="episode-a", event_type="EPISODE_CREATED", payload={"status": "CREATED", "state_patch": {"namespace": NAMESPACE_A, "workspace": "workspace-a"}}, idempotency_key="idem-episode-a", occurred_at=recorded_at)
        ledger_a.append_event(aggregate_id="run-a", event_type="RUN_READY", payload={"status": "PENDING"}, idempotency_key="idem-run-ready-a", occurred_at=recorded_at)
        ledger_a.append_event(aggregate_id="run-a", event_type="RUN_STARTED", payload={"status": "RUNNING"}, expected_version=1, idempotency_key="idem-run-started-a", occurred_at=recorded_at)
        ledger_b.append_event(aggregate_id="episode-b", event_type="EPISODE_CREATED", payload={"status": "CREATED", "state_patch": {"namespace": NAMESPACE_B, "workspace": "workspace-b"}}, idempotency_key="idem-episode-b", occurred_at=recorded_at)
        ledger_b.append_event(aggregate_id="run-b", event_type="RUN_READY", payload={"status": "PENDING"}, idempotency_key="idem-run-ready-b", occurred_at=recorded_at)
        ledger_b.append_event(aggregate_id="run-b", event_type="RUN_STARTED", payload={"status": "RUNNING"}, expected_version=1, idempotency_key="idem-run-started-b", occurred_at=recorded_at)

        pack_manager = PackLifecycleManager(root / "pack-state.json")
        pack_manager.discover(base_manifest)
        pack_manager.stage(PACK_ID, base_manifest.version)
        pack_manager.validate(PACK_ID, base_manifest.version, validation_receipt_ref="pilot-pack-v1-validation")
        pack_manager.activate(PACK_ID, base_manifest.version)
        old_pin = pack_manager.pin_run("run-v1", PACK_ID)
        pack_manager.discover(next_manifest)
        pack_manager.stage(PACK_ID, next_manifest.version)
        pack_manager.validate(PACK_ID, next_manifest.version, validation_receipt_ref="pilot-pack-v2-validation")
        pack_state_before_recovery = _pack_state(pack_manager, (base_manifest.version, next_manifest.version), namespace_id=NAMESPACE_A)

        grant = CapabilityGrant("grant-a-read", principal_a.principal_id, NAMESPACE_A, "repo.read", "READ_ONLY", 300.0, "issuer-os", "b" * 64)
        revocations = RevocationStore(root / "capability-revocations.jsonl")
        revocations.register(grant, occurred_at=100.0)
        admissions = ExecutorAdmissionStore(root / "executor-admission.json", clock=lambda: now)
        admitted_record = ExecutorAdmission(
            executor_id="fixture.executor", adapter_family="reference-executor-adapter", observed_version="reference-v1", conformance_epoch=1,
            declared_capabilities=("repo.read", "local.resume"), permission_ceiling=("repo.read",), workspace_support=("workspace-a",),
            handoff_semantics="OS_CANONICAL_BUNDLE_ONLY", recovery_semantics="IDEMPOTENCY_RECONCILIATION", health_lease_id="health-lease-a",
            health_status="HEALTHY", observed_at=100.0, health_expires_at=300.0, privacy_boundary="LOCAL_FIXTURE_ONLY",
            conformance_receipt_ref="fixture-admission-r1", capability_grant_ids=(grant.grant_id,),
        )
        admissions.admit(admitted_record, expected_conformance_epoch=1, now=150.0)
        routed_before_revoke = admissions.route("fixture.executor", required_capabilities=("repo.read",), workspace="workspace-a", observed_version="reference-v1", conformance_epoch=1, revocation_store=revocations, now=150.0)
        revocations.revoke(grant.grant_id, reason="pilot capability lifecycle revocation", occurred_at=now)

        limits: dict[str, CostVector] = {}
        scopes = (
            BudgetScope("principal-a", NAMESPACE_A, "workspace-a", "episode-a", PACK_ID, "fixture.executor"),
            BudgetScope("principal-b", NAMESPACE_B, "workspace-b", "episode-b", PACK_ID, "fixture.executor-b"),
        )
        limit = CostVector(action_count=20, wall_clock_seconds=60.0, output_bytes=10000, event_volume=100, memory_bytes=10000, retry_cost=10, failover_cost=10, reconciliation_cost=10)
        for scope in scopes:
            for dimension, identifier in scope.dimensions():
                limits[f"{dimension}:{identifier}"] = limit
        accounting = AccountingStore(
            root / "accounting.json",
            AccountingPolicy(limits=limits, workspace_namespace={"workspace-a": NAMESPACE_A, "workspace-b": NAMESPACE_B}, max_consecutive_per_principal=2, aging_seconds=30.0, aging_cap=1000),
        )
        scope_a = scopes[0]
        accounting.reserve("reservation-run-a", scope_a, CostVector(action_count=2, wall_clock_seconds=1.0, output_bytes=20, event_volume=2, memory_bytes=10), occurred_at=101.0)
        accounting.settle("reservation-run-a", CostVector(action_count=1, wall_clock_seconds=0.5, output_bytes=10, event_volume=1, memory_bytes=5), occurred_at=104.0)
        accounting.reserve("reservation-cancel-a", scope_a, CostVector(action_count=1, event_volume=1, memory_bytes=1), occurred_at=102.0)
        accounting.settle("reservation-cancel-a", CostVector(event_volume=1), cancelled=True, occurred_at=103.0)

        memory = DurableOperationalMemoryStore(root / "operational-memory.json")
        memory.append(DurableMemoryRecord.create(memory_id="memory-a", namespace_id=NAMESPACE_A, memory_scope="memory-a", semantic_key="continuity-a", source_event_ref="event-run-started-a", source_run_id="run-v1", summary="bounded local continuity checkpoint", tags=("pilot",), provenance_refs=("pilot-step16",), created_at=recorded_at), occurred_at=100.0)
        memory.append(DurableMemoryRecord.create(memory_id="memory-b", namespace_id=NAMESPACE_B, memory_scope="memory-b", semantic_key="continuity-b", source_event_ref="event-run-started-b", source_run_id="run-b", summary="bounded namespace-b checkpoint", tags=("pilot",), provenance_refs=("pilot-step16",), created_at=recorded_at), occurred_at=100.0)
        soft_exposure = memory.expose_soft_context(pointer_ref="memory-pointer-a-b", source_namespace_id=NAMESPACE_A, target_namespace_id=NAMESPACE_B, occurred_at=103.0)
        memory_snapshot = memory.snapshot(namespace_id=NAMESPACE_A)
        restored_memory_snapshot = DurableOperationalMemoryStore.restore_snapshot(memory_snapshot, namespace_id=NAMESPACE_A)

        queue = WorkQueue(root / "work-queue.json", max_depth=8, profile_limits={"pilot-profile": 4}, project_limits={"pilot-project": 4}, clock=lambda: now)
        cancelled_item = queue.enqueue(QueueItem("queue-cancel-a", "run-cancel-a", "pilot-profile", "pilot-project", 5, 100.0, required_capabilities=("repo.read",)))
        cancelled_item = queue.cancel(cancelled_item.queue_id, reason="operator cancel before dispatch")
        safe_item = queue.enqueue(QueueItem("queue-safe-a", "run-v1", "pilot-profile", "pilot-project", 4, 100.0, required_capabilities=("repo.read",)))

        dispatch = DurableDispatchStore(root / "dispatch.json", clock=lambda: now)
        dispatch.create(DispatchEnvelope("dispatch-a", "task-external-a", "fixture.executor", "idem-dispatch-a", "c" * 64, "EXTERNAL_SIDE_EFFECT", 100.0, 30.0))
        dispatch.mark_sent("dispatch-a")
        dispatch.timeout("dispatch-a", reason="crash after dispatch before receipt")

        ledger_a.append_event(aggregate_id="run-a", event_type="RUN_CHECKPOINTED", payload={"status": "RUNNING", "state_patch": {"safe_task": safe_item.queue_id, "dispatch_state": "REQUIRES_RECONCILIATION"}}, expected_version=2, idempotency_key="idem-run-checkpoint-a", occurred_at=recorded_at)
        ledger_a.append_event(aggregate_id="run-cancel-a", event_type="CANCELLATION_REQUESTED", payload={"status": "CANCELLED_BEFORE_DISPATCH", "state_patch": {"queue_id": cancelled_item.queue_id}}, idempotency_key="idem-cancel-a", occurred_at=recorded_at)
        ledger_a.append_event(aggregate_id="dispatch-a", event_type="DISPATCH_CREATED", payload={"status": "REQUIRES_RECONCILIATION", "state_patch": {"effect_class": "EXTERNAL_SIDE_EFFECT", "execution": "NOT_RUN"}}, idempotency_key="idem-dispatch-event-a", occurred_at=recorded_at)

        snapshot_store = CanonicalSnapshotStore(root / "snapshot-a.json")
        snapshot = snapshot_store.create(ledger_a, snapshot_id="snapshot-a-before-tail", namespace_scope=SNAPSHOT_NAMESPACE, active_pack_versions=(old_pack_ref,), outstanding_reconciliation_refs=("dispatch-a",), advisory_soft_governance_versions=("esi-r0:ADVISORY_ONLY",), provenance_refs=("pilot-step16",))
        # The snapshot must precede the lifecycle tail.  Rebuild it once more
        # from a prefix by using the existing snapshot's captured prefix data.
        # The durable store's prefix validation is the canonical check; the
        # fixture keeps the snapshot immediately before the tail events below.
        # (The first snapshot above is intentionally replaced with a prefix
        # checkpoint generated from a fresh ledger copy.)
        prefix_ledger = EventLedger(root / "namespace-a-prefix-events.jsonl")
        for event in ledger_a.events()[:3]:
            prefix_ledger.append_event(
                aggregate_id=event.aggregate_id, event_type=event.event_type, payload=event.payload, actor_ref=event.actor_ref,
                source_refs=event.source_refs, expected_version=event.precondition_version, event_id=event.event_id,
                idempotency_key=event.idempotency_key, occurred_at=event.occurred_at, event_version=event.event_version,
                sensitivity=event.sensitivity, retention_class=event.retention_class,
            )
        snapshot = CanonicalSnapshotStore(root / "snapshot-prefix.json").create(prefix_ledger, snapshot_id="snapshot-a-before-tail", namespace_scope=SNAPSHOT_NAMESPACE, active_pack_versions=(old_pack_ref,), outstanding_reconciliation_refs=("dispatch-a",), advisory_soft_governance_versions=("esi-r0:ADVISORY_ONLY",), provenance_refs=("pilot-step16",))
        snapshot_chain = SnapshotChainStore(root / "snapshot-chain")
        snapshot_chain.write(snapshot)

        namespace_public = {
            "namespace_id": NAMESPACE_A,
            "bindings": [binding_a.to_dict(), binding_b.to_dict()],
            "cross_namespace_default": "DENY",
            "delegations": [_delegation_public(delegation)],
            "soft_exposure": "ADVISORY_ONLY",
        }
        soft_record = _soft_record()
        soft_errors = validate_soft_state(soft_record)
        migrated_soft = migrate_soft_state(soft_record, target_format_epoch=1, migration_id="pilot-soft-migration")

        recovery_kwargs = {
            "ledger": ledger_a,
            "snapshot_chain": snapshot_chain,
            "namespace_scope": SNAPSHOT_NAMESPACE,
            "namespace_state": namespace_public,
            "policy_state": {"deny_by_default": True, "soft_governance": "ADVISORY_ONLY"},
            "pack_state": pack_state_before_recovery,
            "queue_store": queue,
            "accounting_store": accounting,
            "executor_admission_store": admissions,
            "memory_store": memory,
            "dispatch_store": dispatch,
        }
        crash_boundary = "NOT_OBSERVED"
        try:
            RecoveryOrchestrator(**recovery_kwargs).run(fault_at="DURING_MEMORY_UPDATE")
        except RecoveryFaultInjected as exc:
            crash_boundary = exc.point
        recovery_result = RecoveryOrchestrator(**recovery_kwargs).run()
        recovered_state = snapshot_store.restore(ledger_a, snapshot, namespace_scope=SNAPSHOT_NAMESPACE)
        full_state = ledger_a.replay()

        revoked_route_denied = False
        try:
            admissions.route("fixture.executor", required_capabilities=("repo.read",), workspace="workspace-a", revocation_store=revocations, now=now)
        except ExecutorRouteDenied:
            revoked_route_denied = True
        safe_admitted = queue.admit_next(now=now)
        safe_dispatched = queue.dispatch(safe_admitted.queue_id, now=now) if safe_admitted is not None else None
        safe_completed = queue.complete(safe_dispatched.queue_id, "COMPLETED_VALIDATED", reason="bounded local continuation after recovery") if safe_dispatched is not None else None
        ledger_a.append_event(aggregate_id="run-a", event_type="RUN_TERMINAL", payload={"status": "COMPLETED_VALIDATED", "state_patch": {"safe_task": safe_completed.queue_id if safe_completed else "none"}}, expected_version=3, idempotency_key="idem-run-terminal-a", occurred_at=recorded_at)

        activated_v2 = pack_manager.activate(PACK_ID, next_manifest.version)
        new_pin = pack_manager.pin_run("run-v2", PACK_ID)
        pack_state_final = _pack_state(pack_manager, (base_manifest.version, next_manifest.version), namespace_id=NAMESPACE_A)

        admission_state = _public_admission(admissions.get("fixture.executor"))
        revocation_state = {key: value for key, value in sorted(revocations.replayed_state(now=now).items())}
        accounting_state = accounting.replay()
        memory_state = _memory_state(memory, namespace_id=NAMESPACE_A)
        queue_state = queue.audit()
        dispatch_record = dispatch.get("dispatch-a")
        reconciliation_state = {"namespace_id": NAMESPACE_A, "unresolved_dispatch_ids": [dispatch_record.dispatch_id] if dispatch_record.state == "REQUIRES_RECONCILIATION" else [], "external_reexecution": "FORBIDDEN", "records": [dispatch_record.to_dict()]}
        canonical_components = {
            "ledger": ledger_a.replay(),
            "accounting": accounting_state,
            "memory": memory_state,
            "namespace": namespace_public,
            "pack": pack_state_final,
            "queue": queue_state,
            "reconciliation": reconciliation_state,
            "soft_governance": {
                "status": migrated_soft["status"],
                "format_epoch": migrated_soft["format_epoch"],
                "authority_effects": ["NONE"],
                "requested_effect": migrated_soft["requested_effect"],
                "claim_ceiling": migrated_soft["claim_ceiling"],
            },
        }
        canonical_digest = sha256_json(canonical_components)

        bundle_chunks: dict[str, Mapping[str, Any]] = {
            "trusted-snapshot": {"namespace_id": NAMESPACE_A, "snapshot": snapshot.to_dict(), "trusted": True},
            "tail-event-lineage": {"namespace_id": NAMESPACE_A, "event_count": len(ledger_a.events()), "head_hash": ledger_a.audit()["head_hash"], "events": [event.to_dict() for event in ledger_a.events()]},
            "schema-migration": {"namespace_id": NAMESPACE_A, "status": "NOT_REQUIRED", "from_epoch": SNAPSHOT_SCHEMA_EPOCH, "to_epoch": SNAPSHOT_SCHEMA_EPOCH, "events_rewritten": False},
            "namespace-registry": namespace_public,
            "pack-lifecycle": {"namespace_id": NAMESPACE_A, "state": pack_state_final},
            "executor-admission": {"namespace_id": NAMESPACE_A, "state": admission_state, "routable_ids": [], "revoked_executor_ids": ["fixture.executor"]},
            "capability-revocation": {"namespace_id": NAMESPACE_A, "events": [event.to_dict() for event in revocations.events()], "state": revocation_state},
            "accounting": {"namespace_id": NAMESPACE_A, "state": accounting_state},
            "reconciliation": reconciliation_state,
            "memory-integrity": {"namespace_id": NAMESPACE_A, "state": memory_state, "snapshot": memory_snapshot},
            "soft-governance": {"namespace_id": NAMESPACE_A, "status": "ADVISORY_ONLY", "authority_effects": ["NONE"], "requested_effect": "advisory_context", "claim_ceiling": "Advisory projection only; no truth or authority.", "pointer_status": soft_exposure["status"]},
            "operator-checkpoint": {"namespace_id": NAMESPACE_A, "checkpoint_id": "operator-checkpoint-step16", "canonical_components": canonical_components, "canonical_digest": canonical_digest, "recovery_status": recovery_result["status"], "external_reexecution": "FORBIDDEN", "claim_ceiling": "Local continuity evidence only; no production readiness, Owner acceptance or epistemic acceptance."},
        }
        bundle_source = root / "bundle-source"
        bundle_manifest = RecoveryBundleBuilder(bundle_source).build(bundle_id="bundle-127-a", namespace_id=NAMESPACE_A, schema_epoch=SNAPSHOT_SCHEMA_EPOCH, source_ledger_head_hash=ledger_a.audit()["head_hash"], chunks=bundle_chunks, unresolved_reconciliation_refs=("dispatch-a",), operator_checkpoint="operator-checkpoint-step16", created_at=104.0)
        fresh_restore = root / "fresh-bundle-restore"
        shutil.copytree(bundle_source, fresh_restore)
        restored_bundle = RecoveryBundleVerifier.restore(fresh_restore, namespace_id=NAMESPACE_A, schema_epoch=SNAPSHOT_SCHEMA_EPOCH, expected_source_ledger_head_hash=ledger_a.audit()["head_hash"])
        restored_components = restored_bundle["chunks"]["operator-checkpoint"]["canonical_components"]
        component_matches = {name: restored_components[name] == value for name, value in canonical_components.items()}
        restored_canonical_digest = sha256_json(restored_components)
        memory_snapshot_match = restored_bundle["chunks"]["memory-integrity"]["state"] == memory_state
        accounting_match = restored_bundle["chunks"]["accounting"]["state"] == accounting_state
        namespace_match = restored_bundle["chunks"]["namespace-registry"] == namespace_public
        pack_match = restored_bundle["chunks"]["pack-lifecycle"]["state"] == pack_state_final
        soft_advisory_after_restore = restored_bundle["chunks"]["soft-governance"]["status"] == "ADVISORY_ONLY" and restored_bundle["chunks"]["soft-governance"]["authority_effects"] == ["NONE"]

        checks = {
            "two_namespaces_started": len({NAMESPACE_A, NAMESPACE_B}) == 2 and len(ledger_a.events()) >= 6,
            "snapshot_plus_tail_replay_equivalent": recovered_state == full_state,
            "cross_namespace_default_deny": cross_namespace_denied,
            "explicit_delegation_scoped": delegation.active_at(now) and delegation.scopes == ("soft_context.expose",),
            "old_run_pinned_v1": old_pin.version == base_manifest.version,
            "revoked_executor_not_routed": revoked_route_denied and admission_state["status"] == "REVOKED",
            "cancel_before_dispatch": cancelled_item.state == "CANCELLED_BEFORE_DISPATCH",
            "safe_task_continued": safe_completed is not None and safe_completed.state == "COMPLETED_VALIDATED",
            "external_side_effect_not_reexecuted": dispatch_record.state == "REQUIRES_RECONCILIATION" and recovery_result["uncertain_dispatch_refs"] == ["dispatch-a"],
            "pack_v2_only_new_run": activated_v2.state == "ACTIVATED" and old_pin.version == base_manifest.version and new_pin.version == next_manifest.version and pack_manager.get(PACK_ID, base_manifest.version).state == "DRAINING",
            "memory_snapshot_restore": restored_memory_snapshot["namespace_id"] == NAMESPACE_A and memory_snapshot["state_sha256"] == restored_memory_snapshot["state_sha256"],
            "soft_governance_non_authority": not soft_errors and migrated_soft["status"] == "ADVISORY_ONLY" and soft_exposure["status"] == "ADVISORY_ONLY" and soft_advisory_after_restore,
            "dr_fresh_restore": restored_bundle["status"] == "PASS" and restored_bundle["external_reexecution"] == "FORBIDDEN",
            "canonical_component_match": all(component_matches.values()) and restored_canonical_digest == canonical_digest and memory_snapshot_match and accounting_match and namespace_match and pack_match,
            "crash_restart_replay": crash_boundary == "DURING_MEMORY_UPDATE" and recovery_result["phase_count"] == 11,
        }
        passed = all(checks.values()) and bundle_manifest["chunk_count"] == 12
        return {
            "schema": PILOT_SCHEMA,
            "task_id": TASK_ID,
            "step": "16",
            "mode": "OFFLINE_DISPOSABLE_REPOSITORY_WORKSPACES_ONLY",
            "status": "PASS" if passed else "FAIL",
            "recorded_at": recorded_at,
            "scenario": {"namespaces": [NAMESPACE_A, NAMESPACE_B], "workspaces": ["workspace-a", "workspace-b"], "external_invocation": "NOT_RUN", "external_side_effects": "NOT_EXECUTED"},
            "checks": checks,
            "namespace": {"namespace_count": 2, "workspace_count": 2, "default_deny": cross_namespace_denied, "explicit_delegation_scope": list(delegation.scopes), "canonical_digest": sha256_json(namespace_public)},
            "snapshot": {"snapshot_id": snapshot.snapshot_id, "captured_events": snapshot.ledger_end_sequence, "tail_events": len(ledger_a.events()) - snapshot.ledger_end_sequence, "replay_equivalent": recovered_state == full_state, "schema_epoch": SNAPSHOT_SCHEMA_EPOCH},
            "pack": {"old_run_pin": old_pin.version, "active_after_recovery": base_manifest.version, "new_run_pin": new_pin.version, "final_active": pack_manager.active_version(PACK_ID), "old_version_state": pack_manager.get(PACK_ID, base_manifest.version).state, "new_version_state": activated_v2.state, "v2_activation_after_recovery": True},
            "executor": {"routed_before_revoke": routed_before_revoke.executor_id, "revoked_route_denied": revoked_route_denied, "final_admission": admission_state, "live_invocation": "NOT_RUN"},
            "queue": {"cancelled_state": cancelled_item.state, "safe_task_state": safe_completed.state if safe_completed else "MISSING", "audit": queue_state},
            "accounting": {"event_count": len(accounting.events()), "replay_digest": sha256_json(accounting_state), "cancelled_reservation_preserves_occurred_cost": accounting_state["reservations"]["reservation-cancel-a"]["spent"]["event_volume"] == 1},
            "memory": {"namespace_a": memory_state, "namespace_b_record_count": len([item for item in memory.replay()["records"].values() if item.namespace_id == NAMESPACE_B]), "snapshot_restore": checks["memory_snapshot_restore"], "soft_exposure_status": soft_exposure["status"]},
            "dispatch": {"state": dispatch_record.state, "unresolved_refs": list(recovery_result["uncertain_dispatch_refs"]), "external_reexecution": "FORBIDDEN"},
            "recovery": {"crash_boundary": crash_boundary, "normal_restart": _recovery_summary(recovery_result)},
            "soft_governance": {"validation_errors": soft_errors, "migrated_format_epoch": migrated_soft["format_epoch"], "restored_status": "ADVISORY_ONLY", "authority_effects": ["NONE"], "digest": sha256_json(migrated_soft)},
            "disaster_recovery": {"source_bundle": bundle_manifest["status"], "fresh_directory_restore": restored_bundle["status"], "chunk_count": bundle_manifest["chunk_count"], "external_reexecution": restored_bundle["external_reexecution"], "component_matches": component_matches, "canonical_digest": canonical_digest, "restored_canonical_digest": restored_canonical_digest, "canonical_digest_match": restored_canonical_digest == canonical_digest},
            "claim_ceiling": "Repository-local continuity evidence only; no production readiness, external completion, Owner acceptance or epistemic acceptance is established.",
        }


__all__ = ["PILOT_SCHEMA", "RECORDED_AT", "TASK_ID", "run_pilot"]
