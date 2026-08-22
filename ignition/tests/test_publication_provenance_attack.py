#!/usr/bin/env python3
"""
P4C negative tests: publication provenance is now a *verified registry reference*
(source_rights_entry_id + content_digest_sha256), never a free-text boolean
self-assertion. These prove:

  - source_rights_entry_id must exist in the source-rights-registry
  - source_rights_entry_id must equal source_category (provenance category match)
  - a content_digest_sha256 mismatch against a VERIFIED entry's pinned digest is
    rejected (tamper / consistency check)
  - a caller cannot self-assert provenance_verified:True for a non-pinned source
"""

import os
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(REPO_ROOT, "tools", "governance")
sys.path.insert(0, TOOLS_DIR)

from fail_closed_publication_gate import FailClosedPublicationGate  # noqa: E402

SCHEMA_VERSION = "governance-gate-v1"


def _decision(**overrides):
    d = {
        "material_id": "PROV-001",
        "source_category": "third_party_course_material",
        "gate_decision": "BLOCK",
        "classification_level": 4,
        "source_rights_entry_id": "third_party_course_material",
        "content_digest_sha256": "0" * 64,
        "reason": "course material: author owns copyright",
        "rule_ref": "source-rights-registry:third_party_course_material",
        "schema_version": SCHEMA_VERSION,
    }
    d.update(overrides)
    return d


class PublicationProvenanceAttackTests(unittest.TestCase):
    def setUp(self):
        self.ledger = tempfile.TemporaryDirectory(prefix="publication-provenance-test-")
        self.addCleanup(self.ledger.cleanup)
        self.gate = FailClosedPublicationGate(
            decisions_path=os.path.join(self.ledger.name, "publication-gate-decisions.jsonl")
        )

    def test_entry_id_must_exist_in_registry(self):
        """A provenance reference that does not point to a real registry entry is rejected."""
        d = _decision(source_rights_entry_id="no_such_entry")
        r = self.gate.record_gate_decision(d)
        self.assertFalse(r["success"], f"unknown entry id must be rejected: {r}")
        self.assertTrue(any("source_rights_entry_id" in e for e in r.get("errors", [])),
                        f"error should cite entry id: {r}")

    def test_entry_id_must_equal_source_category(self):
        """Entry id may exist but must match source_category (no cross-category provenance)."""
        d = _decision(source_category="public_domain",
                      source_rights_entry_id="third_party_course_material")
        r = self.gate.record_gate_decision(d)
        self.assertFalse(r["success"], f"entry id != source_category must be rejected: {r}")
        self.assertTrue(any("source_rights_entry_id" in e for e in r.get("errors", [])),
                        f"error should cite provenance category mismatch: {r}")

    def test_digest_mismatch_for_verified_source_rejected(self):
        """For a VERIFIED source with a pinned digest, a submitted mismatch is rejected."""
        # Pin a digest on an in-memory VERIFIED entry (does not touch the on-disk registry).
        cat = self.gate.source_rights_registry["categories"]["open_license_cc_by"]
        cat.setdefault("provenance", {})["content_digest_sha256"] = "a" * 64
        d = _decision(
            source_category="open_license_cc_by",
            gate_decision="PASS",
            classification_level=1,
            source_rights_entry_id="open_license_cc_by",
            content_digest_sha256="b" * 64,
            rule_ref="source-rights-registry:open_license_cc_by",
        )
        r = self.gate.record_gate_decision(d)
        self.assertFalse(r["success"], f"digest mismatch for VERIFIED source must be rejected: {r}")
        self.assertTrue(any("digest" in e.lower() for e in r.get("errors", [])),
                        f"error should cite digest mismatch: {r}")

    def test_self_asserted_provenance_verified_rejected(self):
        """A caller may not claim provenance_verified:True for a non-pinned source."""
        d = _decision(provenance_verified=True)
        r = self.gate.record_gate_decision(d)
        self.assertFalse(r["success"], f"self-asserted provenance_verified must be rejected: {r}")
        self.assertTrue(any("provenance_verified" in e for e in r.get("errors", [])),
                        f"error should cite provenance_verified: {r}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
