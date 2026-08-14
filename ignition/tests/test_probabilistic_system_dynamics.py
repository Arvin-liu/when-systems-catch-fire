import json
from pathlib import Path

from tools.probabilistic_system_dynamics.calculations import (
    brier_score,
    is_normalized_kernel,
    probabilistic_system_diff,
    system_boundary_diff,
    trajectory_probability,
)
from tools.probabilistic_system_dynamics.validator import load_record, validate_all


def test_psd_examples_validate():
    result = validate_all()
    assert result["status"] == "PASS", result
    assert result["checked"] >= 5


def test_kernel_and_trajectory_probability():
    kernel = [[0.7, 0.3], [0.2, 0.8]]
    assert is_normalized_kernel(kernel)
    assert abs(trajectory_probability(kernel, [0, 1, 1]) - 0.24) < 1e-12


def test_brier_score():
    assert abs(brier_score(0.7, 0) - 0.49) < 1e-12
    assert abs(brier_score(0.875, 1) - 0.015625) < 1e-12


def test_intervention_and_observation_are_distinct_in_ai_example():
    record = load_record(Path("data/architecture/probabilistic-system-dynamics/examples/ai-deployment-psd.json"))
    obs = record["intervention_distribution"]["observational_distribution"]
    do = record["intervention_distribution"]["interventional_distribution"]
    assert obs != do
    assert record["intervention_distribution"]["policy_or_action"].startswith("do(")


def test_system_boundary_diff_records_modeling_change_only():
    before = load_record(Path("data/architecture/probabilistic-system-dynamics/examples/open-ecosystem.json"))
    after = json.loads(json.dumps(before))
    after["system_context"]["boundary_rule"] = "expanded basin for sensitivity analysis"
    diff = system_boundary_diff(before, after)
    assert diff["changed_fields"] == ["boundary_rule"]
    assert "not a natural system partition" in diff["claim_ceiling"]


def test_probabilistic_system_diff_detects_transition_change():
    before = load_record(Path("data/architecture/probabilistic-system-dynamics/examples/continuous-time-hazard.json"))
    after = json.loads(json.dumps(before))
    after["transition_law"]["transition_kernel"] = [[0.6, 0.4], [0.2, 0.8]]
    diff = probabilistic_system_diff(before, after)
    assert diff["transition_law_changed"] is True
    assert diff["probability_semantics_changed"] is False

