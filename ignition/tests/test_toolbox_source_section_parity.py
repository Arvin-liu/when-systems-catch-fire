from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
IGNITION_ROOT = REPO_ROOT / "ignition"
TOOLS = IGNITION_ROOT / "tools"
sys.path.insert(0, str(TOOLS))
import toolbox_compare_source_section_bytes as comparator  # noqa: E402

SCRIPT = TOOLS / "toolbox_compare_source_section_bytes.py"
INPUT_SCHEMA = IGNITION_ROOT / "schemas/operations/toolbox-source-section-parity-input-r0.schema.json"
OUTPUT_SCHEMA = IGNITION_ROOT / "schemas/operations/toolbox-source-section-parity-output-r0.schema.json"
START = "### 第一部分"
END = "### 第二部分"


def _request(source: str, candidate_path: str, **changes: object) -> dict:
    source_bytes = source.encode("utf-8")
    value = {
        "schema_version": comparator.INPUT_SCHEMA_VERSION,
        "task_id": "source-section-test",
        "source_ref": "owner/repo@abc123:path/to/source.md",
        "source_document_text": source,
        "source_document_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "candidate_path": candidate_path,
        "start_marker": START,
        "end_marker": END,
    }
    value.update(changes)
    return value


def _candidate(root: Path, data: bytes, *, name: str = "candidate.md") -> str:
    path = root / name
    path.write_bytes(data)
    return path.relative_to(REPO_ROOT).as_posix()


