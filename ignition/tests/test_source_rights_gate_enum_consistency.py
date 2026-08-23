"""Source-rights <-> publication-gate two-way consistency (P5 / F10 / 5.2.6).

Guards V18 F10 closure: the source-rights registry, the fail-closed publication
gate, and the JSON Schemas must not drift from one another. Also asserts P5
official-source provenance (5.2.1) and the US fair-use absolute-language
downgrade (5.2.5).
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "governance"))
from fail_closed_publication_gate import FailClosedPublicationGate  # noqa: E402

PublicationGate = FailClosedPublicationGate
LEVEL_MAP = FailClosedPublicationGate.LEVEL_MAP
GATE_MAP = FailClosedPublicationGate.GATE_MAP

GOV = ROOT / "data" / "governance"
SRC_REG = json.loads((GOV / "source-rights-registry.json").read_text(encoding="utf-8"))
JUR_REG = json.loads((GOV / "jurisdiction-rule-registry.json").read_text(encoding="utf-8"))
SRC_SCHEMA = json.loads((ROOT / "schemas" / "governance" / "source-rights-entry.schema.json").read_text(encoding="utf-8"))
GATE_SCHEMA = json.loads((ROOT / "schemas" / "governance" / "publication-gate-decision.schema.json").read_text(encoding="utf-8"))

SRC_RIGHTS_ENUM = set(SRC_SCHEMA["properties"]["rights_status"]["enum"])
SRC_ACTION_ENUM = set(SRC_SCHEMA["properties"]["governance_action"]["enum"])
GATE_DECISION_ENUM = set(GATE_SCHEMA["properties"]["gate_decision"]["enum"])
VALID_VERIFICATION = {
    "VERIFIED", "OFFICIAL_TEXT_NOT_VERIFIED", "LEGAL_REVIEW_REQUIRED",
    "UNVERIFIED", "COUNSEL_REQUIRED", "PERMISSION_REQUIRED",
    "INSUFFICIENT_INFORMATION", "BLOCKED_PENDING_EVIDENCE",
}


class SourceRightsGateConsistencyTests(unittest.TestCase):
    # ---- two-way enum consistency (no drift) ----------------------------------
    def test_gate_levelmap_rights_status_in_schema_enum(self):
        for rs in LEVEL_MAP:
            self.assertIn(
                rs, SRC_RIGHTS_ENUM,
                f"Gate LEVEL_MAP key {rs!r} is not a valid source-rights schema rights_status",
            )

    def test_gate_gatemap_decisions_in_schema_enum(self):
        for g in GATE_MAP.values():
            self.assertIn(
                g, GATE_DECISION_ENUM,
                f"Gate GATE_MAP value {g!r} is not a valid gate_decision schema enum",
            )

    def test_registry_rights_status_in_schema_enum(self):
        for cat, c in SRC_REG["categories"].items():
            self.assertIn(
                c["rights_status"], SRC_RIGHTS_ENUM,
                f"category {cat} rights_status {c['rights_status']!r} not in schema enum",
            )

    def test_registry_governance_action_in_schema_enum(self):
        for cat, c in SRC_REG["categories"].items():
            self.assertIn(
                c["governance_action"], SRC_ACTION_ENUM,
                f"category {cat} governance_action {c['governance_action']!r} not in schema enum",
            )

    def test_gate_source_category_enum_matches_registry(self):
        enum = set(GATE_SCHEMA["properties"]["source_category"]["enum"])
        cats = set(SRC_REG["categories"].keys())
        self.assertEqual(
            enum, cats,
            f"gate source_category schema enum drifted from source-rights registry: "
            f"only_in_enum={sorted(enum - cats)} only_in_registry={sorted(cats - enum)}",
        )

    # ---- concrete two-way for the contested AI-generated category (F10) -------
    def test_ai_generated_two_way_consistency(self):
        ai = SRC_REG["categories"]["ai_generated_content"]
        self.assertEqual(ai["rights_status"], "UNCERTAIN_U_S jurisprudence_pending")
        self.assertEqual(LEVEL_MAP["UNCERTAIN_U_S jurisprudence_pending"], 5)
        self.assertEqual(GATE_MAP[5], "BLOCK_PENDING_COUNSEL")
        gate = PublicationGate()
        derived = gate._derive_expected("ai_generated_content")
        self.assertIsNotNone(derived)
        self.assertEqual(derived["classification_level"], 5)
        self.assertEqual(derived["gate_decision"], "BLOCK_PENDING_COUNSEL")

    def test_every_registry_category_resolves_via_gate(self):
        gate = PublicationGate()
        for cat, c in SRC_REG["categories"].items():
            derived = gate._derive_expected(cat)
            self.assertIsNotNone(
                derived,
                f"category {cat} (rights_status={c['rights_status']!r}) is unmappable by the gate",
            )

    # ---- P5.2.1: every official rule record binds provenance ------------------
    def test_every_source_rights_category_has_provenance(self):
        for cat, c in SRC_REG["categories"].items():
            self.assertIn("provenance", c, f"category {cat} missing provenance block")
            p = c["provenance"]
            for fld in ("retrieved_date", "canonical_url", "source_authority",
                        "version_id", "content_digest_sha256", "verification_status"):
                self.assertIn(fld, p, f"category {cat} provenance missing {fld}")
            self.assertIn(p["verification_status"], VALID_VERIFICATION)

    # ---- P3 (F8): VERIFIED official sources must pin a real content digest ------
    def test_verified_source_rights_must_have_pinned_digest(self):
        """F8 closure: a category claimed VERIFIED must carry a non-null, well-formed
        pinned content_digest_sha256 (no false VERIFIED claim without an authenticatable text)."""
        for cat, c in SRC_REG["categories"].items():
            if c["provenance"]["verification_status"] == "VERIFIED":
                digest = c["provenance"].get("content_digest_sha256")
                self.assertIsNotNone(
                    digest,
                    f"category {cat} is VERIFIED but has no pinned content_digest_sha256 (F8 violation)",
                )
                self.assertRegex(
                    digest,
                    r"^[0-9a-f]{64}$",
                    f"category {cat} pinned digest is not a 64-char hex SHA-256: {digest!r}",
                )

    def test_verified_source_gate_enforces_real_pinned_digest(self):
        """Integration: a VERIFIED category's pinned real digest is enforced end-to-end
        by the fail-closed gate (correct digest accepted+verified; tampered digest rejected)."""
        with tempfile.TemporaryDirectory(prefix="source-rights-gate-test-") as ledger:
            gate = PublicationGate(decisions_path=str(Path(ledger) / "publication-gate-decisions.jsonl"))
            cat = "open_license_cc_by"
            pinned = SRC_REG["categories"][cat]["provenance"]["content_digest_sha256"]
            ok = gate.record_gate_decision({
                "material_id": "F8-VERIFIED-OK",
                "source_category": cat,
                "gate_decision": "PASS_WITH_COMPLIANCE",
                "classification_level": 2,
                "source_rights_entry_id": cat,
                "content_digest_sha256": pinned,
                "reason": "CC BY 4.0 official text digest matches pinned registry digest",
                "rule_ref": "source-rights-registry:open_license_cc_by",
                "schema_version": "governance-gate-v1",
            })
            self.assertTrue(ok["success"], f"VERIFIED decision with correct digest must be recorded: {ok}")

            bad = gate.record_gate_decision({
                "material_id": "F8-VERIFIED-BAD",
                "source_category": cat,
                "gate_decision": "PASS_WITH_COMPLIANCE",
                "classification_level": 2,
                "source_rights_entry_id": cat,
                "content_digest_sha256": "0" * 64,
                "reason": "tampered digest",
                "rule_ref": "source-rights-registry:open_license_cc_by",
                "schema_version": "governance-gate-v1",
            })
        self.assertFalse(bad["success"], "VERIFIED decision with tampered digest must be rejected")
        self.assertTrue(any("digest" in e.lower() for e in bad.get("errors", [])),
                        f"error should cite digest mismatch: {bad}")

    def test_every_jurisdiction_treaty_platform_has_provenance(self):
        for grp in ("treaty_layer", "jurisdictions", "platform_policy"):
            for key, e in JUR_REG[grp].items():
                self.assertIn("provenance", e, f"{grp}/{key} missing provenance block")
                self.assertIn(e["provenance"]["verification_status"], VALID_VERIFICATION)

    # ---- P5.2.5: US fair-use absolute claim downgraded + bounded --------------
    def test_us_fair_use_claim_not_absolute(self):
        co = JUR_REG["jurisdictions"]["US"]["contract_override"]
        self.assertNotIn("NOT_WAIVABLE", co)
        self.assertNotIn("non-waivable", co)
        self.assertNotIn("不可放弃", co)
        prov = JUR_REG["jurisdictions"]["US"]["contract_override_provenance"]
        self.assertEqual(prov["verification_status"], "LEGAL_REVIEW_REQUIRED")
        notable = JUR_REG["summary"]["contract_override_notable"]["US_fair_use_non_waivable"]
        self.assertNotIn("non-waivable", notable)
        self.assertIn("LEGAL_REVIEW_REQUIRED", notable)


if __name__ == "__main__":
    unittest.main()
