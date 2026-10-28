"""External attestation schema and validator tests.

Tests the validate_external_attestation.py validator by creating
valid and invalid attestation documents and verifying the validator catches errors.
"""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.validate_external_attestation import validate_attestation_schema, REQUIRED_FIELDS


def _valid_attestation():
    """Return a minimal valid attestation document."""
    return {
        "schema_version": "1.0.0",
        "task_id": "121Q32F12",
        "repository": "Arvin-liu/when-systems-catch-fire",
        "pr_number": 61,
        "base_head": "d1bedb074af8dad8202b4324f3f5bbbb6b308b51",
        "subject_head": "abcdef1234567890abcdef1234567890abcdef12",
        "pr_state": "OPEN",
        "draft": True,
        "merged": False,
        "closure_hash": "2af79b0960184bb99e087ff382369900de5cef56106e8abb0ccd028b66ce223c",
        "map_counts": {"groups": 9, "nodes": 41, "edges": 37},
        "changed_files": 62,
        "foundation_run": 99999999999,
        "function_os_run": 99999999998,
        "pages_run": 99999999997,
        "artifact_id": 99999999,
        "artifact_head_sha": "abcdef1234567890abcdef1234567890abcdef12",
        "github_artifact_archive_digest": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
        "github_artifact_archive_bytes": 5000000,
        "pages_payload_tar_digest": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
        "pages_payload_tar_bytes": 3000000,
        "deploy_conclusion": "skipped",
        "q29r_sha256": "c135acd35a2232f0a6b3f933db482932a9fe5d5add51f870af97901faac90d4b",
        "lifecycle": {
            "candidate": True,
            "accepted": False,
            "merged": False,
            "current": False,
        },
        "external_attestation_status": "attested",
        "generated_at": "2026-07-17T23:00:00Z",
        "evidence_sources": ["github_actions", "pr_body", "artifact_download"],
        "claim_ceiling": "validated_typed_change_propagation_candidate_only",
    }


class ExternalAttestationSchemaTests(unittest.TestCase):

    def test_n1_valid_attestation_passes(self):
        doc = _valid_attestation()
        errors = validate_attestation_schema(doc)
        self.assertEqual(errors, [], f"Valid attestation should pass: {errors}")

    def test_a1_missing_required_field(self):
        doc = _valid_attestation()
        del doc["subject_head"]
        errors = validate_attestation_schema(doc)
        self.assertTrue(any("subject_head" in e for e in errors))

    def test_a2_invalid_sha_format(self):
        doc = _valid_attestation()
        doc["subject_head"] = "not-a-valid-sha"
        errors = validate_attestation_schema(doc)
        self.assertTrue(any("subject_head" in e for e in errors))

    def test_a3_subject_head_must_equal_artifact_head(self):
        doc = _valid_attestation()
        doc["artifact_head_sha"] = "0000000000000000000000000000000000000000"
        errors = validate_attestation_schema(doc)
        self.assertTrue(any("subject_head" in e and "artifact_head_sha" in e for e in errors))

    def test_a4_draft_with_accepted_lifecycle(self):
        doc = _valid_attestation()
        doc["lifecycle"]["accepted"] = True
        errors = validate_attestation_schema(doc)
        self.assertTrue(any("draft" in e.lower() for e in errors))

    def test_a5_invalid_pr_state(self):
        doc = _valid_attestation()
        doc["pr_state"] = "UNKNOWN"
        errors = validate_attestation_schema(doc)
        self.assertTrue(any("pr_state" in e for e in errors))

    def test_a6_invalid_deploy_conclusion(self):
        doc = _valid_attestation()
        doc["deploy_conclusion"] = "exploded"
        errors = validate_attestation_schema(doc)
        self.assertTrue(any("deploy_conclusion" in e for e in errors))

    def test_a7_digest_not_sha256(self):
        doc = _valid_attestation()
        doc["github_artifact_archive_digest"] = "md5:abcdef"
        errors = validate_attestation_schema(doc)
        self.assertTrue(any("github_artifact_archive_digest" in e for e in errors))

    def test_a8_identical_digests_same_bytes(self):
        """Identical digests with same bytes must fail unconditionally."""
        doc = _valid_attestation()
        doc["github_artifact_archive_digest"] = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        doc["pages_payload_tar_digest"] = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        doc["github_artifact_archive_bytes"] = 5000
        doc["pages_payload_tar_bytes"] = 5000
        errors = validate_attestation_schema(doc)
        self.assertTrue(any("identical" in e.lower() for e in errors))

    def test_a11_identical_digests_different_bytes(self):
        """Identical digests with different byte lengths must still fail unconditionally."""
        doc = _valid_attestation()
        doc["github_artifact_archive_digest"] = "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        doc["pages_payload_tar_digest"] = "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        doc["github_artifact_archive_bytes"] = 97565
        doc["pages_payload_tar_bytes"] = 440320  # different bytes, same digest
        errors = validate_attestation_schema(doc)
        self.assertTrue(any("identical" in e.lower() for e in errors),
                        f"Identical digests must fail even with different byte lengths: {errors}")

    def test_a9_claim_ceiling_must_indicate_candidate(self):
        doc = _valid_attestation()
        doc["claim_ceiling"] = "full_production_ready"
        errors = validate_attestation_schema(doc)
        self.assertTrue(any("claim_ceiling" in e for e in errors))

    def test_a10_all_required_fields_checked(self):
        """Every field in REQUIRED_FIELDS must be validated."""
        for field in REQUIRED_FIELDS:
            doc = _valid_attestation()
            del doc[field]
            errors = validate_attestation_schema(doc)
            self.assertTrue(len(errors) > 0, f"Missing {field} should produce error")


if __name__ == "__main__":
    unittest.main()
