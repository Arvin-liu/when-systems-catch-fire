from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


IGNITION_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = IGNITION_ROOT.parent
TOOL_PATH = IGNITION_ROOT / "tools/toolbox_batch_resolve_current_assets.py"
SPEC = importlib.util.spec_from_file_location("toolbox_batch_resolver", TOOL_PATH)
TOOL = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TOOL)


class BatchCanonicalResolutionToolTests(unittest.TestCase):
    def test_ordered_batch_resolves_exact_current_refs_and_preserves_unresolved_refs(self) -> None:
        references = [
            "D127",
            "D127 乘法归零律",
            "CLAIM-T2",
            "D127 乘法清零律",
            "统一函数总表/0012-T2-乘法归零律.md",
        ]
        result = TOOL.build_batch_result(references)

        self.assertEqual(result["result_status"], "BATCH_RESOLUTION_PROCESSED")
        self.assertEqual(result["reference_count"], len(references))
        self.assertEqual(result["summary"], {"resolved": 3, "unresolved": 2, "ambiguous": 0})
        self.assertEqual([row["submitted_reference"] for row in result["results"]], references)
        self.assertEqual(result["results"][0]["resolution"]["canonical_id"], "D127")
        self.assertEqual(result["results"][1]["resolution"]["canonical_id"], "T2")
        self.assertEqual(result["results"][2]["resolution"]["canonical_id"], "CLAIM-T2")
        self.assertEqual(result["results"][3]["resolution"]["resolution_status"], TOOL.resolver.UNRESOLVED)
        self.assertEqual(result["results"][4]["resolution"]["resolution_status"], TOOL.resolver.UNRESOLVED)
        self.assertFalse(result["results"][3]["resolution"]["memory_or_fuzzy_resolution_used"])

    def test_receipt_binds_resolver_and_each_exact_authority_snapshot(self) -> None:
        result = TOOL.build_batch_result(["D127"])
        source_by_path = {row["path"]: row for row in result["source_refs"]}
        expected_paths = {TOOL.RESOLVER_SOURCE, *TOOL.AUTHORITY_PATHS.values()}
        self.assertEqual(set(source_by_path), expected_paths)
        for relative_path in expected_paths:
            expected = hashlib.sha256((REPO_ROOT / relative_path).read_bytes()).hexdigest()
            self.assertEqual(source_by_path[relative_path]["sha256"], expected)
        receipt = result.pop("receipt_sha256")
        canonical = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.assertEqual(receipt, hashlib.sha256(canonical).hexdigest())

    def test_path_traversal_and_symlinked_authorities_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(TOOL.BatchResolutionError, "traversal"):
                TOOL._read_repo_file(root, "ignition/../outside.jsonl")

            relative = TOOL.AUTHORITY_PATHS["function_identity_cards"]
            target = root / "outside.jsonl"
            target.write_text("{}\n", encoding="utf-8")
            link = root / relative
            link.parent.mkdir(parents=True)
            link.symlink_to(target)
            with self.assertRaisesRegex(TOOL.BatchResolutionError, "symlink"):
                TOOL._read_repo_file(root, relative)

    def test_invalid_batch_fails_before_partial_stdout(self) -> None:
        for payload in ("{}", '{"references":[]}', '{"references":["D127",""]}'):
            output = io.StringIO()
            errors = io.StringIO()
            with (
                patch.object(TOOL.sys, "stdin", io.StringIO(payload)),
                patch.object(TOOL.sys, "stdout", output),
                patch.object(TOOL.sys, "stderr", errors),
            ):
                status = TOOL.main(["--stdin"])
            self.assertEqual(status, 2)
            self.assertEqual(output.getvalue(), "")
            self.assertIn("BATCH_CANONICAL_RESOLUTION_NOT_AVAILABLE", errors.getvalue())

    def test_cli_emits_json_receipt(self) -> None:
        payload = json.dumps({"references": ["D127", "D127 乘法清零律"]}, ensure_ascii=False)
        process = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input=payload,
            text=True,
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        document = json.loads(process.stdout)
        self.assertEqual(document["summary"], {"resolved": 1, "unresolved": 1, "ambiguous": 0})
        self.assertEqual([row["input_index"] for row in document["results"]], [0, 1])
        self.assertEqual(len(document["receipt_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
