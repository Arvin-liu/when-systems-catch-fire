from __future__ import annotations

import copy
import json
import unittest

from agent_runtime.migration import APPLIED, DRY_RUN, FORBIDDEN, LOSSY_REQUIRES_APPROVAL, MigrationRegistry, StateMigrator, ForbiddenMigrationError, LossyDowngradeRequiresApproval, UnknownEpochError
from tools.validate_durability_migrations import DEFAULT_DATA


class DurabilityMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = MigrationRegistry.from_dict(json.loads(DEFAULT_DATA.read_text(encoding="utf-8")))
        cls.migrator = StateMigrator(cls.registry)

    def test_three_generation_upgrade_and_dry_run_do_not_mutate_input(self) -> None:
        state = {"run_id": "run-1", "lifecycle": {"state": "RUNNING"}}
        original = copy.deepcopy(state)
        result = self.migrator.migrate(state, migration_id="mig-dry", from_epoch="state-epoch-1", to_epoch="state-epoch-3", mode=DRY_RUN, event_lineage=("event-a",))
        self.assertEqual(state, original)
        self.assertEqual(result.receipt.status, DRY_RUN)
        self.assertNotIn("advisory_soft_governance", result.state)
        applied = self.migrator.migrate(state, migration_id="mig-apply", from_epoch="state-epoch-1", to_epoch="state-epoch-3", mode=APPLIED, event_lineage=("event-a",))
        self.assertEqual(applied.receipt.status, APPLIED)
        self.assertEqual(applied.state["lifecycle"]["state"], "RUNNING")
        self.assertEqual(applied.state["advisory_soft_governance"]["status"], "ADVISORY_ONLY")

    def test_lossy_downgrade_requires_approval(self) -> None:
        state = {"advisory_soft_governance": {"status": "ADVISORY_ONLY"}}
        with self.assertRaises(LossyDowngradeRequiresApproval):
            self.migrator.migrate(state, migration_id="mig-lossy", from_epoch="state-epoch-3", to_epoch="state-epoch-2", mode=APPLIED)
        result = self.migrator.migrate(state, migration_id="mig-lossy-approved", from_epoch="state-epoch-3", to_epoch="state-epoch-2", mode=APPLIED, approval=True)
        self.assertEqual(result.receipt.classification, LOSSY_REQUIRES_APPROVAL)
        self.assertNotIn("advisory_soft_governance", result.state)

    def test_unknown_epoch_and_forbidden_path_fail_closed(self) -> None:
        with self.assertRaises(UnknownEpochError):
            self.migrator.migrate({}, migration_id="mig-newer", from_epoch="state-epoch-9", to_epoch="state-epoch-3")
        with self.assertRaises(ForbiddenMigrationError):
            self.migrator.migrate({}, migration_id="mig-forbidden", from_epoch="state-epoch-3", to_epoch="state-epoch-1", mode=APPLIED, approval=True)

    def test_failed_migration_rolls_back_last_known_good_and_preserves_lineage_digest(self) -> None:
        state = {"__migration_fail__": "ADD_ADVISORY_POINTER", "value": "before"}
        result = self.migrator.migrate(state, migration_id="mig-fail", from_epoch="state-epoch-1", to_epoch="state-epoch-3", mode=APPLIED, event_lineage=("e1", "e2"), last_known_good={"value": "known-good"})
        self.assertEqual(result.receipt.status, "ROLLED_BACK")
        self.assertEqual(result.state, {"value": "known-good"})
        self.assertFalse(result.receipt.events_rewritten)


if __name__ == "__main__":
    unittest.main()
