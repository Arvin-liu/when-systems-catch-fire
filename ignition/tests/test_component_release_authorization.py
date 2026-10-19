from __future__ import annotations

import unittest
from pathlib import Path

from tools.operations.release_authorization import independent_approval_is_current


class ComponentReleaseAuthorizationTest(unittest.TestCase):
    def setUp(self):
        self.head_sha = "a" * 40
        self.merged_at = "2026-10-18T12:00:00Z"

    def review(self, review_id, state, *, login="Arvin-liu", commit_id=None, submitted_at="2026-10-18T11:00:00Z"):
        return {
            "id": review_id,
            "state": state,
            "user": {"login": login},
            "commit_id": commit_id or self.head_sha,
            "submitted_at": submitted_at,
        }

    def test_current_independent_approval_for_exact_head_is_accepted(self):
        reviews = [self.review(10, "COMMENTED"), self.review(11, "APPROVED", login="reviewer")]
        self.assertTrue(independent_approval_is_current(reviews, "Arvin-liu", self.head_sha, self.merged_at))

    def test_later_independent_change_request_supersedes_prior_approval(self):
        reviews = [self.review(10, "APPROVED", login="reviewer"), self.review(11, "CHANGES_REQUESTED", login="reviewer")]
        self.assertFalse(independent_approval_is_current(reviews, "Arvin-liu", self.head_sha, self.merged_at))

    def test_later_independent_comment_does_not_revoke_prior_approval(self):
        reviews = [self.review(10, "APPROVED", login="reviewer"), self.review(11, "COMMENTED", login="reviewer")]
        self.assertTrue(independent_approval_is_current(reviews, "Arvin-liu", self.head_sha, self.merged_at))

    def test_later_comment_does_not_clear_an_unresolved_change_request(self):
        reviews = [
            self.review(10, "APPROVED", login="reviewer-a"),
            self.review(11, "CHANGES_REQUESTED", login="reviewer-b"),
            self.review(12, "COMMENTED", login="reviewer-b"),
        ]
        self.assertFalse(independent_approval_is_current(reviews, "Arvin-liu", self.head_sha, self.merged_at))

    def test_explicit_later_approval_resolves_premerge_change_request(self):
        reviews = [
            self.review(10, "CHANGES_REQUESTED", login="reviewer", submitted_at="2026-10-18T10:00:00Z"),
            self.review(11, "APPROVED", login="reviewer", submitted_at="2026-10-18T11:00:00Z"),
        ]
        self.assertTrue(independent_approval_is_current(reviews, "Arvin-liu", self.head_sha, self.merged_at))

    def test_approval_for_an_older_head_does_not_satisfy_independent_review(self):
        old_head = "b" * 40
        reviews = [self.review(10, "APPROVED", login="reviewer", commit_id=old_head)]
        self.assertFalse(independent_approval_is_current(reviews, "Arvin-liu", self.head_sha, self.merged_at))

    def test_pr_author_review_does_not_count_as_independent(self):
        reviews = [self.review(10, "APPROVED", login="Arvin-liu")]
        self.assertFalse(independent_approval_is_current(reviews, "Arvin-liu", self.head_sha, self.merged_at))

    def test_review_without_a_reviewer_identity_does_not_count(self):
        review = self.review(10, "APPROVED", login="reviewer")
        review["user"] = None
        self.assertFalse(independent_approval_is_current([review], "Arvin-liu", self.head_sha, self.merged_at))

    def test_missing_pr_author_identity_fails_closed(self):
        reviews = [self.review(10, "APPROVED", login="reviewer")]
        self.assertFalse(independent_approval_is_current(reviews, "", self.head_sha, self.merged_at))

    def test_independent_review_requires_a_positive_numeric_github_id(self):
        review = self.review(0, "APPROVED", login="reviewer")
        with self.assertRaises(ValueError):
            independent_approval_is_current([review], "Arvin-liu", self.head_sha, self.merged_at)

    def test_exact_head_approval_requires_a_submitted_at_timestamp(self):
        review = self.review(10, "APPROVED", login="reviewer")
        review.pop("submitted_at")
        with self.assertRaises(ValueError):
            independent_approval_is_current([review], "Arvin-liu", self.head_sha, self.merged_at)

    def test_authorization_requires_a_valid_merge_timestamp(self):
        reviews = [self.review(10, "APPROVED", login="reviewer")]
        with self.assertRaises(ValueError):
            independent_approval_is_current(reviews, "Arvin-liu", self.head_sha, "not-a-date")

    def test_one_independent_reviewers_approval_suffices(self):
        reviews = [self.review(10, "APPROVED", login="reviewer")]
        self.assertTrue(independent_approval_is_current(reviews, "Arvin-liu", self.head_sha, self.merged_at))

    def test_another_reviewers_comment_does_not_revoke_current_approval(self):
        reviews = [
            self.review(10, "APPROVED", login="reviewer-a"),
            self.review(11, "COMMENTED", login="reviewer-b"),
        ]
        self.assertTrue(independent_approval_is_current(reviews, "Arvin-liu", self.head_sha, self.merged_at))

    def test_current_independent_change_request_blocks_even_with_another_approval(self):
        reviews = [
            self.review(10, "APPROVED", login="reviewer-a"),
            self.review(11, "CHANGES_REQUESTED", login="reviewer-b"),
        ]
        self.assertFalse(independent_approval_is_current(reviews, "Arvin-liu", self.head_sha, self.merged_at))

    def test_postmerge_approval_does_not_authorize_a_merge(self):
        reviews = [
            self.review(10, "APPROVED", login="reviewer", submitted_at="2026-10-18T13:00:00Z"),
        ]
        self.assertFalse(independent_approval_is_current(reviews, "Arvin-liu", self.head_sha, self.merged_at))

    def test_postmerge_approval_does_not_retroactively_resolve_merge_time_request(self):
        reviews = [
            self.review(10, "CHANGES_REQUESTED", login="reviewer", submitted_at="2026-10-18T11:00:00Z"),
            self.review(11, "APPROVED", login="reviewer", submitted_at="2026-10-18T13:00:00Z"),
        ]
        self.assertFalse(independent_approval_is_current(reviews, "Arvin-liu", self.head_sha, self.merged_at))

    def test_postmerge_change_request_blocks_publication(self):
        reviews = [
            self.review(10, "APPROVED", login="reviewer", submitted_at="2026-10-18T11:00:00Z"),
            self.review(11, "CHANGES_REQUESTED", login="reviewer", submitted_at="2026-10-18T13:00:00Z"),
        ]
        self.assertFalse(independent_approval_is_current(reviews, "Arvin-liu", self.head_sha, self.merged_at))

    def test_release_workflow_requires_owner_for_dispatch_and_rerun(self):
        workflow = Path(__file__).resolve().parents[2] / ".github/workflows/component-release.yml"
        source = workflow.read_text(encoding="utf-8")
        self.assertIn("DISPATCH_ACTOR: ${{ github.actor }}", source)
        self.assertIn("TRIGGERING_ACTOR: ${{ github.triggering_actor || github.actor }}", source)
        self.assertIn('os.environ["DISPATCH_ACTOR"].casefold() != owner', source)
        self.assertIn('os.environ["TRIGGERING_ACTOR"].casefold() != owner', source)
        self.assertIn("current_independent_approvals(", source)
        self.assertIn('reviews, pr.get("user", {}).get("login", ""), head_sha, pr.get("merged_at")', source)
        self.assertIn("authorization_pr_merged_at", source)
        self.assertIn("AUTHORIZATION_ACTOR", source)
        self.assertIn("authorization_pr_head_sha", source)
        self.assertIn("AUTHORIZATION_EVIDENCE_FILE", source)


if __name__ == "__main__":
    unittest.main()
