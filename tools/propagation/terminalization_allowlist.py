#!/usr/bin/env python3
"""Terminalization PR diff allowlist validator (task 108, contract §8/§12/§17).

The terminalization PR is deterministic and narrow: it may change ONLY
lifecycle/current-truth projection paths plus bounded terminal wording. It must
NOT expand semantic scope: no arbitrary scientific conclusions, no Function OS
scope expansion, no unreviewed article prose edits beyond the allowlisted
terminal wording fields, no direct main edits.

Given a git diff (path list with status), this module returns the set of paths
that violate the allowlist. Fail-closed: an unknown or clearly semantic path is
rejected.
"""
from __future__ import annotations

import re
import sys
from typing import Dict, List, Tuple

# Allowlisted path patterns for the terminalization PR. Anything else is a
# scope-expansion violation.
ALLOWED_PATTERNS = [
    r"^data/operations/lifecycle-events\.jsonl$",
    r"^data/operations/current-truth-projection\.json$",
    r"^data/operations/derived-lifecycle-view\.json$",
    r"^data/operations/propagation/108-",
    r"^docs/editorial/source-manifest\.json$",
    r"^docs/editorial/articles/008-.*\.md$",
    r"^docs/project-current-state\.md$",
    r"^RESULTS/LATEST\.md$",
    r"^KNOWLEDGE/WHATS-NEW\.md$",
    r"^reports/operations/lifecycle-audit-\d+\.md$",
    r"^tools/propagation/lifecycle_events\.py$",
    r"^tools/propagation/tag_validator\.py$",
    r"^tools/propagation/terminalization_allowlist\.py$",
    r"^tools/propagation/terminalization_generator\.py$",
    r"^schemas/operations/lifecycle-event\.schema\.json$",
    r"^tests/test_lifecycle_events\.py$",
    r"^tests/test_terminalization_allowlist\.py$",
    r"^tests/fixtures/lifecycle/",
    r"^data/operations/terminal-evidence-core\.json$",
    r"^docs/operations/lifecycle-readme\.md$",
    r"^ITERATION\.md$",
    # Contract §17 (task 108): the terminalization-PR CI itself is part of the
    # terminalization scope. Allowlist edits to this workflow when they are
    # limited to realizing the stated FRESH-FULL-CLONE intent (e.g. fetch-tags
    # so annotated terminal tags for 104-108 are resolvable). Scope expansion of
    # the workflow beyond terminalization validation remains forbidden.
    r"^.github/workflows/iteration-lifecycle-validation\.yml$",
]

# Paths that are EXPLICITLY forbidden in a terminalization PR (semantic scope).
FORBIDDEN_PATTERNS = [
    r"^function-os-candidate/",
    r"^data/foundation/",
    r"^data/math-foundation/",
    r"^docs/editorial/articles/(?!008-).*\.md$",
    r"^tools/(?!propagation/).*\.py$",
]

_compiled_allowed = [re.compile(p) for p in ALLOWED_PATTERNS]
_compiled_forbidden = [re.compile(p) for p in FORBIDDEN_PATTERNS]


def path_allowed(path: str) -> Tuple[bool, str]:
    """Return (allowed, reason)."""
    for pat in _compiled_forbidden:
        if pat.match(path):
            return False, f"forbidden semantic path: {path}"
    for pat in _compiled_allowed:
        if pat.match(path):
            return True, "allowlisted"
    return False, f"not in terminalization allowlist: {path}"


def validate_diff(paths: List[str]) -> List[str]:
    """paths: list of changed file paths. Return violation list."""
    violations: List[str] = []
    for p in paths:
        ok, reason = path_allowed(p)
        if not ok:
            violations.append(reason)
    return violations


def validate_diff_status(diff_entries: List[Dict[str, str]]) -> List[str]:
    """diff_entries: list of {'path':..., 'status':...}.

    Rejects deletions of historical lifecycle evidence and unallowlisted adds.
    """
    violations: List[str] = []
    LEDGER = "data/operations/merged-iteration-ledger.jsonl"
    for e in diff_entries:
        p = e["path"]
        st = e.get("status", "M")
        # Deleting historical candidate/PR_OPEN evidence is always prohibited,
        # regardless of allowlist membership.
        if st == "D" and p == LEDGER:
            violations.append("terminalization PR must not delete historical merged-iteration-ledger.jsonl")
            continue
        ok, reason = path_allowed(p)
        if not ok:
            violations.append(reason)
    return violations


def main() -> int:
    import argparse
    import json
    import sys
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths-file", help="json list of paths")
    ap.add_argument("--diff-file", help="json list of {path,status}")
    args = ap.parse_args()
    violations: List[str] = []
    if args.paths_file:
        with open(args.paths_file) as fh:
            violations += validate_diff(json.load(fh))
    if args.diff_file:
        with open(args.diff_file) as fh:
            violations += validate_diff_status(json.load(fh))
    if violations:
        for v in violations:
            print(f"ALLOWLIST_VIOLATION: {v}", file=sys.stderr)
        return 1
    print("ALLOWLIST_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
