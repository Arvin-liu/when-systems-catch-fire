#!/usr/bin/env python3
"""Read-only audit of the Q33 PR front-door (pull-request description) accuracy.

Detects F2/N8 anti-patterns that make the reviewer-facing front door drift from
reality or over-claim CI results:

  * COMMIT_COUNT_VOLATILE  - a specific "N commits" / "Tracked files changed: N" /
                             "Commits since base: N" figure (drifts as the branch moves).
  * HEAD_HASH_VOLATILE     - a hardcoded specific HEAD SHA presented as the locked head
                             (drifts after every push).
  * AGGREGATED_PASS_CLAIM  - a specific aggregate pass-count (e.g. "230 passed",
                             "55 passed") that lumps Q33 governance + Foundation CI into
                             one number and goes stale / over-claims.

The audit is strictly READ-ONLY: it never modifies the repository, the PR, or any file.
With --verify-git it additionally reports (as informational evidence, never failing the
body audit) local/remote HEAD equality, the branch name, the PR open/draft state, and the
Q29R frozen-asset digest.

Usage:
  python3 tools/governance/audit_pr_front_door.py --pr-number 63
  python3 tools/governance/audit_pr_front_door.py --body-file body.md
  echo "$BODY" | python3 tools/governance/audit_pr_front_door.py --stdin
  python3 tools/governance/audit_pr_front_door.py --pr-number 63 --verify-git
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

# Q29R frozen asset (must never be modified - its digest is an invariant).
Q29R_REL = "docs/publication/works/when-an-army-believes-its-own-back.md"
Q29R_EXPECTED_DIGEST = "c135acd35a2232f0a6b3f933db482932a9fe5d5add51f870af97901faac90d4b"

COMMIT_COUNT_RE = re.compile(
    r"(commits?\s+since\s+base|tracked\s+files?\s+changed|\b\d+\s+commits?\b|\b\d+\s+files?\s+changed)",
    re.IGNORECASE,
)
HEAD_HASH_RE = re.compile(r"head\s+`?[0-9a-f]{7,40}`?", re.IGNORECASE)
AGGREGATED_PASS_RE = re.compile(r"\b\d+\s*pass(?:ed)?\b", re.IGNORECASE)


def audit_body(body: str) -> dict:
    """Return {status, violations} for the PR body text. Read-only."""
    violations = []
    if COMMIT_COUNT_RE.search(body):
        violations.append({
            "code": "COMMIT_COUNT_VOLATILE",
            "message": "Front door asserts a specific commit/file count (drifts as the branch moves). "
                       "Remove volatile counts; let CI be the source of truth.",
        })
    if HEAD_HASH_RE.search(body):
        violations.append({
            "code": "HEAD_HASH_VOLATILE",
            "message": "Front door hardcodes a specific HEAD SHA as the locked head (drifts after every push). "
                       "Do not pin a specific HEAD in the description.",
        })
    if AGGREGATED_PASS_RE.search(body):
        violations.append({
            "code": "AGGREGATED_PASS_CLAIM",
            "message": "Front door asserts a specific aggregate pass-count (e.g. '230 passed'), lumping "
                       "Q33 governance + Foundation CI and going stale / over-claiming. Remove the number; "
                       "separate Local / Q33 / Foundation layers and point to CI runs.",
        })
    return {
        "status": "FAIL" if violations else "PASS",
        "violations": violations,
    }


def verify_git(pr_number: int | None) -> dict:
    """Informational git/PR evidence. Never fails the body audit."""
    info: dict = {"available": False}
    try:
        local = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT),
                               capture_output=True, text=True, check=True).stdout.strip()
        upstream = subprocess.run(["git", "rev-parse", "@{u}"], cwd=str(REPO_ROOT),
                                 capture_output=True, text=True, check=True).stdout.strip()
        branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(REPO_ROOT),
                               capture_output=True, text=True, check=True).stdout.strip()
        info.update({
            "available": True,
            "local_head": local,
            "upstream_head": upstream,
            "local_eq_upstream": local == upstream,
            "branch": branch,
        })
    except Exception as e:  # pragma: no cover - environment dependent
        info["error"] = str(e)
        return info
    # Q29R frozen-asset digest check (informational; must remain unchanged).
    q29r = REPO_ROOT / Q29R_REL
    if q29r.is_file():
        digest = hashlib.sha256(q29r.read_bytes()).hexdigest()
        info["q29r_digest"] = digest
        info["q29r_unchanged"] = (digest == Q29R_EXPECTED_DIGEST)
    # PR state via gh (optional).
    if pr_number:
        try:
            out = subprocess.run(
                ["gh", "pr", "view", str(pr_number), "--json", "state,isDraft,headRefName,baseRefName"],
                cwd=str(REPO_ROOT), capture_output=True, text=True, check=True).stdout.strip()
            pr = json.loads(out)
            info["pr"] = {
                "number": pr_number,
                "state": pr["state"],
                "is_draft": pr["isDraft"],
                "head_ref": pr["headRefName"],
                "base_ref": pr["baseRefName"],
            }
        except Exception:  # pragma: no cover - gh may be unavailable
            info["pr"] = None
    return info


def main() -> int:
    ap = argparse.ArgumentParser(description="Read-only audit of the Q33 PR front-door accuracy")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--pr-number", type=int, help="Fetch the PR body via `gh pr view`")
    src.add_argument("--body-file", type=str, help="Path to a file containing the PR body")
    src.add_argument("--stdin", action="store_true", help="Read the PR body from stdin")
    ap.add_argument("--verify-git", action="store_true",
                    help="Also report local/remote HEAD, branch, PR state, Q29R digest")
    args = ap.parse_args()

    if args.pr_number is not None:
        try:
            body = subprocess.run(
                ["gh", "pr", "view", str(args.pr_number), "--json", "body", "-q", ".body"],
                cwd=str(REPO_ROOT), capture_output=True, text=True, check=True).stdout
        except subprocess.CalledProcessError as e:
            print(json.dumps({"status": "ERROR", "error": f"gh pr view failed: {e.stderr}"},
                            ensure_ascii=False), file=sys.stderr)
            return 2
    elif args.body_file:
        body = Path(args.body_file).read_text(encoding="utf-8")
    else:
        body = sys.stdin.read()

    report = audit_body(body)
    if args.verify_git:
        report["git_state"] = verify_git(args.pr_number)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
