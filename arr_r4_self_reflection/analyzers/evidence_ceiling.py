"""Claim-class and evidence-ceiling review (R4 task §4, §8: independently verified = 0)."""

from __future__ import annotations

from typing import Any, Dict


def analyze_evidence_ceiling(reports: Dict[str, Any], four_axis_summary: Dict[str, Any]) -> Dict[str, Any]:
    agg = reports.get("AGGREGATE_METRICS", {})
    cap = reports.get("CAPABILITY_COVERAGE_MATRIX", {})

    # Claim-class distribution directly from the receipts-derived four-axis summary.
    evidence_axis = four_axis_summary.get("evidence", {})
    independently_supported = evidence_axis.get("INDEPENDENTLY_SUPPORTED", 0)
    source_dependent = evidence_axis.get("SOURCE_DEPENDENT", 0)
    author_report = evidence_axis.get("AUTHOR_OR_SPEAKER_REPORT", 0)
    transcript_inference = evidence_axis.get("TRANSCRIPT_OR_INTERPRETER_INFERENCE", 0)

    all_pass = cap.get("all_pass")
    total_items = cap.get("total_items")

    return {
        "schema": "r4/claim_evidence_ceiling_audit/v1",
        "independently_verified_claim_class": 0,  # R4 fact §4
        "evidence_axis_distribution": {
            "INDEPENDENTLY_SUPPORTED": independently_supported,
            "SOURCE_DEPENDENT": source_dependent,
            "AUTHOR_OR_SPEAKER_REPORT": author_report,
            "TRANSCRIPT_OR_INTERPRETER_INFERENCE": transcript_inference,
        },
        "capability_all_pass": all_pass,
        "capability_total_items": total_items,
        "capability_semantic_items": 0,
        "ceiling": (
            "0 of 836 objects reach INDEPENDENTLY_SUPPORTED. The corpus is a set of extracted/"
            "represented notes (source-dependent, author-reported, or transcript-inference), not "
            "independently verified facts. R4 must not claim the 836 notes are true, independent, "
            "current, semantically understood or scientifically validated."
        ),
        "primary_limitation_class": "EXTRACTION_LIMITATION",
    }
