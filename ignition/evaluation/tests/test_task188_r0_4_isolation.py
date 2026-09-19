from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

IGNITION_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = IGNITION_ROOT.parent
BASE_HEAD = "b388ef4ce191c083460ebab4d77a7aacfa2c69f1"
sys.path.insert(0, str(IGNITION_ROOT / "tools" / "foundation"))
sys.path.insert(0, str(IGNITION_ROOT))

import validate_repository_path_classification as path_classification  # noqa: E402


def task188_evaluation_paths() -> list[str]:
    live = path_classification.live_classification()
    return sorted(
        path
        for path in live
        if path.startswith("ignition/evaluation/heldout/r0.4/")
        or path.startswith("ignition/evaluation/operational-control/r0.4/")
        or path.startswith("ignition/evaluation/tests/test_task188_r0_4_")
        or path.startswith("ignition/reports/evaluations/ignition-188-r0-4-protocol-repair/")
        or path in {
            "ignition/evaluation/r0.4-ledger-closure-protocol.md",
            "ignition/evaluation/tools/finalize_successor_read_ledger_r0_4.py",
        }
    )


def changed_paths() -> set[str]:
    names: set[str] = set()
    for args in (
        ["git", "diff", "--name-only", BASE_HEAD],
        ["git", "diff", "--cached", "--name-only", BASE_HEAD],
    ):
        names.update(
            item
            for item in subprocess.check_output(args, cwd=REPO_ROOT, text=True).splitlines()
            if item
        )
    names.update(
        item
        for item in subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=REPO_ROOT,
            text=True,
        ).splitlines()
        if item
    )
    return names


