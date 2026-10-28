from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from agent_runtime.pack_lifecycle import ADVISORY_OVERLAY_ROLE, PackLifecycleError, PackLifecycleManager, advisory_overlay_record
from agent_runtime.pack_registry import PackLoader, PackRegistry


ROOT = Path(__file__).resolve().parents[1]


class DurabilityPackLifecycleTests(unittest.TestCase):
    def test_four_registered_packs_complete_transactional_lifecycle(self) -> None:
        registry = PackRegistry.discover(ROOT / "packs")
        loader = PackLoader(registry)
        with tempfile.TemporaryDirectory(prefix="pack-lifecycle-") as temp:
            manager = PackLifecycleManager(Path(temp) / "pack-state.json")
            records = []
            for pack_id in registry.pack_ids:
                loaded = loader.load(pack_id)
                manager.discover(loaded.manifest)
                manager.stage(pack_id, loaded.manifest.version)
                records.append(manager.validate(pack_id, loaded.manifest.version, validation_receipt_ref=f"validation-{pack_id}"))
                activated = manager.activate(pack_id, loaded.manifest.version)
                self.assertEqual(activated.state, "ACTIVATED")
            self.assertEqual(len(records), 4)
            self.assertEqual(len(manager.receipts()), 16)

    def test_active_run_stays_pinned_when_new_version_activates(self) -> None:
        registry = PackRegistry.discover(ROOT / "packs")
        manifest = registry.get("knowledge.r0")
        with tempfile.TemporaryDirectory(prefix="pack-lifecycle-") as temp:
            manager = PackLifecycleManager(Path(temp) / "pack-state.json")
            manager.discover(manifest)
            manager.stage(manifest.pack_id, manifest.version)
            manager.validate(manifest.pack_id, manifest.version, validation_receipt_ref="valid-v1")
            manager.activate(manifest.pack_id, manifest.version)
            pin = manager.pin_run("run-v1", manifest.pack_id)
            newer = type(manifest)(**{**manifest.to_dict(), "version": "1.1.0"})
            manager.discover(newer)
            manager.stage(newer.pack_id, newer.version)
            manager.validate(newer.pack_id, newer.version, validation_receipt_ref="valid-v2")
            manager.activate(newer.pack_id, newer.version)
            self.assertEqual(pin.version, "1.0.0")
            self.assertEqual(manager.active_version(manifest.pack_id), "1.1.0")
            self.assertEqual(manager.get(manifest.pack_id, "1.0.0").state, "DRAINING")

    def test_failed_activation_rolls_back_and_quarantine_is_retained(self) -> None:
        registry = PackRegistry.discover(ROOT / "packs")
        manifest = registry.get("research.reos-light")
        with tempfile.TemporaryDirectory(prefix="pack-lifecycle-") as temp:
            manager = PackLifecycleManager(Path(temp) / "pack-state.json")
            manager.discover(manifest); manager.stage(manifest.pack_id, manifest.version); manager.validate(manifest.pack_id, manifest.version, validation_receipt_ref="valid")
            self.assertEqual(manager.activate(manifest.pack_id, manifest.version, fail_activation=True).state, "ROLLED_BACK")
            manager.quarantine(manifest.pack_id, manifest.version, reason="fixture failed activation")
            self.assertEqual(manager.get(manifest.pack_id, manifest.version).state, "QUARANTINED")

    def test_advisory_overlay_cannot_become_domain_truth_pack(self) -> None:
        overlay = advisory_overlay_record(version="structural-surface-r0", manifest_digest="c" * 64)
        self.assertEqual(overlay.role, ADVISORY_OVERLAY_ROLE)
        self.assertEqual(overlay.authority_ceiling, "DECLARED_PACK_SCOPE_ONLY")
        with self.assertRaises(PackLifecycleError):
            advisory_overlay_record(version="structural-surface-r0", manifest_digest="not-a-digest")


if __name__ == "__main__":
    unittest.main()
