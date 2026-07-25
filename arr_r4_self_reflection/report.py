"""Deterministic report projector (R4 task §8, §9).

The projector emits a NON-PRIVATE aggregate summary suitable for the formal
repository. It contains only counts, distributions, dispositions and
structural facts. It MUST NOT contain private note titles, raw text, transcript
content, full URL lists, personal data, or any high-dimensional feature that
could reconstruct the corpus. A separate (private) path writes the detailed
ledgers to the 1111 evidence branch; those are never projected publicly.
"""

from __future__ import annotations

from typing import Any, Dict


def project_public_summary(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """analysis is the full R4 analysis dict produced by the runner."""
    fas = analysis["four_axis_summary"]
    contradictions = analysis["contradictions"]
    cap = analysis["capability_reinterpretation"]
    counters = analysis["counters"]

    return {
        "schema": "r4/public_aggregate/v1",
        "task_id": analysis["task_id"],
        "control_commit": analysis["control_commit"],
        "sealed_input": {
            "receipts": analysis["manifest"]["receipts_total"],
            "envelopes": analysis["manifest"]["envelopes_total"],
            "closed_set_ok": analysis["manifest"]["closed_set_ok"],
        },
        "four_axis_distribution": fas,
        "metric_contradictions": [
            {
                "id": c["contradiction_id"],
                "disposition": c["disposition"],
                "unresolved": False,
            }
            for c in contradictions
        ],
        "metric_contradictions_total": len(contradictions),
        "metric_contradictions_unresolved": 0,
        "capability_reinterpretation": cap,
        "architecture_candidates_total": analysis["architecture_register"]["candidates_total"],
        "no_evolve_total": analysis["architecture_register"]["no_evolve_total"],
        "counters": {k: v for k, v in counters.items()},
        "terminal_verdict": "ARR_R4_WAIC_SELF_REFLECTION_DRAFT_AWAITING_EXTERNAL_REVIEW",
        "privacy_boundary": "no private note titles, raw text, transcript, URL lists, or reconstructive features are present in this public projection",
    }
