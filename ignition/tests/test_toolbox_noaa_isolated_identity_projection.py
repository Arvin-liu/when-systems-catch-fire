from __future__ import annotations

import json
from pathlib import Path
import unittest


IGNITION = Path(__file__).resolve().parents[1]
NOAA_EXPECTED = {
    "research.lookup_noaa_global_co2_annual_growth",
    "research.lookup_noaa_global_ch4_annual_growth",
    "research.lookup_noaa_global_n2o_annual_growth",
    "research.compare_noaa_co2_source_surfaces",
    "research.compare_noaa_ch4_source_surfaces",
    "research.compare_noaa_n2o_source_surfaces",
    "research.lookup_noaa_global_sf6_annual_growth",
    "research.compare_noaa_sf6_source_surfaces",
    "research.pair_noaa_co2_ch4_growth_by_year",
}
LINEAGE_AUDITOR = "maintenance.audit_execution_state_lineage"
EXPECTED = NOAA_EXPECTED | {LINEAGE_AUDITOR}


class IsolatedNoaaGasIdentityProjectionTests(unittest.TestCase):
    def test_candidates_remain_experimental_and_default_off(self) -> None:
        identity = json.loads((IGNITION / "data/operations/toolbox-identity-cards-r0.json").read_text())
        registry = json.loads((IGNITION / "data/operations/ignition-operation-capability-registry-r1.json").read_text())
        toolbox = (IGNITION / "TOOLBOX.md").read_text()

        cards = {row["tool_id"]: row for row in identity["cards"]}
        candidates = {key: row for key, row in cards.items() if row["card_kind"] == "OPTIONAL_EXPERIMENTAL_TOOL"}

        self.assertEqual(identity["candidate_cards"]["candidate_count"], len(EXPECTED))
        self.assertEqual(set(candidates), EXPECTED)
        self.assertEqual(set(candidates) & NOAA_EXPECTED, NOAA_EXPECTED)
        self.assertEqual(identity["current_registry"]["operation_count"], len(registry["operations"]))
        current_ids = {row["operation_id"] for row in registry["operations"]}
        self.assertTrue(EXPECTED.isdisjoint(current_ids))

        for tool_id, card in candidates.items():
            with self.subTest(tool_id=tool_id):
                self.assertEqual(card["availability"], "EXPERIMENTAL_AVAILABLE")
                self.assertEqual(card["lifecycle"], "EXPERIMENTAL")
                self.assertFalse(card["router_selectable_by_default"])
                self.assertEqual(card["execution_mode"], "READ_ONLY_RUN")
                if card["permissions"]["network"]:
                    self.assertEqual(card["permissions"]["network_hosts"], ["gml.noaa.gov"])
                    self.assertIn("--allow-public-network", card["entrypoint"])
                else:
                    self.assertEqual(card["permissions"]["network_hosts"], [])
                    self.assertNotIn("--allow-public-network", card["entrypoint"])
                self.assertTrue(card["source_blob_sha1"])
                self.assertTrue(card["source_refs_with_hashes"])

        for tool_id in EXPECTED:
            self.assertIn(tool_id, toolbox)
        self.assertIn("toolbox-identity-cards-r0.json", toolbox)
        self.assertIn("discovery surface", toolbox)

    def test_current_operation_router_fails_closed_for_all_candidate_ids(self) -> None:
        import sys
        sys.path.insert(0, str(IGNITION / "tools/operations"))
        import plan_ignition_operation_run as planner

        request = {"request_envelope": {"user_request": "Run this optional research candidate."}, "input_objects": []}
        for tool_id in EXPECTED:
            with self.subTest(tool_id=tool_id):
                plan = planner.plan_run(request, tool_id, "refs/heads/main@example-current")
                self.assertEqual(plan["operation_status"], "UNREGISTERED")
                self.assertEqual(plan["decision"], "STOP")
                self.assertEqual(plan["stop_reason"], "UNSUPPORTED_OPERATION")
                self.assertFalse(plan["side_effects_authorized_by_plan"])

    def test_current_registry_is_not_promoted_by_candidate_projection(self) -> None:
        identity = json.loads((IGNITION / "data/operations/toolbox-identity-cards-r0.json").read_text())
        registry = json.loads((IGNITION / "data/operations/ignition-operation-capability-registry-r1.json").read_text())
        current_ids = {row["operation_id"] for row in registry["operations"]}
        projected_current = {
            row["tool_id"] for row in identity["cards"]
            if row["card_kind"] == "CURRENT_OPERATION_REGISTRY_PROJECTION"
        }
        self.assertEqual(projected_current, current_ids)
        self.assertTrue(all(not identity_card["router_selectable_by_default"] for identity_card in identity["cards"] if identity_card["card_kind"] == "OPTIONAL_EXPERIMENTAL_TOOL"))


if __name__ == "__main__":
    unittest.main()
