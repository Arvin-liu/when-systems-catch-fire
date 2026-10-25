from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


IGNITION_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = IGNITION_ROOT.parent
TOOL_PATH = IGNITION_ROOT / "tools/toolbox_read_current_asset_card.py"
SPEC = importlib.util.spec_from_file_location("toolbox_read_current_asset_card", TOOL_PATH)
TOOL = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TOOL)


class ReadCurrentAssetCardTests(unittest.TestCase):
    def test_reads_exact_function_asset_and_verifies_record_and_authority_hashes(self) -> None:
        result = TOOL.build_record_result("A0")
        self.assertEqual(result["result_status"], "CURRENT_CANONICAL_RECORD_READ")
        self.assertEqual(result["record_kind"], "FUNCTION_ASSET")
        self.assertEqual(result["record"]["canonical_id"], "A0")
        self.assertTrue(result["record_sha256_verified"])
        self.assertEqual(result["record_sha256"], result["record"]["record_sha256"])
        self.assertEqual(
            {row["path"] for row in result["source_refs"]},
            set(TOOL.AUTHORITY_PATHS.values()),
        )

    def test_reads_exact_nonfunction_claim_without_scientific_upgrade(self) -> None:
        result = TOOL.build_record_result("CLAIM-T2")
        self.assertEqual(result["record_kind"], "NONFUNCTION_CLAIM")
        self.assertEqual(result["record"]["canonical_id"], "CLAIM-T2")
        self.assertIn("does not establish truth, proof", result["claim_ceiling"])

    def test_aliases_paths_and_unknown_ids_are_not_accepted(self) -> None:
        for value in ("A0 ", "../outside", "known title", "UNKNOWN-CURRENT-ID"):
            with self.subTest(canonical_id=value), self.assertRaises(TOOL.CurrentAssetReadError):
                TOOL.build_record_result(value)

    def test_duplicate_ids_across_authorities_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            card = self._record("DUP", "Function card")
            claim = self._record("DUP", "Nonfunction claim")
            self._write_authorities(root, [card], [claim])
            with self.assertRaisesRegex(TOOL.CurrentAssetReadError, "duplicated"):
                TOOL.build_record_result("DUP", root)

    def test_corrupt_record_hash_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            card = self._record("A1", "Function card")
            card["record_sha256"] = "0" * 64
            self._write_authorities(root, [card], [])
            with self.assertRaisesRegex(TOOL.CurrentAssetReadError, "does not match"):
                TOOL.build_record_result("A1", root)

    def test_symlinked_authority_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "outside.jsonl").write_text("{}\n", encoding="utf-8")
            target = root / "ignition/data/foundation/function-assets/identity-cards.jsonl"
            target.parent.mkdir(parents=True)
            target.symlink_to(root / "outside.jsonl")
            claim = root / "ignition/data/foundation/nonfunction-claims/claim-registry.jsonl"
            claim.parent.mkdir(parents=True)
            claim.write_text("", encoding="utf-8")
            with self.assertRaisesRegex(TOOL.CurrentAssetReadError, "symlink"):
                TOOL.build_record_result("A1", root)

    def test_cli_requires_exact_stdin_shape_and_emits_no_partial_result(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input='{"canonical_id":"UNKNOWN-CURRENT-ID"}',
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, "")
        self.assertIn("CURRENT_FOUNDATION_RECORD_NOT_AVAILABLE", completed.stderr)

        duplicate_key = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input='{"canonical_id":"A0","canonical_id":"A1"}',
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(duplicate_key.returncode, 2)
        self.assertEqual(duplicate_key.stdout, "")
        self.assertIn("duplicate JSON input key", duplicate_key.stderr)

    @staticmethod
    def _record(canonical_id: str, title: str) -> dict[str, object]:
        record: dict[str, object] = {"canonical_id": canonical_id, "title": title}
        encoded = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        record["record_sha256"] = hashlib.sha256(encoded).hexdigest()
        return record

    @staticmethod
    def _write_authorities(root: Path, cards: list[dict[str, object]], claims: list[dict[str, object]]) -> None:
        paths = {
            "ignition/data/foundation/function-assets/identity-cards.jsonl": cards,
            "ignition/data/foundation/nonfunction-claims/claim-registry.jsonl": claims,
        }
        for relative, rows in paths.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
