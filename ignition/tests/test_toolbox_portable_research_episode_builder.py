from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
IGNITION_ROOT = REPO_ROOT / "ignition"
TOOLS = IGNITION_ROOT / "tools"
sys.path.insert(0, str(TOOLS))
import toolbox_build_portable_research_episode as builder  # noqa: E402
from toolbox_portable_research_episode import validate_episode  # noqa: E402


SCRIPT = TOOLS / "toolbox_build_portable_research_episode.py"
INPUT_SCHEMA = IGNITION_ROOT / "schemas/operations/toolbox-portable-research-episode-builder-input-r0.schema.json"
OUTPUT_SCHEMA = IGNITION_ROOT / "schemas/operations/toolbox-portable-research-episode-builder-output-r0.schema.json"


def _base_request(root: Path) -> dict:
    (root / "input.json").write_bytes(b'{"q":"bounded"}\n')
    (root / "result.json").write_bytes(b'{"count":1}\n')
    return {
        "schema_version": builder.INPUT_SCHEMA_VERSION,
        "episode_id": "builder-test-episode",
        "package_revision": "test-revision-0",
        "import_mode": "SOURCE_PACKAGE",
        "required_artifact_ids": ["input", "result"],
        "artifacts": [
            {
                "artifact_id": "input",
                "version_id": "r0",
                "relative_path": "input.json",
                "parent_ref": None,
                "dependency_refs": [],
                "required": True,
                "is_current": True,
            },
            {
                "artifact_id": "result",
                "version_id": "r0",
                "relative_path": "result.json",
                "parent_ref": None,
                "dependency_refs": [{"artifact_id": "input", "version_id": "r0"}],
                "required": True,
                "is_current": True,
            },
        ],
        "executions": [
            {
                "execution_id": "run-1",
                "status": "EXECUTED",
                "run_ref": {"run_id": "run-1", "attempt": 1, "evidence_ref": "evidence.json#/run"},
                "used_artifact_refs": [{"artifact_id": "input", "version_id": "r0"}],
                "attached_artifact_refs": [],
                "produced_artifact_refs": [{"artifact_id": "result", "version_id": "r0"}],
                "not_executed_reason": None,
            }
        ],
        "reviews": [],
        "omissions": [],
        "fork_id_mappings": [],
    }


