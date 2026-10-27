from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

from agent_runtime.cli import main as cli_main
from agent_runtime.pack_registry import PackBus, PackLoader, PackRegistry, PackRegistryError, PackManifest


ROOT = Path(__file__).resolve().parents[1]
PACKS = ROOT / "packs"


class PackRegistryR1Tests(unittest.TestCase):
    def test_discovers_validates_and_loads_registered_packs(self) -> None:
        registry = PackRegistry.discover(PACKS)
        self.assertEqual(registry.pack_ids, ("knowledge.r0", "maintenance.repository", "research.reos-light", "writing.zhiyuan"))
        report = registry.validate()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["pack_count"], 4)
        loader = PackLoader(registry)
        loaded = loader.load_all()
        self.assertEqual(tuple(item.manifest.pack_id for item in loaded), registry.pack_ids)
        self.assertTrue(all(item.health == "PASS" for item in loaded))

    def test_bus_routes_only_loaded_declared_capabilities_and_never_executes_hooks(self) -> None:
        registry = PackRegistry.discover(PACKS)
        loader = PackLoader(registry)
        before = set(sys.modules)
        loader.load_all()
        self.assertEqual(before, set(sys.modules))
        bus = PackBus(registry, loader)
        route = bus.route("maintenance.inspect_repository")
        self.assertEqual(route.pack_id, "maintenance.repository")
        proposal = bus.propose("research.coordinate_obligations", {"run_id": "step02", "kind": "offline"})
        self.assertEqual(proposal["status"], "ROUTED_PROPOSAL")
        self.assertEqual(proposal["execution"], "NOT_PERFORMED_BY_PACK_BUS")
        with self.assertRaises(PackRegistryError):
            bus.route("unknown.capability")

    def test_unload_respects_active_run_boundary(self) -> None:
        registry = PackRegistry.discover(PACKS)
        loader = PackLoader(registry)
        loader.load("maintenance.repository")
        with self.assertRaises(PackRegistryError):
            loader.unload("maintenance.repository", active_pack_ids=("maintenance.repository",))
        result = loader.unload("maintenance.repository")
        self.assertEqual(result["status"], "UNLOADED")
        self.assertFalse(loader.is_loaded("maintenance.repository"))

    def test_manifest_rejects_authority_or_network_expansion(self) -> None:
        raw = json.loads((PACKS / "knowledge/manifest.json").read_text(encoding="utf-8"))
        bad_authority = copy.deepcopy(raw)
        bad_authority["prohibited_authority_upgrades"].remove("kernel_definition")
        with self.assertRaises(PackRegistryError):
            PackManifest.from_dict(bad_authority)
        bad_network = copy.deepcopy(raw)
        bad_network["permissions_requested"]["network"] = True
        manifest = PackManifest.from_dict(bad_network)
        errors = manifest.validate_root(ROOT)
        self.assertIn("network permission is unavailable in offline Pack Bus R1", errors)

    def test_cli_packs_list_show_and_validate(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(cli_main(["packs", "list", "--packs-root", str(PACKS), "--json"]), 0)
        listed = json.loads(output.getvalue())
        self.assertEqual([item["pack_id"] for item in listed], ["knowledge.r0", "maintenance.repository", "research.reos-light", "writing.zhiyuan"])

        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(cli_main(["packs", "show", "--packs-root", str(PACKS), "--pack-id", "writing.zhiyuan", "--json"]), 0)
        shown = json.loads(output.getvalue())
        self.assertEqual(shown["pack"]["pack_id"], "writing.zhiyuan")

        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(cli_main(["packs", "validate", "--packs-root", str(PACKS), "--json"]), 0)
        self.assertEqual(json.loads(output.getvalue())["status"], "PASS")

    def test_discovery_does_not_accept_duplicate_or_missing_manifests(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pack-registry-") as temp:
            root = Path(temp) / "packs"
            root.mkdir()
            (root / "one").mkdir()
            (root / "two").mkdir()
            raw = json.loads((PACKS / "maintenance/manifest.json").read_text(encoding="utf-8"))
            (root / "one/manifest.json").write_text(json.dumps(raw), encoding="utf-8")
            (root / "two/manifest.json").write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaises(PackRegistryError):
                PackRegistry.discover(root)


if __name__ == "__main__":
    unittest.main()
