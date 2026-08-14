from __future__ import annotations


def causal_fabric_diff(before: dict, after: dict) -> dict:
    before_events = {e["event_id"] for e in before.get("events", [])}
    after_events = {e["event_id"] for e in after.get("events", [])}
    before_rel = {r["relation_id"]: r for r in before.get("relations", [])}
    after_rel = {r["relation_id"]: r for r in after.get("relations", [])}

    common_rel = sorted(set(before_rel) & set(after_rel))
    class_changes = [
        {
            "relation_id": rid,
            "before": before_rel[rid]["relation_class"],
            "after": after_rel[rid]["relation_class"],
        }
        for rid in common_rel
        if before_rel[rid]["relation_class"] != after_rel[rid]["relation_class"]
    ]

    ceiling_changes = [
        {
            "relation_id": rid,
            "before": before_rel[rid].get("claim_ceiling"),
            "after": after_rel[rid].get("claim_ceiling"),
        }
        for rid in common_rel
        if before_rel[rid].get("claim_ceiling") != after_rel[rid].get("claim_ceiling")
    ]

    return {
        "before": before.get("fabric_id"),
        "after": after.get("fabric_id"),
        "added_events": sorted(after_events - before_events),
        "removed_events": sorted(before_events - after_events),
        "added_relations": sorted(set(after_rel) - set(before_rel)),
        "removed_relations": sorted(set(before_rel) - set(after_rel)),
        "relation_class_changes": class_changes,
        "claim_ceiling_changes": ceiling_changes,
        "new_residue_count": max(0, len(after.get("unmapped_residue", [])) - len(before.get("unmapped_residue", []))),
    }

