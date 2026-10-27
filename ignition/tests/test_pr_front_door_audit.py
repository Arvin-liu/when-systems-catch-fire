#!/usr/bin/env python3
"""P2 (F2/N8): the PR front-door audit is read-only and catches volatile / over-claim anti-patterns.

It must:
  - flag a specific commit/file count (COMMIT_COUNT_VOLATILE)
  - flag a hardcoded specific HEAD SHA (HEAD_HASH_VOLATILE)
  - flag an aggregated pass-count over-claim (AGGREGATED_PASS_CLAIM)
  - PASS a clean front door that separates Local / Q33 / Foundation layers and cites no counts
  - never mutate its input
"""

import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(REPO_ROOT, "tools", "governance")
sys.path.insert(0, TOOLS_DIR)

from audit_pr_front_door import audit_body  # noqa: E402


CLEAN_BODY = (
    "## Q33 Draft Candidate\n"
    "Status: draft_candidate\n"
    "This is a draft candidate (OPEN / DRAFT / UNMERGED), not merged.\n\n"
    "### Validation\n"
    "- Local Q33 governance suite: run via `pytest tests/` on this branch.\n"
    "- Foundation CI: see the GitHub Actions runs for this branch.\n"
    "- CI is the source of truth for pass/fail; no aggregate pass count is asserted here.\n"
)


class FrontDoorAuditTests(unittest.TestCase):
    def test_clean_body_passes(self):
        r = audit_body(CLEAN_BODY)
        self.assertEqual(r["status"], "PASS", r)
        self.assertEqual(r["violations"], [])

    def test_commit_count_volatile_flagged(self):
        r = audit_body("Commits since base: 55 - Tracked files changed: 53")
        self.assertEqual(r["status"], "FAIL")
        self.assertTrue(any(v["code"] == "COMMIT_COUNT_VOLATILE" for v in r["violations"]))

    def test_head_hash_volatile_flagged(self):
        r = audit_body("Base: f54577a9 -> HEAD `ad4c4787`")
        self.assertEqual(r["status"], "FAIL")
        self.assertTrue(any(v["code"] == "HEAD_HASH_VOLATILE" for v in r["violations"]))

    def test_aggregated_pass_claim_flagged(self):
        r = audit_body("Full local chain: 230 passed, 1 skipped, 38 subtests")
        self.assertEqual(r["status"], "FAIL")
        self.assertTrue(any(v["code"] == "AGGREGATED_PASS_CLAIM" for v in r["violations"]))

    def test_audit_is_read_only(self):
        body = "Commits since base: 55"
        snapshot = body
        audit_body(body)
        self.assertEqual(body, snapshot, "audit_body must not mutate its input")


if __name__ == "__main__":
    unittest.main()
