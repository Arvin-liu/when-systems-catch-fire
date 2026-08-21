from __future__ import annotations

import unittest
from unittest.mock import patch

from tools import validate_post_publication_current as checker


class PostPublicationCurrentTests(unittest.TestCase):
    def test_pre_publication_readiness(self) -> None:
        result = checker.run_checks(post_publication=False)
        self.assertEqual(result["result"], "PASS", result["errors"])
        self.assertEqual(result["mode"], "PRE_PUBLICATION")

    @staticmethod
    def _fake_git(*, head: str, remote: str, branch: str = "main", remotes: str = "origin"):
        def run(*args: str) -> str:
            if args == ("remote",):
                return remotes
            if args and args[0] == "fetch":
                return ""
            if args[:2] == ("ls-remote", "origin"):
                return f"{remote}\trefs/heads/main"
            if args == ("branch", "--show-current"):
                return branch
            if args == ("rev-parse", "HEAD"):
                return head
            if args[:1] == ("status",):
                return ""
            raise AssertionError(f"unexpected git probe: {args}")

        return run

    def test_post_publication_requires_expected_remote_and_local_sha_equality(self) -> None:
        candidate = "a" * 40
        remote = "b" * 40
        fake_git = self._fake_git(head=candidate, remote=remote)
        with patch.object(checker, "git", side_effect=fake_git):
            result = checker.run_checks(post_publication=True, expected_sha=candidate)
        self.assertEqual(result["result"], "FAIL")
        self.assertEqual(result["observed_remote_sha"], remote)
        self.assertTrue(any("remote main SHA differs" in error for error in result["errors"]))

    def test_post_publication_passes_only_when_all_three_shas_match(self) -> None:
        candidate = "a" * 40
        fake_git = self._fake_git(head=candidate, remote=candidate)
        with patch.object(checker, "git", side_effect=fake_git):
            result = checker.run_checks(post_publication=True, expected_sha=candidate)
        self.assertEqual(result["result"], "PASS", result["errors"])
        self.assertEqual(result["observed_ref"], "refs/heads/main")
        self.assertEqual(result["head_sha"], result["observed_remote_sha"])

    def test_missing_origin_is_blocked_with_evidence(self) -> None:
        candidate = "a" * 40
        fake_git = self._fake_git(head=candidate, remote=candidate, remotes="")
        with patch.object(checker, "git", side_effect=fake_git):
            result = checker.run_checks(post_publication=True, expected_sha=candidate)
        self.assertEqual(result["result"], "BLOCKED_WITH_EVIDENCE")
        self.assertTrue(any("origin remote is missing" in error for error in result["errors"]))

    def test_detached_head_is_not_an_allowed_post_publication_mode(self) -> None:
        candidate = "a" * 40
        fake_git = self._fake_git(head=candidate, remote=candidate, branch="")
        with patch.object(checker, "git", side_effect=fake_git):
            result = checker.run_checks(post_publication=True, expected_sha=candidate)
        self.assertEqual(result["result"], "FAIL")
        self.assertTrue(any("branch main" in error for error in result["errors"]))

    def test_remote_parser_rejects_missing_or_ambiguous_ref(self) -> None:
        sha = "a" * 40
        self.assertEqual(checker.parse_remote_ref(""), (None, "remote ref observation is ambiguous or missing for refs/heads/main"))
        parsed, error = checker.parse_remote_ref(f"{sha}\trefs/heads/main\n{sha}\trefs/heads/main")
        self.assertIsNone(parsed)
        self.assertIn("ambiguous", error or "")


if __name__ == "__main__":
    unittest.main()
