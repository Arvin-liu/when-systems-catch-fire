#!/usr/bin/env python3
"""Derived impact contract engine (task 106, contract §5).

Every meaningful iteration must carry BOTH a declaration and a computed impact
result. A declaration alone is not evidence. This module derives, for each of
the nine required dimensions, one of:

  - IMPACT_REQUIRED
  - NO_IMPACT_JUSTIFIED
  - UNRESOLVED_REVIEW_REQUIRED

A ``NO_IMPACT_JUSTIFIED`` result must name the governing source set, show that
no relevant source field changed (by content hash), and pass this validator.
Free-text ``NO_MAP_IMPACT`` / ``NO_ARTICLE_IMPACT`` is insufficient by itself.

The engine is source-driven: it inspects which governed files actually changed
(against the recorded baseline) and derives the decision, then compares the
derivation to the task's declared decision. A declaration that contradicts the
computed result is a fail-closed contradiction.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from typing import Dict, List, Optional

DIMENSIONS = [
    "MACHINE_RECORD_IMPACT",
    "REFERENCE_SURFACE_IMPACT",
    "EDITORIAL_ARTICLE_IMPACT",
    "SYSTEM_MAP_IMPACT",
    "CURRENT_PUBLIC_WORDING_IMPACT",
    "OPEN_QUESTION_IMPACT",
    "PROJECT_STATE_IMPACT",
    "EVIDENCE_PROGRAM_IMPACT",
    "MATURITY_OR_DISPOSITION_IMPACT",
]

DECISIONS = {
    "IMPACT_REQUIRED",
    "NO_IMPACT_JUSTIFIED",
    "UNRESOLVED_REVIEW_REQUIRED",
}

# Per-dimension governed source set for THIS repository. Changing any of these
# files is what makes the dimension require impact; leaving them byte-identical
# is what justifies NO_IMPACT.
GOVERNED_SOURCES = {
    "MACHINE_RECORD_IMPACT": [
        "RESULTS/CLAIM-DELTA.md",
        "RESULTS/IMPACT-ANALYSIS.md",
        "RESULTS/EVIDENCE-LINEAGE.md",
        "RESULTS/SELF-CORRECTION-AUDIT.md",
    ],
    "REFERENCE_SURFACE_IMPACT": [
        "function-os-candidate/v0.2/README.md",
        "docs/architecture/interactive-system-map.md",
    ],
    "EDITORIAL_ARTICLE_IMPACT": [
        "docs/editorial/articles/007-bounded-trust-function-os-v02-capability-benchmark.md",
        "docs/editorial/source-manifest.json",
    ],
    "SYSTEM_MAP_IMPACT": [
        "data/operations/project-components.json",
        "data/operations/change-propagation-topology.json",
        "data/architecture/interactive-system-map-layout.json",
        "tools/generate_interactive_system_map.py",
    ],
    "CURRENT_PUBLIC_WORDING_IMPACT": [
        "README.md",
        "RESULTS/LATEST.md",
        "docs/project-current-state.md",
        "HUMAN-READING.md",
    ],
    "OPEN_QUESTION_IMPACT": [
        "RESULTS/OPEN-QUESTIONS.md",
    ],
    "PROJECT_STATE_IMPACT": [
        "docs/project-current-state.md",
        "ITERATION.md",
    ],
    "EVIDENCE_PROGRAM_IMPACT": [
        "evidence-program/README.md",
        "evidence-program/registry/candidate-portfolio.jsonl",
    ],
    "MATURITY_OR_DISPOSITION_IMPACT": [
        "RESULTS/ADJUDICATION-SUMMARY.md",
        "function-os-candidate/v0.2/schemas/README.md",
    ],
}


def _sha256(path: str) -> Optional[str]:
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_dimension(dimension: str, repo_root: str, baseline: Dict[str, str]) -> Dict:
    """Independently derive a dimension's decision from actual file state.

    ``baseline`` maps governed-source relative path -> expected sha256 at the
    iteration's merge point. Returns a dict with the derived decision, the
    changed sources, and the per-source current hashes (the machine evidence).
    """
    sources = GOVERNED_SOURCES.get(dimension, [])
    current: Dict[str, Optional[str]] = {}
    changed: List[str] = []
    missing: List[str] = []
    for src in sources:
        abs_path = os.path.join(repo_root, src)
        cur = _sha256(abs_path)
        current[src] = cur
        if cur is None:
            missing.append(src)
            continue
        if src not in baseline:
            # New governed source not present at baseline -> cannot assert no-impact.
            changed.append(src)
            continue
        if baseline[src] != cur:
            changed.append(src)
    if missing:
        decision = "UNRESOLVED_REVIEW_REQUIRED"
    elif changed:
        decision = "IMPACT_REQUIRED"
    else:
        decision = "NO_IMPACT_JUSTIFIED"
    return {
        "dimension": dimension,
        "decision": decision,
        "changed_sources": changed,
        "missing_sources": missing,
        "current_hashes": current,
    }


def verify_impact_spec(spec_path: str, repo_root: str) -> List[str]:
    """Verify a per-iteration impact spec: derive each dimension and compare to
    its declared decision. Returns a list of problems (empty == valid)."""
    with open(spec_path, "r", encoding="utf-8") as fh:
        spec = json.load(fh)
    problems: List[str] = []
    declared = spec.get("dimensions", {})
    for dim in DIMENSIONS:
        if dim not in declared:
            problems.append(f"{spec.get('task_number')}: dimension {dim} missing from declared spec")
            continue
        entry = declared[dim]
        baseline = entry.get("baseline_sha256", {})
        derived = compute_dimension(dim, repo_root, baseline)
        if derived["decision"] != entry.get("declared"):
            problems.append(
                f"{spec.get('task_number')}: dimension {dim} declared "
                f"{entry.get('declared')} but derived {derived['decision']} "
                f"(changed={derived['changed_sources']})"
            )
        # A NO_IMPACT_JUSTIFIED claim with no governing source set is free text.
        if entry.get("declared") == "NO_IMPACT_JUSTIFIED":
            if not entry.get("governed_sources"):
                problems.append(
                    f"{spec.get('task_number')}: dimension {dim} NO_IMPACT has no governing source set"
                )
            if derived["decision"] != "NO_IMPACT_JUSTIFIED":
                problems.append(
                    f"{spec.get('task_number')}: dimension {dim} NO_IMPACT not machine-justified "
                    f"(changed={derived['changed_sources']})"
                )
    return problems


def generate_impact_spec(task_number: int, repo_root: str, declared: Dict[str, str]) -> Dict:
    """Build an impact spec with computed baseline hashes from current repo state."""
    dims: Dict[str, Dict] = {}
    for dim in DIMENSIONS:
        sources = GOVERNED_SOURCES.get(dim, [])
        baseline = {s: _sha256(os.path.join(repo_root, s)) for s in sources}
        baseline = {k: v for k, v in baseline.items() if v is not None}
        dims[dim] = {
            "declared": declared.get(dim, "UNRESOLVED_REVIEW_REQUIRED"),
            "governed_sources": sources,
            "baseline_sha256": baseline,
        }
    return {"task_number": task_number, "dimensions": dims}


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True, help="path to per-iteration impact spec JSON")
    ap.add_argument("--repo", default=".", help="repository root")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    problems = verify_impact_spec(args.spec, os.path.abspath(args.repo))
    if problems:
        for p in problems:
            print(f"IMPACT_INVALID: {p}", file=sys.stderr)
        return 1
    print(f"IMPACT_OK spec={args.spec}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
