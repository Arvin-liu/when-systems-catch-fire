from __future__ import annotations

import unittest
from pathlib import Path

from tools.operations.release_authorization import owner_approval_is_current


class ComponentReleaseAuthorizationTest(unittest.TestCase):
    def setUp(self):
        self.head_sha = "a" * 40

    def review(self, review_id, state, *, login="Arvin-liu", commit_id=None):
        return {
            "id": review_id,
            "state": state,
            "user": {"login": login},
            "commit_id": commit_id or self.head_sha,
        }

    def test_current_owner_approval_for_exact_head_is_accepted(self):
        reviews = [self.review(10, "COMMENTED"), self.review(11, "APPROVED")]
        self.assertTrue(owner_approval_is_current(reviews, "arvin-liu", self.head_sha))

    def test_later_owner_change_request_supersedes_prior_approval(self):
        reviews = [self.review(10, "APPROVED"), self.review(11, "CHANGES_REQUESTED")]
        self.assertFalse(owner_approval_is_current(reviews, "Arvin-liu", self.head_sha))

    def test_later_owner_comment_supersedes_prior_approval(self):
        reviews = [self.review(10, "APPROVED"), self.review(11, "COMMENTED")]
        self.assertFalse(owner_approval_is_current(reviews, "Arvin-liu", self.head_sha))

    def test_approval_for_an_older_head_does_not_authorize_release(self):
        old_head = "b" * 40
        reviews = [self.review(10, "APPROVED", commit_id=old_head)]
        self.assertFalse(owner_approval_is_current(reviews, "Arvin-liu", self.head_sha))

    def test_another_reviewers_approval_does_not_substitute_for_owner(self):
        reviews = [self.review(10, "APPROVED", login="reviewer")]
        self.assertFalse(owner_approval_is_current(reviews, "Arvin-liu", self.head_sha))

    def test_release_workflow_requires_owner_for_dispatch_and_rerun(self):
        workflow = Path(__file__).resolve().parents[2] / ".github/workflows/component-release.yml"
        source = workflow.read_text(encoding="utf-8")
        self.assertIn("DISPATCH_ACTOR: ${{ github.actor }}", source)
        self.assertIn("TRIGGERING_ACTOR: ${{ github.triggering_actor || github.actor }}", source)
        self.assertIn('os.environ["DISPATCH_ACTOR"].casefold() != owner', source)
        self.assertIn('os.environ["TRIGGERING_ACTOR"].casefold() != owner', source)


if __name__ == "__main__":
    unittest.main()
