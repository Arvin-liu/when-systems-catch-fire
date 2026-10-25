from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


IGNITION_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = IGNITION_ROOT.parent
TOOL_PATH = IGNITION_ROOT / "tools/toolbox_pack_registry_inspector.py"
SPEC = importlib.util.spec_from_file_location("toolbox_pack_registry_inspector", TOOL_PATH)
TOOL = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TOOL)


class ToolboxPackRegistryInspectorTests(unittest.TestCase):
    def test_lists_four_local_packs_and_declared_routes_with_source_hashes(self) -> None:
        result = TOOL.build_inspection("list")
        self.assertEqual(result["result_status"], "DECLARED_PACK_METADATA_LISTED")
        self.assertEqual(result["source_status"], "LOCAL_PACK_MANIFESTS_ONLY")
        self.assertEqual(result["pack_count"], 4)
        self.assertEqual(result["declared_route_count"], 10)
        self.assertEqual(
            [row["manifest"]["pack_id"] for row in result["packs"]],
            ["knowledge.r0", "maintenance.repository", "research.reos-light", "writing.zhiyuan"],
        )
        for pack in result["packs"]:
            source = REPO_ROOT / pack["manifest_source"]["path"]
            self.assertEqual(pack["manifest_source"]["sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertIn("no Pack module is loaded", result["claim_ceiling"])

    def test_show_returns_one_pack_routes_without_loading_or_unloading(self) -> None:
        from agent_runtime.pack_registry import PackLoader

        with patch.object(PackLoader, "load", side_effect=AssertionError("Pack must not be loaded")), patch.object(
            PackLoader, "unload", side_effect=AssertionError("Pack must not be unloaded")
        ):
            result = TOOL.build_inspection("show", "research.reos-light")
        self.assertEqual(result["pack_count"], 1)
        self.assertEqual(result["packs"][0]["manifest"]["pack_id"], "research.reos-light")
        self.assertEqual(
            {row["capability"] for row in result["packs"][0]["declared_routes"]},
            {"research.coordinate_obligations", "research.validate_reos_light"},
        )

    def test_traversal_and_symlinked_pack_directories_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(TOOL.PackInspectionError, "traversal"):
                TOOL._safe_repo_path(root, "ignition/../outside.json")

            packs = root / "ignition/packs"
            packs.mkdir(parents=True)
            outside = root / "outside"
            outside.mkdir()
            (outside / "manifest.json").write_text("{}", encoding="utf-8")
            (packs / "linked").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(TOOL.PackInspectionError, "symlink"):
                TOOL._manifest_snapshot(root)

    def test_cli_list_is_json_and_unknown_pack_has_no_partial_output(self) -> None:
        listed = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "list"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(listed.returncode, 0, listed.stderr)
        self.assertEqual(json.loads(listed.stdout)["pack_count"], 4)

        unknown = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "show", "pack.does-not-exist"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(unknown.returncode, 2)
        self.assertEqual(unknown.stdout, "")
        self.assertIn("PACK_METADATA_NOT_AVAILABLE", unknown.stderr)


if __name__ == "__main__":
    unittest.main()
