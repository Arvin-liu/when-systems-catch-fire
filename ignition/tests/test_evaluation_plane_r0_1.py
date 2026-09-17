from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools" / "foundation"))

from evaluation.tools import evaluation_plane_r0_1 as plane  # noqa: E402
from evaluation.tools import validate_evaluation_plane_r0_1 as plane_validator  # noqa: E402
from tools.foundation import adjudicate_nonfunction_claims as nonfunction  # noqa: E402
from tools.foundation import build_function_asset_census as function_census  # noqa: E402
from tools.foundation import validate_repository_path_classification as paths  # noqa: E402
from tools.foundation.knowledge_corpus_admission import admission_for_path  # noqa: E402
from tools.governance import run_self_correction as self_correction  # noqa: E402


class EvaluationPlaneR01Tests(unittest.TestCase):
    def test_frozen_receipts_and_successor_packet_validate_without_running_trial(self) -> None:
        self.assertEqual(plane_validator.main(), 0)

    def test_fixture_paths_are_classified_and_manifest_accounted(self) -> None:
        additions = {
            "ignition/reports/evaluations/scratch/report.json",
            "ignition/evaluation/tools/scratch-validator.py",
            "ignition/reports/evaluations/scratch/contamination-disclosure.md",
        }
        live = paths.live_classification()
        for path in additions:
            self.assertEqual(paths.classify(path)[0], "EVALUATION_EVIDENCE", path)
            live[path] = paths.classify(path)
        # A matching generated-manifest fixture demonstrates that all three
        # evaluator-like paths are accounted for, rather than unresolved/missing.
        result = paths.check(live=live, manifest=dict(live))
        self.assertEqual(result, 0)

    def test_admission_policy_excludes_reports_and_tools_from_semantic_discovery(self) -> None:
        for path in (
            "reports/evaluations/fixture/result.json",
            "reports/evaluations/fixture/validator.py",
            "reports/evaluations/fixture/contamination-disclosure.md",
            "evaluation/tools/validator.py",
        ):
            admission = admission_for_path(path)
            self.assertEqual(admission.classification, "EVALUATION_EVIDENCE_ONLY", path)
            self.assertFalse(admission.auto_discovery, path)
            self.assertTrue(admission.provenance_only, path)
        config = json.loads((ROOT / "data/governance/self-correction/config.json").read_text(encoding="utf-8"))
        self.assertFalse(self_correction.is_knowledge_path("evaluation/result.json", config))
        self.assertFalse(self_correction.is_knowledge_path("reports/evaluations/task/result.json", config))
        self.assertTrue(self_correction.is_knowledge_path("reports/operations/old-audit.md", config))
        self.assertFalse(self_correction.is_knowledge_path("docs/foundation/nonfunction-claim-adjudication-index.md", config))
        self.assertTrue(self_correction.is_knowledge_path("docs/human/function-assets/README.md", config))

    def test_function_census_set_does_not_expand_for_evaluation_paths(self) -> None:
        baseline = ["ignition/agent_runtime/example.py"]
        evaluator_only = baseline + [
            "ignition/reports/evaluations/fixture/result.json",
            "ignition/reports/evaluations/fixture/validator.py",
            "ignition/reports/evaluations/fixture/contamination-disclosure.md",
        ]
        def output(paths_in: list[str]) -> list[str]:
            raw = "\0".join(paths_in).encode("utf-8") + b"\0"
            with mock.patch.object(function_census.subprocess, "check_output", return_value=raw):
                return function_census.tracked_text_files()
        self.assertEqual(output(baseline), output(evaluator_only))

    def test_nonfunction_discovery_records_exclusions_without_canonical_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            scratch = Path(temp)
            evaluator_paths = (
                "reports/evaluations/fixture/result.json",
                "reports/evaluations/fixture/validator.py",
                "reports/evaluations/fixture/contamination-disclosure.md",
            )
            contents = {
                evaluator_paths[0]: '{"summary":"Evidence proves a general cognitive mechanism."}\n',
                evaluator_paths[1]: "def validate_claim():\n    return 'verified universal mechanism'\n",
                evaluator_paths[2]: "This contamination disclosure records an empirical claim.\n",
            }
            for path, value in contents.items():
                dest = scratch / path
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(value, encoding="utf-8")
            original_repo_path = nonfunction.repo_path
            def fixture_path(path: str) -> Path:
                if path in contents:
                    return scratch / path
                return original_repo_path(path)
            base_paths = ["data/foundation/claims/claims.jsonl"]
            with mock.patch.object(nonfunction, "repo_path", side_effect=fixture_path), mock.patch.object(nonfunction, "tracked_paths", return_value=base_paths):
                baseline = nonfunction.build()
            with mock.patch.object(nonfunction, "repo_path", side_effect=fixture_path), mock.patch.object(nonfunction, "tracked_paths", return_value=base_paths + list(evaluator_paths)):
                expanded = nonfunction.build()
            self.assertEqual(set(baseline), set(expanded))
            for path in baseline:
                if path.name not in {
                    "source-discovery.jsonl",
                    "closure-summary.json",
                    "discovery-coverage.json",
                    "nonfunction-claim-adjudication-index.md",
                }:
                    self.assertEqual(baseline[path], expanded[path], path)
            source_discovery = next(path for path in baseline if path.name == "source-discovery.jsonl")
            base_rows = [json.loads(line) for line in baseline[source_discovery].splitlines()]
            rows = [json.loads(line) for line in expanded[source_discovery].splitlines()]
            self.assertEqual(
                [row for row in rows if row["path"] not in evaluator_paths],
                base_rows,
            )
            indexed = {row["path"]: row for row in rows}
            for path in evaluator_paths:
                self.assertEqual(indexed[path]["coverage_status"], "EXCLUDED_EVALUATION_EVIDENCE_ONLY")
                self.assertEqual(indexed[path]["candidate_fragments"], 0)
                self.assertEqual(indexed[path]["canonical_claim_ids"], [])
            closure_path = next(path for path in baseline if path.name == "closure-summary.json")
            base_closure = json.loads(baseline[closure_path])
            expanded_closure = json.loads(expanded[closure_path])
            for key in set(base_closure) - {"source_coverage_distribution", "tracked_files_accounted"}:
                self.assertEqual(base_closure[key], expanded_closure[key], key)
            coverage_path = next(path for path in baseline if path.name == "discovery-coverage.json")
            base_coverage = json.loads(baseline[coverage_path])
            expanded_coverage = json.loads(expanded[coverage_path])
            for key in set(base_coverage) - {"coverage_status_counts", "tracked_files"}:
                self.assertEqual(base_coverage[key], expanded_coverage[key], key)

    def test_explicit_transition_creates_candidate_only_and_never_canonicalizes(self) -> None:
        artifact = {
            "schema_version": "evaluation-evidence-r0.1",
            "artifact_id": "fixture-result",
            "artifact_kind": "EVALUATION_RESULT",
            "task_id": "FIXTURE",
            "source": {
                "repository": "Arvin-liu/when-systems-catch-fire",
                "ref": "a" * 40,
                "path": "ignition/reports/evaluations/fixture/result.json",
                "sha256": hashlib.sha256(b"fixture source").hexdigest(),
            },
            "status": "FIXTURE_ONLY",
            "promotion": {"automatic": False, "state": "NO_AUTOMATIC_PROMOTION", "canonicalized": False},
            "claim_ceiling": "Repository-local fixture only.",
        }
        transition = {
            "schema_version": "evaluation-promotion-transition-r0.1",
            "transition_id": "fixture-transition",
            "source_artifact_id": artifact["artifact_id"],
            "source_sha256": artifact["source"]["sha256"],
            "target_kind": "ADJUDICATION_CANDIDATE",
            "authorization": {"authority_type": "OWNER_GPT", "authorization_ref": "fixture-authority-ref"},
            "automatic": False,
            "effect": "CREATE_ADJUDICATION_CANDIDATE_ONLY",
        }
        with tempfile.TemporaryDirectory() as temp:
            canonical = Path(temp) / "canonical.jsonl"
            canonical.write_text('{"stable":"unchanged"}\n', encoding="utf-8")
            before = canonical.read_bytes()
            default = plane.adjudication_boundary(artifact)
            with self.assertRaisesRegex(ValueError, "authorization reference is not verified"):
                plane.adjudication_boundary(artifact, transition)
            authorization = {transition["transition_id"]: transition["authorization"]["authorization_ref"]}
            promoted = plane.adjudication_boundary(artifact, transition, authorized_transitions=authorization)
            self.assertEqual(default["state"], "EVALUATION_EVIDENCE")
            self.assertEqual(promoted["state"], "ADJUDICATION_CANDIDATE_ONLY")
            self.assertFalse(promoted["canonicalized"])
            self.assertEqual(promoted["side_effects"], [])
            self.assertEqual(canonical.read_bytes(), before)
            mismatched = dict(transition, source_sha256="0" * 64)
            with self.assertRaisesRegex(ValueError, "source hash does not match"):
                plane.adjudication_boundary(artifact, mismatched, authorized_transitions=authorization)


if __name__ == "__main__":
    unittest.main()
