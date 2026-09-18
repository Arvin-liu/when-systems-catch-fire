from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

IGNITION_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = IGNITION_ROOT.parent
sys.path.insert(0, str(IGNITION_ROOT / "tools" / "foundation"))

import validate_repository_path_classification as path_classification  # noqa: E402


class Task187R03EvaluationIsolationTests(unittest.TestCase):
    def test_r0_3_evaluation_paths_are_typed_and_non_authoritative(self) -> None:
        live = path_classification.live_classification()
        r0_3_paths = [
            path
            for path in live
            if path.startswith("ignition/evaluation/heldout/r0.3/")
            or path.startswith("ignition/evaluation/operational-control/r0.3/")
            or path in {
                "ignition/evaluation/r0.3-ledger-closure-protocol.md",
                "ignition/evaluation/tools/finalize_successor_read_ledger_r0_3.py",
                "ignition/evaluation/tools/task_branch_guard_r0_3.py",
            }
            or path.startswith("ignition/evaluation/tests/test_task187_r0_3_")
            or path.startswith("ignition/reports/evaluations/ignition-187-r0-3-protocol-repair/")
        ]
        self.assertGreaterEqual(len(r0_3_paths), 20)
        self.assertIn("EVALUATION_EVIDENCE", path_classification.NON_AUTHORITATIVE_CATEGORIES)
        self.assertEqual(
            set(path_classification.AUTHORITATIVE_PREFIXES),
            {"统一函数总表/", "统一案例总表/"},
        )
        for path in r0_3_paths:
            category, matched_rule = path_classification.classify(path)
            self.assertEqual(category, "EVALUATION_EVIDENCE", path)
            self.assertEqual(matched_rule, "EVALUATION_EVIDENCE", path)
            self.assertNotEqual(category, "AUTHORITATIVE_CLAIM_INPUT", path)

    def test_generated_path_manifest_accounts_each_r0_3_artifact(self) -> None:
        manifest = path_classification.read_manifest()
        live = path_classification.live_classification()
        r0_3_paths = [
            path
            for path in live
            if path.startswith("ignition/evaluation/heldout/r0.3/")
            or path.startswith("ignition/evaluation/operational-control/r0.3/")
            or path in {
                "ignition/evaluation/r0.3-ledger-closure-protocol.md",
                "ignition/evaluation/tools/finalize_successor_read_ledger_r0_3.py",
                "ignition/evaluation/tools/task_branch_guard_r0_3.py",
            }
            or path.startswith("ignition/evaluation/tests/test_task187_r0_3_")
            or path.startswith("ignition/reports/evaluations/ignition-187-r0-3-protocol-repair/")
        ]
        for path in r0_3_paths:
            self.assertIn(path, manifest, path)
            self.assertEqual(manifest[path][0], "EVALUATION_EVIDENCE", path)

    def test_knowledge_policy_is_an_explicit_non_discovery_exclusion(self) -> None:
        policy_path = IGNITION_ROOT / "data/foundation/knowledge-corpus-admission-policy.json"
        policy = json.loads(policy_path.read_bytes())
        excluded = policy["classes"]["EVALUATION_EVIDENCE_ONLY"]
        self.assertFalse(excluded["auto_discovery"])
        self.assertTrue(excluded["provenance_only"])
        self.assertIn("cannot become automatic Knowledge or Foundation discovery inputs", excluded["meaning"])
        rule = next(row for row in policy["rules"] if row["classification"] == "EVALUATION_EVIDENCE_ONLY")
        self.assertEqual(set(rule["prefixes"]), {"evaluation/", "reports/evaluations/"})

    def test_task187_does_not_modify_canonical_candidate_or_publication_surfaces(self) -> None:
        changed = subprocess.check_output(
            ["git", "diff", "--name-only", "047fb0ef0b4a734e42efb4a29b4e70b831ef0be4", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
        ).splitlines()
        protected_prefixes = (
            "ignition/data/foundation/function-assets/",
            "ignition/data/foundation/nonfunction-claims/",
            "ignition/KNOWLEDGE/",
            "ignition/data/publication/fire-seeds/",
            "ignition/data/operations/current-state/",
        )
        self.assertFalse(
            [path for path in changed if path.startswith(protected_prefixes)],
            "Task187 must not update canonical candidate or publication surfaces",
        )


if __name__ == "__main__":
    unittest.main()
