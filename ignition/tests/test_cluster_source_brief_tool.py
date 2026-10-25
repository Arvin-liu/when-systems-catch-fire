from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


IGNITION_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = IGNITION_ROOT / "tools/extract_cluster_source_brief.py"
SPEC = importlib.util.spec_from_file_location("cluster_source_brief_tool", TOOL_PATH)
TOOL = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TOOL)


class ClusterSourceBriefTests(unittest.TestCase):
    def _fixture_root(self, root: Path) -> None:
        cards = root / "KNOWLEDGE/cards"
        cards.mkdir(parents=True)
        (cards / "part-01.md").write_text(
            '<a id="asset-D1"></a>\n## Test asset\n'
            '- **身份/来源：** `FUNCTION_ASSET` · `D1`\n'
            '- **当前状态：** `KEEP_AS_STRUCTURAL_METAPHOR`\n'
            '- **主题：** 测试\n'
            '- **来源与证据：** `source:test`\n',
            encoding="utf-8",
        )
        parser_dir = root / "tools"
        parser_dir.mkdir()
        shutil.copyfile(IGNITION_ROOT / "tools/build_corpus_relation_graph.py", parser_dir / "build_corpus_relation_graph.py")
        cluster_dir = root / "analysis/corpus-relation"
        cluster_dir.mkdir(parents=True)
        (cluster_dir / "article_cluster_candidates.json").write_text(json.dumps({
            "cluster_count": 1,
            "clusters": [{
                "id": "C001", "disposition": "REFERENCE_ONLY",
                "proposed_central_question": "Question?", "dominant_topic": "TEST",
                "dominant_ratio": 1.0, "distinct_domains": 1, "size": 1,
                "edge_types": ["related"],
                "members": [{"id": "d1", "title": "Test asset", "asset_type": "FUNCTION_ASSET", "status": "KEEP_AS_STRUCTURAL_METAPHOR", "topics": ["TEST"]}],
            }],
        }, ensure_ascii=False), encoding="utf-8")

    def test_render_is_deterministic_and_does_not_write_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._fixture_root(root)
            first = TOOL.render_briefs(["C001"], root=str(root))
            second = TOOL.render_briefs(["C001"], root=str(root))
            self.assertEqual(first, second)
            self.assertIn("源资产简报 C001", first)
            self.assertIn("Test asset", first)
            self.assertIn("KEEP_AS_STRUCTURAL_METAPHOR", first)
            self.assertFalse((root / "analysis/corpus-relation/cluster_source_briefs").exists())

    def test_unknown_cluster_fails_closed_without_partial_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._fixture_root(root)
            with self.assertRaisesRegex(ValueError, "unknown cluster ID"):
                TOOL.render_briefs(["C001", "C999"], root=str(root))
            self.assertFalse((root / "analysis/corpus-relation/cluster_source_briefs").exists())

    def test_receipt_pins_input_sources_and_exact_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._fixture_root(root)
            receipt = TOOL.render_receipt(["C001"], root=str(root))
            self.assertEqual(receipt["schema_version"], "cluster-source-brief-output-r0")
            self.assertEqual(receipt["source_refs"]["knowledge_cards"]["file_count"], 1)
            brief = receipt["briefs"][0]
            self.assertEqual(brief["cluster_id"], "C001")
            self.assertEqual(brief["output_sha256"], hashlib.sha256(brief["markdown"].encode("utf-8")).hexdigest())
            parser_bytes = (root / "tools/build_corpus_relation_graph.py").read_bytes()
            expected_parser_blob = hashlib.sha1(b"blob " + str(len(parser_bytes)).encode("ascii") + b"\0" + parser_bytes).hexdigest()
            self.assertEqual(receipt["source_refs"]["parser"]["git_blob_sha1"], expected_parser_blob)
            self.assertEqual(receipt["receipt_sha256"], TOOL.render_receipt(["C001"], root=str(root))["receipt_sha256"])
            self.assertFalse((root / "analysis/corpus-relation/cluster_source_briefs").exists())

    def test_duplicate_or_empty_cluster_input_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least one"):
            TOOL.render_briefs([])
        with self.assertRaisesRegex(ValueError, "unique"):
            TOOL.render_briefs(["C000", "C000"])

    def test_symlinked_input_is_rejected_before_reading(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._fixture_root(root)
            parser = root / "tools/build_corpus_relation_graph.py"
            parser.unlink()
            marker = root / "parser-imported-before-validation"
            poison = root.parent / "poison-parser.py"
            poison.write_text("open(%r, 'w').write('executed')\n" % str(marker), encoding="utf-8")
            parser.symlink_to(poison)
            with self.assertRaisesRegex(ValueError, "symlink"):
                TOOL.render_briefs(["C001"], root=str(root))
            self.assertFalse(marker.exists())

    def test_read_only_entrypoint_prints_receipt_without_creating_repository_output(self) -> None:
        output_dir = IGNITION_ROOT / "analysis/corpus-relation/cluster_source_briefs"
        def snapshot(path: Path):
            if not path.exists():
                return None
            rows = []
            for item in sorted(path.rglob("*")):
                relative = item.relative_to(path).as_posix()
                if item.is_symlink():
                    rows.append((relative, "SYMLINK", str(item.readlink())))
                elif item.is_file():
                    rows.append((relative, hashlib.sha256(item.read_bytes()).hexdigest()))
                else:
                    rows.append((relative, "DIRECTORY"))
            return rows

        before = snapshot(output_dir)
        result = subprocess.run(
            [sys.executable, "-B", str(IGNITION_ROOT / "tools/toolbox_cluster_source_brief.py"), "C000"],
            cwd=IGNITION_ROOT.parent,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["briefs"][0]["cluster_id"], "C000")
        self.assertTrue(receipt["receipt_sha256"])
        self.assertEqual(snapshot(output_dir), before)


if __name__ == "__main__":
    unittest.main()
