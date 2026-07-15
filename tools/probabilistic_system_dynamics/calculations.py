from __future__ import annotations


def row_sums(kernel: list[list[float]]) -> list[float]:
    return [sum(row) for row in kernel]


def is_normalized_kernel(kernel: list[list[float]], tolerance: float = 1e-9) -> bool:
    if not kernel:
        return True
    return all(all(0 <= x <= 1 for x in row) and abs(sum(row) - 1.0) <= tolerance for row in kernel)


def trajectory_probability(kernel: list[list[float]], path: list[int]) -> float:
    if len(path) < 2:
        return 1.0
    probability = 1.0
    for source, target in zip(path, path[1:]):
        probability *= kernel[source][target]
    return probability


def brier_score(probability: float, outcome: float) -> float:
    if not 0 <= probability <= 1:
        raise ValueError("probability must be in [0, 1]")
    if outcome not in (0, 1, 0.0, 1.0):
        raise ValueError("outcome must be binary for this helper")
    return (probability - outcome) ** 2


def observation_intervention_distinct(record: dict) -> bool:
    obs = record["intervention_distribution"]["observational_distribution"]
    do = record["intervention_distribution"]["interventional_distribution"]
    return obs != do and record["intervention_distribution"].get("policy_or_action", "").startswith("do(")


def system_boundary_diff(before: dict, after: dict) -> dict:
    b = before["system_context"]
    a = after["system_context"]
    keys = ["boundary_rule", "environment", "inputs", "outputs", "exchanges", "nested_systems", "observer_frame", "purpose_of_model"]
    return {
        "system_id_before": b.get("system_id"),
        "system_id_after": a.get("system_id"),
        "changed_fields": [key for key in keys if b.get(key) != a.get(key)],
        "claim_ceiling": "Boundary diff records modeling changes only, not a natural system partition."
    }

