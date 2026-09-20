from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent_runtime.cognitive_inheritance_r0.src.contracts import (  # noqa: E402
    canonical_json,
    keys_preserved,
    load_json,
    migrate_r0a_to_r0b,
    validate_no_forbidden_fields,
)
from tools.validate_cognitive_inheritance_r0 import (  # noqa: E402
    FINAL_STATE,
    is_allowed_changed_path,
    validate_all,
)


R0 = ROOT / "agent_runtime" / "cognitive_inheritance_r0"


class CognitiveInheritanceR0Tests(unittest.TestCase):
    def test_full_mechanical_validator_passes(self) -> None:
        result = validate_all(ROOT)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["final_state"], FINAL_STATE)
        self.assertEqual(result["builder_verdict"], "NOT_EVALUATED_BY_BUILDER")
        self.assertEqual(result["independent_evaluation"], "NOT_RUN")

    def test_migration_is_deterministic_and_preserves_unknown_relation(self) -> None:
        source = load_json(R0 / "fixtures" / "migration-r0a.json")
        expected = load_json(R0 / "fixtures" / "migration-r0b.expected.json")
        migrated = migrate_r0a_to_r0b(source)
        self.assertTrue(keys_preserved(source, migrated))
        self.assertEqual(canonical_json(migrated), canonical_json(expected))
        self.assertEqual(migrated["relations"][0]["relation_type"], "UNKNOWN_RELATION")
        self.assertEqual(migrated["migration_lineage"][0]["destructive_rewrite"], False)

    def test_forbidden_private_surface_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_no_forbidden_fields({"object": {"hidden_chain_of_thought": "not persisted"}})

    def test_change_allowlist_is_exact_outside_the_r0_artifact_subtree(self) -> None:
        self.assertTrue(is_allowed_changed_path(".github/workflows/q33-governance-validation.yml"))
        self.assertTrue(is_allowed_changed_path("ignition/tests/test_federation_ownership.py"))
        self.assertTrue(is_allowed_changed_path("ignition/data/foundation/nonfunction-claims/source-discovery.jsonl"))
        self.assertTrue(is_allowed_changed_path("ignition/docs/foundation/nonfunction-claim-adjudication-index.md"))
        self.assertTrue(is_allowed_changed_path("ignition/data/architecture/current-facts.json"))
        self.assertTrue(is_allowed_changed_path("ignition/data/governance/self-correction/claim-delta.jsonl"))
        self.assertTrue(is_allowed_changed_path("ignition/data/governance/self-correction/config.json"))
        self.assertTrue(is_allowed_changed_path("ignition/RESULTS/CLAIM-DELTA.md"))
        self.assertTrue(is_allowed_changed_path("ignition/RESULTS/IMPACT-ANALYSIS.md"))
        self.assertTrue(is_allowed_changed_path("ignition/RESULTS/CHRONOLOGY.md"))
        self.assertTrue(is_allowed_changed_path("ignition/data/governance/human-results/census.json"))
        self.assertTrue(is_allowed_changed_path("ignition/data/governance/human-results/result-ledger.jsonl"))
        self.assertFalse(is_allowed_changed_path("ignition/RESULTS/RESEARCH-AND-ARTICLES.md"))
        self.assertTrue(is_allowed_changed_path("ignition/data/governance/knowledge-experience/asset-cards.jsonl"))
        self.assertTrue(is_allowed_changed_path("ignition/data/governance/knowledge-experience/config.json"))
        self.assertTrue(is_allowed_changed_path("ignition/data/governance/knowledge-experience/coverage.json"))
        self.assertTrue(is_allowed_changed_path("ignition/data/governance/knowledge-experience/source-first-seen.json"))
        self.assertTrue(is_allowed_changed_path("ignition/data/governance/knowledge-experience/layered-reading.jsonl"))
        self.assertTrue(is_allowed_changed_path("ignition/data/governance/knowledge-experience/manifest.json"))
        self.assertTrue(is_allowed_changed_path("ignition/data/governance/knowledge-experience/search-index.jsonl"))
        self.assertTrue(is_allowed_changed_path("ignition/data/governance/knowledge-experience/alias-index.jsonl"))
        self.assertTrue(is_allowed_changed_path("ignition/data/governance/knowledge-experience/changes.jsonl"))
        self.assertTrue(is_allowed_changed_path("ignition/KNOWLEDGE/COVERAGE.md"))
        self.assertTrue(is_allowed_changed_path("ignition/KNOWLEDGE/cards/part-015.md"))
        self.assertTrue(is_allowed_changed_path("ignition/data/publication/fire-seeds/seed-census.json"))
        self.assertTrue(is_allowed_changed_path("ignition/agent_runtime/cognitive_inheritance_r0/packages/current-self-model-r0.json"))
        self.assertTrue(is_allowed_changed_path("ignition/evaluation/reports/task181-result.json"))
        self.assertTrue(is_allowed_changed_path("ignition/reports/evaluations/task180/report.json"))
        self.assertFalse(is_allowed_changed_path(".github/workflows/unrelated.yml"))
        self.assertFalse(is_allowed_changed_path("ignition/reports/operations/ordinary-operation.md"))
        self.assertFalse(is_allowed_changed_path("ignition/data/foundation/nonfunction-claims/claim-registry.jsonl"))
        self.assertFalse(is_allowed_changed_path("ignition/data/architecture/current-system-identity.json"))
        self.assertTrue(is_allowed_changed_path("ignition/data/governance/self-correction/impact-analysis.jsonl"))
        self.assertTrue(is_allowed_changed_path("ignition/data/governance/self-correction/audit-findings.jsonl"))
        self.assertTrue(is_allowed_changed_path("ignition/RESULTS/SELF-CORRECTION-AUDIT.md"))
        self.assertFalse(is_allowed_changed_path("ignition/data/governance/knowledge-experience/source-first-seen.json.bak"))
        self.assertFalse(is_allowed_changed_path("ignition/KNOWLEDGE/UNEXPECTED.md"))
        self.assertFalse(is_allowed_changed_path("ignition/data/publication/fire-seeds/CHANGELOG.jsonl"))
        self.assertFalse(is_allowed_changed_path("ignition/data/agent-federation/build-vs-integrate-policy-r1.json.bak"))

    def test_r0_paths_are_excluded_from_canonical_claim_discovery(self) -> None:
        result = validate_all(ROOT)
        discovery = result["foundation_nonfunction_discovery"]
        self.assertGreater(discovery["tracked_paths"], 0)
        self.assertEqual(discovery["candidate_fragments"], 0)
        self.assertEqual(discovery["canonical_claim_ids"], 0)

    def test_evaluator_package_is_not_builder_verdict(self) -> None:
        package = load_json(R0 / "packages" / "independent-evaluation-package.json")
        self.assertFalse(package["roles"]["builder"]["may_issue_final_verdict"])
        self.assertEqual(package["experiment_status"], FINAL_STATE)
        self.assertEqual(package["final_verdict"]["cognitive_inheritance_verdict"], "NOT_EVALUATED_BY_BUILDER")
        self.assertTrue(all(metric["builder_may_measure"] is False for metric in package["metrics"]))

    def test_real_fixtures_remain_distinct_and_body_free(self) -> None:
        content = load_json(R0 / "fixtures" / "content-research-rest.json")
        engineering = load_json(R0 / "fixtures" / "engineering-baseline-freeze.json")
        self.assertNotEqual(content["fixture_id"], engineering["fixture_id"])
        self.assertFalse(content["real_source_binding"]["body_republished"])
        self.assertEqual(engineering["real_source_binding"]["baseline_exact_head"], "68565f2afb50989d2c2b0d346d774e3388702743")
        self.assertEqual(len(engineering["ci_evidence"]), 7)


if __name__ == "__main__":
    unittest.main()
