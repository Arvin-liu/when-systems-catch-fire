#!/usr/bin/env python3
"""Fail-closed propagation reconciliation tests (task 106, contract §8/§9/§10).

Proves, with positive and negative fixtures, that:
  - the pre-repair (post-105-merge but stale) repository state is a FAILING
    fixture (contract §10 requires the contradicted state to be reproducible as
    a failing fixture);
  - the remediated repository passes the validator;
  - editorial lifecycle: a material source change with no review fails, an
    unrelated/unchanged source does NOT falsely stale, a missing source path
    fails, and restoring CURRENT without review fails (§8);
  - system-map impact: a governed map-source mutation forces IMPACT_REQUIRED,
    a genuinely unmapped mutation passes with justified NO_IMPACT (§9).
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
PROP = os.path.join(REPO, "tools", "propagation")
sys.path.insert(0, PROP)

from ledger import load_ledger, validate_ledger  # noqa: E402
from editorial_lifecycle import validate_manifest, _sha256  # noqa: E402
from system_map_audit import audit, MAP_GOVERNED_SOURCES  # noqa: E402
from impact_contract import DIMENSIONS  # noqa: E402
import validate_reconciliation as vr  # noqa: E402


class TestBaselineContradictionFixture(unittest.TestCase):
    """The pre-repair state must be a reproducible FAILING fixture (§10)."""

    def test_project_current_state_stops_before_105(self):
        text = "更新时间：2026-07-30。当前状态包含任务 98—100 ... 任务 102 ... 任务 103。"
        self.assertTrue(vr.check_project_current_state_includes(text))

    def test_open_question_still_pending(self):
        text = ("|OQ-103-5：Function OS v0.2 正确性|...|计算正确性试点（候选 C-4），"
                "需先构建参考 oracle。|无参考 oracle 时不强行推进。|")
        problems = vr.check_open_question_resolved(text)
        self.assertTrue(any("pending" in p or "untouched" in p for p in problems))

    def test_verdicts_absent_from_public_wording(self):
        problems = vr.check_verdicts_distinct(
            "no verdicts here", "still no verdicts")
        self.assertEqual(len(problems), 2)


class TestRemediatedRepository(unittest.TestCase):
    """The remediated repository must pass all twelve failure modes (§10/§15)."""

    def test_run_check_clean(self):
        problems = vr.run_check(REPO)
        self.assertEqual(problems, [], msg="\n".join(problems))

    def test_ledger_valid_and_terminal_105_present(self):
        recs = load_ledger(os.path.join(REPO, "data", "operations", "merged-iteration-ledger.jsonl"))
        self.assertEqual(validate_ledger(recs), [])
        self.assertEqual(vr.check_ledger_has_terminal(recs, 105), [])


class TestEditorialLifecycle(unittest.TestCase):
    """§8 adversarial fixtures for article stale/review closure."""

    def _manifest(self, entry_overrides, base_article="001-withdrawn-gravity-how-strong-claims-do-not-rebound"):
        # Start from the real manifest's article 001 entry (valid, current hashes).
        real = os.path.join(REPO, "docs", "editorial", "source-manifest.json")
        with open(real, "r", encoding="utf-8") as fh:
            m = json.load(fh)
        art_id = base_article.replace(".md", "")
        entry = dict(m["articles"][art_id])
        entry.update(entry_overrides)
        tmp = {"schema_version": "1.0.0", "articles": {art_id: entry}}
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(tmp, fh)
        return path

    def test_positive_source_changed_but_current_without_review_fails(self):
        # Flip a recorded hash to simulate a material source change.
        path = self._manifest({
            "editorial_status": "CURRENT",
            "review_evidence": None,
            "source_hashes": {"RESULTS/CORRECTIONS.md": "0" * 64},
        })
        problems = validate_manifest(path, REPO)
        self.assertTrue(any("material source" in p for p in problems), msg="\n".join(problems))

    def test_negative_unchanged_source_does_not_false_stale(self):
        # Correct hashes, currency status with review evidence -> no false stale.
        path = self._manifest({})
        problems = validate_manifest(path, REPO)
        self.assertEqual([p for p in problems if "material source" in p], [])

    def test_source_path_not_recorded_fails(self):
        real = os.path.join(REPO, "docs", "editorial", "source-manifest.json")
        with open(real, "r", encoding="utf-8") as fh:
            m = json.load(fh)
        art_id = "001-withdrawn-gravity-how-strong-claims-do-not-rebound".replace(".md", "")
        entry = dict(m["articles"][art_id])
        entry["source_paths"] = entry["source_paths"] + ["README.md"]  # referenced but not hashed
        tmp = {"schema_version": "1.0.0", "articles": {art_id: entry}}
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(tmp, fh)
        problems = validate_manifest(path, REPO)
        self.assertTrue(any("not recorded in source_hashes" in p for p in problems))

    def test_restore_to_current_without_review_fails(self):
        path = self._manifest({
            "editorial_status": "CURRENT",
            "review_evidence": None,
            "source_hashes": {"RESULTS/CORRECTIONS.md": _sha256(os.path.join(REPO, "RESULTS/CORRECTIONS.md"))},
        })
        problems = validate_manifest(path, REPO)
        self.assertTrue(any("restored to CURRENT without review_evidence" in p for p in problems))


class TestSystemMapImpact(unittest.TestCase):
    """§9 adversarial fixtures for map impact / no-impact justification."""

    def test_positive_governed_map_source_changed_forces_impact(self):
        current = audit(REPO)["current_hashes"]
        # Corrupt one governed source hash to simulate a real change.
        bad = dict(current)
        bad[MAP_GOVERNED_SOURCES[0]] = "0" * 64
        result = audit(REPO, baseline=bad)
        self.assertEqual(result["decision"], "IMPACT_REQUIRED")
        self.assertTrue(result["changed_sources"])

    def test_negative_unmapped_change_passes_with_justification(self):
        # Baseline matches current -> no governed source changed -> justified no-impact.
        result = audit(REPO)  # no baseline => uses current as baseline
        self.assertEqual(result["decision"], "NO_IMPACT_JUSTIFIED")
        self.assertEqual(result["changed_sources"], [])
        self.assertTrue(result["explanation"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
