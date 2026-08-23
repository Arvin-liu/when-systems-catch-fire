from pathlib import Path
import tempfile
import unittest

from agent_runtime.accounting import AccountingPolicy, AccountingStore, BudgetScope, CostVector
from agent_runtime.dispatch_reconciliation import DurableDispatchStore
from agent_runtime.event_ledger import EventLedger
from agent_runtime.queue_control import WorkQueue
from agent_runtime.resource_arbitration import ResourceArbiter
from agent_runtime.steering import IntentCapsule

from agent_federation.live_admission import LiveAdmissionDecision
from agent_federation.live_bridge import LIVE_DISPATCH_SCHEMA, LiveDispatchEnvelope
from agent_federation.live_orchestration import LiveDispatchCoordinator, LiveOrchestrationError, LiveSteeringBinding


def envelope() -> LiveDispatchEnvelope:
    return LiveDispatchEnvelope(
        schema_version=LIVE_DISPATCH_SCHEMA, task_id="IGNITION-20260823-136", dispatch_id="d-orch", attempt_id="a-orch",
        executor_id="external.codex", adapter_id="codex-live-r2", capability_id="live.readonly.synthetic", capability_lease_ref="lease-orch",
        workspace_ref="DISPOSABLE_FIXTURE_ROOT", workspace_mode="DISPOSABLE_READ_ONLY", permission_ceiling=("repo.read",),
        side_effect_class="READ_ONLY_SYNTHETIC", network_class="INFERENCE_TRANSPORT_ONLY", intent_capsule_ref="capsule:intent-136:goal-136",
        synthetic_input_ref="fixture://136", synthetic_input_digest="a" * 64, success_criteria=("return nonce",),
        output_contract={"format": "json", "required_fields": ["nonce"]}, deadline="2026-08-24T00:00:00Z", timeout_seconds=10,
        retry_policy="NO_BLIND_RETRY", reconciliation_policy="REQUIRE_ON_TIMEOUT_OR_UNKNOWN_EFFECT",
        budget_authority="NO_NEW_BILLING_AUTHORITY", provenance={"controller": "pointfire-os"},
    )


def steering() -> LiveSteeringBinding:
    capsule = IntentCapsule(
        capsule_id="capsule:intent-136:goal-136", intent_id="intent-136", goal_id="goal-136",
        intent_summary="Read the disposable fixture", goal_summary="Produce a bounded structured report",
        success_criteria=("return nonce",), permission_summary=("repo.read",), blocker_refs=(), temporal_refs=(),
        report_contract_refs=("report-contract-136",), minimal_context_refs=("fixture-ref-136",), namespace_ref="namespace-136",
        created_at="2026-08-23T16:00:00+00:00",
    )
    scope = BudgetScope(
        principal_id="principal-136", namespace_id="namespace-136", workspace_id="DISPOSABLE_READ_ONLY",
        episode_id="episode-136", pack_id="pack-live-136", executor_id="external.codex",
    )
    return LiveSteeringBinding(capsule, "why-next-136", 7, "profile-live-136", "IGNITION-20260823-136", scope)


def accounting_policy() -> AccountingPolicy:
    ids = {
        "principal": "principal-136", "namespace": "namespace-136", "workspace": "DISPOSABLE_READ_ONLY",
        "episode": "episode-136", "pack": "pack-live-136", "executor": "external.codex",
    }
    limit = CostVector(action_count=4, wall_clock_seconds=100, output_bytes=100, event_volume=20)
    return AccountingPolicy(
        limits={f"{dimension}:{identifier}": limit for dimension, identifier in ids.items()},
        workspace_namespace={"DISPOSABLE_READ_ONLY": "namespace-136"},
    )


def coordinator(root: Path) -> LiveDispatchCoordinator:
    scope = steering().budget_scope
    return LiveDispatchCoordinator(
        envelope=envelope(), steering=steering(),
        admission=LiveAdmissionDecision("external.codex", "lease-orch", "ADMITTED", ("repo.read",), "test"),
        queue=WorkQueue(root / "queue.json", max_depth=2, profile_limits={"profile-live-136": 2}),
        resources=ResourceArbiter(root / "resources.json"),
        accounting=AccountingStore(root / "accounting.json", accounting_policy()),
        dispatch_store=DurableDispatchStore(root / "dispatch.json"),
        ledger=EventLedger(root / "events.jsonl"),
        clock=lambda: 100.0,
    )


class LiveOrchestrationTests(unittest.TestCase):
    def test_prepare_uses_existing_queue_resource_budget_dispatch_and_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bridge = coordinator(root)
            plan = bridge.prepare()
            public = bridge.public_plan()
            self.assertEqual(plan.status, "PREPARED")
            self.assertEqual(bridge.queue.get(plan.queue_id).state, "DISPATCHED")
            self.assertEqual(bridge.dispatch_store.get(plan.dispatch_id).state, "CREATED")
            self.assertEqual(len(bridge.resources.active(now=100.0)), 1)
            self.assertEqual(len(bridge.accounting.events()), 1)
            self.assertEqual(len(bridge.ledger.events()), 3)
            self.assertFalse(public["executor_canonical_mutation_allowed"])
            self.assertFalse(public["goal_completion_inference_allowed"])
            self.assertEqual(public["billing_authority"], "NO_NEW_BILLING_AUTHORITY")

    def test_start_is_durable_and_duplicate_start_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            bridge = coordinator(Path(directory))
            bridge.prepare()
            started = bridge.start()
            self.assertEqual(started["state"], "ACKNOWLEDGED")
            with self.assertRaises(Exception):
                bridge.start()

    def test_executor_cannot_supply_priority_or_canonical_mutation_authority(self):
        with self.assertRaises(LiveOrchestrationError):
            LiveSteeringBinding(
                steering().capsule, "why-next-136", 7, "profile-live-136", "IGNITION-20260823-136",
                steering().budget_scope, priority_source="executor-suggested-priority",
            )
        with self.assertRaises(Exception):
            IntentCapsule(
                capsule_id="capsule:intent-136:goal-136", intent_id="intent-136", goal_id="goal-136",
                intent_summary="Read fixture", goal_summary="Report", success_criteria=("return nonce",),
                permission_summary=("repo.read",), blocker_refs=(), temporal_refs=(), report_contract_refs=("report-136",),
                minimal_context_refs=(), namespace_ref="namespace-136", created_at="2026-08-23T16:00:00+00:00",
                executor_can_mutate_canonical=True,
            )

    def test_billing_authority_is_fail_closed(self):
        value = envelope()
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(Exception):
                widened = LiveDispatchEnvelope(
                    **{**value.__dict__, "budget_authority": "NEW_PAYG_AUTHORITY"}
                )
                LiveDispatchCoordinator(
                    envelope=widened, steering=steering(),
                    admission=LiveAdmissionDecision("external.codex", "lease-orch", "ADMITTED", ("repo.read",), "test"),
                    queue=WorkQueue(Path(directory) / "queue.json", max_depth=2), resources=ResourceArbiter(Path(directory) / "resources.json"),
                    accounting=AccountingStore(Path(directory) / "accounting.json", accounting_policy()),
                    dispatch_store=DurableDispatchStore(Path(directory) / "dispatch.json"), ledger=EventLedger(Path(directory) / "events.jsonl"),
                )


if __name__ == "__main__":
    unittest.main()
