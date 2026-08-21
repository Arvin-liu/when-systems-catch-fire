from __future__ import annotations

import copy
import json
import unittest

from tools import validate_current_release_lifecycle as lifecycle


class CurrentReleaseLifecycleTests(unittest.TestCase):
    def test_current_lifecycle_owns_content_readiness_not_publication(self) -> None:
        self.assertEqual(lifecycle.validate(), [])
        record = lifecycle.load_json(lifecycle.LIFECYCLE_PATH)
        self.assertIn(record["content_phase"], {"RUNNING", "TERMINAL_CANDIDATE", "RELEASE_READY"})
        self.assertEqual(record["task_id"], "IGNITION-20260822-132")
        self.assertEqual(record["task_identity_source"]["binding"], "MUST_MATCH_CURRENT_FORMAL_AND_EXECUTION_CONTRACT")
        self.assertEqual(record["required_publication_ref"], "refs/heads/main")
        self.assertEqual(record["publication_authority"], "REMOTE_REF_OBSERVATION")
        self.assertEqual(record["embedded_publication_assertion"], "NONE")

    def test_terminal_phase_requires_terminal_task(self) -> None:
        record = lifecycle.load_json(lifecycle.LIFECYCLE_PATH)
        record["content_phase"] = "TERMINAL_CANDIDATE"
        record["current_task_terminal"] = False
        self.assertTrue(any("must be terminal" in error for error in lifecycle.validate(record)))

    def test_negative_fixtures_reject_legacy_and_self_referential_fields(self) -> None:
        base = lifecycle.load_json(lifecycle.LIFECYCLE_PATH)
        fixture_path = lifecycle.ROOT / "data/operations/iterations/131/fixtures/current-release-lifecycle-negative-fixtures-r1.json"
        fixtures = json.loads(fixture_path.read_text(encoding="utf-8"))["fixtures"]
        for fixture in fixtures:
            with self.subTest(fixture_id=fixture["fixture_id"]):
                candidate = copy.deepcopy(base)
                candidate.update(fixture["overrides"])
                self.assertTrue(lifecycle.validate(candidate), fixture["fixture_id"])


if __name__ == "__main__":
    unittest.main()
