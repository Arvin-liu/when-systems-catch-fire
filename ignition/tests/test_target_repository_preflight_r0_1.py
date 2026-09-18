from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evaluation.tools import target_repository_preflight_r0_1 as guard  # noqa: E402


TASK_BRANCH = guard.TASK_BRANCH
TARGET_URL = "https://github.com/Arvin-liu/when-systems-catch-fire.git"


def run_git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    if check and result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return result


def make_repo(root: Path, *, origin: str = TARGET_URL, branch: str = TASK_BRANCH) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    run_git(root, "init", "-q", "-b", branch)
    (root / "ignition/evaluation/tools").mkdir(parents=True)
    (root / "ignition/evaluation/hooks").mkdir(parents=True)
    (root / "ignition/AI-START-HERE.md").write_text("fixture marker\n", encoding="utf-8")
    shutil.copy2(ROOT / "evaluation/tools/target_repository_preflight_r0_1.py", root / "ignition/evaluation/tools/target_repository_preflight_r0_1.py")
    shutil.copy2(ROOT / "evaluation/hooks/pre-commit", root / "ignition/evaluation/hooks/pre-commit")
    run_git(root, "config", "--local", "user.name", guard.ALLOWED_NAME)
    run_git(root, "config", "--local", "user.email", guard.ALLOWED_EMAIL)
    run_git(root, "add", "ignition/AI-START-HERE.md", "ignition/evaluation")
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_AUTHOR_") and not key.startswith("GIT_COMMITTER_")}
    subprocess.run(["git", "commit", "-q", "-m", "fixture base"], cwd=root, env=env, check=True)
    run_git(root, "remote", "add", "origin", origin)
    run_git(root, "config", "--local", f"branch.{TASK_BRANCH}.pushRemote", "origin")
    run_git(root, "config", "--local", "push.default", "current")
    return root


class TargetRepositoryPreflightR01Tests(unittest.TestCase):
    def test_wrong_authority_repository_fails_as_wrong_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = make_repo(Path(temp) / "1111", origin="https://github.com/Arvin-liu/1111.git")
            self.assertEqual(guard.preflight(root), ["FAIL_WRONG_REPOSITORY"])

    def test_unrelated_origin_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = make_repo(Path(temp) / "other", origin="https://github.com/example/other.git")
            self.assertEqual(guard.preflight(root), ["FAIL_WRONG_REMOTE"])

    def test_frozen_historical_branch_is_protected(self) -> None:
        protected = sorted(guard.PROTECTED_BRANCHES)[0]
        with tempfile.TemporaryDirectory() as temp:
            root = make_repo(Path(temp) / "protected", branch=protected)
            self.assertEqual(guard.preflight(root), ["FAIL_PROTECTED_BRANCH"])

    def test_private_email_fails_before_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = make_repo(Path(temp) / "private-email")
            run_git(root, "config", "--local", "user.email", "private@example.net")
            self.assertEqual(guard.preflight(root), ["FAIL_AUTHOR_IDENTITY_BEFORE_COMMIT"])

    def test_mismatched_push_refspec_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = make_repo(Path(temp) / "wrong-push")
            run_git(root, "config", "--local", "remote.origin.push", "HEAD:refs/heads/main")
            self.assertEqual(guard.preflight(root), ["FAIL_PUSH_DESTINATION"])

    def test_correct_target_and_noreply_identity_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = make_repo(Path(temp) / "good")
            self.assertEqual(guard.preflight(root), [])

    def test_installed_precommit_rejects_private_email_without_creating_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = make_repo(Path(temp) / "hook")
            baseline = run_git(root, "rev-parse", "HEAD").stdout.strip()
            run_git(root, "config", "--local", "core.hooksPath", "ignition/evaluation/hooks")
            (root / "staged.md").write_text("a staged change\n", encoding="utf-8")
            run_git(root, "add", "staged.md")
            run_git(root, "config", "--local", "user.email", "private@example.net")
            attempt = run_git(root, "commit", "-m", "must be blocked", check=False)
            self.assertNotEqual(attempt.returncode, 0)
            self.assertIn("FAIL_AUTHOR_IDENTITY_BEFORE_COMMIT", attempt.stderr)
            self.assertEqual(run_git(root, "rev-parse", "HEAD").stdout.strip(), baseline)

    def test_pre_push_allows_new_branch_but_blocks_wrong_ref(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = make_repo(Path(temp) / "push")
            head = run_git(root, "rev-parse", "HEAD").stdout.strip()
            zeros = "0" * len(head)
            line = f"refs/heads/{TASK_BRANCH} {head} refs/heads/{TASK_BRANCH} {zeros}\n"
            self.assertEqual(guard.check_pre_push(root, "origin", TARGET_URL, line), [])
            wrong = f"refs/heads/{TASK_BRANCH} {head} refs/heads/main {zeros}\n"
            self.assertEqual(guard.check_pre_push(root, "origin", TARGET_URL, wrong), ["FAIL_PUSH_DESTINATION"])


if __name__ == "__main__":
    unittest.main()
