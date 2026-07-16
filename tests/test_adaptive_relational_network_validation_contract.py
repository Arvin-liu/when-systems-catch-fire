import copy
from pathlib import Path

from tools.adaptive_relational_network.temporal import path_continuous, time_respecting_graph_path, time_respecting_sequence
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


def make_relation(relation_id, source, target, direction="directed", start=1, end=2):
    return {
        "relation_id": relation_id,
        "source": source,
        "target": target,
        "relation_class": "dependency",
        "direction": direction,
        "sign": "neutral",
        "weight": 1.0,
        "conditions": ["test"],
        "layer": "knowledge",
        "temporal_bounds": {"start": start, "end": end},
        "provenance": ["test"],
        "uncertainty": "test",
        "claim_ceiling": "test relation only",
    }


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


def test_empty_path_false_and_single_edge_true():
    network = valid_network()
    assert not path_continuous(network, [])
    assert not time_respecting_sequence(network, [])
    assert not time_respecting_graph_path(network, [])
    assert path_continuous(network, ["r-info-judgment"])
    assert time_respecting_graph_path(network, ["r-info-judgment"])


def test_stateful_orientation_rejects_global_pairwise_false_positive():
    network = valid_network()
    network["nodes"] = [
        {**network["nodes"][0], "node_id": node_id, "layers": ["knowledge"]}
        for node_id in ["A", "B", "C", "D"]
    ]
    network["relations"] = [
        make_relation("e1", "A", "B", "directed", 1, 2),
        make_relation("e2", "B", "C", "undirected", 3, 4),
        make_relation("e3", "B", "D", "directed", 5, 6),
    ]
    assert not path_continuous(network, ["e1", "e2", "e3"])
    assert not time_respecting_graph_path(network, ["e1", "e2", "e3"])


def test_stateful_orientation_accepts_consistent_undirected_and_bidirectional_paths():
    network = valid_network()
    network["nodes"] = [
        {**network["nodes"][0], "node_id": node_id, "layers": ["knowledge"]}
        for node_id in ["A", "B", "C", "D"]
    ]
    network["relations"] = [
        make_relation("e1", "A", "B", "directed", 1, 2),
        make_relation("e2", "B", "C", "undirected", 3, 4),
        make_relation("e3", "C", "D", "bidirectional", 5, 6),
    ]
    assert path_continuous(network, ["e1", "e2", "e3"])
    assert time_respecting_graph_path(network, ["e1", "e2", "e3"])


def test_unknown_direction_breaks_stateful_path():
    network = valid_network()
    network["relations"][1]["direction"] = "unknown"
    assert not path_continuous(network, ["r-info-judgment", "r-judgment-action"])


def test_empty_claim_ceiling_provenance_alternatives_and_residue_are_rejected():
    network = valid_network()
    network["nodes"][0]["provenance"] = []
    network["relations"][0]["claim_ceiling"] = ""
    network["integration_responses"][0]["alternative_explanations"] = []
    network["unmapped_residue"][0]["description"] = ""
    errors = validate_network(network)
    assert any("provenance" in error for error in errors), errors
    assert any("claim_ceiling" in error for error in errors), errors
    assert any("alternative_explanations" in error for error in errors), errors
    assert any("missing non-empty description" in error for error in errors), errors


def test_temporal_activation_rejects_non_node_relation_targets():
    network = valid_network()
    target_cases = [
        network["layers"][0]["layer_id"],
        network["network_states"][0]["state_id"],
        network["perturbations"][0]["perturbation_id"],
        network["embedding_evidence"][0]["record_id"],
        network["network_spec"]["network_id"],
    ]
    for target in target_cases:
        mutated = valid_network()
        mutated["temporal_activations"][0]["target_ref"] = target
        assert_rejected(mutated, f"dangling reference {target}")


def test_every_id_bearing_collection_rejects_duplicates():
    id_fields = {
        "nodes": "node_id",
        "relations": "relation_id",
        "layers": "layer_id",
        "hyper_relations": "hyper_id",
        "interlayer_couplings": "coupling_id",
        "temporal_activations": "activation_id",
        "network_states": "state_id",
        "perturbations": "perturbation_id",
        "integration_responses": "response_id",
        "reconfiguration_episodes": "episode_id",
        "attractor_or_oscillation": "record_id",
        "cascade_or_spillover": "record_id",
        "embedding_evidence": "record_id",
        "projections": "projection_id",
        "diffs": "diff_id",
        "unmapped_residue": "residue_id",
    }
    for collection, field in id_fields.items():
        network = valid_network()
        network[collection].append(copy.deepcopy(network[collection][0]))
        errors = validate_network(network)
        assert any("duplicate" in error and network[collection][0][field] in error for error in errors), (collection, errors)


