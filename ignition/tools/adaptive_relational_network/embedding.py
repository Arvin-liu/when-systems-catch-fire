from __future__ import annotations


AXES = ("external_availability", "retrieval", "relational_linkage", "conflict_exposure", "judgment_change", "action_change", "transfer", "delayed_stability")


def summarize_embedding_evidence(network: dict) -> dict:
    records = network.get("embedding_evidence", [])
    return {
        "network_id": network["network_spec"]["network_id"],
        "axes": [
            {
                "axis": axis,
                "values": sorted({record.get(axis, "missing") for record in records}),
            }
            for axis in AXES
        ],
        "self_report_separate": True,
        "observable_trace_separate": True,
        "alternatives": sorted({alt for record in records for alt in record.get("alternatives", [])}),
        "claim_ceiling": "Embedding evidence summary is multi-axis; it is not a learning score, truth score or diagnosis."
    }