def _run_cli(request: dict, *, raw: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    payload = raw if raw is not None else json.dumps(request, ensure_ascii=False).encode("utf-8")
    return subprocess.run(
        [sys.executable, "-B", str(SCRIPT), "--stdin"],
        input=payload,
        capture_output=True,
        cwd=REPO_ROOT,
        check=False,
    )


class SourceSectionParityTests(unittest.TestCase):
    def test_exact_section_matches_and_output_does_not_echo_document_text(self) -> None:
        with tempfile.TemporaryDirectory(prefix="source-section-", dir=IGNITION_ROOT) as temporary:
            root = Path(temporary)
            source = "封面\n### 第一部分\n精确正文。\n### 第二部分\n后续内容\n"
            path = _candidate(root, "另有前言\n### 第一部分\n精确正文。\n### 第二部分\n候选文件后续\n".encode())
            process = _run_cli(_request(source, path))
            self.assertEqual(process.returncode, 0, process.stderr.decode())
            output = json.loads(process.stdout)
            self.assertEqual(output["status"], "BYTE_IDENTICAL")
            self.assertTrue(output["byte_identical"])
            self.assertFalse(output["source_ref_authenticated"])
            self.assertFalse(output["effects"]["files_written"])
            self.assertFalse(output["effects"]["network"])
            self.assertFalse(output["effects"]["execution_authorized"])
            self.assertEqual(output["source_section"]["sha256"], output["candidate_section"]["sha256"])
            self.assertEqual(output["source_section"]["byte_count"], len("### 第一部分\n精确正文。\n".encode()))
            self.assertNotIn("精确正文", process.stdout.decode())

    def test_difference_is_a_successful_comparison_result(self) -> None:
        with tempfile.TemporaryDirectory(prefix="source-section-", dir=IGNITION_ROOT) as temporary:
            root = Path(temporary)
            source = "### 第一部分\nsource\n### 第二部分\n"
            path = _candidate(root, b"### \xe7\xac\xac\xe4\xb8\x80\xe9\x83\xa8\xe5\x88\x86\ncandidate\n### \xe7\xac\xac\xe4\xba\x8c\xe9\x83\xa8\xe5\x88\x86\n")
            process = _run_cli(_request(source, path))
            self.assertEqual(process.returncode, 0)
            output = json.loads(process.stdout)
            self.assertEqual(output["status"], "BYTE_DIFFERENT")
            self.assertFalse(output["byte_identical"])
            self.assertNotEqual(output["source_section"]["sha256"], output["candidate_section"]["sha256"])

    def test_source_digest_mismatch_fails_before_candidate_access(self) -> None:
        request = _request("### 第一部分\na\n### 第二部分\n", "ignition/no-such-document.md",
                           source_document_sha256="0" * 64)
        output = json.loads(_run_cli(request).stdout)
        self.assertEqual(output["status"], "INPUT_INVALID")
        self.assertEqual(output["findings"][0]["code"], "SOURCE_DOCUMENT_DIGEST_MISMATCH")
        self.assertFalse(output["effects"]["candidate_file_accessed"])

    def test_source_start_marker_must_be_unique(self) -> None:
        with tempfile.TemporaryDirectory(prefix="source-section-", dir=IGNITION_ROOT) as temporary:
            root = Path(temporary)
            path = _candidate(root, b"unused")
            source = "### 第一部分\na\n### 第一部分\nb\n### 第二部分\n"
            output = json.loads(_run_cli(_request(source, path)).stdout)
            self.assertEqual(output["status"], "COMPARE_FAILED")
            self.assertEqual(output["findings"][0]["code"], "SOURCE_START_MARKER_NOT_UNIQUE")
            self.assertFalse(output["effects"]["candidate_file_accessed"])

    def test_candidate_marker_must_be_unique(self) -> None:
        with tempfile.TemporaryDirectory(prefix="source-section-", dir=IGNITION_ROOT) as temporary:
            root = Path(temporary)
            source = "### 第一部分\na\n### 第二部分\n"
            path = _candidate(root, "### 第一部分\na\n### 第一部分\nb\n### 第二部分\n".encode())
            output = json.loads(_run_cli(_request(source, path)).stdout)
            self.assertEqual(output["status"], "COMPARE_FAILED")
            self.assertEqual(output["findings"][0]["code"], "CANDIDATE_START_MARKER_NOT_UNIQUE")
            self.assertTrue(output["effects"]["candidate_file_accessed"])

    def test_reversed_markers_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="source-section-", dir=IGNITION_ROOT) as temporary:
            root = Path(temporary)
            path = _candidate(root, "### 第二部分\na\n### 第一部分\n".encode())
            source = "### 第一部分\na\n### 第二部分\n"
            output = json.loads(_run_cli(_request(source, path)).stdout)
            self.assertEqual(output["status"], "COMPARE_FAILED")
            self.assertEqual(output["findings"][0]["code"], "CANDIDATE_MARKERS_OUT_OF_ORDER")

    def test_identical_markers_are_rejected_before_file_access(self) -> None:
        with tempfile.TemporaryDirectory(prefix="source-section-", dir=IGNITION_ROOT) as temporary:
            root = Path(temporary)
            path = _candidate(root, b"irrelevant")
            request = _request("### 第一部分\na\n### 第二部分\n", path, end_marker=START)
            output = json.loads(_run_cli(request).stdout)
            self.assertEqual(output["status"], "INPUT_INVALID")
            self.assertEqual(output["findings"][0]["code"], "MARKERS_MUST_DIFFER")
            self.assertFalse(output["effects"]["candidate_file_accessed"])

    def test_traversal_and_non_document_paths_are_rejected(self) -> None:
        source = "### 第一部分\na\n### 第二部分\n"
        for bad_path, expected in (("../.github/README.md", "CANDIDATE_PATH_INVALID"),
                                   (".git/config", "CANDIDATE_PATH_OUTSIDE_HUMAN_DOCUMENTS"),
                                   ("ignition/tools/secrets.py", "CANDIDATE_PATH_OUTSIDE_HUMAN_DOCUMENTS")):
            with self.subTest(path=bad_path):
                output = json.loads(_run_cli(_request(source, bad_path)).stdout)
                self.assertEqual(output["status"], "COMPARE_FAILED")
                self.assertEqual(output["findings"][0]["code"], expected)
                self.assertFalse(output["effects"]["candidate_file_accessed"])

    def test_symlink_file_is_not_followed(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks unavailable")
        with tempfile.TemporaryDirectory(prefix="source-section-", dir=IGNITION_ROOT) as temporary:
            root = Path(temporary)
            real = _candidate(root, b"### \xe7\xac\xac\xe4\xb8\x80\xe9\x83\xa8\xe5\x88\x86\na\n### \xe7\xac\xac\xe4\xba\x8c\xe9\x83\xa8\xe5\x88\x86\n", name="real.md")
            real_path = REPO_ROOT / real
            alias = root / "alias.md"
            alias.symlink_to(real_path)
            alias_rel = alias.relative_to(REPO_ROOT).as_posix()
            source = "### 第一部分\na\n### 第二部分\n"
            output = json.loads(_run_cli(_request(source, alias_rel)).stdout)
            self.assertEqual(output["status"], "COMPARE_FAILED")
            self.assertEqual(output["findings"][0]["code"], "CANDIDATE_PATH_UNAVAILABLE")
            self.assertFalse(output["effects"]["candidate_file_accessed"])

    def test_symlink_parent_is_not_followed(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks unavailable")
        with tempfile.TemporaryDirectory(prefix="source-section-", dir=IGNITION_ROOT) as temporary:
            root = Path(temporary)
            actual_dir = root / "actual"
            actual_dir.mkdir()
            target = _candidate(actual_dir, b"### \xe7\xac\xac\xe4\xb8\x80\xe9\x83\xa8\xe5\x88\x86\na\n### \xe7\xac\xac\xe4\xba\x8c\xe9\x83\xa8\xe5\x88\x86\n")
            alias_dir = root / "alias"
            alias_dir.symlink_to(actual_dir, target_is_directory=True)
            alias_path = (root / "alias" / "candidate.md").relative_to(REPO_ROOT).as_posix()
            source = "### 第一部分\na\n### 第二部分\n"
            output = json.loads(_run_cli(_request(source, alias_path)).stdout)
            self.assertEqual(output["status"], "COMPARE_FAILED")
            self.assertEqual(output["findings"][0]["code"], "CANDIDATE_PATH_UNAVAILABLE")
            self.assertFalse(output["effects"]["candidate_file_accessed"])

    def test_fifo_and_non_utf8_candidates_fail_closed(self) -> None:
        if not hasattr(os, "mkfifo"):
            self.skipTest("named pipes unavailable")
        with tempfile.TemporaryDirectory(prefix="source-section-", dir=IGNITION_ROOT) as temporary:
            root = Path(temporary)
            fifo = root / "fifo.md"
            os.mkfifo(fifo)
            fifo_path = fifo.relative_to(REPO_ROOT).as_posix()
            source = "### 第一部分\na\n### 第二部分\n"
            output = json.loads(_run_cli(_request(source, fifo_path)).stdout)
            self.assertEqual(output["status"], "COMPARE_FAILED")
            self.assertEqual(output["findings"][0]["code"], "CANDIDATE_NOT_REGULAR_FILE")
            bad_utf8 = _candidate(root, b"\xff", name="bad.md")
            output = json.loads(_run_cli(_request(source, bad_utf8)).stdout)
            self.assertEqual(output["findings"][0]["code"], "CANDIDATE_NOT_UTF8")

    def test_candidate_size_limit_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory(prefix="source-section-", dir=IGNITION_ROOT) as temporary:
            root = Path(temporary)
            path = _candidate(root, b"12345")
            source = "### 第一部分\na\n### 第二部分\n"
            request = _request(source, path)
            root_fd = comparator._open_repo_root()
            try:
                with patch.object(comparator, "MAX_CANDIDATE_BYTES", 4):
                    output = comparator.compare_section(request, root_fd)
            finally:
                os.close(root_fd)
            self.assertEqual(output["status"], "COMPARE_FAILED")
            self.assertEqual(output["findings"][0]["code"], "CANDIDATE_FILE_LIMIT_EXCEEDED")

    def test_duplicate_json_keys_are_rejected(self) -> None:
        raw = b'{"schema_version":"toolbox-source-section-parity-input-r0","schema_version":"invalid"}'
        output = json.loads(_run_cli({}, raw=raw).stdout)
        self.assertEqual(output["status"], "INPUT_INVALID")
        self.assertEqual(output["findings"][0]["code"], "DUPLICATE_JSON_KEY")

    def test_stdin_limit_is_enforced_before_candidate_access(self) -> None:
        raw = b" " * (comparator.MAX_INPUT_BYTES + 1)
        output = json.loads(_run_cli({}, raw=raw).stdout)
        self.assertEqual(output["status"], "INPUT_INVALID")
        self.assertEqual(output["findings"][0]["code"], "INPUT_BYTE_LIMIT_EXCEEDED")
        self.assertFalse(output["effects"]["candidate_file_accessed"])

    def test_authority_fields_are_rejected_by_input_schema(self) -> None:
        with tempfile.TemporaryDirectory(prefix="source-section-", dir=IGNITION_ROOT) as temporary:
            root = Path(temporary)
            path = _candidate(root, b"irrelevant")
            request = _request("### 第一部分\na\n### 第二部分\n", path, execution_authorized=True)
            output = json.loads(_run_cli(request).stdout)
            self.assertEqual(output["status"], "INPUT_INVALID")
            self.assertEqual(output["findings"][0]["code"], "INPUT_SCHEMA_INVALID")
            self.assertFalse(output["effects"]["candidate_file_accessed"])

    def test_output_contract_covers_match_mismatch_and_failure(self) -> None:
        schema = json.loads(OUTPUT_SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        with tempfile.TemporaryDirectory(prefix="source-section-", dir=IGNITION_ROOT) as temporary:
            root = Path(temporary)
            source = "### 第一部分\n同一段\n### 第二部分\n"
            match_path = _candidate(root, source.encode(), name="match.md")
            mismatch_path = _candidate(root, source.replace("同一段", "另一段").encode(), name="mismatch.md")
            for request in (_request(source, match_path), _request(source, mismatch_path),
                            _request(source, "../outside.md")):
                output = json.loads(_run_cli(request).stdout)
                self.assertEqual(list(validator.iter_errors(output)), [])

    def test_same_input_is_deterministic_and_offsets_count_utf8_bytes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="source-section-", dir=IGNITION_ROOT) as temporary:
            root = Path(temporary)
            source = "前缀\n### 第一部分\n中\n### 第二部分\n"
            path = _candidate(root, source.encode())
            request = _request(source, path)
            first = _run_cli(request)
            second = _run_cli(request)
            self.assertEqual(first.stdout, second.stdout)
            output = json.loads(first.stdout)
            self.assertEqual(output["source_section"]["start_offset_bytes"], len("前缀\n".encode()))


if __name__ == "__main__":
    unittest.main()
