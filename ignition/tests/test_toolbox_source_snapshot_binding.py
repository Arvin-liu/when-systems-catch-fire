from __future__ import annotations

import contextlib
import hashlib
import io
import json
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch


IGNITION_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = IGNITION_ROOT.parent
sys.path.insert(0, str(IGNITION_ROOT))
from tools.toolbox_bind_offline_source_snapshot_run import main  # noqa: E402
from ignition.research_workflow import slot  # noqa: E402


class OfflineSourceSnapshotToolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="ignition-source-snapshot-")
        self.root = Path(self.temp.name)
        self.captures = self.root / "captures"
        self.captures.mkdir()
        self.capture_text = "Frozen source result: the reported mean changed by 2.4 units.\n"
        self.capture_bytes = self.capture_text.encode("utf-8")
        (self.captures / "source.txt").write_bytes(self.capture_bytes)
        manifest_row = {
            "title": "Frozen source report",
            "source_url": "https://example.org/report",
            "capture_path": "source.txt",
            "capture_kind": "web_run_observation",
            "captured_at_utc": "2026-10-17T00:00:00Z",
            "locator": "Results, paragraph 1",
            "query_ids": ["Q1"],
        }
        self.manifest = self.captures / "manifest.jsonl"
        self.manifest.write_text(json.dumps(manifest_row) + "\n", encoding="utf-8")
        self.digest_lock = self.root / "expected-digests.json"
        self.digest_lock.write_text(json.dumps({
            "S1": hashlib.sha256(self.capture_bytes).hexdigest(),
        }) + "\n", encoding="utf-8")
        self.draft = self.root / "draft.md"
        self.draft.write_text("The frozen report records a change of 2.4 units [S1].\n", encoding="utf-8")
        self.claim_reviews = self.root / "claim-reviews.jsonl"
        claim = {
            "claim_id": "C1",
            "claim_text": "The report records a change of 2.4 units.",
            "source_id": "S1",
            "review_judgment": "SUPPORTS",
            "reviewer_type": "HUMAN",
            "reviewer": "fixture-reviewer",
            "reviewed_at_utc": "2026-10-17T00:00:00Z",
            "evidence_field": "captured_text",
            "evidence_quote": self.capture_text.strip(),
        }
        self.claim_reviews.write_text(json.dumps(claim) + "\n", encoding="utf-8")
        sources, _, _, _, _ = slot._snapshot_sources(str(self.manifest), str(self.digest_lock), 1)
        self.source_set_digest = slot._canonical_source_set_digest(sources)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _base_args(self, output: Path, digest: str | None = None) -> list[str]:
        return [
            "--source-snapshots", str(self.manifest),
            "--expected-digests", str(self.digest_lock),
            "--query-count", "1",
            "--question", "What does the saved source report?",
            "--output-dir", str(output),
            "--draft", str(self.draft),
            "--claim-reviews", str(self.claim_reviews),
            "--task-id", "TASK-TOOLBOX-SNAPSHOT-TEST",
            "--episode-id", "EPISODE-01",
            "--source-set-id", "FROZEN-SOURCES-01",
            "--namespace", "research/fixture",
            "--authorization-scope", "offline-saved-captures-only",
            "--expected-source-set-digest", digest or self.source_set_digest,
        ]

    def test_digest_preview_verifies_capture_lock_without_creating_run_files(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = main([
                "--source-snapshots", str(self.manifest),
                "--expected-digests", str(self.digest_lock),
                "--query-count", "1",
                "--print-source-set-digest",
            ])
        receipt = json.loads(output.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(receipt["adapter_id"], "e37-source-snapshot-v1")
        self.assertEqual(receipt["canonical_source_set_sha256"], self.source_set_digest)
        self.assertEqual(receipt["network_requests"], 0)

    def test_run_is_offline_fixed_to_e37_and_preserves_hash_locked_capture(self) -> None:
        output_dir = self.root / "run-output"
        stdout = io.StringIO()
        with patch("urllib.request.urlopen", side_effect=AssertionError("network call attempted")), \
             patch.object(socket.socket, "connect", side_effect=AssertionError("socket connection attempted")), \
             contextlib.redirect_stdout(stdout):
            result = main(self._base_args(output_dir))
        summary = json.loads(stdout.getvalue())
        receipt = json.loads((output_dir / "receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(result, 0)
        self.assertEqual(summary["adapter_id"], "e37-source-snapshot-v1")
        self.assertEqual(receipt["context"]["adapter_id"], "e37-source-snapshot-v1")
        self.assertEqual(receipt["status"], "COMPLETED")
        self.assertEqual(receipt["counts"]["model_calls"], 0)
        self.assertEqual(receipt["counts"]["search_calls"], 0)
        self.assertEqual(receipt["counts"]["network_requests"], 0)
        self.assertEqual((output_dir / "raw/source-S1.txt").read_bytes(), self.capture_bytes)

    def test_bad_digest_and_repository_output_path_fail_before_writing(self) -> None:
        bad_output = self.root / "bad-run"
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main(self._base_args(bad_output, "0" * 64))
        self.assertFalse(bad_output.exists())

        inside_repo = REPO_ROOT / "ignition" / "tmp-source-snapshot-test"
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main(self._base_args(inside_repo))
        self.assertFalse(inside_repo.exists())

    def test_symlink_and_nonempty_output_directories_are_rejected(self) -> None:
        target = self.root / "symlink-target"
        target.mkdir()
        link = self.root / "run-link"
        link.symlink_to(target, target_is_directory=True)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main(self._base_args(link))
        self.assertEqual(list(target.iterdir()), [])

        nonempty = self.root / "nonempty-run"
        nonempty.mkdir()
        sentinel = nonempty / "keep.txt"
        sentinel.write_text("preserve existing output", encoding="utf-8")
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main(self._base_args(nonempty))
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve existing output")
        self.assertFalse((nonempty / "receipt.json").exists())

    def test_legacy_adapter_selection_is_not_exposed_by_this_tool(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main(self._base_args(self.root / "legacy-attempt") + ["--adapter", "legacy-openalex-v1"])
        self.assertFalse((self.root / "legacy-attempt").exists())


if __name__ == "__main__":
    unittest.main()
