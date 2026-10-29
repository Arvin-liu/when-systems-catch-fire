import json
from pathlib import Path

from tools.adaptive_relational_network.diff import network_diff, pairwise_projection_with_residue, stable_hash
from tools.adaptive_relational_network.embedding import summarize_embedding_evidence
from tools.adaptive_relational_network.projector import project_from_sources
from tools.adaptive_relational_network.renderer import render_markdown, render_timeline
from tools.adaptive_relational_network.temporal import static_aggregation_false_positive, time_respecting


REAL = Path("data/architecture/adaptive-relational-network/real-history")
BEFORE = "1f3815538cf56d0f35cc06c6b2396fadf33a34a2"


def load(name):
    return json.loads((REAL / name).read_text())


def test_real_history_diff_is_from_real_commit_pair():
    diff = load("network-diff.json")
    replay = load("deterministic-replay.json")
    assert diff["from_ref"] == BEFORE
    assert diff["to_ref"] == replay["after_commit"]
    assert replay["before_source_count"] == 0
    assert replay["after_source_count"] >= 10
    assert diff["added_nodes"]
    assert diff["added_relations"]


def test_real_history_replay_hash_is_deterministic():
    before = load("before-projection.json")
    after = load("after-projection.json")
    diff = network_diff(before, after)
    replay = load("deterministic-replay.json")
    assert diff["deterministic_hash"] == replay["diff_hash"]
    assert stable_hash(before) == replay["before_hash"]
    assert stable_hash(after) == replay["after_hash"]


def test_temporal_valid_and_static_false_positive_paths():
    after = load("after-projection.json")
    replay = load("deterministic-replay.json")
    assert time_respecting(after, replay["valid_path"])
    assert replay["valid_path"] == ["rel-repo-1", "rel-chain-1"]
    assert replay["valid_path_time_respecting_graph_path"] is True
    false_positive = replay["invalid_static_path"]
    assert false_positive["static_exists"] is True
    assert false_positive["time_respecting_sequence"] is True
    assert false_positive["time_respecting_graph_path"] is False
    assert false_positive["time_respecting"] is False
    assert false_positive["is_false_positive"] is True
    temporal_negative = replay["temporally_invalid_connected_path"]
    assert temporal_negative["path"] == ["rel-repo-1", "rel-backdated-1"]
    assert temporal_negative["time_respecting_graph_path"] is False


def test_higher_order_pairwise_projection_records_residue():
    after = load("after-projection.json")
    pairwise = pairwise_projection_with_residue(after)
    saved = load("pairwise-hyperrelation-projection.json")
    assert pairwise == saved
    assert pairwise["residue"]
    loss_text = pairwise["residue"][0]["information_loss"].lower()
    assert "loss" in loss_text or "loses" in loss_text


def test_embedding_summary_keeps_axes_independent():
    after = load("after-projection.json")
    summary = summarize_embedding_evidence(after)
    saved = load("embedding-summary.json")
    assert summary == saved
    axes = {axis["axis"] for axis in summary["axes"]}
    assert {"external_availability", "retrieval", "judgment_change", "action_change", "transfer"} <= axes
    assert "not a learning score" in summary["claim_ceiling"]


def test_renderer_outputs_are_projection_limited():
    after = load("after-projection.json")
    md = render_markdown(after, layer="architecture")
    timeline = render_timeline(after)
    assert "projection" in md.lower()
    assert "Timeline" in timeline
