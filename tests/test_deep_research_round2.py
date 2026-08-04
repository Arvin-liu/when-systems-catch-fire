"""Round 2 — serial, crash-resumable queue runtime.

Deterministic tests for: ranking/ordering, deterministic selector, model
proposal cannot override hard gates, lease idempotency / duplicate prevention /
expiry, crash recovery (resume), episode-result ingestion (never stops), and
every campaign-level stop type. Also proves a long report / many URLs /
executor success NEVER stops the queue.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from deep_research import records as R
from deep_research import queue_runtime as Q


def _cand(cid, **kw):
    base = dict(candidate_id=cid, proposed_question=cid, source_of_seed="PROJECT_GAP",
                proposed_strategy_pack="sp", status="CANDIDATE")
    base.update(kw)
    return R.make_topic_candidate(**base)


def _item(cid, cand, **kw):
    base = dict(queue_item_id=cid, topic_candidate=cand, status="QUEUED")
    base.update(kw)
    return R.make_queue_item(**base)


class Round2RankingTests(unittest.TestCase):
    def test_ranking_deterministic(self):
        cands = [_cand("A", materiality=0.1), _cand("B", materiality=0.9)]
        s1 = Q.rank_candidates(cands)
        s2 = Q.rank_candidates(list(reversed(cands)))
        self.assertEqual([x[1]["candidate_id"] for x in s1],
                         [x[1]["candidate_id"] for x in s2])

    def test_ranking_sorts_by_score(self):
        cands = [_cand("low", materiality=0.1, risk=0.9),
                 _cand("high", materiality=0.9, risk=0.1)]
        scored = Q.rank_candidates(cands)
        self.assertEqual(scored[0][1]["candidate_id"], "high")

    def test_tie_breaks_by_queue_item_id(self):
        a = _item("qi-A", _cand("A", materiality=0.5))
        b = _item("qi-B", _cand("B", materiality=0.5))
        scored = Q.rank_candidates([a, b])
        self.assertEqual(scored[0][1]["queue_item_id"], "qi-A")


class Round2SelectionTests(unittest.TestCase):
    def test_selector_picks_highest(self):
        items = [_item("qi-A", _cand("A", materiality=0.1)),
                 _item("qi-B", _cand("B", materiality=0.9))]
        sel = Q.select_next(items, now_iso="2026-02-01T00:00:00Z", owner="workbuddy")
        self.assertEqual(sel["queue_item_id"], "qi-B")
        self.assertEqual(sel["status"], "ACTIVE")  # lease claim sets ACTIVE

    def test_selector_respects_hard_gate_blocked(self):
        a = _item("qi-A", _cand("A", materiality=0.9))
        b = _item("qi-B", _cand("B", materiality=0.1), status="BLOCKED")
        sel = Q.select_next([a, b], now_iso="2026-02-01T00:00:00Z")
        self.assertEqual(sel["queue_item_id"], "qi-A")

    def test_model_proposal_cannot_override_gate(self):
        # qi-X has an unexpired lease held by another owner -> gate fails.
        x = _item("qi-X", _cand("X", materiality=0.9),
                  lease={"owner": "other", "expiry": "2099-01-01T00:00:00Z", "claim_id": "l1"})
        y = _item("qi-Y", _cand("Y", materiality=0.1))
        sel = Q.select_next([x, y], now_iso="2026-02-01T00:00:00Z",
                            model_proposal=["qi-X", "qi-Y"])
        self.assertEqual(sel["queue_item_id"], "qi-Y")  # X gated out despite proposal

    def test_model_proposal_reorders_equal_scores(self):
        a = _item("qi-A", _cand("A", materiality=0.5))
        b = _item("qi-B", _cand("B", materiality=0.5))
        sel = Q.select_next([a, b], now_iso="2026-02-01T00:00:00Z",
                            model_proposal=["qi-B", "qi-A"])
        self.assertEqual(sel["queue_item_id"], "qi-B")


class Round2LeaseTests(unittest.TestCase):
    def test_idempotent_claim_refreshes(self):
        item = _item("qi-A", _cand("A"))
        ok1, r1 = Q.claim_lease(item, "owner1", "2026-02-01T00:00:00Z", ttl_seconds=3600)
        cid = item["lease"]["claim_id"]
        ok2, r2 = Q.claim_lease(item, "owner1", "2026-02-01T00:30:00Z", ttl_seconds=3600)
        self.assertTrue(ok1 and ok2)
        self.assertEqual(r1, "LEASE_ACQUIRED")
        self.assertEqual(r2, "LEASE_REFRESHED")
        self.assertEqual(item["lease"]["claim_id"], cid)  # stable claim id

    def test_duplicate_prevention_blocks_other_owner(self):
        item = _item("qi-A", _cand("A"))
        Q.claim_lease(item, "owner1", "2026-02-01T00:00:00Z", ttl_seconds=3600)
        ok, reason = Q.claim_lease(item, "owner2", "2026-02-01T00:00:30Z", ttl_seconds=3600)
        self.assertFalse(ok)
        self.assertEqual(reason, "LEASE_HELD_BY_OTHER")
        self.assertEqual(item["lease"]["owner"], "owner1")

    def test_expired_lease_allows_takeover(self):
        item = _item("qi-A", _cand("A"))
        Q.claim_lease(item, "owner1", "2020-01-01T00:00:00Z", ttl_seconds=10)
        ok, reason = Q.claim_lease(item, "owner2", "2026-02-01T00:00:00Z", ttl_seconds=3600)
        self.assertTrue(ok)
        self.assertEqual(reason, "LEASE_ACQUIRED")
        self.assertEqual(item["lease"]["owner"], "owner2")

    def test_release_lease_by_owner(self):
        item = _item("qi-A", _cand("A"))
        Q.claim_lease(item, "owner1", "2026-02-01T00:00:00Z", ttl_seconds=3600)
        self.assertTrue(Q.release_lease(item, "owner1"))
        self.assertIsNone(item["lease"])


class Round2RecoveryTests(unittest.TestCase):
    def test_recover_returns_expired_active_to_queued(self):
        item = _item("qi-A", _cand("A"), status="ACTIVE",
                     lease={"owner": "w", "expiry": "2020-01-01T00:00:00Z", "claim_id": "l1"})
        rec = Q.recover([item], now_iso="2026-02-01T00:00:00Z")
        self.assertEqual(rec, ["qi-A"])
        self.assertEqual(item["status"], "QUEUED")
        self.assertIsNone(item["lease"])

    def test_recover_preserves_checkpoint(self):
        item = _item("qi-A", _cand("A"), status="ACTIVE", checkpoint_commit="abc123",
                     lease={"owner": "w", "expiry": "2020-01-01T00:00:00Z", "claim_id": "l1"})
        Q.recover([item], now_iso="2026-02-01T00:00:00Z")
        self.assertEqual(item["checkpoint_commit"], "abc123")  # resumable, not blind restart

    def test_recover_leaves_blocked_alone(self):
        item = _item("qi-A", _cand("A"), status="BLOCKED")
        rec = Q.recover([item], now_iso="2026-02-01T00:00:00Z")
        self.assertEqual(rec, [])
        self.assertEqual(item["status"], "BLOCKED")


class Round2IngestionTests(unittest.TestCase):
    def test_ingest_completes_and_records_checkpoint(self):
        item = _item("qi-A", _cand("A"))
        item["episode_id"] = "ep-A"
        res = R.make_episode_result(episode_id="ep-A", final_state="CANDIDATE_COMPLETE",
                                     machine_trace_ref="trace-abc")
        qid = Q.ingest_result([item], res, now_iso="2026-02-01T00:00:00Z")
        self.assertEqual(qid, "qi-A")
        self.assertEqual(item["status"], "COMPLETED")
        self.assertEqual(item["checkpoint_commit"], "trace-abc")

    def test_long_report_many_urls_success_never_stops(self):
        """The core Round 2 invariant: volume/success must not stop the queue,
        and the queue must continue to the next pending item."""
        campaign = R.make_campaign(stop_conditions={"queue_empty_stops": False})
        q = Q.SerialQueue(campaign=campaign, owner="w")
        item_a = q.add_candidate(_cand("A"))
        item_a["episode_id"] = "ep-A"
        item_b = q.add_candidate(_cand("B"))  # still pending -> queue continues
        # A 'successful' result with a long report and many URLs.
        big_res = R.make_episode_result(
            episode_id="ep-A", final_state="CANDIDATE_COMPLETE",
            report_ref="reports/huge-report-with-500-urls.md",
            source_records=[{"source_id": f"src-{i}"} for i in range(200)],
            sufficiency_decision={"decision": "STOP_SUFFICIENT_CANDIDATE"},
        )
        q.ingest_result(big_res, now_iso="2026-02-01T00:00:00Z")
        stopped, reason = q.should_stop(now_iso="2026-02-01T00:00:00Z")
        self.assertFalse(stopped, "long report / many URLs / success must never stop queue")
        # queue continues to the still-pending item B
        nxt = q.select_next(now_iso="2026-02-01T00:00:00Z")
        self.assertIsNotNone(nxt)
        self.assertEqual(nxt["queue_item_id"], item_b["queue_item_id"])


class Round2StopTests(unittest.TestCase):
    NOW = "2026-06-01T00:00:00Z"

    def _queue_with_one_queued(self):
        q = Q.SerialQueue(owner="w")
        it = q.add_candidate(_cand("A"))
        it["episode_id"] = "ep-A"
        return q, it

    def test_stop_owner(self):
        q = Q.SerialQueue(campaign=R.make_campaign(
            stop_conditions={"owner_stop": True}), owner="w")
        stopped, reason = q.should_stop(now_iso=self.NOW)
        self.assertTrue(stopped) and self.assertEqual(reason, "OWNER_STOP")

    def test_stop_deadline(self):
        q = Q.SerialQueue(campaign=R.make_campaign(
            stop_conditions={"deadline": "2026-01-01T00:00:00Z"}), owner="w")
        stopped, reason = q.should_stop(now_iso=self.NOW)
        self.assertTrue(stopped) and self.assertEqual(reason, "DEADLINE")

    def test_stop_max_episodes(self):
        q = Q.SerialQueue(campaign=R.make_campaign(
            stop_conditions={"max_episodes": 2}), owner="w")
        q.stats["completions"] = 2
        stopped, reason = q.should_stop(now_iso=self.NOW)
        self.assertTrue(stopped) and self.assertEqual(reason, "MAX_EPISODES")

    def test_stop_budget(self):
        q = Q.SerialQueue(campaign=R.make_campaign(
            stop_conditions={"budget": 10.0}), owner="w")
        q.stats["cost"] = 12.0
        stopped, reason = q.should_stop(now_iso=self.NOW)
        self.assertTrue(stopped) and self.assertEqual(reason, "BUDGET")

    def test_stop_queue_empty(self):
        q = Q.SerialQueue(campaign=R.make_campaign(
            stop_conditions={"queue_empty_stops": True}), owner="w")
        it = q.add_candidate(_cand("A"))
        it["episode_id"] = "ep-A"
        it["status"] = "COMPLETED"
        stopped, reason = q.should_stop(now_iso=self.NOW)
        self.assertTrue(stopped) and self.assertEqual(reason, "QUEUE_EMPTY")

    def test_stop_safety_blocker(self):
        q = Q.SerialQueue(campaign=R.make_campaign(
            stop_conditions={"safety_blocker_stops": True,
                             "queue_empty_stops": False}), owner="w")
        it = q.add_candidate(_cand("A"))
        it["status"] = "BLOCKED"
        stopped, reason = q.should_stop(now_iso=self.NOW)
        self.assertTrue(stopped) and self.assertEqual(reason, "SAFETY_BLOCKER")

    def test_stop_low_information(self):
        q = Q.SerialQueue(campaign=R.make_campaign(
            stop_conditions={"low_information_stops": True,
                             "queue_empty_stops": False}), owner="w")
        it = q.add_candidate(_cand("A"))
        it["episode_id"] = "ep-A"
        q.stats["consecutive_low_info"] = 3
        stopped, reason = q.should_stop(now_iso=self.NOW)
        self.assertTrue(stopped) and self.assertEqual(reason, "LOW_INFORMATION")

    def test_no_stop_when_conditions_absent(self):
        q = Q.SerialQueue(campaign=R.make_campaign(stop_conditions={}), owner="w")
        it = q.add_candidate(_cand("A"))
        it["episode_id"] = "ep-A"
        stopped, reason = q.should_stop(now_iso=self.NOW)
        self.assertFalse(stopped)
        self.assertIsNone(reason)


if __name__ == "__main__":
    unittest.main()
