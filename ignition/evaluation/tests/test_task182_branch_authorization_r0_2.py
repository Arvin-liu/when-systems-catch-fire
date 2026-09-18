from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from evaluation.tools import task_branch_guard_r0_2 as guard  # noqa: E402


LOGIN = "Arvin-liu"
EMAIL = "49422864+Arvin-liu@users.noreply.github.com"
REPO_URL = "https://github.com/Arvin-liu/when-systems-catch-fire.git"
TASK_ID = "IGNITION-20260918-182-R2"
SUCCESSOR_BRANCH = "work/IGNITION-20260918-182-r2-heldout-successor-r0-2-retry"
BUILDER_BRANCH = "work/IGNITION-20260917-181-cognitive-inheritance-r0-1-isolation-protocol"
HISTORICAL_TRIAL_BRANCH = "work/IGNITION-20260917-182-heldout-successor-r0-1-trial"


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return result.stdout.strip()


class Task182BranchAuthorizationR02Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        run_git(self.root, "init", "--initial-branch=main")
        run_git(self.root, "config", "--local", "user.name", LOGIN)
        run_git(self.root, "config", "--local", "user.email", EMAIL)
        (self.root / "ignition").mkdir()
        (self.root / "ignition" / "AI-START-HERE.md").write_text("fixture marker\n", encoding="utf-8")
        run_git(self.root, "add", "ignition/AI-START-HERE.md")
        run_git(self.root, "commit", "-m", "fixture base")
        self.base = run_git(self.root, "rev-parse", "HEAD")
        run_git(self.root, "checkout", "-b", SUCCESSOR_BRANCH)
        (self.root / "successor.txt").write_text("fixture successor branch\n", encoding="utf-8")
        run_git(self.root, "add", "successor.txt")
        run_git(self.root, "commit", "-m", "fixture successor output")
        run_git(self.root, "remote", "add", "origin", REPO_URL)
        run_git(self.root, "remote", "set-url", "--push", "origin", REPO_URL)
        run_git(self.root, "config", "--local", "core.hooksPath", guard.HOOKS_PATH)
        run_git(self.root, "config", "--local", f"branch.{SUCCESSOR_BRANCH}.pushRemote", "origin")
        run_git(self.root, "config", "--local", "push.default", "current")
        self.receipt = self.make_receipt()
        self.write_receipt(self.receipt)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def make_receipt(
        self,
        *,
        task_id: str = TASK_ID,
        branch: str = SUCCESSOR_BRANCH,
        base: str | None = None,
        email: str = EMAIL,
    ) -> dict:
        return {
            "schema_version": "task-branch-authorization-r0.2",
            "authority": {
                "source_kind": "TEST_FIXTURE",
                "command_repository_full_name": "fixture/control",
                "command_path": "fixture/task.md",
                "command_ref": "a" * 40,
                "command_blob_sha": "b" * 40,
            },
            "repository_full_name": "Arvin-liu/when-systems-catch-fire",
            "task_id": task_id,
            "authorized_base_head": base or self.base,
            "authorized_branch": branch,
            "expected_push_remote": "origin",
            "expected_push_url": REPO_URL,
            "public_noreply_identity": {"login": LOGIN, "email": email},
            "allowed_operation_class": "TASK_BRANCH_COMMIT_AND_PUSH",
        }

    def write_receipt(self, receipt: dict) -> None:
        path = self.root / ".git" / "ignition" / "task-authorization.json"
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        path.write_text(json.dumps(receipt), encoding="utf-8")
        path.chmod(0o600)

    def pre_push(self, *, remote: str = "origin", url: str = REPO_URL, target: str | None = None) -> str:
        head = run_git(self.root, "rev-parse", "HEAD")
        ref = target or f"refs/heads/{SUCCESSOR_BRANCH}"
        stdin = f"refs/heads/{SUCCESSOR_BRANCH} {head} {ref} {'0' * 40}\n"
        return guard.check_pre_push(self.root, remote, url, stdin)

    def test_authorized_successor_branch_noreply_identity_and_remote_pass(self) -> None:
        self.assertEqual(guard.preflight(self.root, operation="COMMIT"), guard.PASS)
        self.assertEqual(self.pre_push(), guard.PASS)

    def test_task181_builder_branch_is_not_authorized_for_future_successor(self) -> None:
        run_git(self.root, "checkout", "-b", BUILDER_BRANCH)
        self.assertEqual(guard.preflight(self.root), "FAIL_BRANCH_UNAUTHORIZED")

    def test_wrong_repository_fails_closed(self) -> None:
        run_git(self.root, "remote", "set-url", "origin", "https://github.com/Arvin-liu/1111.git")
        run_git(self.root, "remote", "set-url", "--push", "origin", "https://github.com/Arvin-liu/1111.git")
        self.assertEqual(guard.preflight(self.root), "FAIL_WRONG_REPOSITORY")

    def test_wrong_remote_name_and_wrong_remote_url_fail_closed(self) -> None:
        self.assertEqual(self.pre_push(remote="upstream"), "FAIL_PUSH_DESTINATION")
        self.assertEqual(self.pre_push(url="https://github.com/Arvin-liu/1111.git"), "FAIL_PUSH_DESTINATION")

    def test_private_email_fails_closed(self) -> None:
        run_git(self.root, "config", "--local", "user.email", "private@example.com")
        self.assertEqual(guard.preflight(self.root), "FAIL_AUTHOR_IDENTITY")

    def test_historical_main_write_fails_closed(self) -> None:
        run_git(self.root, "checkout", "main")
        self.assertEqual(guard.preflight(self.root), "FAIL_BRANCH_UNAUTHORIZED")

    def test_historical_task182_trial_branch_write_fails_closed(self) -> None:
        run_git(self.root, "checkout", "-b", HISTORICAL_TRIAL_BRANCH)
        self.assertEqual(guard.preflight(self.root), "FAIL_BRANCH_UNAUTHORIZED")

    def test_unapproved_push_ref_fails_closed(self) -> None:
        self.assertEqual(self.pre_push(target="refs/heads/main"), "FAIL_PUSH_DESTINATION")

    def test_non_ancestor_remote_update_is_rejected(self) -> None:
        unrelated = "c" * 40
        head = run_git(self.root, "rev-parse", "HEAD")
        stdin = f"HEAD {head} refs/heads/{SUCCESSOR_BRANCH} {unrelated}\n"
        self.assertEqual(guard.check_pre_push(self.root, "origin", REPO_URL, stdin), "FAIL_FORCE_PUSH")

    def test_wrong_base_head_fails_closed(self) -> None:
        receipt = self.make_receipt(base="d" * 40)
        self.write_receipt(receipt)
        self.assertEqual(guard.preflight(self.root), "FAIL_BASE_ANCESTRY")

    def test_r2_receipt_cannot_authorize_a_task181_branch_name(self) -> None:
        receipt = self.make_receipt(branch=BUILDER_BRANCH)
        self.assertFalse(guard._validate_authorization(receipt))

    def test_missing_or_permissive_receipt_fails_closed(self) -> None:
        path = self.root / ".git" / "ignition" / "task-authorization.json"
        path.unlink()
        self.assertEqual(guard.preflight(self.root), "FAIL_AUTHORIZATION_RECEIPT")
        self.write_receipt(self.receipt)
        path.chmod(0o666)
        self.assertEqual(guard.preflight(self.root), "FAIL_AUTHORIZATION_RECEIPT")

    def test_changed_hooks_path_fails_closed(self) -> None:
        run_git(self.root, "config", "--local", "core.hooksPath", "/dev/null")
        self.assertEqual(guard.preflight(self.root), "FAIL_HOOK_CONFIGURATION")


if __name__ == "__main__":
    unittest.main()
