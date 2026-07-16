import copy
from pathlib import Path

from tools.adaptive_relational_network.temporal import time_respecting_graph_path, time_respecting_sequence
from tools.adaptive_relational_network.validator import (
    load_network,
    validate_embedding_probe_contract,
    validate_network,
)


FIXTURE = Path("data/architecture/adaptive-relational-network/examples/ai-external-knowledge-vs-internal-integration.json")


def valid_network():
    return load_network(FIXTURE)


def assert_rejected(network, text):
    errors = validate_network(network)
    assert errors
    assert any(text in error for error in errors), errors


def test_schema_rejects_missing_required_field():
    network = valid_network()
    del network["network_spec"]["claim_ceiling"]
    assert_rejected(network, "claim_ceiling")


def test_schema_rejects_illegal_enum_and_type():
    network = valid_network()
    network["relations"][0]["direction"] = "sideways"
    network["relations"][0]["weight"] = "strong"
    errors = validate_network(network)
    assert any("sideways" in error or "not one of" in error for error in errors), errors
    assert any("not of type 'number'" in error for error in errors), errors


def test_schema_rejects_forbidden_undeclared_property():
    network = valid_network()
    network["nodes"][0]["silent_extra"] = "forbidden"
    assert_rejected(network, "Additional properties")


def test_duplicate_ids_are_not_hidden_by_sets():
    network = valid_network()
    network["nodes"].append(copy.deepcopy(network["nodes"][0]))
    assert_rejected(network, "duplicate node id")


def test_dangling_references_are_rejected():
    network = valid_network()
    network["relations"][0]["source"] = "missing-node"
    network["nodes"][0]["layers"] = ["missing-layer"]
    network["integration_responses"][0]["evidence_ref"] = "missing-evidence"
    errors = validate_network(network)
    assert any("dangling endpoint" in error for error in errors), errors
    assert any("dangling reference missing-layer" in error for error in errors), errors
    assert any("dangling reference missing-evidence" in error for error in errors), errors


def test_hyperrelation_repeated_and_nonexistent_members_are_rejected():
    network = valid_network()
    network["hyper_relations"][0]["members"] = ["n-info", "n-info", "missing-member"]
    errors = validate_network(network)
    assert any("repeated member" in error for error in errors), errors
    assert any("dangling reference missing-member" in error for error in errors), errors


def test_reversed_relation_and_activation_intervals_are_rejected():
    network = valid_network()
    network["relations"][0]["temporal_bounds"] = {"start": 5, "end": 1}
    network["temporal_activations"][0]["start"] = 9
    network["temporal_activations"][0]["end"] = 2
    errors = validate_network(network)
    assert any("invalid interval" in error for error in errors), errors
    assert any("activation" in error and "invalid interval" in error for error in errors), errors


def test_temporally_valid_but_topologically_disconnected_sequence_is_not_graph_path():
    network = valid_network()
    network["relations"] = [
        {**network["relations"][0], "relation_id": "a", "source": "n-info", "target": "n-judgment", "temporal_bounds": {"start": 1, "end": 2}},
        {**network["relations"][1], "relation_id": "b", "source": "n-info", "target": "n-action", "temporal_bounds": {"start": 3, "end": 4}},
    ]
    assert time_respecting_sequence(network, ["a", "b"])
    assert not time_respecting_graph_path(network, ["a", "b"])


def test_topologically_connected_but_temporally_invalid_path_is_rejected():
    network = valid_network()
    network["relations"] = [
        {**network["relations"][0], "relation_id": "a", "source": "n-info", "target": "n-judgment", "temporal_bounds": {"start": 5, "end": 6}},
        {**network["relations"][1], "relation_id": "b", "source": "n-judgment", "target": "n-action", "temporal_bounds": {"start": 1, "end": 2}},
    ]
    assert not time_respecting_sequence(network, ["a", "b"])
    assert not time_respecting_graph_path(network, ["a", "b"])


def test_nonexistent_relation_and_unknown_direction_paths_are_rejected():
    network = valid_network()
    assert not time_respecting_graph_path(network, ["missing-relation"])
    network["relations"][0]["direction"] = "unknown"
    assert not time_respecting_graph_path(network, ["r-info-judgment", "r-judgment-action"])


def test_empty_claim_ceiling_provenance_alternatives_and_residue_are_rejected():
    network = valid_network()
    network["nodes"][0]["provenance"] = []
    network["relations"][0]["claim_ceiling"] = ""
    network["integration_responses"][0]["alternative_explanations"] = []
    network["unmapped_residue"][0]["description"] = ""
    errors = validate_network(network)
    assert any("missing provenance" in error for error in errors), errors
    assert any("missing claim_ceiling" in error for error in errors), errors
    assert any("alternative_explanations" in error for error in errors), errors
    assert any("missing non-empty description" in error for error in errors), errors


def test_embedding_probe_has_independent_strict_contract():
    probe = load_network(Path("data/architecture/adaptive-relational-network/examples/embedding-probe.json"))
    assert validate_embedding_probe_contract(probe) == []
    probe["silent_extra"] = "forbidden"
    assert validate_embedding_probe_contract(probe)
