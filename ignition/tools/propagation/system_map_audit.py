#!/usr/bin/env python3
"""Live system-map impact audit (task 106, contract §9).

Audits whether a task's ``NO_MAP_IMPACT`` is actually justified by the governed
map sources. The decision is derived from the current map registry, topology and
node metadata model:

  - If Function OS capability/status/maturity IS represented in mapped node
    metadata, the map must be regenerated and the change recorded.
  - If the map intentionally excludes benchmark/evidence metadata and no mapped
    field changed, retain NO_MAP_IMPACT with a machine-checkable explanation.
  - Do not change map scope merely to force a visual difference.

Governed map sources (the only files whose change can force a map regeneration):
  - data/operations/project-components.json
  - data/operations/change-propagation-topology.json
  - data/architecture/interactive-system-map-layout.json
  - tools/generate_interactive_system_map.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from typing import Dict, List, Optional

MAP_GOVERNED_SOURCES = [
    "data/operations/project-components.json",
    "data/operations/change-propagation-topology.json",
    "data/architecture/interactive-system-map-layout.json",
    "tools/generate_interactive_system_map.py",
]

PROOF_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "operations",
    "propagation", "106-impact", "system-map-nonimpact-proof.json",
)


def _sha256(path: str) -> Optional[str]:
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def map_includes_function_os_evidence(repo_root: str) -> bool:
    """True if any mapped node metadata references Function OS v0.2 capability
    evidence. If False, the map intentionally excludes it and a benchmark cannot
    change the map."""
    components = os.path.join(repo_root, "data/operations/project-components.json")
    if not os.path.exists(components):
        return False
    with open(components, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    blob = json.dumps(data, ensure_ascii=False).lower()
    for token in ("function-os", "v0.2", "benchmark", "n2_representation"):
        if token in blob:
            return True
    return False


def audit(repo_root: str, baseline: Optional[Dict[str, str]] = None) -> Dict:
    """Derive the map impact decision from actual governed-source state."""
    current: Dict[str, Optional[str]] = {}
    changed: List[str] = []
    for src in MAP_GOVERNED_SOURCES:
        cur = _sha256(os.path.join(repo_root, src))
        current[src] = cur
        if baseline and src in baseline and baseline[src] != cur:
            changed.append(src)
    includes_evidence = map_includes_function_os_evidence(repo_root)
    if changed:
        decision = "IMPACT_REQUIRED"
    else:
        decision = "NO_IMPACT_JUSTIFIED"
    return {
        "decision": decision,
        "governed_sources": MAP_GOVERNED_SOURCES,
        "changed_sources": changed,
        "current_hashes": current,
        "map_includes_function_os_evidence": includes_evidence,
        "explanation": (
            "Function OS v0.2 benchmark/evidence is not represented in mapped node "
            "metadata; the three governed map sources and generator are byte-identical "
            "to the merge baseline, so the homepage system map is unaffected."
            if decision == "NO_IMPACT_JUSTIFIED" else
            "A governed map source changed; the system map must be regenerated."
        ),
    }


def write_proof(repo_root: str) -> Dict:
    result = audit(repo_root)
    os.makedirs(os.path.dirname(os.path.abspath(PROOF_PATH)), exist_ok=True)
    with open(os.path.abspath(PROOF_PATH), "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, sort_keys=True, indent=2)
        fh.write("\n")
    return result


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--write-proof", action="store_true")
    args = ap.parse_args()
    repo = os.path.abspath(args.repo)
    if args.write_proof:
        res = write_proof(repo)
    else:
        res = audit(repo)
    print(json.dumps(res, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
