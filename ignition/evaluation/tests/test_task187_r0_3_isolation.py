from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

IGNITION_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = IGNITION_ROOT.parent
sys.path.insert(0, str(IGNITION_ROOT / "tools" / "foundation"))
sys.path.insert(0, str(IGNITION_ROOT))

import validate_repository_path_classification as path_classification  # noqa: E402


def task187_evaluation_paths() -> list[str]:
    live = path_classification.live_classification()
    return [
        path
        for path in live
        if path.startswith("ignition/evaluation/heldout/r0.3/")
        or path.startswith("ignition/evaluation/hooks/r0.3/")
        or path.startswith("ignition/evaluation/operational-control/r0.3/")
        or path in {
            "ignition/evaluation/r0.3-ledger-closure-protocol.md",
            "ignition/evaluation/tools/finalize_successor_read_ledger_r0_3.py",
            "ignition/evaluation/tools/task_branch_guard_r0_3.py",
        }
        or path.startswith("ignition/evaluation/tests/test_task187_r0_")
        or path.startswith("ignition/reports/evaluations/ignition-187-r0-3-protocol-repair/")
    ]


class Task187R03EvaluationIsolationTests(unittest.TestCase):
    def test_task187_evaluation_paths_are_typed_and_non_authoritative(self) -> None:
        task_paths = task187_evaluation_paths()
        self.assertGreaterEqual(len(task_paths), 37)
        self.assertIn("EVALUATION_EVIDENCE", path_classification.NON_AUTHORITATIVE_CATEGORIES)
        self.assertEqual(
            set(path_classification.AUTHORITATIVE_PREFIXES),
            {"统一函数总表/", "统一案例总表/"},
        )
        for path in task_paths:
            category, matched_rule = path_classification.classify(path)
            self.assertEqual(category, "EVALUATION_EVIDENCE", path)
            self.assertEqual(matched_rule, "EVALUATION_EVIDENCE", path)
            self.assertNotEqual(category, "AUTHORITATIVE_CLAIM_INPUT", path)

    def test_generated_path_manifest_accounts_each_task187_artifact(self) -> None:
        manifest = path_classification.read_manifest()
        for path in task187_evaluation_paths():
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

    def test_task187_reports_are_excluded_from_knowledge_experience(self) -> None:
        report_sources = {
            path.removeprefix("ignition/")
            for path in task187_evaluation_paths()
            if path.startswith("ignition/reports/evaluations/") and path.endswith(".md")
        }
        config_path = IGNITION_ROOT / "data/governance/knowledge-experience/config.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        excluded = set(config["excluded_generated_result_sources"])
        from tools.governance.build_knowledge_experience import knowledge_result_rows

        knowledge_sources = {row["source"] for row in knowledge_result_rows(config)}
        self.assertEqual(len(report_sources), 5)
        self.assertTrue(report_sources.issubset(excluded))
        self.assertTrue(report_sources.isdisjoint(knowledge_sources))

    def test_nonfunction_discovery_keeps_every_task187_path_excluded(self) -> None:
        discovery_path = IGNITION_ROOT / "data/foundation/nonfunction-claims/source-discovery.jsonl"
        discovery = {
            row["path"]: row
            for row in (json.loads(line) for line in discovery_path.read_text(encoding="utf-8").splitlines())
            if row
        }
        for repository_path in task187_evaluation_paths():
            path = repository_path.removeprefix("ignition/")
            with self.subTest(path=path):
                row = discovery.get(path)
                self.assertIsNotNone(row, f"unaccounted nonfunction-discovery path: {path}")
                self.assertEqual(row["coverage_status"], "EXCLUDED_EVALUATION_EVIDENCE_ONLY")
                self.assertEqual(row["candidate_fragments"], 0)
                self.assertEqual(row["canonical_claim_ids"], [])

    def test_task187_does_not_promote_candidate_or_publication_content(self) -> None:
        committed = subprocess.check_output(
            ["git", "diff", "--name-only", "047fb0ef0b4a734e42efb4a29b4e70b831ef0be4", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
        ).splitlines()
        working = subprocess.check_output(
            ["git", "diff", "--name-only"], cwd=REPO_ROOT, text=True
        ).splitlines()
        changed = set(committed) | set(working)
        protected_prefixes = (
            "ignition/data/foundation/function-assets/",
            "ignition/KNOWLEDGE/",
            "ignition/data/operations/current-state/",
        )
        derived_nonfunction_accounting = {
            "ignition/data/foundation/nonfunction-claims/source-discovery.jsonl",
            "ignition/data/foundation/nonfunction-claims/discovery-coverage.json",
            "ignition/data/foundation/nonfunction-claims/closure-summary.json",
        }
        changed_canonical_claim_paths = [
            path
            for path in changed
            if path.startswith("ignition/data/foundation/nonfunction-claims/")
            and path not in derived_nonfunction_accounting
        ]
        self.assertFalse(
            [path for path in changed if path.startswith(protected_prefixes)] + changed_canonical_claim_paths,
            "Task187 must not update canonical candidate or publication content",
        )

        fire_seed_census = "ignition/data/publication/fire-seeds/seed-census.json"
        fire_seed_human = "ignition/PUBLICATIONS/pointfire-results-book/12-火种：点火跑出来的发现、问题与写作种子.md"
        changed_fire_seed_paths = {
            path for path in changed if path.startswith("ignition/data/publication/fire-seeds/")
        }
        self.assertLessEqual(changed_fire_seed_paths, {fire_seed_census})
        self.assertNotIn(fire_seed_human, changed)

        if fire_seed_census in changed:
            baseline = json.loads(
                subprocess.check_output(
                    ["git", "show", f"047fb0ef0b4a734e42efb4a29b4e70b831ef0be4:{fire_seed_census}"],
                    cwd=REPO_ROOT,
                )
            )
            current = json.loads((REPO_ROOT / fire_seed_census).read_text(encoding="utf-8"))

            def without_source_hashes(census: dict) -> dict:
                normalized = json.loads(json.dumps(census))
                for row in normalized["source_census"]:
                    row.pop("source_sha256", None)
                return normalized

            self.assertEqual(without_source_hashes(current), without_source_hashes(baseline))
            self.assertTrue(
                {
                    path.removeprefix("ignition/")
                    for path in task187_evaluation_paths()
                    if path.startswith("ignition/reports/evaluations/") and path.endswith(".md")
                }.isdisjoint({row["source_path"] for row in current["source_census"]})
            )
            seed_sources = {
                source for seed in current["seeds"] for source in seed["source_links"]
            }
            self.assertTrue(
                {
                    path.removeprefix("ignition/")
                    for path in task187_evaluation_paths()
                    if path.startswith("ignition/reports/evaluations/") and path.endswith(".md")
                }.isdisjoint(seed_sources)
            )


if __name__ == "__main__":
    unittest.main()
