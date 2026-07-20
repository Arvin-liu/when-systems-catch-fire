#!/usr/bin/env python3
"""P2 (F3): negative/mutation tests proving the generator-only authority bypass is closed.

Each case builds a malicious/incorrect authority and asserts the validator REJECTS it
(non-zero exit and an expected failure substring). The validator is invoked end-to-end
via subprocess so the schema + registry verification both run.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VALIDATOR = os.path.join(REPO_ROOT, "tools", "operations", "validate_generated_output_authority.py")
GEN_REG = os.path.join(REPO_ROOT, "data", "operations", "generator-registry.json")
HEAD = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=REPO_ROOT).stdout.strip()

DUMMY_DIGEST = "0" * 64


def _run(authority_obj):
    with tempfile.NamedTemporaryFile("w", suffix=".json", dir=REPO_ROOT, delete=False, encoding="utf-8") as af:
        json.dump(authority_obj, af)
        auth_path = af.name
    req = {"changed_paths": [], "base_identity": HEAD}
    with tempfile.NamedTemporaryFile("w", suffix=".json", dir=REPO_ROOT, delete=False, encoding="utf-8") as rf:
        json.dump(req, rf)
        req_path = rf.name
    try:
        r = subprocess.run(
            [sys.executable, VALIDATOR, "--authority", auth_path,
             "--request", req_path, "--base", HEAD, "--generator-registry", GEN_REG],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        return r.returncode, r.stdout + r.stderr
    finally:
        os.unlink(auth_path)
        os.unlink(req_path)


def _authority(entries):
    return {
        "schema_version": "1.0.0",
        "task_id": "121Q33-NEG",
        "description": "negative test authority",
        "generated_outputs": entries,
    }


class GeneratedOutputAuthorityNegativeTests(unittest.TestCase):
    def test_q32_authority_is_schema_valid(self):
        """The real Q32 authority (with registered_generator entries) must pass schema validation."""
        import jsonschema
        from jsonschema import Draft202012Validator
        auth = json.load(open(os.path.join(REPO_ROOT, "data", "operations", "generated-output-authority.json"), encoding="utf-8"))
        schema = json.load(open(os.path.join(REPO_ROOT, "schemas", "operations", "generated-output-authority.schema.json"), encoding="utf-8"))
        errs = list(Draft202012Validator(schema).iter_errors(auth))
        self.assertEqual(errs, [], f"Q32 authority schema errors: {[e.message for e in errs]}")

    def test_generator_registry_is_schema_valid(self):
        import jsonschema
        from jsonschema import Draft202012Validator
        reg = json.load(open(GEN_REG, encoding="utf-8"))
        schema = json.load(open(os.path.join(REPO_ROOT, "schemas", "operations", "generator-registry.schema.json"), encoding="utf-8"))
        errs = list(Draft202012Validator(schema).iter_errors(reg))
        self.assertEqual(errs, [], f"Generator registry schema errors: {[e.message for e in errs]}")

    def test_free_string_generator_rejected(self):
        """A free-string `generator` field (the old bypass) must fail schema validation."""
        auth = _authority([{
            "path": "README.md",
            "generator": "ATTACKER_FREE_STRING",
            "justification": "launder a sensitive file",
        }])
        rc, out = _run(auth)
        self.assertNotEqual(rc, 0, "free-string generator must be rejected")
        self.assertIn("Schema error", out, "expected schema rejection of free-string generator")

    def test_unregistered_generator_id_rejected(self):
        auth = _authority([{
            "path": "README.md",
            "generator_id": "NOPE_NOT_REGISTERED",
            "canonical_tool": "tools/evil.py",
            "input_authorities": ["README.md"],
            "output_type": "report",
            "freshness_mode": "timestamp_based",
            "coverage_class": "generated_output",
            "lifecycle_status": "active",
            "authority_schema_version": "1.0.0",
            "content_digest_sha256": DUMMY_DIGEST,
            "justification": "x",
        }])
        rc, out = _run(auth)
        self.assertNotEqual(rc, 0)
        self.assertIn("NOT in generator-registry.json", out)

    def test_generator_not_allowed_for_path_rejected(self):
        auth = _authority([{
            "path": "README.md",
            "generator_id": "compute_change_propagation",
            "canonical_tool": "tools/operations/compute_change_propagation.py",
            "input_authorities": [
                "data/operations/propagation/121Q32I-request.json",
                "data/operations/project-components.json",
                "data/operations/change-propagation-topology.json",
                "data/operations/synchronization-surfaces.json",
            ],
            "output_type": "report",
            "freshness_mode": "byte_level_recompute",
            "coverage_class": "generated_output",
            "lifecycle_status": "active",
            "authority_schema_version": "1.0.0",
            "content_digest_sha256": DUMMY_DIGEST,
            "justification": "x",
        }])
        rc, out = _run(auth)
        self.assertNotEqual(rc, 0)
        self.assertIn("not an allowed output", out)

    def test_input_authority_drift_rejected(self):
        auth = _authority([{
            "path": "data/operations/propagation/121Q32I-report.json",
            "generator_id": "compute_change_propagation",
            "canonical_tool": "tools/operations/compute_change_propagation.py",
            "input_authorities": ["README.md"],  # drifted from registry required inputs
            "output_type": "report",
            "freshness_mode": "byte_level_recompute",
            "coverage_class": "generated_output",
            "lifecycle_status": "active",
            "authority_schema_version": "1.0.0",
            "content_digest_sha256": DUMMY_DIGEST,
            "justification": "x",
        }])
        rc, out = _run(auth)
        self.assertNotEqual(rc, 0)
        self.assertIn("input_authorities", out)

    def test_stale_digest_rejected(self):
        auth = _authority([{
            "path": "data/operations/propagation/121Q32I-report.json",
            "generator_id": "compute_change_propagation",
            "canonical_tool": "tools/operations/compute_change_propagation.py",
            "input_authorities": [
                "data/operations/propagation/121Q32I-request.json",
                "data/operations/project-components.json",
                "data/operations/change-propagation-topology.json",
                "data/operations/synchronization-surfaces.json",
            ],
            "output_type": "report",
            "freshness_mode": "byte_level_recompute",
            "coverage_class": "generated_output",
            "lifecycle_status": "active",
            "authority_schema_version": "1.0.0",
            "content_digest_sha256": DUMMY_DIGEST,  # wrong digest -> stale/tampered
            "justification": "x",
        }])
        rc, out = _run(auth)
        self.assertNotEqual(rc, 0)
        self.assertIn("content_digest_sha256 mismatch", out)

    def test_historical_record_cannot_claim_current(self):
        seal_file = "reports/operations/121Q33-completion-seal.json"
        seal_digest = subprocess.run(
            ["git", "hash-object", seal_file], capture_output=True, text=True, cwd=REPO_ROOT
        ).stdout.strip()
        auth = _authority([{
            "path": "data/operations/propagation/121Q33-closure.json",
            "sealed_ref": "121Q33",
            "seal_file": seal_file,
            "seal_sha256": seal_digest if seal_digest else DUMMY_DIGEST,
            "output_type": "materialized_projection",
            "coverage_class": "generated_output",
            "historical_only": True,
            "lifecycle_status": "active",  # illegal: historical record cannot be current
            "justification": "x",
        }])
        rc, out = _run(auth)
        self.assertNotEqual(rc, 0)
        self.assertIn("MUST NOT claim lifecycle_status", out)

    def test_duplicate_semantic_authority_rejected(self):
        auth = _authority([
            {"path": "data/operations/propagation/121Q32-closure.json",
             "producer_id": "compute_change_propagation",
             "producer_command": "python tools/operations/compute_change_propagation.py",
             "input_authorities": ["data/operations/propagation/121Q32-request.json"],
             "output_type": "materialized_projection", "freshness_mode": "byte_level_recompute",
             "coverage_class": "generated_output", "justification": "x"},
            {"path": "data/operations/propagation/121Q32-closure-DUP.json",
             "producer_id": "compute_change_propagation",
             "producer_command": "python tools/operations/compute_change_propagation.py",
             "input_authorities": ["data/operations/propagation/121Q32-request.json"],
             "output_type": "materialized_projection", "freshness_mode": "byte_level_recompute",
             "coverage_class": "generated_output", "justification": "x"},
        ])
        rc, out = _run(auth)
        self.assertNotEqual(rc, 0)
        self.assertIn("INCONSISTENT duplicate", out)


if __name__ == "__main__":
    unittest.main()
