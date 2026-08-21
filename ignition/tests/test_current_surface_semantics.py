from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from tools import build_current_snapshot
from tools import current_surface_compiler
from tools import validate_current_surface_semantics as gate


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "data/operations/iterations/130/fixtures/current-surface-semantic-negative-fixtures-r1.json"


class CurrentSurfaceSemanticGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot = build_current_snapshot.build_snapshot()

    def test_ten_negative_fixtures_fail_closed(self) -> None:
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(len(fixture["negative_cases"]), 10)
        for case in fixture["negative_cases"]:
            with self.subTest(case=case["id"]):
                text = case.get("text")
                profile = case.get("surface_profile", case.get("generated_profile", "human"))
                if case.get("generated_profile"):
                    text = current_surface_compiler.render_block(self.snapshot, case["generated_profile"])
                    if case.get("tamper"):
                        text = text.replace("- current_map: `0.12.0` Current", case["tamper"])
                        text = re.sub(r"- current_task: `[^`]+`", case["tamper"], text, count=1)
                issues = gate.validate_documents(
                    {"fixture.md": text or ""},
                    snapshot=self.snapshot,
                    surface_specs=[{"surface_id": "fixture", "path": "fixture.md", "profile": profile}],
                    require_blocks=bool(case.get("generated_profile")),
                )
                self.assertFalse(not issues, case["id"])

    def test_positive_boundaries_remain_allowed(self) -> None:
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        for case in fixture["positive_boundaries"]:
            with self.subTest(case=case["id"]):
                issues = gate.validate_documents(
                    {"fixture.md": case["text"]},
                    snapshot=self.snapshot,
                    surface_specs=[{"surface_id": "fixture", "path": "fixture.md", "profile": "human"}],
                    require_blocks=False,
                )
                self.assertEqual(bool(issues), not case["expected_valid"], issues)

    def test_real_surface_gate_is_valid_after_step08_repairs(self) -> None:
        result = gate.validate_repository()
        self.assertEqual(result["result"], "VALID", result["issues"])
        self.assertEqual(result["issue_count"], 0)


if __name__ == "__main__":
    unittest.main()
