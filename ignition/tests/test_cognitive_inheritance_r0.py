from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

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
    TASK229_ADMISSION_BEFORE_READ_SUCCESSOR_PATH,
    TASK229_ADMISSION_BEFORE_READ_SUCCESSOR_SHA256,
    TASK229_R4_TASK179_SUCCESSOR_SHA256,
    TASK217_FREEZE_RELATIVE,
    TASK217_FREEZE_SIDECAR_RELATIVE,
    TASK220_FREEZE_RELATIVE,
    TASK220_FREEZE_SIDECAR_RELATIVE,
    TASK225_KNOWLEDGE_SUCCESSOR_REPLACEMENTS,
    TASK225_REPLACEMENT_PATHS,
    TASK225_FIRE_SEED_CENSUS_PATH,
    TASK225_FIRE_SEED_CENSUS_SHA256,
    TASK225_SUCCESSOR_PROVENANCE,
    TASK225_SUCCESSOR_HEAD_COMMIT,
    TASK225_SUCCESSOR_SOURCE_PATH,
    ValidationFailure,
    task217_generated_fire_seed_paths,
    is_allowed_changed_path,
    is_task229_r4_task179_successor,
    task217_generated_knowledge_paths,
    task220_projection_hashes,
    task225_projection_chain_coverage,
    task220_source_bytes,
    validate_task225_successor_lock,
    validate_changed_paths,
    validate_human_results_excluded_prefixes,
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
        self.assertEqual(
            result["projection_chain_coverage"],
            {
                "task220_unchanged": "105/109",
                "task225_exact_successor_replacements": "4/4",
                "effective_projection_chain_coverage": "109/109",
            },
        )

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
        self.assertTrue(is_allowed_changed_path("ignition/KNOWLEDGE/cards/part-018.md"))
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

    def test_task229_successor_exception_is_exact_content_bound(self) -> None:
        # Preserve the R3 byte lock as history while testing the separately
        # authorized R4 successor identity at its exact path and full hash.
        self.assertEqual(
            TASK229_ADMISSION_BEFORE_READ_SUCCESSOR_SHA256,
            "f089743b3e07b1ed3b63027e6d0b0e3846a10cffba88487ab3a6d4b917f21e99",
        )
        self.assertFalse(is_allowed_changed_path(TASK229_ADMISSION_BEFORE_READ_SUCCESSOR_PATH))

        successors = {}
        for relative_path, expected_sha256 in TASK229_R4_TASK179_SUCCESSOR_SHA256.items():
            source_bytes = (ROOT.parent / relative_path).read_bytes()
            self.assertEqual(hashlib.sha256(source_bytes).hexdigest(), expected_sha256)
            self.assertTrue(is_task229_r4_task179_successor(relative_path, ROOT.parent))
            self.assertFalse(is_allowed_changed_path(relative_path))
            successors[relative_path] = source_bytes

        for relative_path, source_bytes in successors.items():
            with self.subTest(successor_path=relative_path), tempfile.TemporaryDirectory() as temp_dir:
                repo_root = Path(temp_dir)
                ignition_root = repo_root / "ignition"
                ignition_root.mkdir()
                (repo_root / ".git").mkdir()
                candidate = repo_root / relative_path
                candidate.parent.mkdir(parents=True)

                def validate_single_change(changed_path: str, passes: bool) -> None:
                    completed = subprocess.CompletedProcess(
                        args=["git", "diff", "--name-only", "BASELINE", "HEAD"],
                        returncode=0,
                        stdout=changed_path + "\n",
                        stderr="",
                    )
                    with patch(
                        "tools.validate_cognitive_inheritance_r0.subprocess.run",
                        return_value=completed,
                    ), patch(
                        "tools.validate_cognitive_inheritance_r0.task217_generated_knowledge_paths",
                        return_value=set(),
                    ), patch(
                        "tools.validate_cognitive_inheritance_r0.task217_generated_fire_seed_paths",
                        return_value=set(),
                    ):
                        if passes:
                            validate_changed_paths(ignition_root)
                        else:
                            with self.assertRaises(ValidationFailure):
                                validate_changed_paths(ignition_root)

                candidate.write_bytes(source_bytes)
                validate_single_change(relative_path, passes=True)

                candidate.write_bytes(source_bytes + b"\nbyte drift\n")
                validate_single_change(relative_path, passes=False)

                candidate.unlink()
                validate_single_change(relative_path, passes=False)

                candidate.mkdir()
                validate_single_change(relative_path, passes=False)
                candidate.rmdir()

                candidate.symlink_to(ROOT.parent / relative_path)
                validate_single_change(relative_path, passes=False)
                candidate.unlink()

                third_path = "ignition/tools/foundation/adjudicate_core.py"
                validate_single_change(third_path, passes=False)
                protected_path = "ignition/data/foundation/nonfunction-claims/claim-registry.jsonl"
                validate_single_change(protected_path, passes=False)

    def test_human_results_isolation_is_exact_and_preserves_unrelated_reports(self) -> None:
        config = json.loads((ROOT / "data/governance/human-results/config.json").read_text(encoding="utf-8"))
        validate_human_results_excluded_prefixes(config["excluded_prefixes"])

        for broad_prefix in (
            "reports/evaluations/",
            "reports/",
            "reports/evaluations/ignition-217-method-dependency-benchmark-r0/",
            "reports/evaluations/ignition-220-cognitive-evolution-r0/",
            "reports/evaluations/ignition-223/",
            "reports/evaluations/ignition-224/",
        ):
            with self.subTest(broad_prefix=broad_prefix), self.assertRaises(ValidationFailure):
                validate_human_results_excluded_prefixes([*config["excluded_prefixes"], broad_prefix])

        from tools.governance.build_human_results import discover

        discovered = set(discover(config))
        self.assertIn(
            "reports/evaluations/ignition-220-cognitive-evolution-r0/families/FAMILY03/m0.md",
            discovered,
        )
        self.assertNotIn(
            "reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0/packets/PKT-92DE30/cases/CASE-03/facts.md",
            discovered,
        )
        self.assertNotIn(
            "reports/evaluations/ignition-225-cognitive-evolution-r0-1/design/repair-round-3/A-case-designer-report.md",
            discovered,
        )

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

            self.assertEqual(
                task220_projection_hashes(repo, "external_generated_knowledge_experience"),
                {projection: current_digest},
            )
            exact_paths = task217_generated_knowledge_paths(repo)
            self.assertEqual(exact_paths, {projection})
            self.assertTrue(is_allowed_changed_path(projection, exact_extra_paths=exact_paths))
            self.assertFalse(is_allowed_changed_path("ignition/KNOWLEDGE/cards/part-999.md", exact_extra_paths=exact_paths))

            artifact.write_text("tampered after Task220 freeze\n", encoding="utf-8")
            with self.assertRaises(ValidationFailure):
                task217_generated_knowledge_paths(repo)

    def test_task225_inline_lock_preserves_105_hashes_and_scientific_freeze(self) -> None:
        sys.path.insert(0, str(ROOT / "tools/foundation"))
        from legacy_table_migration import migration_paths

        raw_paths = subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=ROOT.parent,
        )
        indexed_paths = {item.decode("utf-8") for item in raw_paths.split(b"\0") if item}
        current_tracked_file_count = len(indexed_paths | set(migration_paths()))
        current_source_lines = (ROOT.parent / TASK225_SUCCESSOR_SOURCE_PATH).read_text(encoding="utf-8").splitlines()
        self.assertIn(f"- 已核算跟踪文件：{current_tracked_file_count}", current_source_lines)
        self.assertEqual(TASK225_SUCCESSOR_PROVENANCE["tracked_file_census_after"], 6868)
        task225_part018 = subprocess.run(
            [
                "git",
                "cat-file",
                "-e",
                f"{TASK225_SUCCESSOR_HEAD_COMMIT}:ignition/KNOWLEDGE/cards/part-018.md",
            ],
            cwd=ROOT.parent,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(task225_part018.returncode, 0)

        historical = task220_projection_hashes(ROOT.parent, "external_generated_knowledge_experience")
        self.assertEqual(len(historical), 109)
        self.assertEqual(set(TASK225_KNOWLEDGE_SUCCESSOR_REPLACEMENTS), TASK225_REPLACEMENT_PATHS)
        self.assertEqual(len(task217_generated_knowledge_paths(ROOT.parent)), 109)
        fire_seed_hashes = task220_projection_hashes(ROOT.parent, "external_generated_fire_seed_census")
        self.assertEqual(len(fire_seed_hashes), 2)
        task225_fire_seed_bytes = subprocess.check_output(
            ["git", "show", f"{TASK225_SUCCESSOR_HEAD_COMMIT}:{TASK225_FIRE_SEED_CENSUS_PATH}"],
            cwd=ROOT.parent,
        )
        self.assertEqual(hashlib.sha256(task225_fire_seed_bytes).hexdigest(), TASK225_FIRE_SEED_CENSUS_SHA256)
        self.assertIn(TASK225_FIRE_SEED_CENSUS_PATH, task217_generated_fire_seed_paths(ROOT.parent))
        self.assertEqual(
            task225_projection_chain_coverage(ROOT.parent),
            {
                "task220_unchanged": "105/109",
                "task225_exact_successor_replacements": "4/4",
                "effective_projection_chain_coverage": "109/109",
            },
        )

    def test_task225_fire_seed_successor_rejects_wrong_hash(self) -> None:
        with patch("tools.validate_cognitive_inheritance_r0.TASK225_FIRE_SEED_CENSUS_SHA256", "0" * 64):
            with self.assertRaises(ValidationFailure):
                task220_projection_hashes(ROOT.parent, "external_generated_fire_seed_census")

        scientific_root = ROOT / "reports/evaluations/ignition-225-cognitive-evolution-r0-1"
        manifest_path = scientific_root / "freeze-manifest.json"
        sidecar_path = scientific_root / "freeze.sha256"
        manifest_bytes = manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes)
        self.assertEqual(len(manifest["frozen_files"]), 55)
        self.assertEqual(
            sidecar_path.read_text(encoding="utf-8"),
            f"{hashlib.sha256(manifest_bytes).hexdigest()}  freeze-manifest.json\n",
        )
        for entry in manifest["frozen_files"]:
            artifact = ROOT.parent / entry["path"]
            self.assertEqual(hashlib.sha256(artifact.read_bytes()).hexdigest(), entry["sha256"])
        self.assertFalse((scientific_root / "projection-replacement-freeze.json").exists())
        self.assertFalse((scientific_root / "projection-replacement-freeze.sha256").exists())

    def test_task225_inline_lock_rejects_a_fifth_or_missing_path(self) -> None:
        fifth_path = "ignition/KNOWLEDGE/cards/task225-unapproved-fifth.md"
        with patch(
            "tools.validate_cognitive_inheritance_r0.TASK225_KNOWLEDGE_SUCCESSOR_REPLACEMENTS",
            {**TASK225_KNOWLEDGE_SUCCESSOR_REPLACEMENTS, fifth_path: "0" * 64},
        ):
            with self.assertRaises(ValidationFailure):
                validate_task225_successor_lock(ROOT.parent)

        missing = dict(TASK225_KNOWLEDGE_SUCCESSOR_REPLACEMENTS)
        missing.pop(next(iter(missing)))
        with patch("tools.validate_cognitive_inheritance_r0.TASK225_KNOWLEDGE_SUCCESSOR_REPLACEMENTS", missing):
            with self.assertRaises(ValidationFailure):
                validate_task225_successor_lock(ROOT.parent)

    def test_task225_inline_lock_rejects_wrong_projection_and_source_hashes(self) -> None:
        wrong_projection = dict(TASK225_KNOWLEDGE_SUCCESSOR_REPLACEMENTS)
        first_path = next(iter(wrong_projection))
        wrong_projection[first_path] = "0" * 64
        with patch("tools.validate_cognitive_inheritance_r0.TASK225_KNOWLEDGE_SUCCESSOR_REPLACEMENTS", wrong_projection):
            with self.assertRaises(ValidationFailure):
                validate_task225_successor_lock(ROOT.parent)

        with patch("tools.validate_cognitive_inheritance_r0.TASK225_SUCCESSOR_SOURCE_SHA256", "0" * 64):
            with self.assertRaises(ValidationFailure):
                validate_task225_successor_lock(ROOT.parent)

    def test_task225_inline_lock_rejects_any_source_delta_beyond_census_token(self) -> None:
        historical_source = task220_source_bytes(ROOT.parent)
        current_source_path = ROOT.parent / "ignition/docs/foundation/nonfunction-claim-adjudication-index.md"
        tampered_source = current_source_path.read_bytes() + b"\nextra changed line\n"
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            source_path = repo / "ignition/docs/foundation/nonfunction-claim-adjudication-index.md"
            source_path.parent.mkdir(parents=True)
            source_path.write_bytes(tampered_source)
            with patch(
                "tools.validate_cognitive_inheritance_r0.TASK225_SUCCESSOR_SOURCE_SHA256",
                hashlib.sha256(tampered_source).hexdigest(),
            ):
                with patch(
                    "tools.validate_cognitive_inheritance_r0.task225_source_bytes",
                    return_value=tampered_source,
                ):
                    with self.assertRaisesRegex(ValidationFailure, "differs beyond the exact"):
                        validate_task225_successor_lock(repo, task220_source=historical_source)

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
