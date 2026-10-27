"""Round 5 — frozen offline anti-overfit fixtures + separate metrics + replay.

Covers TASK.md Round 5:
  * >=24 frozen, deterministic fixtures (16 episode + 11 queue) that exercise
    the anti-overfit/error-stop surface: many URLs without reading, repeated
    same-family sources, summary-as-fulltext, unsupported citation, absent
    contrary evidence, conflicting estimands, ceiling reduction, numerical
    mismatch, high-stakes escalation, prompt injection, queue crash/resume and
    duplicate lease, deadline/task-count/budget/owner/safety/queue-empty/low-
    information stops, and the invariant that a long report / executor success
    NEVER stops the queue.
  * Deterministic replay: the live evaluator/queue runtime must reproduce each
    fixture's frozen ``expect`` block exactly (regression guard).
  * Separate, UNCOLLAPSED metrics: brief/rubric coverage, obligation coverage,
    source independence (family count), abstract-only / none-access / injection
    signals, contrary-evidence sought, and every sufficiency-vector dimension.
  * False-positive / false-negative stop rates measured against an independent
    ground-truth stop/continue label (not against the evaluator's own output),
    so a real evaluator regression surfaces instead of being hidden by a single
    aggregate score.

Run:  python3 tests/test_deep_research_round5.py
"""

from __future__ import annotations

import glob
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "tools") not in __import__("sys").path:
    __import__("sys").path.insert(0, str(REPO_ROOT / "tools"))

from research_os import kernel as K  # noqa: E402
from deep_research import adapters as A  # noqa: E402
from deep_research import records as R  # noqa: E402
from deep_research import episode_loop as E  # noqa: E402
from deep_research import queue_runtime as Q  # noqa: E402

FIX = REPO_ROOT / "tests" / "fixtures" / "deep_research" / "round5"
PACK = "SYSTEMATIC_EVIDENCE_SYNTHESIS"

# Independent ground-truth stop/continue labels for the EPISODE fixtures,
# capturing the anti-overfit intent separately from the evaluator output.
#   stop  = the episode should terminate (sufficient / insufficient / blocked /
#           escalate); continue = it must NOT be marked complete.
# r5-006 (conflicting estimands) is labelled "continue": two contradictory
# material claims both asserted is a defect, so marking it STOP_SUFFICIENT_*
# is a KNOWN false-positive gap (no contradiction gate yet). This label exists
# so the metric reports the gap instead of hiding it; Round 7 tracks the fix.
EPISODE_GT_STOP = {
    "r5-001-many-urls-no-reading": False,
    "r5-002-repeated-same-family": False,
    "r5-003-summary-as-fulltext": False,
    "r5-004-unsupported-citation": False,
    "r5-005-absent-contrary-evidence": False,
    "r5-006-conflicting-estimands": False,
    "r5-007-ceiling-reduction": True,
    "r5-008-numerical-mismatch": True,
    "r5-009-high-stakes-escalation": True,
    "r5-010-prompt-injection": True,
    "r5-011-genuinely-sufficient": True,
    "r5-012-unfrozen-scope": False,
    "r5-013-open-severe-obligation": False,
    "r5-014-single-family-material": False,
    "r5-015-blocked-evidence-route": True,
    "r5-016-nonentailing-pair": False,
}

# Independent ground-truth stop/continue labels for the QUEUE should_stop /
# ingest fixtures. Long-report and executor-success must NOT stop (False).
QUEUE_GT_STOP = {
    "r5-019-deadline-stop": True,
    "r5-020-max-episodes-stop": True,
    "r5-021-budget-stop": True,
    "r5-022-owner-stop": True,
    "r5-023-safety-blocker-stop": True,
    "r5-024-queue-empty-stop": True,
    "r5-025-long-report-never-stops": False,
    "r5-026-executor-success-never-stops": False,
    "r5-027-low-information-stop": True,
}


def _load():
    epis, queues = [], []
    for p in sorted(glob.glob(str(FIX / "*.json"))):
        if p.endswith("ROUND5_METRICS.json"):
            continue
        data = json.loads(Path(p).read_text(encoding="utf-8"))
        if data.get("kind") == "episode":
            epis.append(data)
        elif data.get("kind") == "queue":
            queues.append(data)
    return epis, queues


