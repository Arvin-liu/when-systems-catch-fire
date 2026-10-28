#!/usr/bin/env python3
"""Negative/positive fixture tests for the terminalization allowlist (task 108, §12/§17)."""
from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(REPO, "tools", "propagation"))

import terminalization_allowlist as ta  # noqa: E402


class TestAllowlist(unittest.TestCase):
    ALLOWED = [
        "data/operations/lifecycle-events.jsonl",
        "data/operations/current-truth-projection.json",
        "data/operations/derived-lifecycle-view.json",
        "data/operations/propagation/108-impact/system-map-nonimpact-proof.json",
        "docs/editorial/source-manifest.json",
        "docs/editorial/articles/008-stale-current-truth.md",
        "docs/project-current-state.md",
        "RESULTS/LATEST.md",
        "KNOWLEDGE/WHATS-NEW.md",
        "reports/operations/lifecycle-audit-108.md",
        "tools/propagation/lifecycle_events.py",
        "tools/propagation/tag_validator.py",
        "tools/propagation/terminalization_allowlist.py",
        "tools/propagation/terminalization_generator.py",
        "schemas/operations/lifecycle-event.schema.json",
        "tests/test_lifecycle_events.py",
        "tests/test_terminalization_allowlist.py",
        "tests/fixtures/lifecycle/positive-1.json",
        "data/operations/terminal-evidence-core.json",
        "docs/operations/lifecycle-readme.md",
        "ITERATION.md",
    ]

    FORBIDDEN = [
        "function-os-candidate/v0.2/README.md",
        "data/foundation/nonfunction-claims/adjudication-ledger.jsonl",
        "data/math-foundation/function-provenance-ledger.jsonl",
        "docs/editorial/articles/007-benchmark.md",
        "tools/era_resolver.py",
    ]

    def test_allowed_paths(self):
        for p in self.ALLOWED:
            ok, reason = ta.path_allowed(p)
            self.assertTrue(ok, f"expected allowed: {p} ({reason})")

    def test_forbidden_paths(self):
        for p in self.FORBIDDEN:
            ok, reason = ta.path_allowed(p)
            self.assertFalse(ok, f"expected forbidden: {p}")

    def test_no_delete_of_ledger(self):
        violations = ta.validate_diff_status([
            {"path": "data/operations/merged-iteration-ledger.jsonl", "status": "D"},
        ])
        self.assertTrue(any("must not delete" in v for v in violations))

    def test_validate_diff_aggregates(self):
        violations = ta.validate_diff(self.FORBIDDEN)
        self.assertEqual(len(violations), len(self.FORBIDDEN))


if __name__ == "__main__":
    unittest.main(verbosity=2)
