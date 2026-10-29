from __future__ import annotations

import unittest

from life_integrity_r5a import manifest
from life_integrity_r5a.life_integrity import LifeIntegrityGate


class R5ALifeIntegrityRouteConsumerTest(unittest.TestCase):
    def test_candidate_manifest_and_gate_remain_non_activating(self) -> None:
        self.assertTrue(manifest.manifest_flags_consistent())
        self.assertEqual(
            manifest.CANDIDATE_MANIFEST["activation_status"], "CANDIDATE_ONLY"
        )
        self.assertFalse(manifest.CANDIDATE_MANIFEST["external_acceptance_claimed"])
        self.assertFalse(LifeIntegrityGate().activated)


if __name__ == "__main__":
    unittest.main()
