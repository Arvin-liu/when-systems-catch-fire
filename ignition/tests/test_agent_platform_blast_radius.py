#!/usr/bin/env python3
"""R2 source-contract and blast-radius boundary tests."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.propagation.agent_platform_blast_radius import (
    CONTRACT_PATH,
    REPORT_PATH,
    build_report,
    load_blast_radius_contract,
    validate_contract,
)
from tools.propagation.impact_contract import derive_blast_radius


ROOT = Path(__file__).resolve().parents[1]


class AgentPlatformBlastRadiusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_blast_radius_contract(str(ROOT))

    def test_contract_and_four_fixtures_pass(self) -> None:
        self.assertEqual(validate_contract(self.contract), [])
        report = build_report(self.contract)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(set(report["fixtures"]), {"runtime_only", "knowledge_claim", "writing_surface", "pack_manifest"})

    def test_runtime_only_fixture_cannot_reach_knowledge_writing_or_pack_registry(self) -> None:
        fixture = self.contract["fixtures"]["runtime_only"]
        result = derive_blast_radius(fixture["changed_paths"], self.contract)
        self.assertEqual(result["source_domains"], {"agent_runtime": fixture["changed_paths"]})
        self.assertEqual(set(result["affected_projections"]), set(fixture["expected_affected_projections"]))
        self.assertTrue(set(result["affected_projections"]).isdisjoint(fixture["forbidden_affected_projections"]))

    def test_knowledge_change_does_not_change_runtime_permission_projections(self) -> None:
        fixture = self.contract["fixtures"]["knowledge_claim"]
        result = derive_blast_radius(fixture["changed_paths"], self.contract)
        self.assertEqual(set(result["source_domains"]), {"knowledge"})
        self.assertNotIn("agent_platform.runtime", result["affected_projections"])
        self.assertNotIn("agent_platform.pack_routing", result["affected_projections"])

    def test_unmapped_or_mixed_paths_fail_closed(self) -> None:
        unmapped = derive_blast_radius(["unregistered/runtime-helper.txt"], self.contract)
        self.assertEqual(unmapped["unmapped_paths"], ["unregistered/runtime-helper.txt"])
        mixed = derive_blast_radius(
            ["agent_runtime/fixtures/runtime-only-helper.py", "docs/publication/zhiyuan-writing-method.md"],
            self.contract,
        )
        self.assertEqual(set(mixed["source_domains"]), {"agent_runtime", "writing"})
        self.assertIn("agent_platform.runtime", mixed["affected_projections"])
        self.assertIn("writing.human_surface", mixed["affected_projections"])

    def test_committed_report_is_json_and_matches_generator(self) -> None:
        self.assertTrue(CONTRACT_PATH.is_file())
        self.assertTrue(REPORT_PATH.is_file())
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(report, build_report(self.contract))


if __name__ == "__main__":
    unittest.main(verbosity=2)
