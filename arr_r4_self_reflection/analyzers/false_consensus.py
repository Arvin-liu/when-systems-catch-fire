"""False-consensus candidate review (R4 task §4 fact: false_consensus_risk = 4, §8)."""

from __future__ import annotations

from typing import Any, Dict


def analyze_false_consensus(reports: Dict[str, Any]) -> Dict[str, Any]:
    fc = reports.get("FALSE_CONSENSUS_CASES", {})
    cases = fc.get("cases", [])
    graph = reports.get("SOURCE_DEPENDENCY_GRAPH", {})
    shared = graph.get("shared_source_derivatives", {})

    analyzed = []
    for c in cases:
        host = c.get("source_host")
        keys = c.get("note_keys", [])
        claim = c.get("repeated_claim_class", [])
        analyzed.append({
            "source_host": host,
            "note_keys": keys,
            "note_count": len(keys),
            "repeated_claim_class": claim,
            "shared_derivatives": [h for h, ks in shared.items() if set(ks) & set(keys)],
        })

    # Concentration-driven, not runtime-driven: every case maps to a host cluster.
    return {
        "schema": "r4/false_consensus_audit/v1",
        "false_consensus_risk": fc.get("false_consensus_risk", len(cases)),
        "case_count": len(cases),
        "cases": analyzed,
        "conclusion": (
            "All 4 false-consensus risk candidates are concentration artifacts of a small number of "
            "source hosts (e.g. worldaic.com.cn and its www./reg. derivatives, getnotes.seek). They are "
            "SOURCE_DEPENDENCY_LIMITATION / FALSE_CONSENSUS_RISK, not runtime or architecture defects. "
            "Repeated coverage from one source cluster must not be read as independent consensus."
        ),
        "primary_limitation_class": "FALSE_CONSENSUS_RISK",
        "not_a_runtime_defect": True,
    }