class Round5FixtureCountTests(unittest.TestCase):
    def test_total_fixtures_ge_24(self):
        epis, queues = _load()
        self.assertGreaterEqual(len(epis) + len(queues), 24,
                                "Round 5 requires >=24 frozen fixtures")


class Round5EpisodeReplayTests(unittest.TestCase):
    def setUp(self):
        self.epis, _ = _load()

    def test_replay_each_episode_matches_expect(self):
        for fx in self.epis:
            with self.subTest(fid=fx["id"]):
                dec = E.SufficiencyEvaluator().evaluate(fx["episode"])
                self.assertEqual(dec["decision"], fx["expect"]["decision"],
                                 f"{fx['id']}: decision diverged from frozen intent")
                self.assertEqual(set(dec["failed_gates"]),
                                 set(fx["expect"]["failed_gates"]),
                                 f"{fx['id']}: failed_gates diverged from frozen intent")


class Round5QueueReplayTests(unittest.TestCase):
    def setUp(self):
        _, self.queues = _load()

    def _replay(self, fx):
        op = fx["expect"]["op"]
        if op == "recover":
            q = Q.SerialQueue(campaign=fx["campaign"], items=fx["items"], owner="workbuddy")
            rec = q.recover(now_iso=fx["now_iso"])
            self.assertEqual(rec, fx["expect"]["recovered_ids"])
            if fx["expect"].get("preserves_checkpoint"):
                for it in q.items:
                    self.assertIsNotNone(it.get("checkpoint_commit"),
                                         f"{fx['id']}: checkpoint lost on resume")
        elif op == "duplicate_lease":
            first = Q.select_next(fx["items"], now_iso=fx["now_iso"], owner="ownerA")
            self.assertIsNotNone(first, f"{fx['id']}: first owner could not select")
            second = Q.select_next(fx["items"], now_iso=fx["now_iso"], owner="ownerB")
            self.assertEqual(second, fx["expect"]["second_owner_selects"],
                             f"{fx['id']}: second owner wrongly claimed unexpired lease")
        elif op == "should_stop":
            stats = fx.get("stats",
                           {"completions": 0, "attempts": 0, "cost": 0.0,
                            "consecutive_low_info": 0})
            stopped, reason = Q.should_stop(
                fx["campaign"], fx["items"], stats, fx["now_iso"],
                low_info_threshold=fx.get("low_info_threshold", 3))
            self.assertEqual(stopped, fx["expect"]["stopped"],
                             f"{fx['id']}: stopped diverged")
            self.assertEqual(reason, fx["expect"]["reason"],
                             f"{fx['id']}: stop reason diverged")
        elif op == "ingest_never_stops":
            q = Q.SerialQueue(campaign=fx["campaign"], items=fx["items"], owner="workbuddy")
            q.items[0]["episode_id"] = fx["ingest"]["episode_id"]
            q.ingest_result(fx["ingest"], now_iso=fx["now_iso"])
            stopped, _ = q.should_stop(now_iso=fx["now_iso"])
            self.assertEqual(stopped, fx["expect"]["stopped"],
                             f"{fx['id']}: ingest must never stop the queue")
        else:
            raise AssertionError(f"unknown queue op: {op}")

    def test_replay_each_queue_op_matches_expect(self):
        for fx in self.queues:
            with self.subTest(fid=fx["id"]):
                self._replay(fx)


