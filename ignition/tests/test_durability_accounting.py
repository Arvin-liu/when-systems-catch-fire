from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from agent_runtime.accounting import (
    AccountingDuplicate,
    AccountingPolicy,
    AccountingQuotaExceeded,
    AccountingStore,
    BoundedFairScheduler,
    BudgetScope,
    CostVector,
    FairWorkItem,
)


class DurabilityAccountingTests(unittest.TestCase):
    def policy(self, *, action_limit: int = 8, workspace_namespace: dict[str, str] | None = None) -> AccountingPolicy:
        scope = {
            "principal:principal-a", "namespace:namespace-a", "workspace:workspace-a", "episode:episode-a", "pack:pack-a", "executor:executor-a",
        }
        limit = CostVector(action_limit, 100, 10000, 100, 10000, action_limit, action_limit, action_limit)
        return AccountingPolicy({key: limit for key in scope}, workspace_namespace or {"workspace-a": "namespace-a"}, max_consecutive_per_principal=2, aging_seconds=10, aging_cap=1000)

    def scope(self, *, namespace: str = "namespace-a") -> BudgetScope:
        return BudgetScope("principal-a", namespace, "workspace-a", "episode-a", "pack-a", "executor-a")

    def test_replay_rebuilds_all_scope_dimensions_and_cost_classes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="accounting-") as temp:
            store = AccountingStore(Path(temp) / "accounting.jsonl", self.policy())
            estimated = CostVector(action_count=1, wall_clock_seconds=10, output_bytes=20, event_volume=2, memory_bytes=30, retry_cost=1, failover_cost=1, reconciliation_cost=1)
            store.reserve("reservation-a", self.scope(), estimated, attempt_kind="PRIMARY", occurred_at=1)
            store.settle("reservation-a", CostVector(action_count=1, wall_clock_seconds=4, output_bytes=10, event_volume=1, memory_bytes=12, retry_cost=0, failover_cost=0, reconciliation_cost=0), occurred_at=2)
            replay = store.replay()
            self.assertEqual(set(replay["totals"]), {"principal:principal-a", "namespace:namespace-a", "workspace:workspace-a", "episode:episode-a", "pack:pack-a", "executor:executor-a"})
            self.assertEqual(replay["totals"]["episode:episode-a"]["spent"]["wall_clock_seconds"], 4)
            self.assertEqual(replay["totals"]["episode:episode-a"]["reserved"]["action_count"], 0)
            self.assertEqual(len(store.events()), 2)

    def test_retry_must_account_cost_and_cannot_bypass_budget(self) -> None:
        with tempfile.TemporaryDirectory(prefix="accounting-") as temp:
            store = AccountingStore(Path(temp) / "accounting.jsonl", self.policy(action_limit=1))
            primary = CostVector(action_count=1, event_volume=1)
            store.reserve("primary-a", self.scope(), primary, attempt_kind="PRIMARY", occurred_at=1)
            store.settle("primary-a", primary, occurred_at=2)
            with self.assertRaises(AccountingQuotaExceeded):
                store.reserve("retry-a", self.scope(), CostVector(action_count=1, event_volume=1), attempt_kind="RETRY", occurred_at=3)
            with self.assertRaises(AccountingQuotaExceeded):
                store.reserve("retry-b", self.scope(), CostVector(action_count=1, event_volume=1, retry_cost=1), attempt_kind="RETRY", occurred_at=3)

    def test_cancel_releases_unused_budget_but_keeps_occurred_cost(self) -> None:
        with tempfile.TemporaryDirectory(prefix="accounting-") as temp:
            store = AccountingStore(Path(temp) / "accounting.jsonl", self.policy())
            estimate = CostVector(action_count=1, wall_clock_seconds=10, event_volume=2)
            store.reserve("cancel-a", self.scope(), estimate, occurred_at=1)
            receipt = store.settle("cancel-a", CostVector(action_count=1, wall_clock_seconds=3, event_volume=1), cancelled=True, occurred_at=2)
            self.assertEqual(receipt.released_cost.wall_clock_seconds, 7)
            totals = store.totals_for("principal", "principal-a")
            self.assertEqual(totals["spent"].wall_clock_seconds, 3)
            self.assertEqual(totals["reserved"].wall_clock_seconds, 0)

    def test_double_settlement_is_not_double_accounted(self) -> None:
        with tempfile.TemporaryDirectory(prefix="accounting-") as temp:
            store = AccountingStore(Path(temp) / "accounting.jsonl", self.policy())
            cost = CostVector(action_count=1, event_volume=1)
            store.reserve("double-a", self.scope(), cost, occurred_at=1)
            store.settle("double-a", cost, occurred_at=2)
            with self.assertRaises(AccountingDuplicate):
                store.settle("double-a", CostVector(action_count=2, event_volume=2), occurred_at=3)
            self.assertEqual(len(store.events()), 2)

    def test_namespace_quota_escape_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="accounting-") as temp:
            store = AccountingStore(Path(temp) / "accounting.jsonl", self.policy(),)
            with self.assertRaises(AccountingQuotaExceeded):
                store.reserve("escape-a", self.scope(namespace="namespace-b"), CostVector(action_count=1), occurred_at=1)

    def test_bounded_fairness_prevents_starvation_and_infinite_preemption(self) -> None:
        scheduler = BoundedFairScheduler(self.policy())
        scheduler.enqueue(FairWorkItem("high-1", "principal-a", 1000, 0))
        scheduler.enqueue(FairWorkItem("high-2", "principal-a", 1000, 0))
        scheduler.enqueue(FairWorkItem("high-3", "principal-a", 1000, 0))
        scheduler.enqueue(FairWorkItem("low-1", "principal-b", 0, 0))
        first = scheduler.select(now=1)
        second = scheduler.select(now=1)
        third = scheduler.select(now=1)
        self.assertEqual((first.principal_id, second.principal_id), ("principal-a", "principal-a"))
        self.assertEqual(third.principal_id, "principal-b")
        self.assertTrue(scheduler.fairness_state()["bounded"])

    def test_aging_can_raise_old_work_without_exceeding_priority_ceiling(self) -> None:
        scheduler = BoundedFairScheduler(self.policy())
        scheduler.enqueue(FairWorkItem("old", "principal-a", 0, 0))
        scheduler.enqueue(FairWorkItem("new", "principal-b", 900, 50))
        selected = scheduler.select(now=20000)
        self.assertEqual(selected.work_id, "old")
        self.assertLessEqual(scheduler.fairness_state()["priority_ceiling"], 1000)


if __name__ == "__main__":
    unittest.main()
