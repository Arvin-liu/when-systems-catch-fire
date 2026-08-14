from __future__ import annotations


def parse_interval(bounds: dict) -> tuple[float, float]:
    start, end = float(bounds["start"]), float(bounds["end"])
    if start > end:
        raise ValueError(f"reversed interval: {start} > {end}")
    return start, end


def _relation_connections(relation: dict) -> set[tuple[str, str]]:
    source, target = relation["source"], relation["target"]
    direction = relation.get("direction", "directed")
    if direction == "directed":
        return {(source, target)}
    if direction in {"undirected", "bidirectional"}:
        return {(source, target), (target, source)}
    if direction == "unknown":
        return set()
    return set()


def oriented_transitions(relation: dict) -> set[tuple[str, str]]:
    return _relation_connections(relation)


def time_respecting_sequence(network: dict, relation_path: list[str]) -> bool:
    if not relation_path:
        return False
    rels = {r["relation_id"]: r for r in network.get("relations", [])}
    previous_end: float | None = None
    for rid in relation_path:
        if rid not in rels:
            return False
        try:
            start, end = parse_interval(rels[rid]["temporal_bounds"])
        except (KeyError, TypeError, ValueError):
            return False
        if previous_end is not None and start < previous_end:
            return False
        previous_end = end
    return True


def path_continuous(network: dict, relation_path: list[str]) -> bool:
    if not relation_path:
        return False
    rels = {r["relation_id"]: r for r in network.get("relations", [])}
    reachable_arrivals: set[str] | None = None
    for rid in relation_path:
        relation = rels.get(rid)
        if relation is None:
            return False
        transitions = oriented_transitions(relation)
        if not transitions:
            return False
        if reachable_arrivals is None:
            compatible = transitions
        else:
            compatible = {(departure, arrival) for departure, arrival in transitions if departure in reachable_arrivals}
        if not compatible:
            return False
        reachable_arrivals = {arrival for _departure, arrival in compatible}
    return True


def time_respecting_graph_path(network: dict, relation_path: list[str]) -> bool:
    return path_continuous(network, relation_path) and time_respecting_sequence(network, relation_path)


def time_respecting(network: dict, relation_path: list[str]) -> bool:
    return time_respecting_graph_path(network, relation_path)


def static_aggregation_false_positive(network: dict, relation_path: list[str]) -> dict:
    rel_ids = {r["relation_id"] for r in network.get("relations", [])}
    static_exists = all(rid in rel_ids for rid in relation_path)
    graph_path_valid = time_respecting_graph_path(network, relation_path) if static_exists else False
    sequence_valid = time_respecting_sequence(network, relation_path) if static_exists else False
    return {
        "path": relation_path,
        "static_exists": static_exists,
        "time_respecting_sequence": sequence_valid,
        "time_respecting_graph_path": graph_path_valid,
        "time_respecting": graph_path_valid,
        "is_false_positive": static_exists and not graph_path_valid,
        "claim_ceiling": "Static adjacency or temporal ordering cannot invent a topology-continuous time-respecting graph path."
    }

def activation_windows(network: dict) -> list[dict]:
    return sorted(network.get("temporal_activations", []), key=lambda x: (x["start"], x["end"], x["activation_id"]))
