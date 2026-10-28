from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

IGNITION_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = IGNITION_ROOT.parent
sys.path.insert(0, str(IGNITION_ROOT))

from evaluation.tools import task_branch_guard_r0_3 as guard  # noqa: E402


LOGIN = "Arvin-liu"
EMAIL = "49422864+Arvin-liu@users.noreply.github.com"
REPO_URL = "https://github.com/Arvin-liu/when-systems-catch-fire.git"
TASK_ID = "IGNITION-20260918-182-R3"
SUCCESSOR_BRANCH = "work/IGNITION-20260918-182-r3-r0-3-heldout-trial"
TASK181_BUILDER_BRANCH = "work/IGNITION-20260917-181-cognitive-inheritance-r0-1-isolation-protocol"


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return result.stdout.strip()


class Task187R03AuthorizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="task187-r0-3-auth-")
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        run_git(self.root, "init", "--initial-branch=main")
        run_git(self.root, "config", "--local", "user.name", LOGIN)
        run_git(self.root, "config", "--local", "user.email", EMAIL)
        marker = self.root / "ignition" / "AI-START-HERE.md"
        marker.parent.mkdir(parents=True)
        marker.write_text("synthetic repository marker\n", encoding="utf-8")
        run_git(self.root, "add", "ignition/AI-START-HERE.md")
        run_git(self.root, "commit", "-m", "synthetic base")
        self.base = run_git(self.root, "rev-parse", "HEAD")

        run_git(self.root, "checkout", "-b", SUCCESSOR_BRANCH)
        (self.root / "synthetic-output.txt").write_text("synthetic output\n", encoding="utf-8")
        run_git(self.root, "add", "synthetic-output.txt")
        run_git(self.root, "commit", "-m", "synthetic successor output")
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
            "schema_version": "task-branch-authorization-r0.3",
            "authority": {
                "source_kind": "TEST_FIXTURE",
                "command_repository_full_name": "synthetic/control",
                "command_path": "synthetic/task.md",
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

    def receipt_path(self) -> Path:
        return self.root / ".git" / "ignition" / "task-authorization.json"

    def write_receipt(self, receipt: dict) -> None:
        path = self.receipt_path()
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        path.write_text(json.dumps(receipt), encoding="utf-8")
        path.chmod(0o600)

    def pre_push(self, *, remote: str = "origin", url: str = REPO_URL, target: str | None = None) -> str:
        head = run_git(self.root, "rev-parse", "HEAD")
        ref = target or f"refs/heads/{SUCCESSOR_BRANCH}"
        stdin = f"refs/heads/{SUCCESSOR_BRANCH} {head} {ref} {'0' * 40}\n"
        return guard.check_pre_push(self.root, remote, url, stdin)

    def test_authorized_task_branch_identity_remote_and_pre_push_pass(self) -> None:
        self.assertEqual(guard.preflight(self.root, operation="CHECK"), guard.PASS)
        self.assertEqual(guard.preflight(self.root, operation="COMMIT"), guard.PASS)
        self.assertEqual(self.pre_push(), guard.PASS)

    def test_owner_authorization_installs_private_receipt_and_versioned_hooks(self) -> None:
        self.receipt_path().unlink()
        authorization_file = Path(self.temp.name) / "owner-authorized-receipt.json"
        authorization_file.write_text(json.dumps(self.receipt), encoding="utf-8")

        self.assertEqual(guard.install_authorization(self.root, authorization_file), guard.PASS)
        self.assertEqual(self.receipt_path().stat().st_mode & 0o777, 0o600)
        self.assertEqual(run_git(self.root, "config", "--local", "--get", "core.hooksPath"), guard.HOOKS_PATH)
        self.assertEqual(
            run_git(self.root, "config", "--local", "--get", f"branch.{SUCCESSOR_BRANCH}.pushRemote"),
            "origin",
        )

    def test_wrong_repository_fails_closed(self) -> None:
        run_git(self.root, "remote", "set-url", "origin", "https://github.com/Arvin-liu/1111.git")
        run_git(self.root, "remote", "set-url", "--push", "origin", "https://github.com/Arvin-liu/1111.git")
        self.assertEqual(guard.preflight(self.root), "FAIL_WRONG_REPOSITORY")

    def test_wrong_remote_name_and_url_fail_closed(self) -> None:
        self.assertEqual(self.pre_push(remote="upstream"), "FAIL_PUSH_DESTINATION")
        self.assertEqual(self.pre_push(url="https://github.com/Arvin-liu/1111.git"), "FAIL_PUSH_DESTINATION")

    def test_private_email_fails_closed(self) -> None:
        run_git(self.root, "config", "--local", "user.email", "private@example.com")
        self.assertEqual(guard.preflight(self.root), "FAIL_AUTHOR_IDENTITY")

    def test_wrong_task_branch_and_main_fail_closed(self) -> None:
        run_git(self.root, "checkout", "-b", TASK181_BUILDER_BRANCH)
        self.assertEqual(guard.preflight(self.root), "FAIL_BRANCH_UNAUTHORIZED")
        run_git(self.root, "checkout", "main")
        self.assertEqual(guard.preflight(self.root), "FAIL_BRANCH_UNAUTHORIZED")

    def test_wrong_base_head_fails_closed(self) -> None:
        self.write_receipt(self.make_receipt(base="d" * 40))
        self.assertEqual(guard.preflight(self.root), "FAIL_BASE_ANCESTRY")

    def test_unapproved_ref_and_non_fast_forward_update_are_rejected(self) -> None:
        self.assertEqual(self.pre_push(target="refs/heads/main"), "FAIL_PUSH_DESTINATION")
        head = run_git(self.root, "rev-parse", "HEAD")
        stdin = f"HEAD {head} refs/heads/{SUCCESSOR_BRANCH} {'c' * 40}\n"
        self.assertEqual(guard.check_pre_push(self.root, "origin", REPO_URL, stdin), "FAIL_FORCE_PUSH")

    def test_changed_hook_path_fails_closed(self) -> None:
        run_git(self.root, "config", "--local", "core.hooksPath", "/dev/null")
        self.assertEqual(guard.preflight(self.root), "FAIL_HOOK_CONFIGURATION")

    def test_missing_permissive_or_wrong_version_receipt_fails_closed(self) -> None:
        path = self.receipt_path()
        path.unlink()
        self.assertEqual(guard.preflight(self.root), "FAIL_AUTHORIZATION_RECEIPT")

        self.write_receipt(self.receipt)
        path.chmod(0o666)
        self.assertEqual(guard.preflight(self.root), "FAIL_AUTHORIZATION_RECEIPT")

        self.write_receipt({**self.receipt, "schema_version": "task-branch-authorization-r0.2"})
        self.assertEqual(guard.preflight(self.root), "FAIL_AUTHORIZATION_RECEIPT")

    def test_untracked_evidence_and_status_staging_do_not_change_cognitive_disposition(self) -> None:
        evidence = self.root / "synthetic-evidence.json"
        ledger = self.root / "synthetic-ledger.json"
        cognitive_marker = self.root / "cognitive-disposition.txt"
        evidence.write_text('{"evidence":"synthetic"}\n', encoding="utf-8")
        ledger.write_text('{"trial_disposition":"CLEAN","entries":[]}\n', encoding="utf-8")
        cognitive_marker.write_text("CLEAN\n", encoding="utf-8")
        self.assertEqual(guard.preflight(self.root, operation="COMMIT"), "FAIL_UNEXPLAINED_WORKTREE")

        run_git(self.root, "add", "synthetic-evidence.json", "synthetic-ledger.json", "cognitive-disposition.txt")
        self.assertEqual(guard.preflight(self.root, operation="COMMIT"), guard.PASS)
        ledger.write_text(
            '{"trial_disposition":"CLEAN","entries":[{"status":"PASS_BRANCH_AUTHORIZED"}]}\n',
            encoding="utf-8",
        )
        self.assertEqual(guard.preflight(self.root, operation="COMMIT"), "FAIL_UNEXPLAINED_WORKTREE")
        run_git(self.root, "add", "synthetic-ledger.json")
        self.assertEqual(guard.preflight(self.root, operation="COMMIT"), guard.PASS)
        self.assertEqual(json.loads(ledger.read_bytes())["trial_disposition"], "CLEAN")
        self.assertEqual(cognitive_marker.read_text(encoding="utf-8"), "CLEAN\n")

    def test_r0_3_auth_schema_only_versions_the_r0_2_boundary(self) -> None:
        old_path = IGNITION_ROOT / "evaluation/operational-control/r0.2/task-branch-authorization-r0.2.schema.json"
        new_path = IGNITION_ROOT / "evaluation/operational-control/r0.3/task-branch-authorization-r0.3.schema.json"
        old = json.loads(old_path.read_text(encoding="utf-8"))
        new = json.loads(new_path.read_text(encoding="utf-8"))
        old["$id"] = new["$id"]
        old["title"] = new["title"]
        old["properties"]["schema_version"]["const"] = "task-branch-authorization-r0.3"
        self.assertEqual(new, old)
        self.assertEqual(guard.HOOKS_PATH, "ignition/evaluation/hooks/r0.3")
        for hook in ("pre-commit", "pre-push"):
            hook_path = REPO_ROOT / "ignition/evaluation/hooks/r0.3" / hook
            self.assertTrue(hook_path.stat().st_mode & 0o111)
            self.assertIn("task_branch_guard_r0_3.py", hook_path.read_text(encoding="utf-8"))
            self.assertNotIn("legacy_guard", hook_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
