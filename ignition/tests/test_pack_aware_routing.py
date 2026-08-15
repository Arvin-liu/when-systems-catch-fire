from __future__ import annotations

from pathlib import Path
import unittest

from agent_runtime.pack_registry import PackLoader, PackRegistry
from agent_runtime.routing import PackAwareRouter, PackRoutingError
from agent_runtime.transport import GatewayRequest, ReasonerGateway, ScriptedGatewayAdapter


ROOT = Path(__file__).resolve().parents[1]


class PackAwareRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = PackRegistry.discover(ROOT / "packs")
        self.loader = PackLoader(self.registry)
        self.loader.load_all()
        self.router = PackAwareRouter(self.registry, self.loader)

    def test_catalog_and_action_provenance_are_manifest_bound(self) -> None:
        catalog = self.router.catalog()
        self.assertEqual(set(catalog["packs"]), set(self.registry.pack_ids))
        provenance = self.router.annotate_action(
            "action-claim-validation", "knowledge.validate_claim", object_type="claim",
            validator_ref="tools/validate_epistemic_governance_relationships.py",
            hook_ref="knowledge.plan_validation",
        )
        self.assertEqual(provenance.pack_id, "knowledge.r0")
        self.assertEqual(provenance.source, "PACK_AWARE_PLANNER")
        self.assertIn("NO_RUNTIME_PERMISSION", provenance.authority_boundary)
        proposal = self.router.propose_hook("writing.zhiyuan", "writing.plan_source_bounded_revision", payload={"source_ref": "draft-1"})
        self.assertEqual(proposal["execution"], "NOT_PERFORMED_BY_PACK_AWARE_ROUTER")

    def test_profile_scoped_router_cannot_route_unselected_pack(self) -> None:
        scoped = PackAwareRouter(self.registry, self.loader, allowed_pack_ids=("research.reos-light",))
        self.assertEqual(scoped.available_pack_ids, ("research.reos-light",))
        with self.assertRaises(PackRoutingError):
            scoped.route("knowledge.validate_claim")
        with self.assertRaises(PackRoutingError):
            scoped.annotate_action("action-writing", "writing.apply_editorial_method", object_type="editorial_source")

    def test_cross_pack_authority_does_not_escalate(self) -> None:
        with self.assertRaises(PackRoutingError):
            self.router.route_validator(
                "knowledge.r0", "tools/validate_epistemic_governance_relationships.py",
                object_type="claim", result={"status": "PASS", "summary": "claim structure passed", "truth_authority": True},
            )
        with self.assertRaises(PackRoutingError):
            self.router.route_validator(
                "writing.zhiyuan", "tools/governance/validate_human_surface_contract.py",
                object_type="human_surface_entry", result={"status": "PASS", "summary": "prose surface passed", "epistemically_accepted": True},
            )
        with self.assertRaises(PackRoutingError):
            self.router.route_validator(
                "research.reos-light", "tests/test_reos_vnext_minimal_kernel.py",
                object_type="research_obligation", result={"status": "PASS", "summary": "obligation workflow passed", "owner_acceptance": True},
            )
        receipt = self.router.route_validator(
            "research.reos-light", "tests/test_reos_vnext_minimal_kernel.py",
            object_type="research_obligation", result={"status": "PASS", "summary": "obligation workflow passed"},
        )
        self.assertEqual(receipt.authority_effect, "DECLARED_SCOPE_ONLY_NOT_RUNTIME_PERMISSION_OR_TRUTH")

    def test_gateway_rejects_unlisted_pack_request_without_loading_it(self) -> None:
        request = GatewayRequest(
            phase="PLAN", run_id="run-pack-catalog", goal_summary="bounded plan",
            environment_summary="offline", capability_catalog=("read.files",),
            available_packs=("research.reos-light",),
        )
        adapter = ScriptedGatewayAdapter((), requested_packs=("knowledge.r0",))
        with self.assertRaises(Exception):
            ReasonerGateway(adapter).request(request)
        self.assertFalse(self.loader.is_loaded("knowledge.unknown"))


if __name__ == "__main__":
    unittest.main()
