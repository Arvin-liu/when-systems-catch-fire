import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.operations.validate_phase_e_candidate import (
    ROOT,
    DEMO,
    MANIFEST,
    REQUEST,
    validate,
    resolve_demo_era_ref,
    load,
)
from tools.operations.plan_incremental_execution import build_authority_bundle, plan, git_json


class PhaseECandidateTests(unittest.TestCase):
    def test_real_lifecycle_passes(self):
        result = validate()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["decision"], "FULL_REBUILD_REQUIRED")

    def test_lifecycle_inflation_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fixture = Path(td)
            for rel in ("data/operations/propagation/121Q32I-request.json", "reports/operations/121Q32I-incremental-execution-demonstration.json", "data/operations/iterations/121Q32I.json", "reports/operations/121Q32I-completion-seal.json", "docs/publication/works/when-an-army-believes-its-own-back.md", "data/operations/project-components.json", "data/operations/change-propagation-topology.json", "data/operations/component-execution-profiles.json"):
                target = fixture / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / rel).read_bytes())
            manifest_path = fixture / "data/operations/iterations/121Q32I.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["status"]["accepted"] = False
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "E_PHASE_E_LIFECYCLE"):
                validate(fixture)

    def _resolved_era(self):
        return resolve_demo_era_ref(load(DEMO), load(MANIFEST)["branch_pr"]["merge_commit"])

    def test_live_authority_bundle_differs_from_q32i_era(self):
        era = self._resolved_era()
        _, era_fp = build_authority_bundle(era)
        _, live_fp = build_authority_bundle(None)
        self.assertNotEqual(live_fp, era_fp, "live authority must differ from the Q32I sealed era authority")

    def test_persisted_demo_equals_era_recompute(self):
        era = self._resolved_era()
        era_bundle, era_fp = build_authority_bundle(era)
        era_request = git_json(era, str(REQUEST.relative_to(ROOT)))
        era_plan = plan(era_request, era_ref=era, authority_bundle=era_bundle, authority_fingerprint_value=era_fp)
        self.assertEqual(era_plan, load(DEMO)["planner_output"])

    def test_persisted_demo_differs_from_live_recompute(self):
        live_request = load(REQUEST)
        live_bundle, live_fp = build_authority_bundle(None)
        live_plan = plan(live_request, era_ref=None, authority_bundle=live_bundle, authority_fingerprint_value=live_fp)
        self.assertNotEqual(live_plan["plan_hash"], load(DEMO)["planner_output"]["plan_hash"])

    def test_current_lifecycle_validated_by_sealed_era(self):
        era = self._resolved_era()
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        self.assertNotEqual(era, head, "Phase E must validate against the sealed era, not the live HEAD")
        result = validate()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["plan_hash"], load(DEMO)["planner_output"]["plan_hash"])

    def test_missing_era_ref_is_rejected(self):
        with self.assertRaises(ValueError):
            build_authority_bundle("0" * 40)

    def test_era_resolution_fails_closed_on_tampered_demo(self):
        tampered = json.loads(json.dumps(load(DEMO)))
        tampered["planner_output"]["plan_hash"] = "0" * 64
        with self.assertRaises(ValueError):
            resolve_demo_era_ref(tampered, load(MANIFEST)["branch_pr"]["merge_commit"])


if __name__ == "__main__":
    unittest.main()
