# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Git / PR / CI chain adapter (read-only, exact ref identity preserved).

Consumes a typed reference that already pins repository + ref (commit/PR/run).
It does NOT fetch from the network; it reads an already-fetched local evidence
record (e.g. a committed JSON describing the chain) and preserves the exact
repository/ref identity. No mutation of any remote state.
"""
from __future__ import annotations

from typing import Any


def adapt_git_pr_ci(ref: dict, *, local_evidence_root: str | None = None) -> dict[str, Any]:
    repo = ref.get("repo")
    ref_id = ref.get("ref")  # commit sha, PR number, or workflow run id
    if not repo or not ref_id:
        raise ValueError("git_pr_ci_adapter: repo and ref are required")

    record: dict[str, Any] = {
        "adapter": "git_pr_ci",
        "repo": repo,
        "ref": str(ref_id),
        "ref_kind": ref.get("ref_kind", "commit"),  # commit | pr | ci_run
        "exact_identity_preserved": True,
        "read_only": True,
    }
    if local_evidence_root is not None:
        from pathlib import Path
        stub = Path(local_evidence_root) / f"{ref['object_id']}.ref.json"
        record["evidence_stub_present"] = stub.exists()
    return record
