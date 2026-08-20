from __future__ import annotations

import unittest

from agent_runtime.driver_console import DriverConsoleError, build_driver_recovery_surface, render_driver_recovery_surface


def sources() -> dict[str, object]:
    return {
        "os_identity": "OS_CONTROL_PLANE",
        "schema_epoch": "os-durability-r1",
        "recovery": {"status": "RECOVERED_WITH_OPEN_OBLIGATIONS", "snapshot": {"id": "snapshot-a", "tail_events": 2}, "uncertain_dispatch_refs": ["dispatch-a"], "operator_recovery_state": {"trusted_snapshot": "snapshot-a", "unresolved_reconciliation_refs": ["dispatch-a"]}, "accounting": {"status": "PASS", "event_count": 4, "reservation_count": 2, "dimension_count": 6}},
        "last_known_good": {"snapshot_id": "snapshot-a", "pack_versions": ["knowledge.r0@1.0.0"]},
        "episode_states": {"episode-a": "RUNNING", "episode-b": "QUEUED", "episode-c": "REQUIRES_RECONCILIATION"},
        "packs": {"active_versions": ["knowledge.r0@1.0.0", "maintenance.repository@1.0.0"]},
        "executors": {"routable_ids": ["reference.executor"], "status": "PASS"},
        "health": {"healthy": 1, "stale": 1},
        "revocation": {"revoked": 1},
        "budget_pressure": {"status": "PRESSURED", "remaining": "bounded"},
        "namespace_delegation_anomalies": ["delegation-expiring"],
        "soft_governance": {"status": "CANDIDATE_ESI_SIGNAL", "authority_effects": ["NONE"], "claim_ceiling": "Advisory candidate only; not truth or authority.", "pointers": ["esi-r0"]},
        "technical_refs": ["agent-results/recovery.json", "data/operations/durability/accounting.json"],
    }


class DriverRecoverySurfaceTests(unittest.TestCase):
    def test_human_first_projection_contains_all_recovery_views(self) -> None:
        surface = build_driver_recovery_surface(sources())
        self.assertEqual(surface["schema"], "ignition-driver-recovery-surface-r2")
        self.assertEqual(surface["trusted_snapshot"]["id"], "snapshot-a")
        self.assertEqual(surface["episodes"]["reconciliation"], 1)
        self.assertTrue(surface["soft_governance"]["candidate_or_advisory"])
        self.assertEqual(surface["soft_governance"]["authority_effects"], ["NONE"])
        text = render_driver_recovery_surface(surface)
        self.assertLess(text.index("人话："), text.index("Technical records:"))
        self.assertIn("reconciliation", text)
        self.assertIn("Advisory", text)

    def test_soft_to_hard_injection_is_fail_closed(self) -> None:
        value = sources()
        value["soft_governance"] = {"status": "CANDIDATE_ESI_SIGNAL", "authority_effects": ["GRANT_PERMISSION"], "claim_ceiling": "candidate"}
        with self.assertRaises(DriverConsoleError):
            build_driver_recovery_surface(value)

    def test_projection_does_not_require_or_create_a_second_truth_source(self) -> None:
        surface = build_driver_recovery_surface(sources())
        self.assertIn("Projection only", " ".join(surface["boundaries"]))
        self.assertEqual(surface["technical_refs"], ["agent-results/recovery.json", "data/operations/durability/accounting.json"])


if __name__ == "__main__":
    unittest.main()
