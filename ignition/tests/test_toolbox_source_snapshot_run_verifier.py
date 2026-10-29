from __future__ import annotations

import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT))
sys.path.insert(0, str(IGNITION_ROOT / "tools"))

from ignition.research_workflow import slot  # noqa: E402
import toolbox_verify_handoff_artifact_files as handoff_verifier  # noqa: E402
from tools.toolbox_verify_offline_source_snapshot_run import REPO_ROOT, evaluate, main  # noqa: E402


class OfflineSourceSnapshotRunVerifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="ignition-e37-receipt-verifier-")
        self.root = Path(self.temp.name).resolve()
        self.capture = b"Saved source bytes for a bounded receipt check.\n"
        (self.root / "capture.txt").write_bytes(self.capture)
        manifest_row = {
            "title": "Captured source",
            "source_url": "https://example.org/capture",
            "capture_path": "capture.txt",
            "capture_kind": "web_run_observation",
            "captured_at_utc": "2026-10-17T00:00:00Z",
            "locator": "Fixture paragraph 1",
            "query_ids": ["Q1"],
        }
        self.manifest = self.root / "manifest.jsonl"
        self.manifest.write_text(json.dumps(manifest_row) + "\n", encoding="utf-8")
        self.digest_lock = self.root / "expected-digests.json"
        self.digest_lock.write_text(json.dumps({"S1": hashlib.sha256(self.capture).hexdigest()}), encoding="utf-8")
        self.draft = self.root / "draft.md"
        self.draft.write_text("The saved source contains a bounded claim [S1].\n", encoding="utf-8")
        self.claims = self.root / "claim-reviews.jsonl"
        self.claims.write_text(json.dumps({
            "claim_id": "C1",
            "claim_text": "The saved source contains a bounded claim.",
            "source_id": "S1",
            "review_judgment": "SUPPORTS",
            "reviewer_type": "HUMAN",
            "reviewer": "fixture-reviewer",
            "reviewed_at_utc": "2026-10-17T00:00:00Z",
            "evidence_field": "captured_text",
            "evidence_quote": self.capture.decode().strip(),
        }) + "\n", encoding="utf-8")
        snapshots, _, _, _, _ = slot._snapshot_sources(self.manifest, self.digest_lock, 1)
        self.source_set_digest = slot._canonical_source_set_digest(snapshots)
        self.run_dir = self.root / "run-output"
        slot.run_binding(
            adapter_id="e37-source-snapshot-v1",
            question="What does the saved capture contain?",
            output_dir=self.run_dir,
            draft_path=self.draft,
            claim_review_path=self.claims,
            task_id="TASK-E37-VERIFY-01",
            episode_id="EPISODE-E37-01",
            source_set_id="SAVED-SOURCE-SET-01",
            namespace="research/fixture",
            authorization_scope="offline-saved-captures-only",
            implementation_commit="a" * 40,
            expected_source_set_digest=self.source_set_digest,
            source_snapshots_path=self.manifest,
            expected_digests_path=self.digest_lock,
            query_count=1,
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _run_cli(self) -> tuple[int, dict]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["--run-dir", str(self.run_dir)])
        return code, json.loads(output.getvalue())

    def test_real_e37_run_verifies_all_receipted_bytes_without_writing(self) -> None:
        before = {
            path.relative_to(self.run_dir).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in self.run_dir.rglob("*") if path.is_file()
        }
        code, result = self._run_cli()
        after = {
            path.relative_to(self.run_dir).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in self.run_dir.rglob("*") if path.is_file()
        }

        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "ALL_ARTIFACT_DIGESTS_MATCH")
        self.assertEqual(result["receipt_authenticity"], "NOT_ESTABLISHED_UNKEYED_DIGEST")
        self.assertFalse(result["execution_authorized"])
        self.assertEqual(result["network_requests"], 0)
        self.assertEqual(before, after)

    def test_existing_federation_verifier_rejects_the_e37_receipt_contract(self) -> None:
        receipt = json.loads((self.run_dir / "receipt.json").read_text(encoding="utf-8"))
        result, code = handoff_verifier.evaluate(
            {"schema_version": "handoff-artifact-byte-check-r0", "source_receipt": receipt},
            self.run_dir,
        )

        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "INPUT_INVALID")
        self.assertIn("SOURCE_RECEIPT_INVALID", {item["code"] for item in result["findings"]})

    def test_tampered_artifact_fails_closed(self) -> None:
        source = self.run_dir / "raw/source-S1.txt"
        original = source.read_bytes()
        source.write_bytes(b"x" * len(original))
        code, result = self._run_cli()

        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "ARTIFACT_BYTES_MISMATCH")
        self.assertIn("DIGEST_MISMATCH", {row["status"] for row in result["artifacts"]})

    def test_unlisted_file_fails_exact_file_set_check(self) -> None:
        (self.run_dir / "unlisted.txt").write_text("extra", encoding="utf-8")
        code, result = self._run_cli()

        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "ARTIFACT_SET_MISMATCH")
        self.assertEqual(result["unlisted_paths"], ["unlisted.txt"])

    def test_missing_receipted_file_fails_exact_file_set_check(self) -> None:
        (self.run_dir / "raw/source-S1.txt").unlink()
        code, result = self._run_cli()

        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "ARTIFACT_SET_MISMATCH")
        self.assertEqual(result["missing_paths"], ["raw/source-S1.txt"])

    def test_symlink_in_run_tree_is_rejected_without_following_it(self) -> None:
        target = self.root / "outside-secret.txt"
        target.write_text("not an E37 artifact", encoding="utf-8")
        artifact = self.run_dir / "raw/source-S1.txt"
        artifact.unlink()
        artifact.symlink_to(target)
        code, result = self._run_cli()

        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "RUN_TREE_UNSAFE_ENTRY")
        self.assertEqual(target.read_text(encoding="utf-8"), "not an E37 artifact")

    def test_symlink_root_and_repository_root_are_rejected(self) -> None:
        link = self.root / "run-link"
        link.symlink_to(self.run_dir, target_is_directory=True)
        linked, linked_code = evaluate(link)
        repository, repository_code = evaluate(REPO_ROOT)

        self.assertEqual(linked_code, 2)
        self.assertEqual(linked["status"], "RUN_ROOT_SYMLINK_OR_NOT_DIRECTORY")
        self.assertEqual(repository_code, 2)
        self.assertEqual(repository["status"], "RUN_ROOT_INSIDE_OR_CONTAINS_REPOSITORY")

    def test_receipt_path_traversal_and_duplicate_keys_are_rejected(self) -> None:
        receipt_path = self.run_dir / "receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["artifacts"][0]["path"] = "../outside.txt"
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        traversal, traversal_code = evaluate(self.run_dir)
        self.assertEqual(traversal_code, 2)
        self.assertEqual(traversal["status"], "ARTIFACT_PATH_UNSAFE")

        receipt_path.write_text('{"schema":"one","schema":"two"}', encoding="utf-8")
        duplicate, duplicate_code = evaluate(self.run_dir)
        self.assertEqual(duplicate_code, 2)
        self.assertEqual(duplicate["status"], "RECEIPT_DUPLICATE_JSON_KEY")


if __name__ == "__main__":
    unittest.main()
