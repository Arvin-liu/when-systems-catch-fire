#!/usr/bin/env python3
"""Editorial stale/review lifecycle (task 106, contract §8).

Every article must have a machine-readable source manifest. When a material
source changes, CI must FAIL if the article remains silently CURRENT. A
generator may mark the article stale and update metadata, but it must not
silently rewrite the prose to recover current status.

This module validates ``docs/editorial/source-manifest.json``:
  - every article has an entry with the required fields;
  - editorial_status is one of the five required states;
  - a material source change is not hidden behind a CURRENT/REVIEWED_CURRENT
    status without review evidence;
  - a source path referenced by the article is recorded in the manifest;
  - restoring currency without review evidence fails.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from typing import Dict, List

REQUIRED_STATES = {
    "CURRENT",
    "STALE_REVIEW_REQUIRED",
    "UNDER_REVIEW",
    "REVIEWED_CURRENT",
    "RETIRED_OR_SUPERSEDED",
}

# Statuses that assert currency and therefore require review evidence when a
# material source has changed since the last review.
CURRENCY_STATES = {"CURRENT", "REVIEWED_CURRENT"}

MANIFEST_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "docs", "editorial", "source-manifest.json"
)


def _sha256(path: str) -> Optional[str]:
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _resolve_source_path(repo_root: str, source: str) -> str:
    """Resolve a source path while preserving historical path spellings.

    The editorial manifest is historical evidence.  In particular, task 104
    recorded the then-root ``README.md``; the current GitHub landing page is
    now ``.github/README.md`` after the governed root normalization.  Resolve
    that alias for validation without rewriting the historical manifest.
    """
    direct = os.path.join(repo_root, source)
    if os.path.exists(direct):
        return direct
    repository_root = os.path.dirname(os.path.abspath(repo_root))
    if source == "README.md":
        return os.path.join(repository_root, ".github", "README.md")
    if source.startswith(".github/"):
        return os.path.join(repository_root, source)
    return direct


def validate_manifest(manifest_path: str, repo_root: str) -> List[str]:
    problems: List[str] = []
    with open(manifest_path, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    articles = manifest.get("articles", {})
    for art_id, entry in articles.items():
        status = entry.get("editorial_status")
        if status not in REQUIRED_STATES:
            problems.append(f"article {art_id}: invalid editorial_status {status!r}")
        # Required fields present.
        for field in ("file", "source_paths", "source_hashes", "last_reviewed_commit",
                      "current_claim_ceiling"):
            if field not in entry:
                problems.append(f"article {art_id}: missing manifest field {field}")
        # Source path referenced but not recorded in hashes -> manifest stale.
        recorded = entry.get("source_hashes", {})
        for src in entry.get("source_paths", []):
            if src not in recorded:
                problems.append(
                    f"article {art_id}: source path {src} not recorded in source_hashes "
                    f"(manifest must be updated when a source path changes)"
                )
        # Material source changed since last review.
        changed = []
        for src, expected in recorded.items():
            cur = _sha256(_resolve_source_path(repo_root, src))
            if cur is None:
                problems.append(f"article {art_id}: recorded source {src} missing on disk")
                continue
            if cur != expected:
                changed.append(src)
        if changed:
            if status in CURRENCY_STATES and not entry.get("review_evidence"):
                problems.append(
                    f"article {art_id}: material source(s) {changed} changed but status "
                    f"{status} has no review_evidence (must be STALE_REVIEW_REQUIRED/UNDER_REVIEW "
                    f"until reviewed)"
                )
        # §8 (currency-state closure): a CURRENT/REVIEWED_CURRENT claim must
        # ALWAYS carry review evidence, independent of whether a material source
        # changed since the last review. Fail-closed: a currency claim without
        # review evidence is invalid even when no source moved. This check is
        # deliberately OUTSIDE `if changed:` so that a silently-CURRENT article
        # with stale/missing review evidence is still caught.
        if status in CURRENCY_STATES and entry.get("review_evidence") is None:
            problems.append(
                f"article {art_id}: restored to CURRENT without review_evidence"
            )
    return problems


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=os.path.abspath(MANIFEST_PATH))
    ap.add_argument("--repo", default=".")
    args = ap.parse_args()
    problems = validate_manifest(args.manifest, os.path.abspath(args.repo))
    if problems:
        for p in problems:
            print(f"EDITORIAL_INVALID: {p}", file=sys.stderr)
        return 1
    print(f"EDITORIAL_OK articles={len(load_article_ids(args.manifest))}")
    return 0


def load_article_ids(manifest_path: str) -> List[str]:
    with open(manifest_path, "r", encoding="utf-8") as fh:
        return list(json.load(fh).get("articles", {}).keys())


if __name__ == "__main__":
    sys.exit(main())
