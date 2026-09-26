from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
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
    TASK217_FREEZE_RELATIVE,
    TASK217_FREEZE_SIDECAR_RELATIVE,
    TASK220_FREEZE_RELATIVE,
    TASK220_FREEZE_SIDECAR_RELATIVE,
    ValidationFailure,
    task217_generated_fire_seed_paths,
    is_allowed_changed_path,
    task217_generated_knowledge_paths,
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
        self.assertTrue(is_allowed_changed_path("ignition/data/governance/human-results/config.json"))
        self.assertFalse(is_allowed_changed_path("ignition/data/governance/human-results/config.json.bak"))
        self.assertFalse(is_allowed_changed_path("ignition/data/governance/human-results/unrelated.json"))
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
        self.assertTrue(is_allowed_changed_path("ignition/KNOWLEDGE/cards/part-002.md"))
        self.assertTrue(is_allowed_changed_path("ignition/KNOWLEDGE/indexes/systems/part-003.md"))
        self.assertTrue(is_allowed_changed_path("ignition/KNOWLEDGE/indexes/writing_publication.md"))
        self.assertTrue(is_allowed_changed_path("ignition/KNOWLEDGE/reading-layers/part-001.md"))
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

    def test_task217_generated_knowledge_allowance_is_hash_bound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            projection = "ignition/KNOWLEDGE/cards/part-016.md"
            artifact = repo / projection
            artifact.parent.mkdir(parents=True)
            artifact.write_text("frozen generated projection\n", encoding="utf-8")
            digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
            freeze = {
                "external_generated_knowledge_experience": {
                    "files": [{"path": projection, "sha256": digest}],
                },
            }
            freeze_path = repo / TASK217_FREEZE_RELATIVE
            freeze_path.parent.mkdir(parents=True)
            freeze_bytes = (json.dumps(freeze, sort_keys=True, indent=2) + "\n").encode("utf-8")
            freeze_path.write_bytes(freeze_bytes)
            sidecar_path = repo / TASK217_FREEZE_SIDECAR_RELATIVE
            sidecar_path.write_text(
                f"{hashlib.sha256(freeze_bytes).hexdigest()}  {TASK217_FREEZE_RELATIVE.as_posix()}\n",
                encoding="utf-8",
            )

            exact_paths = task217_generated_knowledge_paths(repo)
            self.assertEqual(exact_paths, {projection})
            self.assertTrue(is_allowed_changed_path(projection, exact_extra_paths=exact_paths))
            self.assertFalse(is_allowed_changed_path("ignition/KNOWLEDGE/cards/part-999.md", exact_extra_paths=exact_paths))

            artifact.write_text("tampered projection\n", encoding="utf-8")
            with self.assertRaises(ValidationFailure):
                task217_generated_knowledge_paths(repo)

    def test_task217_fire_seed_allowance_is_hash_bound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            projections = {
                "ignition/data/publication/fire-seeds/seed-census.json": "frozen seed census\n",
                "ignition/data/publication/fire-seeds/CHANGELOG.jsonl": "frozen no-delta event\n",
            }
            files = []
            for path, body in projections.items():
                artifact = repo / path
                artifact.parent.mkdir(parents=True, exist_ok=True)
                artifact.write_text(body, encoding="utf-8")
                files.append({"path": path, "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest()})
            freeze = {
                "external_generated_fire_seed_census": {
                    "scope": "machine source census only; no human Fire Seeds entry changed",
                    "files": files,
                },
            }
            freeze_path = repo / TASK217_FREEZE_RELATIVE
            freeze_path.parent.mkdir(parents=True)
            freeze_bytes = (json.dumps(freeze, sort_keys=True, indent=2) + "\n").encode("utf-8")
            freeze_path.write_bytes(freeze_bytes)
            sidecar_path = repo / TASK217_FREEZE_SIDECAR_RELATIVE
            sidecar_path.write_text(
                f"{hashlib.sha256(freeze_bytes).hexdigest()}  {TASK217_FREEZE_RELATIVE.as_posix()}\n",
                encoding="utf-8",
            )

            exact_paths = task217_generated_fire_seed_paths(repo)
            self.assertEqual(exact_paths, set(projections))
            self.assertTrue(is_allowed_changed_path("ignition/data/publication/fire-seeds/CHANGELOG.jsonl", exact_extra_paths=exact_paths))
            self.assertFalse(is_allowed_changed_path("ignition/data/publication/fire-seeds/unlisted.jsonl", exact_extra_paths=exact_paths))

            (repo / "ignition/data/publication/fire-seeds/CHANGELOG.jsonl").write_text("tampered\n", encoding="utf-8")
            with self.assertRaises(ValidationFailure):
                task217_generated_fire_seed_paths(repo)

    def test_task220_frozen_projection_supersedes_only_matching_task217_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            projection = "ignition/KNOWLEDGE/cards/part-016.md"
            artifact = repo / projection
            artifact.parent.mkdir(parents=True)
            artifact.write_text("Task220 regenerated navigation projection\n", encoding="utf-8")
            current_digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
            old_digest = hashlib.sha256(b"Task217 frozen projection\n").hexdigest()

            task217_freeze = {
                "external_generated_knowledge_experience": {
                    "files": [{"path": projection, "sha256": old_digest}],
                },
            }
            task217_bytes = (json.dumps(task217_freeze, sort_keys=True, indent=2) + "\n").encode("utf-8")
            task217_path = repo / TASK217_FREEZE_RELATIVE
            task217_path.parent.mkdir(parents=True)
            task217_path.write_bytes(task217_bytes)
            (repo / TASK217_FREEZE_SIDECAR_RELATIVE).write_text(
                f"{hashlib.sha256(task217_bytes).hexdigest()}  {TASK217_FREEZE_RELATIVE.as_posix()}\n",
                encoding="utf-8",
            )

            task220_freeze = {
                "task_id": "IGNITION-20260926-220",
                "external_generated_knowledge_experience": {
                    "files": [{"path": projection, "sha256": current_digest}],
                },
            }
            task220_bytes = (json.dumps(task220_freeze, sort_keys=True, indent=2) + "\n").encode("utf-8")
            task220_path = repo / TASK220_FREEZE_RELATIVE
            task220_path.parent.mkdir(parents=True)
            task220_path.write_bytes(task220_bytes)
            (repo / TASK220_FREEZE_SIDECAR_RELATIVE).write_text(
                f"{hashlib.sha256(task220_bytes).hexdigest()}  {TASK220_FREEZE_RELATIVE.as_posix()}\n",
                encoding="utf-8",
            )

            exact_paths = task217_generated_knowledge_paths(repo)
            self.assertEqual(exact_paths, {projection})
            self.assertTrue(is_allowed_changed_path(projection, exact_extra_paths=exact_paths))
            self.assertFalse(is_allowed_changed_path("ignition/KNOWLEDGE/cards/part-999.md", exact_extra_paths=exact_paths))

            artifact.write_text("tampered after Task220 freeze\n", encoding="utf-8")
            with self.assertRaises(ValidationFailure):
                task217_generated_knowledge_paths(repo)

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
