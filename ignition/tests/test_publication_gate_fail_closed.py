#!/usr/bin/env python3
"""
P3 (F4) negative / mutation tests for the fail-closed publication gate.

These prove the gate can no longer be tricked into recording a fail-open decision:
  - private note reported as level 0 + PASS is rejected (no self-reported lower risk)
  - unknown source category fails closed (not recorded)
  - missing verified provenance reference / reason / rule / version is rejected
  - extra unknown field is rejected by the schema (additionalProperties:false)
  - forged classification level is rejected
  - registry<->gate enum drift is rejected
  - ai_generated_content maps to level 5 / BLOCK_PENDING_COUNSEL
"""

import json
import os
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(REPO_ROOT, "tools", "governance")
SRC_REG_PATH = os.path.join(REPO_ROOT, "data", "governance", "source-rights-registry.json")
sys.path.insert(0, TOOLS_DIR)

from fail_closed_publication_gate import FailClosedPublicationGate  # noqa: E402


def _pinned_digest_for(category):
    """Return the registry-pinned content_digest_sha256 for a VERIFIED source category,
    else None. Lets _good_decision supply a digest that passes the gate's provenance
    verification so each test exercises its intended assertion (not a digest-mismatch pre-emption)."""
    try:
        with open(SRC_REG_PATH, "r", encoding="utf-8") as f:
            reg = json.load(f)
        prov = reg.get("categories", {}).get(category, {}).get("provenance", {})
        if prov.get("verification_status") == "VERIFIED":
            return prov.get("content_digest_sha256")
    except Exception:
        pass
    return None


SCHEMA_VERSION = "governance-gate-v1"


def _good_decision(**overrides):
    d = {
        "material_id": "NEG-001",
        "source_category": "third_party_course_material",
        "gate_decision": "BLOCK",
        "classification_level": 4,
        "reason": "course material: author owns copyright",
        "rule_ref": "source-rights-registry:third_party_course_material",
        "schema_version": SCHEMA_VERSION,
    }
    d.update(overrides)
    # Verified provenance reference (source_rights_entry_id + content_digest_sha256).
    # For VERIFIED sources with a pinned registry digest, supply the real digest so the
    # gate's provenance verification passes and the test exercises its intended assertion.
    d.setdefault("source_rights_entry_id", d["source_category"])
    d.setdefault("content_digest_sha256", _pinned_digest_for(d["source_category"]) or "0" * 64)
    return d


