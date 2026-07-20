#!/usr/bin/env python3
"""P1 (N7): table-driven fail-closed fixtures for the Q33 publication gate.

Each FAILOSED fixture is an attempt to record a too-lenient / malformed decision; the
gate MUST reject every one (fail-closed). Exactly one VALID fixture MUST be accepted.
These run in the Q33 Governance CI so a regression in fail-closed behavior breaks the build.
"""

import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(REPO_ROOT, "tools", "governance")
sys.path.insert(0, TOOLS_DIR)

from fail_closed_publication_gate import FailClosedPublicationGate  # noqa: E402

SCHEMA_VERSION = "governance-gate-v1"


def _base(**over):
    d = {
        "material_id": "FIX",
        "source_category": "third_party_course_material",
        "gate_decision": "BLOCK",
        "classification_level": 4,
        "source_rights_entry_id": "third_party_course_material",
        "content_digest_sha256": "0" * 64,
        "reason": "fixture",
        "rule_ref": "source-rights-registry:third_party_course_material",
        "schema_version": SCHEMA_VERSION,
    }
    d.update(over)
    return d


# (label, override) attempts that MUST be rejected (fail-closed).
FAILOSED = [
    ("self_downgrade_to_pass", {"gate_decision": "PASS", "classification_level": 0}),
    ("forged_lower_level", {"classification_level": 2, "gate_decision": "PASS_WITH_COMPLIANCE"}),
    ("unknown_category", {"source_category": "nope", "source_rights_entry_id": "nope"}),
    ("missing_reason", {"reason": ""}),
    ("missing_rule_ref", {"rule_ref": ""}),
    ("missing_schema_version", {"schema_version": ""}),
    ("bad_digest_format", {"content_digest_sha256": "zzz"}),
    ("self_asserted_provenance", {"provenance_verified": True}),
    ("unknown_field", {"internal_memo": "x"}),
]


class FailClosedFixtureTests(unittest.TestCase):
    def setUp(self):
        self.gate = FailClosedPublicationGate()

    def test_failed_fixtures_rejected(self):
        for label, over in FAILOSED:
            with self.subTest(label):
                r = self.gate.record_gate_decision(_base(**over))
                self.assertFalse(r["success"], f"{label} must be rejected (fail-closed): {r}")

    def test_valid_fixture_accepted(self):
        r = self.gate.record_gate_decision(_base())
        self.assertTrue(r["success"], f"valid fixture must be accepted: {r}")


if __name__ == "__main__":
    unittest.main()
