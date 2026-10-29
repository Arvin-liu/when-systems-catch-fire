# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Resolve the R5-A candidate's changed paths against its active PR base.

The R5-A frozen head remains the historical content anchor. When the PR is
integrated with a newer base, inherited base changes must not be attributed to
the R5-A candidate's own scope.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def _git(repo_root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def _pull_request_event_base(event_path: Path | None) -> tuple[str, str] | None:
    if event_path is None or not event_path.is_file():
        return None
    event = json.loads(event_path.read_text(encoding="utf-8"))
    pull_request = event.get("pull_request")
    if not isinstance(pull_request, dict):
        return None
    base_sha = pull_request.get("base", {}).get("sha")
    head_sha = pull_request.get("head", {}).get("sha")
    if not isinstance(base_sha, str) or not _SHA_RE.fullmatch(base_sha):
        raise ValueError("pull_request event has no exact base SHA")
    if not isinstance(head_sha, str) or not _SHA_RE.fullmatch(head_sha):
        raise ValueError("pull_request event has no exact head SHA")
    return base_sha, head_sha


def _is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    result = _git(
        repo_root, "merge-base", "--is-ancestor", ancestor, descendant, check=False
    )
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    raise RuntimeError(result.stderr.strip() or "git merge-base failed")


def _integrated_base(repo_root: Path, frozen_head: str, current_head: str) -> str | None:
    """Find the nearest source-branch sync merge and return its base parent.

    Conflict repairs are made from the candidate branch and merge the newer
    base into it, so the candidate lineage is normally the first parent.
    GitHub pull-request events use their exact event base instead.
    """
    commits = _git(repo_root, "rev-list", "--first-parent", current_head).stdout.splitlines()
    for commit in commits:
        parents = _git(repo_root, "rev-list", "--parents", "-n", "1", commit).stdout.split()
        if len(parents) != 3:
            continue
        first_parent, second_parent = parents[1:]
        first_has_candidate = _is_ancestor(repo_root, frozen_head, first_parent)
        second_has_candidate = _is_ancestor(repo_root, frozen_head, second_parent)
        if first_has_candidate and not second_has_candidate:
            return second_parent
        if second_has_candidate and not first_has_candidate:
            return first_parent
    return None


def changed_paths_for_candidate_scope(
    repo_root: Path,
    frozen_head: str,
    *,
    event_path: Path | None = None,
) -> list[str]:
    """Return tracked plus untracked paths changed by the active candidate.

    Exact pull-request event SHAs take precedence. Local/push validation uses
    the newest source sync merge's base parent, then falls back to the original
    frozen head when no newer base has been integrated.
    """
    repo_root = repo_root.resolve()
    if event_path is None:
        configured_event = os.environ.get("GITHUB_EVENT_PATH")
        if configured_event:
            event_path = Path(configured_event)
    head = _git(repo_root, "rev-parse", "HEAD").stdout.strip()
    event_binding = _pull_request_event_base(event_path)
    if event_binding is not None:
        base, target = event_binding
    else:
        base = _integrated_base(repo_root, frozen_head, head) or frozen_head
        target = head
    changed = _git(repo_root, "diff", "--name-only", base, target).stdout.splitlines()
    untracked = _git(
        repo_root, "ls-files", "--others", "--exclude-standard"
    ).stdout.splitlines()
    return sorted(set(filter(None, changed)) | set(filter(None, untracked)))
