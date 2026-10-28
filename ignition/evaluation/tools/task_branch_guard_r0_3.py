#!/usr/bin/env python3
"""Task-scoped, fail-closed local branch guard for Evaluation Plane R0.3."""
from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any


IGNITION_ROOT = Path(__file__).resolve().parents[2]
REPO_MARKER = "ignition/AI-START-HERE.md"
AUTH_SCHEMA = IGNITION_ROOT / "evaluation" / "operational-control" / "r0.3" / "task-branch-authorization-r0.3.schema.json"
HOOKS_PATH = "ignition/evaluation/hooks/r0.3"
PASS = "PASS_BRANCH_AUTHORIZED"
STATUS_CODES = (
    PASS,
    "FAIL_WRONG_REPOSITORY",
    "FAIL_WRONG_REMOTE",
    "FAIL_BRANCH_UNAUTHORIZED",
    "FAIL_BASE_ANCESTRY",
    "FAIL_AUTHOR_IDENTITY",
    "FAIL_PUSH_DESTINATION",
    "FAIL_FORCE_PUSH",
    "FAIL_HOOK_CONFIGURATION",
    "FAIL_UNEXPLAINED_WORKTREE",
    "FAIL_AUTHORIZATION_RECEIPT",
)


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


def repo_root(candidate: Path | None = None) -> Path | None:
    result = git((candidate or Path.cwd()).resolve(), "rev-parse", "--show-toplevel", check=False)
    return Path(result.stdout.strip()).resolve() if result.returncode == 0 else None


def git_directory(root: Path) -> Path | None:
    result = git(root, "rev-parse", "--git-dir", check=False)
    if result.returncode != 0:
        return None
    path = Path(result.stdout.strip())
    return (root / path).resolve() if not path.is_absolute() else path.resolve()


def authorization_path(root: Path) -> Path | None:
    git_dir = git_directory(root)
    return git_dir / "ignition" / "task-authorization.json" if git_dir else None


def _validate_authorization(receipt: dict[str, Any]) -> bool:
    try:
        import jsonschema

        schema = json.loads(AUTH_SCHEMA.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        errors = list(jsonschema.Draft202012Validator(schema).iter_errors(receipt))
        if errors:
            return False
    except (ImportError, OSError, json.JSONDecodeError, ValueError):
        return False
    task_id = receipt["task_id"]
    task_prefix = task_id.replace("-R", "-r")
    branch = receipt["authorized_branch"]
    return branch.startswith(f"work/{task_prefix}-")


def load_authorization(root: Path) -> dict[str, Any] | None:
    path = authorization_path(root)
    if path is None or path.is_symlink() or not path.is_file():
        return None
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
        if mode & 0o022 or path.stat().st_size > 16384:
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) and _validate_authorization(value) else None


def _single_remote_url(root: Path, remote: str, *, push: bool) -> str | None:
    args = ["remote", "get-url", "--all"]
    if push:
        args.insert(2, "--push")
    args.append(remote)
    result = git(root, *args, check=False)
    if result.returncode != 0:
        return None
    values = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return values[0] if len(values) == 1 else None


def _identity_email(root: Path, kind: str) -> str | None:
    result = git(root, "var", f"GIT_{kind}_IDENT", check=False)
    if result.returncode != 0:
        return None
    match = re.search(r"<([^>]+)>", result.stdout)
    return match.group(1) if match else None


def _failure_worktree(root: Path) -> bool:
    status = git(root, "status", "--porcelain=v1", "--untracked-files=all", check=False)
    if status.returncode != 0:
        return True
    for line in status.stdout.splitlines():
        if len(line) < 2 or "?" in line[:2] or line[1] != " ":
            return True
    return False


def _preflight_with_authorization(
    root: Path,
    receipt: dict[str, Any],
    *,
    require_installation: bool = True,
    require_push_config: bool = True,
) -> str:
    top = repo_root(root)
    if top is None:
        return "FAIL_WRONG_REPOSITORY"
    marker = top / REPO_MARKER
    marker_tracked = git(top, "ls-files", "--error-unmatch", REPO_MARKER, check=False)
    if not marker.is_file() or marker_tracked.returncode != 0:
        return "FAIL_WRONG_REPOSITORY"

    expected_repository = receipt["repository_full_name"].casefold()
    origin = _single_remote_url(top, "origin", push=False)
    push_url = _single_remote_url(top, receipt["expected_push_remote"], push=True)
    if origin is None or repository_id(origin) != expected_repository:
        return "FAIL_WRONG_REPOSITORY" if repository_id(origin or "") == "arvin-liu/1111" else "FAIL_WRONG_REMOTE"
    if push_url != receipt["expected_push_url"] or repository_id(push_url or "") != expected_repository:
        return "FAIL_WRONG_REMOTE"

    branch_result = git(top, "branch", "--show-current", check=False)
    branch = branch_result.stdout.strip()
    if branch_result.returncode != 0 or branch != receipt["authorized_branch"] or branch in {"main", "master"}:
        return "FAIL_BRANCH_UNAUTHORIZED"
    base = receipt["authorized_base_head"]
    if git(top, "cat-file", "-e", f"{base}^{{commit}}", check=False).returncode != 0:
        return "FAIL_BASE_ANCESTRY"
    if git(top, "merge-base", "--is-ancestor", base, "HEAD", check=False).returncode != 0:
        return "FAIL_BASE_ANCESTRY"

    identity = receipt["public_noreply_identity"]
    local_name = git(top, "config", "--local", "--get", "user.name", check=False)
    local_email = git(top, "config", "--local", "--get", "user.email", check=False)
    if (
        local_name.returncode != 0
        or local_email.returncode != 0
        or local_name.stdout.strip() != identity["login"]
        or local_email.stdout.strip() != identity["email"]
        or _identity_email(top, "AUTHOR") != identity["email"]
        or _identity_email(top, "COMMITTER") != identity["email"]
    ):
        return "FAIL_AUTHOR_IDENTITY"

    if require_installation:
        hooks = git(top, "config", "--local", "--get", "core.hooksPath", check=False)
        if hooks.returncode != 0 or hooks.stdout.strip() != HOOKS_PATH:
            return "FAIL_HOOK_CONFIGURATION"
    if require_push_config:
        configured_remote = git(top, "config", "--local", "--get", f"branch.{branch}.pushRemote", check=False)
        push_default = git(top, "config", "--local", "--get", "push.default", check=False)
        if configured_remote.returncode != 0 or configured_remote.stdout.strip() != receipt["expected_push_remote"]:
            return "FAIL_PUSH_DESTINATION"
        if push_default.returncode != 0 or push_default.stdout.strip() != "current":
            return "FAIL_PUSH_DESTINATION"
        refspecs = git(top, "config", "--local", "--get-all", f"remote.{receipt['expected_push_remote']}.push", check=False)
        if refspecs.returncode == 0:
            allowed = {
                f"HEAD:refs/heads/{branch}",
                f"refs/heads/{branch}:refs/heads/{branch}",
            }
            if any(item.strip() not in allowed for item in refspecs.stdout.splitlines()):
                return "FAIL_PUSH_DESTINATION"
    if _failure_worktree(top):
        return "FAIL_UNEXPLAINED_WORKTREE"
    return PASS