class Round5MetricsTests(unittest.TestCase):
    """Measure SEPARATE (uncollapsed) metrics and FP/FN stop rates."""

    def setUp(self):
        self.epis, self.queues = _load()

    # -- per-fixture descriptive metrics (no single score) ------------------
    def _episode_metrics(self, fx):
        ep = fx["episode"]
        dec = E.SufficiencyEvaluator().evaluate(ep)
        vec = {v["dimension"]: v["value"] for v in dec["sufficiency_vector"]}
        fams = set()
        for s in ep.get("source_identities", []):
            fams.add((s.get("source_id") or "").split(":", 1)[0] or "unknown")
        obls = ep.get("evidence_obligations", [])
        sat = sum(1 for o in obls if o.get("status") == "SATISFIED")
        abst = sum(1 for s in ep.get("source_identities", [])
                   if s.get("access_level") == "ABSTRACT_ONLY")
        none = sum(1 for s in ep.get("source_identities", [])
                   if s.get("access_level") == "NONE")
        inj = any((p.get("injection_detected")
                   for o in ep.get("observations", [])
                   for p in (o.get("provenance") or [])))
        return {
            "id": fx["id"],
            "decision": dec["decision"],
            # brief/rubric coverage proxy
            "brief_present": bool(ep.get("brief")),
            "obligation_coverage": (sat / len(obls)) if obls else 1.0,
            # source independence
            "source_family_count": len(fams),
            # citation groundedness signals
            "abstract_only_count": abst,
            "none_access_count": none,
            "injection_detected": bool(inj),
            # contrary-evidence sought
            "contrary_sought": bool(ep.get("contrary_evidence_sought")),
            # full sufficiency vector (each dimension reported separately)
            **vec,
        }

    def _queue_metrics(self):
        out = []
        for fx in self.queues:
            out.append({
                "id": fx["id"],
                "op": fx["expect"]["op"],
                "expect_stopped": fx["expect"].get("stopped"),
                "expect_reason": fx["expect"].get("reason"),
            })
        return out

    def test_separate_metrics_reported_not_collapsed(self):
        metrics = [self._episode_metrics(fx) for fx in self.epis]

        # decision distribution (separate indicator, not a score)
        decisions = {}
        for m in metrics:
            decisions[m["decision"]] = decisions.get(m["decision"], 0) + 1

        # episode FP/FN vs independent ground truth (never against self)
        tp = fp = fn = tn = 0
        fp_ids, fn_ids = [], []
        for m in metrics:
            gt = EPISODE_GT_STOP[m["id"]]
            pred_stop = m["decision"] != "CONTINUE_RESEARCH"
            if pred_stop and gt:
                tp += 1
            elif pred_stop and not gt:
                fp += 1
                fp_ids.append(m["id"])
            elif (not pred_stop) and gt:
                fn += 1
                fn_ids.append(m["id"])
            else:
                tn += 1

        # queue FP/FN vs independent ground truth
        qtp = qfp = qfn = qtn = 0
        for fx in self.queues:
            gt = QUEUE_GT_STOP.get(fx["id"])
            if gt is None:
                continue
            pred_stop = bool(fx["expect"].get("stopped"))
            if pred_stop and gt:
                qtp += 1
            elif pred_stop and not gt:
                qfp += 1
            elif (not pred_stop) and gt:
                qfn += 1
            else:
                qtn += 1

        report = {
            "episode_metrics": metrics,
            "queue_metrics": self._queue_metrics(),
            "decision_counts": decisions,
            "episode_stop_confusion": {
                "tp": tp, "fp": fp, "fn": fn, "tn": tn,
                "fp_ids": fp_ids, "fn_ids": fn_ids,
            },
            "queue_stop_confusion": {
                "tp": qtp, "fp": qfp, "fn": qfn, "tn": qtn,
            },
        }
        print(json.dumps(report, indent=2))
        (FIX / "ROUND5_METRICS.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8")

        # --- hard invariants (regression guards, not a single score) -------
        # (1) The queue must NEVER false-stop on a long report or executor
        #     success — this is the core anti-overfit property.
        for fid in ("r5-025-long-report-never-stops",
                    "r5-026-executor-success-never-stops"):
            fx = next(f for f in self.queues if f["id"] == fid)
            self.assertFalse(fx["expect"]["stopped"],
                             f"{fid}: long report / executor success must not stop")
        # (2) Queue stop classification must be exact (no FP, no FN).
        self.assertEqual(qfp, 0, "queue false-positive stop detected")
        self.assertEqual(qfn, 0, "queue false-negative stop detected")
        # (3) Exactly one known episode false-positive stop (the contradiction
        #     gap), and zero false negatives. If this fails, an evaluator
        #     regression occurred or a contradiction gate was added (update the
        #     GT label and acknowledge the fix for Round 7).
        self.assertEqual(fp, 1, f"expected 1 known FP stop, got {fp_ids}")
        self.assertEqual(fp_ids, ["r5-006-conflicting-estimands"],
                         "the known FP stop must be the contradiction scenario")
        self.assertEqual(fn, 0, f"episode false-negative stop detected: {fn_ids}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
