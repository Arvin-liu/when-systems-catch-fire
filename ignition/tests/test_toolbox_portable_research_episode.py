from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any


IGNITION_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = IGNITION_ROOT.parent
FIXTURE = IGNITION_ROOT / "tests/fixtures/toolbox-portable-research-episode/valid-source-package-r0.json"
TOOL_PATH = IGNITION_ROOT / "tools/toolbox_portable_research_episode.py"
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import toolbox_portable_research_episode as tool  # noqa: E402


def valid_episode() -> dict[str, Any]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def finding_codes(result: dict[str, Any]) -> set[str]:
    return {row["code"] for row in result["findings"]}


def warning_codes(result: dict[str, Any]) -> set[str]:
    return {row["code"] for row in result["warnings"]}


class PortableResearchEpisodeTests(unittest.TestCase):
    def test_versioned_package_distinguishes_execution_attachment_and_stale_review(self) -> None:
        result = tool.validate_episode(valid_episode())

        self.assertEqual(result["status"], "EPISODE_MANIFEST_CONSISTENT")
        self.assertEqual(result["findings"], [])
        self.assertIn("REVIEW_TARGET_IS_NOT_CURRENT_VERSION", warning_codes(result))
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["import_performed"])
        self.assertFalse(result["artifact_bytes_verified"])
        relations = {row["execution_id"]: row for row in result["summary"]["execution_relations"]}
        self.assertEqual(relations["planned-review-step"]["declared_status"], "PLANNED")
        self.assertEqual(relations["planned-review-step"]["used_artifact_ref_count"], 0)
        self.assertEqual(relations["planned-review-step"]["attached_artifact_ref_count"], 1)
        self.assertEqual(relations["revision-run"]["declared_status"], "EXECUTED")

    def test_required_omission_is_incomplete_not_a_pass(self) -> None:
        episode = valid_episode()
        episode["required_artifact_ids"].append("review-ledger")
        episode["omissions"].append({
            "artifact_id": "review-ledger",
            "version_id": None,
            "reason": "UNAVAILABLE_NOT_SHARED",
            "required": True,
            "rationale": "The source workspace did not export the required ledger.",
        })

        result = tool.validate_episode(episode)

        self.assertEqual(result["status"], "EPISODE_MANIFEST_INCOMPLETE")
        self.assertIn("REQUIRED_CONTENT_EXPLICITLY_OMITTED", warning_codes(result))
        self.assertFalse(result["execution_authorized"])

    def test_unaccounted_required_artifact_is_incomplete(self) -> None:
        episode = valid_episode()
        episode["required_artifact_ids"].append("missing-artifact")

        result = tool.validate_episode(episode)

        self.assertEqual(result["status"], "EPISODE_MANIFEST_INCOMPLETE")
        self.assertIn("REQUIRED_ARTIFACT_UNACCOUNTED", warning_codes(result))

    def test_planned_step_cannot_claim_used_or_produced_artifacts(self) -> None:
        episode = valid_episode()
        episode["executions"][1]["produced_artifact_refs"] = [{
            key: episode["artifacts"][2][key] for key in ("artifact_id", "version_id", "sha256")
        }]

        result = tool.validate_episode(episode)

        self.assertEqual(result["status"], "EPISODE_MANIFEST_INVALID")
        self.assertIn("NONRUN_STATUS_CLAIMS_PRODUCED_OUTPUT", finding_codes(result))

    def test_executed_step_requires_a_run_reference(self) -> None:
        episode = valid_episode()
        episode["executions"][2]["run_ref"] = None

        result = tool.validate_episode(episode)

        self.assertIn("EXECUTION_STATUS_REQUIRES_RUN_REF", finding_codes(result))

    def test_not_executed_step_cannot_carry_a_run_reference(self) -> None:
        episode = valid_episode()
        episode["executions"][3]["run_ref"] = {"run_id": "run-44", "attempt": 1, "evidence_ref": "receipt://run-44"}

        result = tool.validate_episode(episode)

        self.assertIn("NONRUN_STATUS_HAS_RUN_REF", finding_codes(result))

    def test_digest_bound_dependency_must_resolve_exactly(self) -> None:
        episode = valid_episode()
        episode["artifacts"][2]["parent_ref"]["sha256"] = "d" * 64

        result = tool.validate_episode(episode)

        self.assertIn("ARTIFACT_VERSION_REF_UNKNOWN", finding_codes(result))

    def test_review_timestamp_must_be_a_valid_rfc3339_datetime(self) -> None:
        episode = valid_episode()
        episode["reviews"][0]["reviewed_at_utc"] = "not-a-date"

        result = tool.validate_episode(episode)

        self.assertEqual(result["status"], "EPISODE_MANIFEST_INVALID")
        self.assertIn("INPUT_SCHEMA_INVALID", finding_codes(result))

    def test_dependency_cycle_is_rejected(self) -> None:
        episode = valid_episode()
        episode["artifacts"][0]["dependency_refs"] = [{
            key: episode["artifacts"][2][key] for key in ("artifact_id", "version_id", "sha256")
        }]

        result = tool.validate_episode(episode)

        self.assertIn("ARTIFACT_DEPENDENCY_CYCLE", finding_codes(result))

    def test_fork_preview_requires_complete_unique_id_mapping(self) -> None:
        episode = valid_episode()
        episode["import_mode"] = "READ_ONLY_FORK_PREVIEW"
        mappings = [("EPISODE", "episode-research-42")]
        mappings += [("ARTIFACT", item) for item in ("source-capture", "analysis-report")]
        mappings += [("EXECUTION", row["execution_id"]) for row in episode["executions"]]
        mappings += [("REVIEW", row["review_id"]) for row in episode["reviews"]]
        episode["fork_id_mappings"] = [
            {"entity_type": entity_type, "source_id": source_id, "fork_id": f"fork-{source_id}"}
            for entity_type, source_id in mappings
        ]

        result = tool.validate_episode(episode)

        self.assertEqual(result["status"], "EPISODE_MANIFEST_CONSISTENT")
        self.assertFalse(result["import_performed"])

        episode["fork_id_mappings"].pop()
        incomplete = tool.validate_episode(episode)
        self.assertIn("FORK_ID_MAPPING_INCOMPLETE", finding_codes(incomplete))

    def test_source_package_cannot_smuggle_fork_mappings(self) -> None:
        episode = valid_episode()
        episode["fork_id_mappings"] = [{"entity_type": "EPISODE", "source_id": "episode-research-42", "fork_id": "fork-episode"}]

        result = tool.validate_episode(episode)

        self.assertIn("SOURCE_PACKAGE_HAS_FORK_ID_MAPPINGS", finding_codes(result))

    def test_duplicate_json_keys_fail_closed(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input=b'{"episode_id":"a","episode_id":"b"}',
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 2)
        result = json.loads(completed.stdout.decode("utf-8"))
        self.assertIn("DUPLICATE_JSON_KEY", finding_codes(result))
        self.assertFalse(result["execution_authorized"])

    def test_oversized_stdin_fails_closed(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input=b" " * (tool.MAX_INPUT_BYTES + 1),
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 2)
        result = json.loads(completed.stdout.decode("utf-8"))
        self.assertIn("INPUT_UNAVAILABLE_OR_INVALID", finding_codes(result))
        self.assertFalse(result["import_performed"])

    def test_cli_returns_json_for_consistent_manifest(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input=FIXTURE.read_bytes(),
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", errors="replace"))
        result = json.loads(completed.stdout.decode("utf-8"))
        self.assertEqual(result["status"], "EPISODE_MANIFEST_CONSISTENT")
        self.assertFalse(result["execution_authorized"])


if __name__ == "__main__":
    unittest.main()