def preflight(root: Path | None = None, *, operation: str = "CHECK") -> str:
    candidate = (root or Path.cwd()).resolve()
    top = repo_root(candidate)
    if top is None:
        return "FAIL_WRONG_REPOSITORY"
    receipt = load_authorization(top)
    if receipt is None:
        return "FAIL_AUTHORIZATION_RECEIPT"
    if operation not in {"CHECK", "COMMIT", "PUSH"} or receipt.get("allowed_operation_class") != "TASK_BRANCH_COMMIT_AND_PUSH":
        return "FAIL_PUSH_DESTINATION"
    return _preflight_with_authorization(top, receipt)


def check_pre_push(root: Path, remote_name: str, remote_url: str, stdin: str) -> str:
    candidate = root.resolve()
    top = repo_root(candidate)
    if top is None:
        return "FAIL_WRONG_REPOSITORY"
    receipt = load_authorization(top)
    if receipt is None:
        return "FAIL_AUTHORIZATION_RECEIPT"
    status = _preflight_with_authorization(top, receipt)
    if status != PASS:
        return status
    if remote_name != receipt["expected_push_remote"] or remote_url != receipt["expected_push_url"]:
        return "FAIL_PUSH_DESTINATION"
    rows = [line.split() for line in stdin.splitlines() if line.strip()]
    if len(rows) != 1 or len(rows[0]) != 4:
        return "FAIL_PUSH_DESTINATION"
    local_ref, local_sha, remote_ref, remote_sha = rows[0]
    branch = receipt["authorized_branch"]
    expected_ref = f"refs/heads/{branch}"
    head = git(top, "rev-parse", "HEAD", check=False)
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
        return "FAIL_PUSH_DESTINATION"
    if remote_sha and not remote_is_new:
        ancestor = git(top, "merge-base", "--is-ancestor", remote_sha, local_sha, check=False)
        if ancestor.returncode != 0:
            return "FAIL_FORCE_PUSH"
    return PASS


def install_authorization(root: Path, authorization_file: Path) -> str:
    top = repo_root(root.resolve())
    if top is None:
        return "FAIL_WRONG_REPOSITORY"
    try:
        receipt = json.loads(authorization_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return "FAIL_AUTHORIZATION_RECEIPT"
    if not isinstance(receipt, dict) or not _validate_authorization(receipt):
        return "FAIL_AUTHORIZATION_RECEIPT"
    status = _preflight_with_authorization(top, receipt, require_installation=False, require_push_config=False)
    if status != PASS:
        return status

    target = authorization_path(top)
    if target is None:
        return "FAIL_AUTHORIZATION_RECEIPT"
    if target.exists() or target.is_symlink():
        return "FAIL_AUTHORIZATION_RECEIPT"
    try:
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(receipt, stream, ensure_ascii=False, sort_keys=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        for args in (
            ("config", "--local", "--replace-all", "core.hooksPath", HOOKS_PATH),
            ("config", "--local", "--replace-all", f"branch.{receipt['authorized_branch']}.pushRemote", receipt["expected_push_remote"]),
            ("config", "--local", "--replace-all", "push.default", "current"),
        ):
            if git(top, *args, check=False).returncode != 0:
                return "FAIL_HOOK_CONFIGURATION"
    except OSError:
        return "FAIL_AUTHORIZATION_RECEIPT"
    return preflight(top, operation="CHECK")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operation", choices=["CHECK", "COMMIT", "PUSH"], default="CHECK")
    parser.add_argument("--remote")
    parser.add_argument("--url")
    parser.add_argument("--install-authorization", type=Path)
    args = parser.parse_args(argv)
    root = repo_root(Path.cwd())
    if root is None:
        status = "FAIL_WRONG_REPOSITORY"
    elif args.install_authorization:
        status = install_authorization(root, args.install_authorization.resolve())
    elif args.operation == "PUSH":
        status = check_pre_push(root, args.remote or "", args.url or "", sys.stdin.read())
    else:
        status = preflight(root, operation=args.operation)
    if status != PASS:
        print(status, file=sys.stderr)
        return 1
    print(status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