def test_attractor_and_cascade_need_semantic_content():
    network = valid_network()
    network["attractor_or_oscillation"][0]["loop_pattern"] = []
    network["cascade_or_spillover"][0]["path"] = []
    errors = validate_network(network)
    assert any("loop_pattern" in error for error in errors), errors
    assert any("path" in error for error in errors), errors


def test_diff_refs_must_be_local_or_declared_external_refs():
    network = valid_network()
    network["diffs"] = [{
        "diff_id": "d1",
        "from_ref": "arbitrary-before",
        "to_ref": "arbitrary-after",
        "node_changes": [],
        "relation_changes": [],
        "layer_changes": [],
        "boundary_changes": [],
        "claim_ceiling": "diff only",
    }]
    errors = validate_network(network)
    assert any("dangling reference arbitrary-before" in error for error in errors), errors
    assert any("dangling reference arbitrary-after" in error for error in errors), errors
    network["diffs"][0]["external_refs"] = [
        {"ref_id": "arbitrary-before", "ref_type": "git_commit", "claim_ceiling": "external ref only"},
        {"ref_id": "arbitrary-after", "ref_type": "git_commit", "claim_ceiling": "external ref only"},
    ]
    assert validate_network(network) == []


def test_diff_external_refs_reject_duplicates_conflicts_and_local_collisions():
    network = valid_network()
    local_id = network["network_spec"]["network_id"]
    network["diffs"] = [{
        "diff_id": "d1",
        "from_ref": "ext",
        "to_ref": "ext",
        "external_refs": [
            {"ref_id": "ext", "ref_type": "git_commit", "claim_ceiling": "external ref only"},
            {"ref_id": "ext", "ref_type": "git_commit", "claim_ceiling": "external ref only"},
        ],
        "node_changes": [],
        "relation_changes": [],
        "layer_changes": [],
        "boundary_changes": [],
        "claim_ceiling": "diff only",
    }]
    assert_rejected(network, "duplicate external ref id ext")
    network["diffs"][0]["external_refs"][1]["ref_type"] = "external_projection"
    assert_rejected(network, "conflicting external ref ext")
    network["diffs"][0]["external_refs"] = [{"ref_id": local_id, "ref_type": "git_commit", "claim_ceiling": "external ref only"}]
    network["diffs"][0]["from_ref"] = local_id
    network["diffs"][0]["to_ref"] = local_id
    assert_rejected(network, f"external_ref {local_id} collides with local diff reference")


def test_diff_local_reference_namespace_must_not_collide():
    network = valid_network()
    network["network_states"][0]["state_id"] = network["network_spec"]["network_id"]
    assert_rejected(network, "diff reference namespace collision")


def test_semantic_nonblank_rejects_whitespace_only_required_content():
    network = valid_network()
    network["attractor_or_oscillation"][0]["loop_pattern"] = ["  ", "\t"]
    network["cascade_or_spillover"][0]["path"] = ["   "]
    network["nodes"][0]["provenance"] = ["  "]
    network["integration_responses"][0]["alternative_explanations"] = ["  "]
    network["reconfiguration_episodes"][0]["residue"] = ["  "]
    network["embedding_evidence"][0]["evidence"] = ["  "]
    network["embedding_evidence"][0]["claim_ceiling"] = "   "
    errors = validate_network(network)
    assert any("loop_pattern" in error for error in errors), errors
    assert any("path" in error for error in errors), errors
    assert any("provenance" in error for error in errors), errors
    assert any("alternative_explanations" in error for error in errors), errors
    assert any("residue" in error for error in errors), errors
    assert any("evidence" in error for error in errors), errors
    assert any("claim_ceiling" in error for error in errors), errors


def test_optional_empty_diff_change_arrays_remain_valid():
    network = valid_network()
    network["diffs"] = [{
        "diff_id": "d1",
        "from_ref": network["network_states"][0]["state_id"],
        "to_ref": network["projections"][0]["projection_id"],
        "node_changes": [],
        "relation_changes": [],
        "layer_changes": [],
        "boundary_changes": [],
        "claim_ceiling": "diff with no category changes is allowed",
    }]
    assert validate_network(network) == []


def test_embedding_probe_has_independent_strict_contract():
    probe = load_network(Path("data/architecture/adaptive-relational-network/examples/embedding-probe.json"))
    assert validate_embedding_probe_contract(probe) == []
    probe["silent_extra"] = "forbidden"
    assert validate_embedding_probe_contract(probe)
