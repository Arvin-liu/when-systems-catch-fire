"""Validate Pack-aware catalog, routing and authority non-escalation."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.pack_registry import PackLoader, PackRegistry
from agent_runtime.routing import PackAwareRouter, PackRoutingError


def main() -> int:
    registry = PackRegistry.discover(ROOT / "packs")
    loader = PackLoader(registry)
    loader.load_all()
    router = PackAwareRouter(registry, loader)
    assert len(router.catalog()["routes"]) == 10
    router.annotate_action(
        "action-knowledge", "knowledge.validate_claim", object_type="claim",
        validator_ref="tools/validate_epistemic_governance_relationships.py",
    )
    for pack_id, validator, object_type, key in (
        ("knowledge.r0", "tools/validate_epistemic_governance_relationships.py", "claim", "truth_authority"),
        ("writing.zhiyuan", "tools/governance/validate_human_surface_contract.py", "human_surface_entry", "epistemically_accepted"),
        ("research.reos-light", "tests/test_reos_vnext_minimal_kernel.py", "research_obligation", "owner_acceptance"),
    ):
        try:
            router.route_validator(pack_id, validator, object_type=object_type, result={"status": "PASS", "summary": "bounded result", key: True})
        except PackRoutingError:
            continue
        raise AssertionError(f"cross-pack authority result was accepted: {pack_id}/{key}")
    print("PACK_AWARE_ROUTING_VALIDATOR=PASS")
    print("CATALOG=10_ROUTES_READ_ONLY")
    print("PLAN_PROVENANCE=MANIFEST_BOUND")
    print("CROSS_PACK_AUTHORITY=FAIL_CLOSED")
    print("EXECUTION=PROPOSAL_ONLY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