class PublicationGateFailClosedTests(unittest.TestCase):
    def setUp(self):
        self.ledger = tempfile.TemporaryDirectory(prefix="publication-gate-test-")
        self.addCleanup(self.ledger.cleanup)
        self.gate = FailClosedPublicationGate(
            decisions_path=os.path.join(self.ledger.name, "publication-gate-decisions.jsonl")
        )

    def test_private_note_reported_as_level0_pass_is_rejected(self):
        """F4 core: a critical private note cannot be downgraded to level 0 + PASS."""
        d = _good_decision(
            material_id="NEG-PRIVATE",
            source_category="third_party_private_note",
            gate_decision="PASS",
            classification_level=0,
            rule_ref="source-rights-registry:third_party_private_note",
        )
        r = self.gate.record_gate_decision(d)
        self.assertFalse(r["success"], f"private note level0+PASS must be rejected, got {r}")
        self.assertTrue(any("classification_level" in e for e in r.get("errors", [])),
                        f"error should cite classification_level drift: {r}")

    def test_unknown_category_fails_closed(self):
        """Unknown source category must not be recorded (fail-closed default)."""
        d = _good_decision(
            material_id="NEG-UNKNOWN",
            source_category="nonexistent_category",
            gate_decision="BLOCK",
            classification_level=6,
            rule_ref="n/a",
        )
        r = self.gate.record_gate_decision(d)
        self.assertFalse(r["success"], f"unknown category must fail closed, got {r}")
        self.assertTrue(any("fail-closed" in e.lower() for e in r.get("errors", [])),
                        f"error should mention fail-closed: {r}")

    def test_missing_provenance_reason_rule_version_rejected(self):
        """Missing verified provenance reference / reason / rule / version are rejected."""
        # verified provenance reference (source_rights_entry_id) missing
        d = _good_decision()
        del d["source_rights_entry_id"]
        r = self.gate.record_gate_decision(d)
        self.assertFalse(r["success"])
        self.assertTrue(any("source_rights_entry_id" in e for e in r["errors"]))

        # content_digest_sha256 missing
        d = _good_decision()
        del d["content_digest_sha256"]
        r = self.gate.record_gate_decision(d)
        self.assertFalse(r["success"])
        self.assertTrue(any("content_digest_sha256" in e for e in r["errors"]))

        # reason missing
        d = _good_decision()
        del d["reason"]
        r = self.gate.record_gate_decision(d)
        self.assertFalse(r["success"])
        self.assertTrue(any("reason" in e for e in r["errors"]))

        # rule_ref missing
        d = _good_decision()
        del d["rule_ref"]
        r = self.gate.record_gate_decision(d)
        self.assertFalse(r["success"])
        self.assertTrue(any("rule_ref" in e for e in r["errors"]))

        # schema_version missing
        d = _good_decision()
        del d["schema_version"]
        r = self.gate.record_gate_decision(d)
        self.assertFalse(r["success"])
        self.assertTrue(any("schema_version" in e for e in r["errors"]))

    def test_self_asserted_provenance_verified_rejected(self):
        """A caller may not self-assert provenance_verified:True for a non-pinned source."""
        d = _good_decision(provenance_verified=True)
        r = self.gate.record_gate_decision(d)
        self.assertFalse(r["success"])
        self.assertTrue(any("provenance_verified" in e for e in r["errors"]))

    def test_extra_unknown_field_rejected_by_schema(self):
        """A sneaked-in unknown field must be rejected by additionalProperties:false."""
        d = _good_decision(internal_memo="should not be here")
        r = self.gate.record_gate_decision(d)
        self.assertFalse(r["success"], f"unknown field must be rejected by schema, got {r}")
        joined = " ".join(r.get("errors", [])).lower()
        self.assertTrue("unknown" in joined or "additional" in joined or "internal_memo" in joined,
                        f"error should cite unknown field: {r}")

    def test_forged_classification_level_rejected(self):
        """Report a lower classification_level than the registry derives -> rejected."""
        d = _good_decision(
            material_id="NEG-FORGE",
            source_category="third_party_paywall_article",  # PUBLISHER_OR_AUTHOR_OWNS -> level 4
            gate_decision="PASS_WITH_COMPLIANCE",
            classification_level=2,  # forged down
            rule_ref="source-rights-registry:third_party_paywall_article",
        )
        r = self.gate.record_gate_decision(d)
        self.assertFalse(r["success"], f"forged level 2 must be rejected, got {r}")
        self.assertTrue(any("classification_level" in e for e in r.get("errors", [])),
                        f"error should cite classification_level: {r}")

    def test_registry_gate_enum_drift_rejected(self):
        """Gate decision that drifts from the registry-derived gate is rejected."""
        d = _good_decision(
            material_id="NEG-DRIFT",
            source_category="open_license_cc_by_nc_sa",  # NON_COMMERCIAL_ONLY -> level 3 -> CONDITIONAL_PASS
            gate_decision="PASS",  # drift from CONDITIONAL_PASS
            classification_level=3,
            rule_ref="source-rights-registry:open_license_cc_by_nc_sa",
        )
        r = self.gate.record_gate_decision(d)
        self.assertFalse(r["success"], f"gate enum drift must be rejected, got {r}")
        self.assertTrue(any("gate_decision" in e for e in r.get("errors", [])),
                        f"error should cite gate_decision: {r}")

    def test_ai_generated_content_maps_to_level5_counsel(self):
        """F10: ai_generated_content has unsettled US jurisprudence -> level 5, counsel."""
        c = self.gate.classify_material("NEG-AI", "ai_generated_content")
        self.assertEqual(c["classification_level"], 5, c)
        self.assertEqual(c["gate_decision"], "BLOCK_PENDING_COUNSEL", c)
        # And a correctly-submitted level-5 decision is accepted.
        d = _good_decision(
            material_id="NEG-AI",
            source_category="ai_generated_content",
            gate_decision="BLOCK_PENDING_COUNSEL",
            classification_level=5,
            rule_ref="source-rights-registry:ai_generated_content",
        )
        r = self.gate.record_gate_decision(d)
        self.assertTrue(r["success"], f"level-5 AI decision should be recorded, got {r}")

    def test_valid_decision_is_recorded(self):
        """Sanity: a correct submission is accepted and persisted in-memory."""
        d = _good_decision()
        r = self.gate.record_gate_decision(d)
        self.assertTrue(r["success"], f"valid decision should be recorded, got {r}")
        self.assertEqual(r["gate_decision"], "BLOCK")


if __name__ == "__main__":
    unittest.main(verbosity=2)
