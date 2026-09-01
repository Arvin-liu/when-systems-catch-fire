import copy
import json
import unittest

from tools.validate_task150_step10_license_drift import ARTIFACT_PATH, validate


class Task150Step10LicenseDriftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_license_and_drift_receipt_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_mit_attribution_is_recorded(self):
        attribution = self.document["attribution"]
        self.assertEqual(attribution["license"], "MIT")
        self.assertEqual(attribution["copyright_lines"], ["Copyright (c) 2026 tt-a1i (Archify)", "Copyright (c) 2025 Cocoon AI"])
        self.assertTrue(attribution["recorded_in_ignition"])

    def test_compatibility_envelope_is_pinned(self):
        envelope = self.document["compatibility_envelope"]
        self.assertEqual(envelope["name"], "TESTED_COMPATIBILITY_ENVELOPE_ONLY")
        self.assertEqual(envelope["result"], "PASS_AT_PINNED_REVISION_ONLY")
        self.assertEqual(envelope["provider_revision"], "7a16d30322f5bd09c832386faa95d8c9a933f0c0")

    def test_future_revision_requires_fresh_check(self):
        policy = self.document["drift_policy"]
        self.assertTrue(policy["compatibility_check_before_use"])
        self.assertFalse(policy["automatic_update"])
        self.assertEqual(policy["future_claim"], "NO_FUTURE_VERSION_COMPATIBILITY_CLAIM")
        mutated = copy.deepcopy(self.document)
        mutated["drift_policy"]["automatic_update"] = True
        self.assertTrue(validate(mutated))

    def test_upstream_source_is_not_vendored(self):
        self.assertFalse(self.document["upstream_observation"]["vendor_source"])
        mutated = copy.deepcopy(self.document)
        mutated["upstream_observation"]["vendor_source"] = True
        self.assertTrue(validate(mutated))

    def test_scope_and_current_boundaries_remain_closed(self):
        scope = self.document["scope_freeze"]
        self.assertEqual(scope["current_admission"], "NOT_ADMITTED")
        self.assertEqual(scope["agent_reach"], "NO_CHANGE")
        self.assertEqual(scope["authenticated_channels"], "NO_AUTHENTICATED_ADMISSION")
        self.assertEqual(scope["live_external_invocation"], "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN")


if __name__ == "__main__":
    unittest.main()
