#!/usr/bin/env python3
"""Fail-closed negative fixtures for the universal path-accounting preflight.

Contract Task 107 §4 (Required negative fixtures 1-4).  Every test here proves
the preflight *fails closed* on a specific violation; the positive test proves the
current tree passes.  The preflight module is the source of truth and is imported
directly so individual violations can be injected without mutating the real repo.
"""
from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "foundation"))
import validate_repository_path_classification as preflight  # noqa: E402

FIX = ROOT / "tests" / "foundation" / "fixtures" / "repository-path-classification"


class _Capture:
    def __init__(self) -> None:
        self.buf = io.StringIO()
        self._cm = mock.patch("sys.stdout", self.buf)

    def __enter__(self) -> "_Capture":
        self._cm.__enter__()
        return self

    def __exit__(self, *exc: object) -> None:
        self._cm.__exit__(*exc)

    def text(self) -> str:
        return self.buf.getvalue()


class PositiveTreeTest(unittest.TestCase):
    def test_current_tree_passes(self) -> None:
        with _Capture() as c:
            rc = preflight.check()
        self.assertEqual(rc, 0, c.text())
        self.assertIn("REPOSITORY_PATH_CLASSIFICATION_VALID", c.text())


class NegativeClassificationTest(unittest.TestCase):
    def _live_real(self) -> dict:
        return preflight.live_classification()

    # Negative fixture 1: a brand-new top-level directory with no rule -> UNRESOLVED.
    def test_neg_new_unclassified_path(self) -> None:
        live = self._live_real()
        live["zzz_unknown_topdir/some-file.md"] = (preflight.UNRESOLVED, preflight.UNRESOLVED)
        with _Capture() as c:
            rc = preflight.check(live=live)
        self.assertEqual(rc, 1, c.text())
        self.assertIn("FAIL classification:no-unresolved", c.text())

    # Negative fixture 3: a tracked path removed from the tree but still in manifest.
    def test_neg_deleted_path_stale(self) -> None:
        live = self._live_real()
        removed = next(iter(live))
        del live[removed]
        with _Capture() as c:
            rc = preflight.check(live=live)
        self.assertEqual(rc, 1, c.text())
        self.assertIn("FAIL manifest:no-stale-path", c.text())

    # Negative fixture 2: same path appears twice with conflicting categories.
    def test_neg_duplicate_category(self) -> None:
        tmp = FIX / "bad-duplicate.manifest.jsonl"
        with mock.patch.object(preflight, "MANIFEST", tmp):
            with _Capture() as c:
                rc = preflight.check()
        self.assertEqual(rc, 1, c.text())
        self.assertIn("FAIL classification:no-duplicate", c.text())

    # Negative fixture 4: an editorial path wrongly marked AUTHORITATIVE in manifest.
    def test_neg_editorial_mislabeled_authoritative(self) -> None:
        tmp = FIX / "bad-authoritative-mislabel.manifest.jsonl"
        with mock.patch.object(preflight, "MANIFEST", tmp):
            with _Capture() as c:
                rc = preflight.check()
        self.assertEqual(rc, 1, c.text())
        self.assertIn("FAIL anti-backflow:manifest-authoritative-allowlist", c.text())


if __name__ == "__main__":
    unittest.main()