class Task188R04EvaluationIsolationTests(unittest.TestCase):
    def test_task188_paths_are_typed_and_non_authoritative(self) -> None:
        task_paths = task188_evaluation_paths()
        required = {
            "ignition/evaluation/heldout/r0.4/successor-visible/packet-manifest-r0.4.json",
            "ignition/evaluation/heldout/r0.4/successor-visible/cases/IGNITION-20260919-188-EXP-01.md",
            "ignition/evaluation/heldout/r0.4/successor-visible/cases/IGNITION-20260919-188-GOV-01.md",
            "ignition/evaluation/tools/finalize_successor_read_ledger_r0_4.py",
            "ignition/reports/evaluations/ignition-188-r0-4-protocol-repair/evaluation-plane-isolation-fixed-point.md",
        }
        self.assertTrue(required.issubset(task_paths))
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

    def test_generated_path_manifest_accounts_every_task188_artifact(self) -> None:
        manifest = path_classification.read_manifest()
        for path in task188_evaluation_paths():
            with self.subTest(path=path):
                self.assertIn(path, manifest)
                self.assertEqual(manifest[path][0], "EVALUATION_EVIDENCE")

    def test_reused_evaluation_contract_is_explicitly_non_promoting(self) -> None:
        policy = json.loads(
            (IGNITION_ROOT / "data/foundation/knowledge-corpus-admission-policy.json").read_bytes()
        )
        excluded = policy["classes"]["EVALUATION_EVIDENCE_ONLY"]
        self.assertFalse(excluded["auto_discovery"])
        self.assertTrue(excluded["provenance_only"])
        rule = next(
            row for row in policy["rules"] if row["classification"] == "EVALUATION_EVIDENCE_ONLY"
        )
        self.assertEqual(set(rule["prefixes"]), {"evaluation/", "reports/evaluations/"})

        contract = json.loads(
            (IGNITION_ROOT / "evaluation/evaluation-plane-contract-r0.1.json").read_bytes()
        )
        self.assertEqual(
            set(contract["path_prefixes"]),
            {"ignition/evaluation/", "ignition/reports/evaluations/"},
        )
        self.assertEqual(
            contract["visibility_and_discovery"]["function_asset_discovery"],
            "EXCLUDED",
        )
        self.assertEqual(
            contract["visibility_and_discovery"]["nonfunction_claim_discovery"],
            "EXCLUDED_WITH_AUDIT_ROW",
        )
        self.assertFalse(contract["promotion_boundary"]["automatic_promotion"])
        self.assertFalse(contract["promotion_boundary"]["canonicalization_by_this_contract"])

    def test_nonfunction_discovery_keeps_every_task188_path_excluded(self) -> None:
        discovery_path = IGNITION_ROOT / "data/foundation/nonfunction-claims/source-discovery.jsonl"
        discovery = {
            row["path"]: row
            for row in (
                json.loads(line)
                for line in discovery_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            )
        }
        for repository_path in task188_evaluation_paths():
            path = repository_path.removeprefix("ignition/")
            with self.subTest(path=path):
                row = discovery.get(path)
                self.assertIsNotNone(row, f"unaccounted nonfunction-discovery path: {path}")
                self.assertEqual(row["coverage_status"], "EXCLUDED_EVALUATION_EVIDENCE_ONLY")
                self.assertEqual(row["candidate_fragments"], 0)
                self.assertEqual(row["canonical_claim_ids"], [])

    def test_r0_4_is_absent_from_knowledge_canonical_surfaces(self) -> None:
        task_sources = {
            path.removeprefix("ignition/")
            for path in task188_evaluation_paths()
        }
        report_sources = {
            path.removeprefix("ignition/")
            for path in task188_evaluation_paths()
            if path.startswith("ignition/reports/evaluations/") and path.endswith(".md")
        }
        config_path = IGNITION_ROOT / "data/governance/knowledge-experience/config.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        from tools.governance.build_knowledge_experience import knowledge_result_rows

        knowledge_sources = {row["source"] for row in knowledge_result_rows(config)}
        self.assertTrue(report_sources.isdisjoint(knowledge_sources))
        for relative_path in (
            "data/governance/knowledge-experience/asset-cards.jsonl",
            "data/governance/knowledge-experience/layered-reading.jsonl",
            "data/governance/knowledge-experience/search-index.jsonl",
        ):
            rows = [
                json.loads(line)
                for line in (IGNITION_ROOT / relative_path).read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            generated_sources = {row.get("canonical_source") for row in rows}
            self.assertTrue(task_sources.isdisjoint(generated_sources), relative_path)

        generated_projection_refresh = {
            "ignition/data/governance/knowledge-experience/asset-cards.jsonl",
            "ignition/data/governance/knowledge-experience/layered-reading.jsonl",
            "ignition/data/governance/knowledge-experience/search-index.jsonl",
            "ignition/data/governance/knowledge-experience/manifest.json",
        }
        changed = changed_paths()
        changed_knowledge = {
            path for path in changed if path.startswith("ignition/data/governance/knowledge-experience/")
        }
        self.assertLessEqual(changed_knowledge, generated_projection_refresh)

    def test_no_function_nonfunction_knowledge_fire_seed_or_current_mutation(self) -> None:
        changed = changed_paths()
        protected_prefixes = (
            "ignition/data/foundation/function-assets/",
            "ignition/KNOWLEDGE/",
            "ignition/data/publication/fire-seeds/",
            "ignition/data/operations/current-state/",
        )
        self.assertFalse(
            sorted(path for path in changed if path.startswith(protected_prefixes)),
            "R0.4 evaluation evidence must not mutate canonical or downstream surfaces",
        )

        allowed_nonfunction_accounting = {
            "ignition/data/foundation/nonfunction-claims/source-discovery.jsonl",
            "ignition/data/foundation/nonfunction-claims/discovery-coverage.json",
            "ignition/data/foundation/nonfunction-claims/closure-summary.json",
            "ignition/docs/foundation/nonfunction-claim-adjudication-index.md",
        }
        changed_nonfunction = {
            path
            for path in changed
            if path.startswith("ignition/data/foundation/nonfunction-claims/")
        }
        self.assertLessEqual(changed_nonfunction, allowed_nonfunction_accounting)

    def test_closure_report_records_fixed_point_and_exclusions(self) -> None:
        report = (
            IGNITION_ROOT
            / "reports/evaluations/ignition-188-r0-4-protocol-repair/evaluation-plane-isolation-fixed-point.md"
        ).read_text(encoding="utf-8")
        for marker in (
            "EVALUATION_EVIDENCE",
            "EXCLUDED_EVALUATION_EVIDENCE_ONLY",
            "SECOND_GENERATION_BYTE_FIXED_POINT=PASS",
            "FOUNDATION_CANDIDATE_KNOWLEDGE_CURRENT_FIRE_SEEDS_MUTATIONS=NONE",
            "NO_AUTOMATIC_PROMOTION",
        ):
            self.assertIn(marker, report)


if __name__ == "__main__":
    unittest.main()
