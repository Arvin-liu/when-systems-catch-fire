#!/usr/bin/env python3
"""Fail-closed Task181 repository, identity, worktree and push preflight."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


TARGET_REPOSITORY = "Arvin-liu/when-systems-catch-fire"
TASK_BRANCH = "work/IGNITION-20260917-181-cognitive-inheritance-r0-1-isolation-protocol"
ALLOWED_NAME = "Arvin-liu"
ALLOWED_EMAIL = "49422864+Arvin-liu@users.noreply.github.com"
PROTECTED_BRANCHES = {
    "main",
    "work/IGNITION-20260912-172-knowledge-routing-universal-corpus",
    "work/IGNITION-20260916-179-cognitive-inheritance-evolution-r0",
    "eval/IGNITION-20260917-180-cognitive-inheritance-r0-independent-evaluation",
}


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "git command failed")
    return result


def repository_id(url: str) -> str | None:
    value = url.strip()
    match = re.fullmatch(r"(?:[^@]+@)?([^:/]+):([^:]+)", value)
    if match and "." in match.group(1):
        host, path = match.groups()
    else:
        match = re.fullmatch(r"(?:https?|ssh)://(?:[^@/]+@)?([^/]+)/(.+)", value)
        if not match:
            return None
        host, path = match.groups()
    if host.casefold() != "github.com":
        return None
    path = path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    parts = path.split("/")
    if len(parts) != 2 or not all(parts):
        return None
    return f"{parts[0]}/{parts[1]}".casefold()


def identity_email(root: Path, kind: str) -> str | None:
    result = git(root, "var", f"GIT_{kind}_IDENT", check=False)
    if result.returncode != 0:
        return None
    match = re.search(r"<([^>]+)>", result.stdout)
    return match.group(1) if match else None


def preflight(
    root: Path | None = None,
    *,
    expected_repository: str = TARGET_REPOSITORY,
    task_branch: str = TASK_BRANCH,
    push_remote: str = "origin",
    push_branch: str = TASK_BRANCH,
    require_push_config: bool = True,
) -> list[str]:
    """Return stable failure codes; an empty list means the assertion passed."""
    candidate = (root or Path.cwd()).resolve()
    top = git(candidate, "rev-parse", "--show-toplevel", check=False)
    if top.returncode != 0:
        return ["FAIL_WRONG_REPOSITORY"]
    repo_root = Path(top.stdout.strip()).resolve()

    marker = repo_root / "ignition" / "AI-START-HERE.md"
    tracked_marker = git(repo_root, "ls-files", "--error-unmatch", "ignition/AI-START-HERE.md", check=False)
    if not marker.is_file() or tracked_marker.returncode != 0:
        return ["FAIL_WRONG_REPOSITORY"]

    origin = git(repo_root, "remote", "get-url", "origin", check=False)
    if origin.returncode != 0:
        return ["FAIL_WRONG_REMOTE"]
    origin_id = repository_id(origin.stdout)
    if origin_id == "arvin-liu/1111":
        return ["FAIL_WRONG_REPOSITORY"]
    if origin_id != expected_repository.casefold():
        return ["FAIL_WRONG_REMOTE"]
    push_url = git(repo_root, "remote", "get-url", "--push", "origin", check=False)
    if push_url.returncode != 0 or repository_id(push_url.stdout) != expected_repository.casefold():
        return ["FAIL_WRONG_REMOTE"]

    branch_result = git(repo_root, "branch", "--show-current", check=False)
    branch = branch_result.stdout.strip()
    if branch in PROTECTED_BRANCHES:
        return ["FAIL_PROTECTED_BRANCH"]
    if branch_result.returncode != 0 or branch != task_branch:
        return ["FAIL_TASK_BRANCH_MISMATCH"]

    local_name = git(repo_root, "config", "--local", "--get", "user.name", check=False)
    local_email = git(repo_root, "config", "--local", "--get", "user.email", check=False)
    if (
        local_name.returncode != 0
        or local_email.returncode != 0
        or local_name.stdout.strip() != ALLOWED_NAME
        or local_email.stdout.strip() != ALLOWED_EMAIL
        or identity_email(repo_root, "AUTHOR") != ALLOWED_EMAIL
        or identity_email(repo_root, "COMMITTER") != ALLOWED_EMAIL
    ):
        return ["FAIL_AUTHOR_IDENTITY_BEFORE_COMMIT"]

    if push_branch != task_branch or push_remote != "origin":
        return ["FAIL_PUSH_DESTINATION"]
    if require_push_config:
        configured_push_remote = git(repo_root, "config", "--local", "--get", f"branch.{task_branch}.pushRemote", check=False)
        push_default = git(repo_root, "config", "--local", "--get", "push.default", check=False)
        if configured_push_remote.returncode != 0 or configured_push_remote.stdout.strip() != push_remote:
            return ["FAIL_PUSH_DESTINATION"]
        if push_default.returncode != 0 or push_default.stdout.strip() != "current":
            return ["FAIL_PUSH_DESTINATION"]
        refspecs = git(repo_root, "config", "--local", "--get-all", "remote.origin.push", check=False)
        if refspecs.returncode == 0:
            valid = {f"HEAD:refs/heads/{task_branch}", f"refs/heads/{task_branch}:refs/heads/{task_branch}"}
            if any(item.strip() not in valid for item in refspecs.stdout.splitlines()):
                return ["FAIL_PUSH_DESTINATION"]

    status = git(repo_root, "status", "--porcelain=v1", "--untracked-files=all", check=False)
    if status.returncode != 0:
        return ["FAIL_UNEXPLAINED_WORKTREE"]
    for line in status.stdout.splitlines():
        state = line[:2]
        if "?" in state or len(state) < 2 or state[1] != " ":
            return ["FAIL_UNEXPLAINED_WORKTREE"]
    return []


def install_hooks(root: Path | None = None) -> list[str]:
    candidate = (root or Path.cwd()).resolve()
    failures = preflight(candidate, require_push_config=False)
    if failures:
        return failures
    top = Path(git(candidate, "rev-parse", "--show-toplevel").stdout.strip()).resolve()
    commands = [
        ("config", "--local", f"branch.{TASK_BRANCH}.pushRemote", "origin"),
        ("config", "--local", "push.default", "current"),
        ("config", "--local", "core.hooksPath", "ignition/evaluation/hooks"),
    ]
    for args in commands:
        result = git(top, *args, check=False)
        if result.returncode != 0:
            return ["FAIL_PUSH_DESTINATION"]
    return preflight(top)


def check_pre_push(root: Path, remote_name: str, remote_url: str, stdin: str) -> list[str]:
    failures = preflight(root)
    if failures:
        return failures
    if remote_name != "origin" or repository_id(remote_url) != TARGET_REPOSITORY.casefold():
        return ["FAIL_PUSH_DESTINATION"]
    rows = [line.split() for line in stdin.splitlines() if line.strip()]
    if len(rows) != 1 or len(rows[0]) != 4:
        return ["FAIL_PUSH_DESTINATION"]
    local_ref, local_sha, remote_ref, remote_sha = rows[0]
    expected_ref = f"refs/heads/{TASK_BRANCH}"
    head = git(root, "rev-parse", "HEAD", check=False)
    remote_is_new = bool(remote_sha) and set(remote_sha) == {"0"}
    if (
        remote_ref != expected_ref
        or local_ref not in {"HEAD", expected_ref}
        or head.returncode != 0
        or local_sha != head.stdout.strip()
        or not re.fullmatch(r"[0-9a-f]{40,64}", local_sha)
        or (remote_sha and not re.fullmatch(r"[0-9a-f]{40,64}", remote_sha))
        or set(local_sha) == {"0"}
    ):
        return ["FAIL_PUSH_DESTINATION"]
    if remote_sha and not remote_is_new:
        ancestor = git(root, "merge-base", "--is-ancestor", remote_sha, local_sha, check=False)
        if ancestor.returncode != 0:
            return ["FAIL_FORCE_PUSH"]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install-hooks", action="store_true")
    parser.add_argument("--pre-push", nargs=2, metavar=("REMOTE", "URL"))
    args = parser.parse_args(argv)
    if args.install_hooks:
        failures = install_hooks()
    elif args.pre_push:
        failures = check_pre_push(Path.cwd(), args.pre_push[0], args.pre_push[1], sys.stdin.read())
    else:
        failures = preflight()
    if failures:
        for code in failures:
            print(code, file=sys.stderr)
        return 1
    print("TARGET_REPOSITORY_PREFLIGHT_R0_1=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
