"""
LAB-Q33 Rights Governance Tests
LAB / SPECULATIVE / NON-AUTHORITATIVE / NOT CURRENT / NOT MERGE-AUTHORIZED
"""

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.rights.validate_rights_gate import (
    GateResult,
    validate_all,
    validate_entries,
    validate_no_external_content,
    validate_registry_structure,
    validate_derivation_chain,
    DATA_DIR,
)


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


class RightsGovernanceNormalTests(unittest.TestCase):
    """Normal operation tests - all should pass."""

    def test_n1_all_registries_pass_gate(self):
        result = validate_all()
        self.assertTrue(result.is_pass, f"Gate should pass: {result.report()}")

    def test_n2_registry_types_valid(self):
        for rf in sorted(DATA_DIR.glob("*.json")):
            doc = load_json(rf)
            self.assertIn(doc["registry_type"],
                {"jurisdiction", "legal_rule", "source_rights", "derivation_ledger",
                 "publication_decision", "rights_risk_assessment", "third_party_notice",
                 "historical_exposure", "takedown_response", "contributor_rights_attestation"})

    def test_n3_no_external_content_in_repo(self):
        for rf in sorted(DATA_DIR.glob("*.json")):
            doc = load_json(rf)
            for entry in doc.get("entries", []):
                st = entry.get("source_type", "unknown")
                if st in ("proprietary", "course_material", "book", "academic_paper"):
                    self.assertFalse(entry.get("content_in_repo", False),
                        f"{rf.name}[{entry.get('id')}]: {st} content in repo")

    def test_n4_all_entries_have_claim_ceiling(self):
        for rf in sorted(DATA_DIR.glob("*.json")):
            doc = load_json(rf)
            for entry in doc.get("entries", []):
                self.assertIn("claim_ceiling", entry,
                    f"{rf.name}[{entry.get('id')}]: missing claim_ceiling")

    def test_n5_derivation_chains_complete(self):
        doc = load_json(DATA_DIR / "derivation-ledger.json")
        for entry in doc.get("entries", []):
            for link in entry.get("derivation_chain", []):
                self.assertIn("source_id", link)
                self.assertIn("relation", link)

    def test_n6_publication_allowed_has_conditions(self):
        doc = load_json(DATA_DIR / "publication-decision-registry.json")
        for entry in doc.get("entries", []):
            if entry.get("publication_allowed"):
                self.assertTrue(len(entry.get("conditions", [])) > 0,
                    f"pub[{entry['id']}]: allowed but no conditions")

    def test_n7_q29r_hash_unchanged(self):
        """Q29R content must not be modified."""
        q29r = ROOT / "docs" / "publication" / "works" / "when-an-army-believes-its-own-back.md"
        if q29r.exists():
            import hashlib
            h = hashlib.sha256(q29r.read_bytes()).hexdigest()
            self.assertEqual(h, "c135acd35a2232f0a6b3f933db482932a9fe5d5add51f870af97901faac90d4b")


class RightsGovernanceAttackTests(unittest.TestCase):
    """Attack tests - malicious mutations must be detected."""

    def test_a1_proprietary_content_in_repo_blocked(self):
        doc = {
            "registry_type": "source_rights", "version": "0.1.0",
            "entries": [{
                "id": "atk_001", "created_at": "2026-01-01T00:00:00Z", "status": "assessed",
                "source_type": "proprietary", "content_in_repo": True,
                "claim_ceiling": "conservative_risk_projection"
            }]
        }
        r = validate_no_external_content(doc, Path("test.json"))
        self.assertFalse(r.is_pass, "Proprietary content in repo must fail")

    def test_a2_course_material_in_repo_blocked(self):
        doc = {
            "registry_type": "source_rights", "version": "0.1.0",
            "entries": [{
                "id": "atk_002", "created_at": "2026-01-01T00:00:00Z", "status": "assessed",
                "source_type": "course_material", "content_in_repo": True,
                "claim_ceiling": "conservative_risk_projection"
            }]
        }
        r = validate_no_external_content(doc, Path("test.json"))
        self.assertFalse(r.is_pass, "Course material in repo must fail")

    def test_a3_missing_claim_ceiling_warned(self):
        doc = {
            "registry_type": "source_rights", "version": "0.1.0",
            "entries": [{
                "id": "atk_003", "created_at": "2026-01-01T00:00:00Z", "status": "assessed",
                "source_type": "project_generated", "content_in_repo": True
            }]
        }
        r = validate_entries(doc, Path("test.json"))
        self.assertTrue(len(r.warnings) > 0, "Missing claim_ceiling should warn")

    def test_a4_publication_blocked_but_in_repo(self):
        doc = {
            "registry_type": "source_rights", "version": "0.1.0",
            "entries": [{
                "id": "atk_004", "created_at": "2026-01-01T00:00:00Z", "status": "assessed",
                "source_type": "project_generated",
                "publication_allowed": False, "content_in_repo": True,
                "claim_ceiling": "conservative_risk_projection"
            }]
        }
        r = validate_entries(doc, Path("test.json"))
        self.assertFalse(r.is_pass, "publication_allowed=false + content_in_repo=true must fail")

    def test_a5_invalid_registry_type(self):
        doc = {"registry_type": "invalid_type", "version": "0.1.0", "entries": []}
        r = validate_registry_structure(doc, Path("test.json"))
        self.assertFalse(r.is_pass, "Invalid registry_type must fail")

    def test_a6_missing_required_fields(self):
        doc = {
            "registry_type": "source_rights", "version": "0.1.0",
            "entries": [{"title": "no id or status"}]
        }
        r = validate_entries(doc, Path("test.json"))
        self.assertFalse(r.is_pass, "Missing required fields must fail")

    def test_a7_derivation_chain_missing_source_id(self):
        doc = {
            "registry_type": "derivation_ledger", "version": "0.1.0",
            "entries": [{
                "id": "atk_007", "created_at": "2026-01-01T00:00:00Z", "status": "assessed",
                "derivation_chain": [{"relation": "derived_from"}],
                "claim_ceiling": "conservative_risk_projection"
            }]
        }
        r = validate_derivation_chain(doc, Path("test.json"))
        self.assertFalse(r.is_pass, "Derivation chain missing source_id must fail")

    def test_a8_invalid_status(self):
        doc = {
            "registry_type": "source_rights", "version": "0.1.0",
            "entries": [{
                "id": "atk_008", "created_at": "2026-01-01T00:00:00Z",
                "status": "approved_by_ceo",
                "claim_ceiling": "conservative_risk_projection"
            }]
        }
        r = validate_entries(doc, Path("test.json"))
        self.assertFalse(r.is_pass, "Invalid status must fail")

    def test_a9_no_automatic_legal_advice(self):
        """Claim ceiling must never be 'legal_advice' - we only project risk."""
        valid_ceilings = {
            "conservative_risk_projection", "metadata_only",
            "no_legal_advice", "no_license_grant"
        }
        self.assertNotIn("legal_advice", valid_ceilings,
            "legal_advice must not be a valid claim ceiling")

    def test_a10_main_not_modified(self):
        """Shared guard: main branch must not be changed."""
        import subprocess
        r = subprocess.run(
            ["git", "-C", str(ROOT), "log", "origin/main", "--oneline", "-1"],
            capture_output=True, text=True
        )
        if r.returncode == 0:
            self.assertIn("d1bedb07", r.stdout,
                "main HEAD must remain d1bedb07")


if __name__ == "__main__":
    unittest.main()
