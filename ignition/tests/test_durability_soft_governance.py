from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from agent_runtime.durability import CanonicalSnapshotStore
from agent_runtime.event_ledger import EventLedger
from agent_runtime.soft_governance_durability import SoftGovernanceDurabilityError, migrate_soft_state, validate_soft_state


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/operations/durability/soft-governance-durability-r1.json"


class DurabilitySoftGovernanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.record = json.loads(DATA.read_text(encoding="utf-8"))

    def test_baseline_is_advisory_and_migrates_without_promotion(self) -> None:
        self.assertEqual(validate_soft_state(self.record), [])
        migrated = migrate_soft_state(self.record, target_format_epoch=2, migration_id="soft-migration-1")
        self.assertEqual(migrated["status"], "CANDIDATE_ESI_SIGNAL")
        self.assertEqual(migrated["authority_effects"]["permission_delta"], "NONE")
        downgraded = migrate_soft_state(migrated, target_format_epoch=1, migration_id="soft-migration-2")
        self.assertEqual(downgraded["status"], "CANDIDATE_ESI_SIGNAL")

    def test_withdrawal_replays_as_withdrawn_and_stays_advisory(self) -> None:
        withdrawn = copy.deepcopy(self.record)
        withdrawn["status"] = "WITHDRAWN"
        withdrawn["withdrawal_reason"] = "bounded fixture withdrawal"
        migrated = migrate_soft_state(withdrawn, target_format_epoch=2, migration_id="soft-withdrawal")
        self.assertEqual(migrated["status"], "WITHDRAWN")
        self.assertEqual(migrated["authority_effects"]["truth_status_delta"], "NONE")

    def test_hard_authority_injection_is_rejected(self) -> None:
        attack = copy.deepcopy(self.record)
        attack["authority_effects"]["permission_delta"] = "GRANTED"
        self.assertTrue(validate_soft_state(attack))
        attack = copy.deepcopy(self.record)
        attack["requested_effect"] = "authorize_from_soft_context"
        with self.assertRaises(SoftGovernanceDurabilityError):
            migrate_soft_state(attack, target_format_epoch=2, migration_id="soft-attack")

    def test_snapshot_pointer_does_not_change_soft_status(self) -> None:
        with tempfile.TemporaryDirectory(prefix="soft-durability-") as temp:
            root = Path(temp)
            ledger = EventLedger(root / "events.jsonl")
            ledger.append_event(aggregate_id="soft-state", event_type="RUN_STARTED", payload={"status": "ADVISORY_ONLY"}, idempotency_key="soft-ledger-1")
            store = CanonicalSnapshotStore(root / "snapshot.json")
            snapshot = store.create(ledger, snapshot_id="soft-snapshot", advisory_soft_governance_versions=("structural-surface-r0:ADVISORY_ONLY",))
            store.write(snapshot)
            restored = store.restore(ledger)
            self.assertEqual(restored, ledger.replay())
            self.assertIn("ADVISORY_ONLY", snapshot.advisory_soft_governance_versions[0])


if __name__ == "__main__":
    unittest.main()