def _run_cli(request: dict, root: Path, raw: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    payload = raw if raw is not None else json.dumps(request, ensure_ascii=False).encode("utf-8")
    return subprocess.run(
        [sys.executable, "-B", str(SCRIPT), "--stdin", "--workspace-root", str(root)],
        input=payload,
        capture_output=True,
        cwd=REPO_ROOT,
        check=False,
    )


class PortableResearchEpisodeBuilderTests(unittest.TestCase):
    def test_real_cli_build_hashes_files_and_existing_validator_checks_manifest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="episode-builder-", dir=IGNITION_ROOT) as temporary:
            root = Path(temporary)
            request = _base_request(root)
            process = _run_cli(request, root)
            self.assertEqual(process.returncode, 0, process.stderr.decode())
            output = json.loads(process.stdout)
            self.assertEqual(output["status"], "BUILD_SUCCEEDED")
            self.assertFalse(output["execution_authorized"])
            self.assertFalse(output["files_copied"])
            self.assertFalse(output["files_written"])
            self.assertEqual(output["source_authenticity"], "NOT_ESTABLISHED")
            episode = output["episode"]
            self.assertEqual(episode["schema_version"], "ignition-portable-research-episode-r0")
            result = validate_episode(episode)
            self.assertEqual(result["status"], "EPISODE_MANIFEST_CONSISTENT")
            receipts = {row["artifact_id"]: row for row in output["file_receipts"]}
            for artifact_id, name in (("input", "input.json"), ("result", "result.json")):
                data = (root / name).read_bytes()
                self.assertEqual(receipts[artifact_id]["sha256"], hashlib.sha256(data).hexdigest())
                self.assertEqual(receipts[artifact_id]["byte_count"], len(data))
            self.assertEqual(sorted(path.name for path in root.iterdir()), ["input.json", "result.json"])

    def test_output_is_deterministic_for_same_files_and_declarations(self) -> None:
        with tempfile.TemporaryDirectory(prefix="episode-builder-", dir=IGNITION_ROOT) as temporary:
            root = Path(temporary)
            request = _base_request(root)
            first = _run_cli(request, root)
            second = _run_cli(request, root)
            self.assertEqual(first.returncode, 0)
            self.assertEqual(first.stdout, second.stdout)

    def test_path_traversal_is_rejected_before_any_file_read(self) -> None:
        with tempfile.TemporaryDirectory(prefix="episode-builder-", dir=IGNITION_ROOT) as temporary:
            root = Path(temporary)
            request = _base_request(root)
            request["artifacts"][0]["relative_path"] = "../outside.json"
            output = json.loads(_run_cli(request, root).stdout)
            self.assertEqual(output["status"], "BUILD_FAILED")
            self.assertEqual(output["findings"][0]["code"], "UNSAFE_RELATIVE_PATH")
            self.assertEqual(output["total_bytes_read"], 0)
            self.assertIsNone(output["episode"])

    def test_symlink_artifact_is_rejected_without_following_it(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks are unavailable")
        with tempfile.TemporaryDirectory(prefix="episode-builder-", dir=IGNITION_ROOT) as temporary:
            root = Path(temporary)
            request = _base_request(root)
            (root / "alias.json").symlink_to(root / "input.json")
            request["artifacts"][0]["relative_path"] = "alias.json"
            output = json.loads(_run_cli(request, root).stdout)
            self.assertEqual(output["status"], "BUILD_FAILED")
            self.assertEqual(output["findings"][0]["code"], "ARTIFACT_PATH_UNAVAILABLE")
            self.assertEqual(output["total_bytes_read"], 0)

    def test_unknown_event_reference_is_rejected_before_file_reads(self) -> None:
        with tempfile.TemporaryDirectory(prefix="episode-builder-", dir=IGNITION_ROOT) as temporary:
            root = Path(temporary)
            request = _base_request(root)
            request["executions"][0]["used_artifact_refs"] = [{"artifact_id": "missing", "version_id": "r0"}]
            output = json.loads(_run_cli(request, root).stdout)
            self.assertEqual(output["status"], "INPUT_INVALID")
            self.assertEqual(output["findings"][0]["code"], "UNKNOWN_ARTIFACT_VERSION_REFERENCE")
            self.assertEqual(output["total_bytes_read"], 0)

    def test_duplicate_json_keys_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="episode-builder-", dir=IGNITION_ROOT) as temporary:
            root = Path(temporary)
            _base_request(root)
            raw = b'{"schema_version":"portable-research-episode-builder-input-r0","schema_version":"bad"}'
            output = json.loads(_run_cli({}, root, raw=raw).stdout)
            self.assertEqual(output["status"], "INPUT_INVALID")
            self.assertEqual(output["findings"][0]["code"], "DUPLICATE_JSON_KEY")
            self.assertEqual(output["total_bytes_read"], 0)

    def test_workspace_root_outside_ignition_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="episode-builder-outside-") as temporary:
            outside = Path(temporary)
            request = _base_request_in_external_root(outside)
            output = json.loads(_run_cli(request, outside).stdout)
            self.assertEqual(output["status"], "INPUT_INVALID")
            self.assertEqual(output["findings"][0]["code"], "WORKSPACE_ROOT_OUTSIDE_IGNITION")
            self.assertEqual(output["total_bytes_read"], 0)

    def test_per_file_limit_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory(prefix="episode-builder-", dir=IGNITION_ROOT) as temporary:
            root = Path(temporary)
            request = _base_request(root)
            (root / "large.bin").write_bytes(b"12345")
            request["artifacts"] = [{
                "artifact_id": "large", "version_id": "r0", "relative_path": "large.bin",
                "parent_ref": None, "dependency_refs": [], "required": True, "is_current": True,
            }]
            request["required_artifact_ids"] = ["large"]
            request["executions"] = []
            fd = builder._open_workspace_root(root)
            try:
                original = builder.MAX_FILE_BYTES
                builder.MAX_FILE_BYTES = 4
                output = builder.build_episode(request, fd)
            finally:
                builder.MAX_FILE_BYTES = original
                os.close(fd)
            self.assertEqual(output["status"], "BUILD_FAILED")
            self.assertEqual(output["findings"][0]["code"], "ARTIFACT_FILE_LIMIT_EXCEEDED")
            self.assertEqual(output["total_bytes_read"], 0)

    def test_success_and_error_envelopes_conform_to_output_schema(self) -> None:
        schema = json.loads(OUTPUT_SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        with tempfile.TemporaryDirectory(prefix="episode-builder-", dir=IGNITION_ROOT) as temporary:
            root = Path(temporary)
            request = _base_request(root)
            success = json.loads(_run_cli(request, root).stdout)
            self.assertEqual(list(validator.iter_errors(success)), [])
            request["artifacts"][0]["relative_path"] = "../bad"
            failure = json.loads(_run_cli(request, root).stdout)
            self.assertEqual(list(validator.iter_errors(failure)), [])

    def test_input_schema_rejects_extra_authority_fields(self) -> None:
        schema = json.loads(INPUT_SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        request = {
            "schema_version": builder.INPUT_SCHEMA_VERSION,
            "episode_id": "x",
            "package_revision": "x",
            "import_mode": "SOURCE_PACKAGE",
            "required_artifact_ids": [],
            "artifacts": [],
            "executions": [],
            "reviews": [],
            "omissions": [],
            "fork_id_mappings": [],
            "execution_authorized": True,
        }
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(request)))


def _base_request_in_external_root(root: Path) -> dict:
    (root / "input.json").write_bytes(b'{"q":"bounded"}\n')
    (root / "result.json").write_bytes(b'{"count":1}\n')
    return _base_request_without_writing(root)


def _base_request_without_writing(root: Path) -> dict:
    return {
        "schema_version": builder.INPUT_SCHEMA_VERSION,
        "episode_id": "builder-test-episode",
        "package_revision": "test-revision-0",
        "import_mode": "SOURCE_PACKAGE",
        "required_artifact_ids": ["input", "result"],
        "artifacts": [
            {"artifact_id": "input", "version_id": "r0", "relative_path": "input.json", "parent_ref": None, "dependency_refs": [], "required": True, "is_current": True},
            {"artifact_id": "result", "version_id": "r0", "relative_path": "result.json", "parent_ref": None, "dependency_refs": [{"artifact_id": "input", "version_id": "r0"}], "required": True, "is_current": True},
        ],
        "executions": [], "reviews": [], "omissions": [], "fork_id_mappings": [],
    }


if __name__ == "__main__":
    unittest.main()
