#!/usr/bin/env python3
"""Generate the machine-readable editorial source manifest (task 106, §8).

Every article gets a record with: source IDs/paths, source hashes (governed
version IDs), materiality rules, last reviewed commit, editorial status, review
evidence and current claim ceiling. Hashes are computed from the current repo
so the lifecycle validator can detect a material source change that was not
accompanied by a review.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(REPO, "docs", "editorial", "source-manifest.json")


def _sha256(path: str) -> str:
    p = os.path.join(REPO, path)
    if not os.path.exists(p):
        raise FileNotFoundError(f"source path missing: {path}")
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# (article file, source paths, review commit, status, review evidence, claim ceiling)
ARTICLES = [
    ("docs/editorial/articles/001-withdrawn-gravity-how-strong-claims-do-not-rebound.md",
     ["RESULTS/CORRECTIONS.md", "docs/foundation/historical-correction-log.md"],
     "16f64004", "REVIEWED_CURRENT",
     "task 104 reviewed against PR #160 merge 16f64004; claim ceiling unchanged",
     "only what ignition's own assets support; no four-force unification / quantum gravity"),
    ("docs/editorial/articles/002-two-surfaces-one-truth-registry-and-human-layer.md",
     ["RESULTS/ADJUDICATION-SUMMARY.md", "HUMAN-READING.md"],
     "16f64004", "REVIEWED_CURRENT",
     "task 104 reviewed against PR #160 merge 16f64004",
     "alignment is accounting closure, not proof closure"),
    ("docs/editorial/articles/003-from-candidate-to-current-evidence-chain.md",
     ["docs/operations/stage-snapshot-publication.md"],
     "16f64004", "REVIEWED_CURRENT",
     "task 104 reviewed against PR #160 merge 16f64004",
     "candidate/validated/merged/Current are distinct; 'passed' is not 'proven'"),
    ("docs/editorial/articles/004-gated-model-bounded-projection-open-unification.md",
     ["docs/physics_boundary.md", "README.md"],
     "16f64004", "REVIEWED_CURRENT",
     "task 104 reviewed against PR #160 merge 16f64004",
     "gated model does not unify forces and does not prove impossibility"),
    ("docs/editorial/articles/005-description-is-not-proof-systems-representations.md",
     ["docs/architecture/multiscale-causal-fabric.md"],
     "16f64004", "REVIEWED_CURRENT",
     "task 104 reviewed against PR #160 merge 16f64004",
     "representation capacity is not causal or empirical proof"),
    ("docs/editorial/articles/006-readable-works-with-boundaries.md",
     ["docs/publication/zhiyuan-writing-method.md"],
     "16f64004", "REVIEWED_CURRENT",
     "task 104 reviewed against PR #160 merge 16f64004",
     "articles organize narrative; registry remains authority"),
    ("docs/editorial/articles/007-bounded-trust-function-os-v02-capability-benchmark.md",
     ["function-os-candidate/v0.2/README.md",
      "function-os-candidate/v0.2/benchmark/30_EXECUTION_LOG.md"],
     "9d7d5ab512ffe3fd109a60ebd3d9d246b3a42d19", "REVIEWED_CURRENT",
     "article 007 reviewed against task-105 exact head 9d7d5ab5; original and repaired "
     "verdicts kept distinct; bounded N2 defect repaired",
     "original-target PARTIALLY_SUPPORTED_WITH_IDENTIFIED_FAILURES; repaired-target "
     "SUPPORTED_WITHIN_BOUNDED_DOMAIN; no claim of complete sandboxing, production readiness "
     "or universal correctness"),
    ("docs/editorial/articles/008-merged-but-stale-public-truth.md",
     ["data/operations/merged-iteration-ledger.jsonl",
      "tools/propagation/validate_reconciliation.py"],
     "task-106-exact-head", "REVIEWED_CURRENT",
     "article 008 reviewed against task-106 exact head at ordinary merge; explains "
     "post-merge current-truth lag without new claims",
     "explanatory only; no new scientific/mathematical/empirical conclusion; asserts only "
     "that a fail-closed propagation mechanism now exists"),
]


def main() -> int:
    articles = {}
    for file, sources, commit, status, evidence, ceiling in ARTICLES:
        hashes = {s: _sha256(s) for s in sources}
        articles[os.path.basename(file).replace(".md", "")] = {
            "file": file,
            "source_ids": [os.path.basename(s) for s in sources],
            "source_paths": sources,
            "source_hashes": hashes,
            "materiality_rules": [
                "any change to a listed source path requires re-review before currency",
                "changing only an unrelated source does not force staleness",
            ],
            "last_reviewed_commit": commit,
            "editorial_status": status,
            "review_evidence": evidence,
            "current_claim_ceiling": ceiling,
        }
    manifest = {
        "schema_version": "1.0.0",
        "generated_by": "tools/propagation/generate_editorial_manifest.py",
        "articles": articles,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, sort_keys=True, indent=2)
        fh.write("\n")
    print(f"EDITORIAL_MANIFEST_OK articles={len(articles)} -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
