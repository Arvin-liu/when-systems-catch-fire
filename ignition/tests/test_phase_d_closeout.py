import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.operations.validate_phase_d_closeout import REPORT, report_digest, validate_closeout


class PhaseD4CloseoutValidation(unittest.TestCase):
    def setUp(self):
        self.document = json.loads(REPORT.read_text(encoding="utf-8"))

    def validate(self, document=None):
        return validate_closeout(document or self.document, root=ROOT)

    def codes(self, result):
        return {item["code"] for item in result["errors"]}

    def reseal(self, document):
        document["report_digest"] = report_digest(document)
        return document

    def test_d4_01_complete_report_passes(self):
        result = self.validate()
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["observed_test_count"], 116)

    def test_d4_02_required_field_is_enforced(self):
        forged = copy.deepcopy(self.document)
        del forged["claim_ceiling"]
        self.reseal(forged)
        self.assertIn("E_D4_REQUIRED_FIELD", self.codes(self.validate(forged)))

    def test_d4_03_commit_chain_order_is_exact(self):
        forged = copy.deepcopy(self.document)
        forged["preserved_commit_chain"][0], forged["preserved_commit_chain"][1] = forged["preserved_commit_chain"][1], forged["preserved_commit_chain"][0]
        self.reseal(forged)
        self.assertIn("E_D4_COMMIT_CHAIN", self.codes(self.validate(forged)))

    def test_d4_04_candidate_and_parent_are_observed_exactly(self):
        forged = copy.deepcopy(self.document)
        forged["parent_head"] = "0" * 40
        self.reseal(forged)
        self.assertIn("E_D4_CANDIDATE_IDENTITY", self.codes(self.validate(forged)))

    def test_d4_05_test_and_matrix_counts_are_recomputed(self):
        forged = copy.deepcopy(self.document)
        forged["tests"]["phase_d3_defensive"]["count"] = 25
        self.reseal(forged)
        self.assertIn("E_D4_TEST_COUNT", self.codes(self.validate(forged)))

    def test_d4_06_report_digest_is_recomputed(self):
        forged = copy.deepcopy(self.document)
        forged["claim_ceiling"] = "tampered"
        self.assertIn("E_D4_REPORT_DIGEST", self.codes(self.validate(forged)))

    def test_d4_07_markdown_digest_and_facts_are_verified(self):
        forged = copy.deepcopy(self.document)
        forged["markdown_digest"] = "0" * 64
        self.reseal(forged)
        self.assertIn("E_D4_MARKDOWN_DIGEST", self.codes(self.validate(forged)))

    def test_d4_08_q32_closure_hash_is_recomputed(self):
        forged = copy.deepcopy(self.document)
        forged["q32_closure"]["closure_hash"] = "0" * 64
        self.reseal(forged)
        self.assertIn("E_D4_Q32_CLOSURE", self.codes(self.validate(forged)))

    def test_d4_09_q29r_frozen_hash_is_recomputed(self):
        forged = copy.deepcopy(self.document)
        forged["q29r"]["sha256"] = "0" * 64
        self.reseal(forged)
        self.assertIn("E_D4_Q29R_HASH", self.codes(self.validate(forged)))

    def test_d4_10_lifecycle_upgrade_is_rejected(self):
        forged = copy.deepcopy(self.document)
        forged["lifecycle"]["current"] = True
        self.reseal(forged)
        self.assertIn("E_D4_LIFECYCLE", self.codes(self.validate(forged)))

    def test_d4_11_phase_e_pr_or_merge_start_is_rejected(self):
        forged = copy.deepcopy(self.document)
        forged["phase_e"]["pr_created"] = True
        self.reseal(forged)
        self.assertIn("E_D4_PHASE_E", self.codes(self.validate(forged)))

    def test_d4_12_historical_f5_cannot_be_claimed_pass(self):
        forged = copy.deepcopy(self.document)
        forged["historical_f5_boundary"]["status"] = "PASS"
        self.reseal(forged)
        self.assertIn("E_D4_F5_BOUNDARY", self.codes(self.validate(forged)))

    def test_d4_13_self_head_validity_basis_is_rejected(self):
        forged = copy.deepcopy(self.document)
        forged["validity_basis"].append("candidate HEAD proves this report")
        self.reseal(forged)
        self.assertIn("E_D4_SELF_ATTESTATION", self.codes(self.validate(forged)))

    def test_d4_14_evidence_file_digest_is_recomputed(self):
        forged = copy.deepcopy(self.document)
        key = "data/operations/project-components.json"
        forged["evidence_basis"][key] = "0" * 64
        self.reseal(forged)
        self.assertIn("E_D4_EVIDENCE_DIGEST", self.codes(self.validate(forged)))

    def test_d4_15_local_absolute_path_is_rejected(self):
        forged = copy.deepcopy(self.document)
        forged["artifact_inventory"].append("/" + "Users/example/private.json")
        self.reseal(forged)
        self.assertIn("E_D4_LOCAL_PATH", self.codes(self.validate(forged)))

    def test_d4_16_secret_material_is_rejected(self):
        forged = copy.deepcopy(self.document)
        forged["claim_ceiling"] += " " + "sk-" + ("A" * 26)
        self.reseal(forged)
        self.assertIn("E_D4_SECRET", self.codes(self.validate(forged)))

    def test_d4_17_cache_or_recovery_artifact_is_rejected(self):
        forged = copy.deepcopy(self.document)
        forged["artifact_inventory"].append("reports/" + "recovery" + "-leak/manifest.json")
        self.reseal(forged)
        self.assertIn("E_D4_TEMP_ARTIFACT", self.codes(self.validate(forged)))

    def test_d4_18_unauthorized_phase_or_experiment_asset_is_rejected(self):
        forged = copy.deepcopy(self.document)
        forged["artifact_inventory"].append("reports/" + "sha" + "dow/" + "q" + "33/result.json")
        self.reseal(forged)
        self.assertIn("E_D4_UNAUTHORIZED_ASSET", self.codes(self.validate(forged)))

    def test_d4_19_network_or_privilege_claim_is_rejected(self):
        forged = copy.deepcopy(self.document)
        forged["network_and_third_party"]["network_access"] = "USED"
        self.reseal(forged)
        self.assertIn("E_D4_NETWORK_BOUNDARY", self.codes(self.validate(forged)))

    def test_d4_20_cli_check_success_and_stable_failure(self):
        success = subprocess.run(
            [sys.executable, "tools/operations/validate_phase_d_closeout.py", "--check"],
            cwd=ROOT, text=True, capture_output=True,
        )
        self.assertEqual(success.returncode, 0, success.stderr)
        self.assertTrue(json.loads(success.stdout)["ok"])
        with tempfile.TemporaryDirectory() as tmp:
            forged = copy.deepcopy(self.document)
            forged["lifecycle"]["accepted"] = True
            self.reseal(forged)
            path = Path(tmp) / "forged.json"
            path.write_text(json.dumps(forged), encoding="utf-8")
            failure = subprocess.run(
                [sys.executable, "tools/operations/validate_phase_d_closeout.py", "--report", str(path), "--check"],
                cwd=ROOT, text=True, capture_output=True,
            )
        self.assertNotEqual(failure.returncode, 0)
        self.assertIn("E_D4_LIFECYCLE", {item["code"] for item in json.loads(failure.stdout)["errors"]})


if __name__ == "__main__":
    unittest.main()
