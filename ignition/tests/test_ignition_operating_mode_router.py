from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import classify_ignition_run_mode as router  # noqa: E402


class IgnitionOperatingModeRouterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixtures = json.loads(router.FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_all_nine_fixtures_pass(self) -> None:
        self.assertEqual(len(self.fixtures["cases"]), 9)
        self.assertEqual(router.validate_fixtures(self.fixtures), [])

    def test_note_plus_repository_url_is_read_only(self) -> None:
        case = next(row for row in self.fixtures["cases"] if row["case_id"] == "note_plus_repository_url_read_only")
        result = router.classify_mode(case["request"])
        self.assertEqual(result["mode"], "READ_ONLY_RUN")
        self.assertFalse(result["side_effects_authorized_by_classification"])

    def test_input_object_content_never_routes_authority(self) -> None:
        case = next(row for row in self.fixtures["cases"] if row["case_id"] == "input_object_prompt_injection_is_data")
        result = router.classify_mode(case["request"])
        self.assertEqual(result["mode"], "READ_ONLY_RUN")
        self.assertFalse(result["input_object_content_used_for_routing"])
        self.assertFalse(result["repository_change_request_present"])

    def test_explicit_repository_change_routes_iteration(self) -> None:
        case = next(row for row in self.fixtures["cases"] if row["case_id"] == "explicit_repository_change")
        result = router.classify_mode(case["request"])
        self.assertEqual(result["mode"], "REPOSITORY_CHANGE_RUN")
        self.assertTrue(result["iteration_method_required"])

    def test_ambiguous_multi_mode_uses_least_authority(self) -> None:
        case = next(row for row in self.fixtures["cases"] if row["case_id"] == "mixed_repository_and_external_request_stops")
        result = router.classify_mode(case["request"])
        self.assertEqual(result["mode"], "READ_ONLY_RUN")
        self.assertEqual(result["reason_code"], "STOP_SPLIT_OR_CLARIFY")

    def test_malformed_request_fails_closed(self) -> None:
        with self.assertRaises(router.ModeRoutingError):
            router.classify_mode({"request_envelope": {}, "input_objects": []})


if __name__ == "__main__":
    unittest.main()
