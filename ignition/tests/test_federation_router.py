from __future__ import annotations

from pathlib import Path
import unittest

from agent_federation import (
    ApprovalPolicy,
    ExecutorDescriptor,
    ExecutorHealth,
    FederationRouter,
    RoutingRequest,
    load_routing_policy,
)
from agent_federation.router import RoutingError


ROOT = Path(__file__).resolve().parents[1]


def descriptor(executor_id: str, capabilities: tuple[str, ...], *, health: str = "HEALTHY", availability: str = "AVAILABLE", granularities: tuple[str, ...] = ("ACTION", "SUBTASK")) -> ExecutorDescriptor:
    return ExecutorDescriptor(
        executor_id=executor_id,
        family="fixture-family",
        version="fixture-1",
        transport_kind=("FIXTURE",),
        availability=availability,
        health=ExecutorHealth(health, "2026-08-16T00:00:00Z", f"fixture {health.lower()}"),
        capability_tokens=capabilities,
        supported_task_granularities=granularities,
        workspace_semantics="fixture-local",
        permission_control_semantics="fixture-policy-intersection",
        structured_output_support="structured_progress" in capabilities,
        progress_support="structured_progress" in capabilities,
        cancel_support=False,
        native_resume_support=False,
        external_session_refs=(),
        network_semantics="disabled",
        max_task_duration_seconds=None,
        adapter_version="fixture-router-r1",
        limitations=(),
    )


def request(*, task_type: str = "read_only", required_capabilities: tuple[str, ...] = ("repo.read",), required_effects: tuple[str, ...] = ("read",), pinned: str | None = None, pin_strict: bool = False, approval: ApprovalPolicy | None = None) -> RoutingRequest:
    return RoutingRequest(
        federation_task_id="route-task-001",
        owner_ref="owner-ref",
        profile_ref="profile-ref",
        task_type=task_type,
        required_capabilities=required_capabilities,
        required_effects=required_effects,
        task_granularity="ACTION",
        privacy_class="LOCAL_FIXTURE",
        workspace_locality="LOCAL",
        approval_policy=approval or ApprovalPolicy("DENY", False, required_capabilities),
        pinned_executor_id=pinned,
        pin_strict=pin_strict,
    )


class FederationRouterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = load_routing_policy(ROOT / "data" / "agent-federation" / "federation-routing-policy-r1.json")

    def test_policy_roundtrip_and_data_driven_preference(self) -> None:
        self.assertEqual(load_routing_policy(ROOT / "data" / "agent-federation" / "federation-routing-policy-r1.json").to_dict(), self.policy.to_dict())
        router = FederationRouter(self.policy, (
            descriptor("external.codex", ("repo.read", "structured_progress")),
            descriptor("external.hermes", ("repo.read",)),
        ))
        decision = router.route(request())
        self.assertEqual(decision.status, "SELECTED")
        self.assertEqual(decision.selected_executor_id, "external.hermes")
        self.assertEqual(decision.fallback_order, ("external.codex",))
        self.assertIn("effective_permission", decision.to_dict() | {"effective_permission": decision.effective_permission})

    def test_explicit_pin_has_priority_without_vendor_branching(self) -> None:
        router = FederationRouter(self.policy, (
            descriptor("external.codex", ("repo.read", "structured_progress")),
            descriptor("external.hermes", ("repo.read",)),
        ))
        decision = router.route(request(pinned="external.codex"))
        self.assertEqual(decision.selected_executor_id, "external.codex")
        self.assertIn("explicit pin priority", decision.selection_reason)

    def test_capability_mismatch_fails_closed_without_expansion(self) -> None:
        router = FederationRouter(self.policy, (
            descriptor("external.hermes", ("repo.read",)),
            descriptor("external.openclaw", ("long_task",)),
        ))
        decision = router.route(request(required_capabilities=("repo.write",), required_effects=("write",), task_type="repo_coding", approval=ApprovalPolicy("REQUIRE_OWNER", True, ("repo.write",))))
        self.assertEqual(decision.status, "NO_MATCH")
        self.assertIsNone(decision.selected_executor_id)
        self.assertTrue(all(any("MISMATCH" in reason for reason in item.rejection_reasons) for item in decision.candidates))

    def test_unavailable_executor_falls_back_only_to_eligible_candidate(self) -> None:
        router = FederationRouter(self.policy, (
            descriptor("external.hermes", ("repo.read",), health="UNAVAILABLE", availability="UNAVAILABLE"),
            descriptor("external.codex", ("repo.read", "structured_progress")),
        ))
        decision = router.route(request())
        self.assertEqual(decision.selected_executor_id, "external.codex")
        hermes = next(item for item in decision.candidates if item.executor_id == "external.hermes")
        self.assertIn("EXECUTOR_UNAVAILABLE", hermes.rejection_reasons)

    def test_strict_pin_does_not_silently_fallback(self) -> None:
        router = FederationRouter(self.policy, (descriptor("external.hermes", ("repo.read",)),))
        decision = router.route(request(pinned="external.codex", pin_strict=True))
        self.assertEqual(decision.status, "PIN_UNAVAILABLE")
        self.assertEqual(decision.fallback_order, ())

    def test_privacy_workspace_and_granularity_are_independent_filters(self) -> None:
        limited = descriptor("external.hermes", ("repo.read",), granularities=("ACTION",))
        router = FederationRouter(self.policy, (limited,))
        bad = RoutingRequest(
            federation_task_id="route-task-002", owner_ref="owner-ref", profile_ref="profile-ref",
            task_type="read_only", required_capabilities=("repo.read",), required_effects=("read",),
            task_granularity="EPISODE", privacy_class="PRIVATE_SECRET", workspace_locality="REMOTE",
            approval_policy=ApprovalPolicy("DENY", False, ("repo.read",)),
        )
        decision = router.route(bad)
        reasons = next(item for item in decision.candidates if item.executor_id == "external.hermes").rejection_reasons
        self.assertIn("GRANULARITY_UNSUPPORTED", reasons)
        self.assertIn("PRIVACY_INCOMPATIBLE", reasons)
        self.assertIn("WORKSPACE_LOCALITY_INCOMPATIBLE", reasons)

    def test_policy_rejects_duplicate_profiles(self) -> None:
        data = self.policy.to_dict()
        data["profiles"].append(data["profiles"][0])
        with self.assertRaises(RoutingError):
            load_routing_policy_from_dict(data)


def load_routing_policy_from_dict(data):
    from agent_federation.router import RoutingPolicy
    return RoutingPolicy.from_dict(data)


if __name__ == "__main__":
    unittest.main()
