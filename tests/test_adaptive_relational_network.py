import json
from pathlib import Path

from tools.adaptive_relational_network.validator import (
    load_network,
    network_diff,
    render_summary,
    time_respecting,
    validate_all,
)


def test_arn_examples_validate():
    result = validate_all()
    assert result["status"] == "PASS", result
    assert result["checked"] >= 5


def test_time_respecting_path():
    network = load_network(Path("data/architecture/adaptive-relational-network/examples/ai-external-knowledge-vs-internal-integration.json"))
    assert time_respecting(network, ["r-info-judgment", "r-judgment-action"])


def test_network_diff_representation_only():
    before = load_network(Path("data/architecture/adaptive-relational-network/examples/ai-external-knowledge-vs-internal-integration.json"))
    after = json.loads(json.dumps(before))
    after["nodes"].append({"node_id":"n-new","label":"new node","node_type":"note","layers":["knowledge"],"provenance":["test"],"uncertainty":"low","claim_ceiling":"test"})
    diff = network_diff(before, after)
    assert diff["added_nodes"] == ["n-new"]
    assert "not proof" in diff["claim_ceiling"]


def test_renderer_summary_contains_claim_ceiling():
    network = load_network(Path("data/architecture/adaptive-relational-network/examples/atomic-lookup-negative-control.json"))
    summary = render_summary(network)
    assert "claim ceiling" in summary

