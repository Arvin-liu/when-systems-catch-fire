from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.operations.route_component_validation import MAP_PATH, digest_json, load_json
from tools.operations.prepare_component_release import (
    RoutingBlocked,
    prepare_release,
    simulate_rollback,
    validate_release_manifest,
)
from tools.operations.run_component_validation_targets import collect_registered_test_ids


class ComponentReleasePreparationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validation_map = load_json(MAP_PATH)
        cls.r_target = next(
            target for target in cls.validation_map["targets"]
            if target["target_id"] == "r_research_slot_consumers"
        )

    def _git(self, repo, *args):
        return subprocess.run(
            ["git", "-C", str(repo), *args], check=True,
            capture_output=True, text=True,
        ).stdout.strip()

    def _source_repository(self, repo, *, include_crossref=True):
        self._git(repo, "init", "-q", "-b", "main")
        self._git(repo, "config", "user.name", "Component Fixture")
        self._git(repo, "config", "user.email", "component@example.invalid")
        files = {
            "ignition/research_workflow/slot.py": "VERSION = 'r1'\n",
            "ignition/research_workflow/test_pluggable_slot.py": (
                "import unittest\n"
                "class Fixture(unittest.TestCase):\n"
                "    def test_research(self): pass\n"
            ),
            "ignition/research_workflow/test_research_workflow.py": (
                "import unittest\n"
                "class Fixture(unittest.TestCase):\n"
                "    def test_research(self): pass\n"
            ),
            "ignition/scripts/external-research/openalex_client.py": "PROVIDER = 'openalex'\n",
        }
        if include_crossref:
            files["ignition/evidence-program/tools/run_crossref_verification.py"] = "PROVIDER = 'crossref'\n"
        for relative, content in files.items():
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        self._git(repo, "add", ".")
        self._git(repo, "commit", "-m", "R component source")
        return self._git(repo, "rev-parse", "HEAD")

    def _evidence(self, directory, source_sha, repo):
        test_ids = collect_registered_test_ids(
            self.r_target["modules"], repo_root=repo,
            import_roots=self.r_target.get("import_roots", []), validation_sha=source_sha,
        )
        report_lines = [f"{test_id.rsplit('.', 1)[-1]} ({test_id}) ... ok" for test_id in test_ids]
        test_word = "test" if len(test_ids) == 1 else "tests"
        test_report = "\n".join(report_lines) + f"\n\nRan {len(test_ids)} {test_word} in 0.001s\n\nOK\n"
        plan = {
            "schema_version": "1.0.0",
            "mode": "TARGETED",
            "source": {
                "base_sha": source_sha,
                "head_sha": source_sha,
                "validation_sha": source_sha,
            },
            "validation_map_sha256": digest_json(self.validation_map),
            "selected_target_ids": ["r_research_slot_consumers"],
        }
        plan["plan_sha256"] = digest_json(plan)
        receipt = {
            "schema_version": "1.0.0",
            "head_sha": source_sha,
            "base_sha": source_sha,
            "validation_sha": source_sha,
            "python_version": "3.12.0",
            "plan_sha256": plan["plan_sha256"],
            "validation_map_sha256": plan["validation_map_sha256"],
            "target_results": [{
                "target_id": "r_research_slot_consumers",
                "domain": "R",
                "successful": True,
                "tests": {
                    "modules": self.r_target["modules"],
                    "tests_run": len(test_ids),
                    "tests_executed": len(test_ids),
                    "failures": 0,
                    "errors": 0,
                    "skipped": 0,
                    "expected_failures": [],
                    "unexpected_successes": [],
                    "test_outcomes": [{"test": test_id, "status": "passed"} for test_id in test_ids],
                    "test_report": test_report,
                    "test_report_sha256": hashlib.sha256(test_report.encode("utf-8")).hexdigest(),
                    "test_report_bytes": len(test_report.encode("utf-8")),
                    "successful": True,
                    "status": "PASSED",
                },
                "commands": [],
            }],
            "claim_ceiling": "repository fixture",
        }
        receipt["receipt_sha256"] = digest_json(receipt)
        plan_path = directory / "plan.json"
        receipt_path = directory / "receipt.json"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        return plan_path, receipt_path, plan, receipt

    def _prepare(self, repo, source_sha, output_dir, version, plan_path, receipt_path):
        return prepare_release(
            repo_root=repo, component_id="research_workflow_slot", version=version,
            source_sha=source_sha, source_repository="Arvin-liu/when-systems-catch-fire",
            plan_path=plan_path, receipt_path=receipt_path, output_dir=output_dir,
        )

    def test_component_bundle_is_deterministic_source_bound_and_self_verifying(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            repo = parent / "source"
            repo.mkdir()
            source_sha = self._source_repository(repo)
            plan_path, receipt_path, _, _ = self._evidence(parent, source_sha, repo)
            first = self._prepare(repo, source_sha, parent / "first", "1.0.0", plan_path, receipt_path)
            second = self._prepare(repo, source_sha, parent / "second", "1.0.0", plan_path, receipt_path)
            first_archive = parent / "first" / first["artifact_file"]
            second_archive = parent / "second" / second["artifact_file"]
            self.assertEqual(first["artifact_state"], "CONTENT_ADDRESSED")
            self.assertEqual(first["artifact_sha256"], second["artifact_sha256"])
            self.assertEqual(first_archive.read_bytes(), second_archive.read_bytes())
            self.assertEqual(len(first["files"]), 5)
            verified = validate_release_manifest(first, first_archive, repo_root=repo)
            self.assertEqual(verified["source_commit_sha"], source_sha)

    def test_release_prep_blocks_missing_registered_adapter_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            repo = parent / "source"
            repo.mkdir()
            source_sha = self._source_repository(repo, include_crossref=False)
            plan_path, receipt_path, _, _ = self._evidence(parent, source_sha, repo)
            with self.assertRaisesRegex(RoutingBlocked, "no regular source files.*crossref_verifier_r1"):
                self._prepare(repo, source_sha, parent / "release", "1.0.0", plan_path, receipt_path)

    def test_release_prep_rejects_a_receipt_with_a_skip(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            repo = parent / "source"
            repo.mkdir()
            source_sha = self._source_repository(repo)
            plan_path, receipt_path, _, receipt = self._evidence(parent, source_sha, repo)
            tests = receipt["target_results"][0]["tests"]
            tests["tests_run"] = 2
            tests["tests_executed"] = 1
            tests["skipped"] = 1
            module = tests["modules"][0]
            tests["test_outcomes"].append({"test": f"{module}.Fixture.test_skip", "status": "skipped"})
            receipt.pop("receipt_sha256")
            receipt["receipt_sha256"] = digest_json(receipt)
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            with self.assertRaisesRegex(RoutingBlocked, "incomplete, skipped"):
                self._prepare(repo, source_sha, parent / "release", "1.0.0", plan_path, receipt_path)

    def test_archive_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            repo = parent / "source"
            repo.mkdir()
            source_sha = self._source_repository(repo)
            plan_path, receipt_path, _, _ = self._evidence(parent, source_sha, repo)
            manifest = self._prepare(repo, source_sha, parent / "release", "1.0.0", plan_path, receipt_path)
            archive_path = parent / "release" / manifest["artifact_file"]
            archive_path.write_bytes(archive_path.read_bytes() + b"tamper")
            with self.assertRaisesRegex(RoutingBlocked, "archive digest or size"):
                validate_release_manifest(manifest, archive_path)

    def test_rollback_selects_an_earlier_verified_digest_without_activation(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            repo = parent / "source"
            repo.mkdir()
            source_sha = self._source_repository(repo)
            plan_path, receipt_path, _, _ = self._evidence(parent, source_sha, repo)
            earlier = self._prepare(repo, source_sha, parent / "v1", "1.0.0", plan_path, receipt_path)
            current = self._prepare(repo, source_sha, parent / "v2", "1.1.0", plan_path, receipt_path)
            event = simulate_rollback(
                current, parent / "v2" / current["artifact_file"],
                earlier, parent / "v1" / earlier["artifact_file"],
                repo_root=repo,
            )
            self.assertEqual(event["release_status"], "SIMULATED_UNPUBLISHED")
            self.assertFalse(event["activation_performed"])
            self.assertEqual(event["selected_previous_release"]["artifact_sha256"], earlier["artifact_sha256"])

    def test_rollback_rejects_a_target_that_is_not_earlier(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            repo = parent / "source"
            repo.mkdir()
            source_sha = self._source_repository(repo)
            plan_path, receipt_path, _, _ = self._evidence(parent, source_sha, repo)
            earlier = self._prepare(repo, source_sha, parent / "v1", "1.0.0", plan_path, receipt_path)
            current = self._prepare(repo, source_sha, parent / "v2", "1.1.0", plan_path, receipt_path)
            with self.assertRaisesRegex(RoutingBlocked, "earlier component version"):
                simulate_rollback(
                    earlier, parent / "v1" / earlier["artifact_file"],
                    current, parent / "v2" / current["artifact_file"],
                    repo_root=repo,
                )

    def test_publication_witness_uses_named_environment_inputs_after_release_creation(self):
        workflow = Path(__file__).resolve().parents[2] / ".github/workflows/component-release.yml"
        source = workflow.read_text(encoding="utf-8")
        publish_section = source.split('"$RUNNER_TEMP/published-release.json"', 1)[1].split("\n          PY", 1)[0]
        self.assertIn('int(os.environ["AUTHORIZATION_PR"])', publish_section)
        self.assertIn('os.environ["VALIDATION_RUN_ID"]', publish_section)
        self.assertIn('os.environ["VALIDATION_RUN_ATTEMPT"]', publish_section)
        self.assertIn('os.environ["SOURCE_SHA"]', publish_section)
        self.assertNotIn("int(sys.argv[3])", publish_section)


if __name__ == "__main__":
    unittest.main()
