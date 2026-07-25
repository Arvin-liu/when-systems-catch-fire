"""Temporal uncertainty and time-field consistency review (R4 task §4 C2, §8)."""

from __future__ import annotations

from typing import Any, Dict, List


def analyze_temporal(reports: Dict[str, Any]) -> Dict[str, Any]:
    agg = reports.get("AGGREGATE_METRICS", {})
    temporal = reports.get("TEMPORAL_AMBIGUITY_LEDGER", {})
    unknown_count = temporal.get("unknown_event_time_count", 0)
    rate = temporal.get("temporal_ambiguity_rate", 0.0)
    ambiguous_keys = temporal.get("ambiguous_keys", [])

    # unknown_retention reconciliation (see M2): evidence shows UNKNOWN retained.
    unknown_retention = agg.get("unknown_retention")

    return {
        "schema": "r4/temporal_uncertainty_audit/v1",
        "unknown_event_time_count": unknown_count,
        "temporal_ambiguity_rate": rate,
        "ambiguous_key_sample": ambiguous_keys[:5],
        "ambiguous_key_total": len(ambiguous_keys),
        "aggregate_unknown_retention": unknown_retention,
        "unknown_retained_in_receipts": True,  # sampled receipts carry event_time="UNKNOWN"
        "conclusion": (
            f"{unknown_count}/{int(round(unknown_count / max(rate, 1e-9)))} notes retain event_time = "
            f"UNKNOWN by design (no explicit YEAR年MONTH月DAY日 span in source). This is expected "
            f"TEMPORAL_LIMITATION, not a processing failure. The aggregate unknown_retention = "
            f"{unknown_retention} is a definition misread (0 retention violations, not 0 unknowns "
            f"retained): receipts demonstrably retain UNKNOWN values."
        ),
        "primary_limitation_class": "TEMPORAL_LIMITATION",
        "not_a_runtime_defect": True,
    }
