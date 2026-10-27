from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from agent_runtime.dr_bundle import DR_BUNDLE_EPOCH, DRBundleError, DRBundleIntegrityError, REQUIRED_CHUNKS, RecoveryBundleBuilder, RecoveryBundleVerifier


class DurabilityDRBundleTests(unittest.TestCase):
    def chunks(self, namespace: str = "namespace-a") -> dict[str, dict[str, object]]:
        return {name: {"namespace_id": namespace, "chunk": name, "digest_ref": f"digest-{name}"} for name in REQUIRED_CHUNKS if name != "soft-governance"} | {
            "soft-governance": {"namespace_id": namespace, "status": "ADVISORY_ONLY", "authority_effects": ["NONE"], "claim_ceiling": "Advisory only; no truth or authority."},
        }

    def test_build_and_restore_in_fresh_directory_with_canonical_digest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="dr-bundle-") as temp:
            target = Path(temp) / "bundle"
            result = RecoveryBundleBuilder(target).build(bundle_id="bundle-a", namespace_id="namespace-a", schema_epoch=DR_BUNDLE_EPOCH, source_ledger_head_hash="a" * 64, chunks=self.chunks(), unresolved_reconciliation_refs=("dispatch-a",), operator_checkpoint="checkpoint-a", created_at=1)
            restored = RecoveryBundleVerifier.restore(target, namespace_id="namespace-a", schema_epoch=DR_BUNDLE_EPOCH, expected_source_ledger_head_hash="a" * 64)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(restored["canonical_digest"], result["canonical_digest"])
            self.assertEqual(restored["chunk_count"], 12)
            self.assertEqual(restored["external_reexecution"], "FORBIDDEN")

    def test_missing_corrupt_wrong_namespace_stale_and_wrong_epoch_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="dr-bundle-") as temp:
            target = Path(temp) / "bundle"
            RecoveryBundleBuilder(target).build(bundle_id="bundle-a", namespace_id="namespace-a", schema_epoch=DR_BUNDLE_EPOCH, source_ledger_head_hash="a" * 64, chunks=self.chunks(), created_at=1)
            (target / "chunks" / "accounting.json").unlink()
            with self.assertRaises(DRBundleIntegrityError):
                RecoveryBundleVerifier.verify(target, namespace_id="namespace-a", schema_epoch=DR_BUNDLE_EPOCH, expected_source_ledger_head_hash="a" * 64)

            fresh = Path(temp) / "fresh"
            RecoveryBundleBuilder(fresh).build(bundle_id="bundle-b", namespace_id="namespace-a", schema_epoch=DR_BUNDLE_EPOCH, source_ledger_head_hash="a" * 64, chunks=self.chunks(), created_at=1)
            accounting = fresh / "chunks" / "accounting.json"
            accounting.write_text(accounting.read_text(encoding="utf-8").replace("accounting", "tampered"), encoding="utf-8")
            with self.assertRaises(DRBundleIntegrityError):
                RecoveryBundleVerifier.verify(fresh, namespace_id="namespace-a", schema_epoch=DR_BUNDLE_EPOCH, expected_source_ledger_head_hash="a" * 64)
            with self.assertRaises(DRBundleIntegrityError):
                RecoveryBundleVerifier.verify(fresh, namespace_id="namespace-b", schema_epoch=DR_BUNDLE_EPOCH, expected_source_ledger_head_hash="a" * 64)
            with self.assertRaises(DRBundleIntegrityError):
                RecoveryBundleVerifier.verify(fresh, namespace_id="namespace-a", schema_epoch=DR_BUNDLE_EPOCH, expected_source_ledger_head_hash="b" * 64)
            with self.assertRaises(DRBundleIntegrityError):
                RecoveryBundleVerifier.verify(fresh, namespace_id="namespace-a", schema_epoch="other-epoch", expected_source_ledger_head_hash="a" * 64)

    def test_soft_to_hard_authority_injection_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="dr-bundle-") as temp:
            bad = self.chunks()
            bad["soft-governance"]["authorization"] = "GRANTED"
            with self.assertRaises(DRBundleError):
                RecoveryBundleBuilder(Path(temp) / "bundle").build(bundle_id="bundle-bad", namespace_id="namespace-a", schema_epoch=DR_BUNDLE_EPOCH, source_ledger_head_hash="a" * 64, chunks=bad, created_at=1)


if __name__ == "__main__":
    unittest.main()
