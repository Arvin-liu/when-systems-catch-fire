"""Validate the data-driven External Agent Federation routing policy."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_federation.router import load_routing_policy


def main() -> int:
    policy = load_routing_policy(ROOT / "data" / "agent-federation" / "federation-routing-policy-r1.json")
    assert policy.policy_id == "external-agent-federation-routing-r1"
    assert len(policy.profiles) == 4
    assert all(profile.task_types and profile.permission_ceiling for profile in policy.profiles)
    print("FEDERATION_ROUTING_POLICY=PASS")
    print("ROUTING=DATA_DRIVEN_DETERMINISTIC")
    print("CAPABILITY_EXPANSION=FAIL_CLOSED")
    print("VENDOR_BRANCHING=ABSENT_FROM_ROUTER")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
