from __future__ import annotations


def parse_interval(bounds: dict) -> tuple[float, float]:
    return float(bounds["start"]), float(bounds["end"])


def time_respecting(network: dict, relation_path: list[str]) -> bool:
    rels = {r["relation_id"]: r for r in network.get("relations", [])}
    previous_end: float | None = None
    for rid in relation_path:
        if rid not in rels:
            return False
        start, end = parse_interval(rels[rid]["temporal_bounds"])
        if previous_end is not None and start < previous_end:
            return False
        previous_end = end
    return True


def static_aggregation_false_positive(network: dict, relation_path: list[str]) -> dict:
    rel_ids = {r["relation_id"] for r in network.get("relations", [])}
    static_exists = all(rid in rel_ids for rid in relation_path)
    temporal_valid = time_respecting(network, relation_path) if static_exists else False
    return {
        "path": relation_path,
        "static_exists": static_exists,
        "time_respecting": temporal_valid,
        "is_false_positive": static_exists and not temporal_valid,
        "claim_ceiling": "Static adjacency cannot invent time-impossible paths."
    }

def activation_windows(network: dict) -> list[dict]:
    return sorted(network.get("temporal_activations", []), key=lambda x: (x["start"], x["end"], x["activation_id"]))

