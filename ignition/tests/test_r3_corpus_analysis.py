# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""R3 corpus runtime — analysis layer (dedup, temporal, source-independence).

Mechanism checks on the synthetic corpus: exact/near duplicates, temporal index +
ambiguity ledger, source-dependency graph, false-consensus risk, independent-source
estimate. All derived from hashes/hosts only.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.r3_synthetic_corpus import (
    build_synthetic_corpus,
    EXACT_DUP_PAIR,
    NEAR_DUP_PAIR,
    SHARED_HOST,
    SHARED_PAIR,
    EVT_NOTE,
)
from tools.adaptive_relational_runtime.corpus import run_full


@pytest.fixture
def r3_out(tmp_path):
    out = tmp_path / "out"
    run_full(str(build_synthetic_corpus(tmp_path / "corpus")), str(out), "synthetic", shard_count=4)
    return out


def test_exact_byte_duplicate_detected(r3_out):
    d = json.loads((r3_out / "EXACT_DUPLICATES.json").read_text(encoding="utf-8"))
    assert d["exact_duplicate_groups"] >= 1
    # the dup pair is normalized-text identical (different note_id in frontmatter)
    flat = {h: ks for h, ks in d["normalized_identical_groups"].items()}
    joined = [k for ks in flat.values() for k in ks]
    assert EXACT_DUP_PAIR[0] in joined and EXACT_DUP_PAIR[1] in joined


def test_near_duplicate_cluster_detected(r3_out):
    d = json.loads((r3_out / "NEAR_DUPLICATE_CLUSTERS.json").read_text(encoding="utf-8"))
    assert d["near_duplicate_clusters"] >= 1
    joined = [k for grp in d["clusters"] for k in grp]
    assert NEAR_DUP_PAIR[0] in joined and NEAR_DUP_PAIR[1] in joined


def test_temporal_index_and_ambiguity(r3_out):
    idx = json.loads((r3_out / "TEMPORAL_INDEX.json").read_text(encoding="utf-8"))
    amb = json.loads((r3_out / "TEMPORAL_AMBIGUITY_LEDGER.json").read_text(encoding="utf-8"))
    assert EVT_NOTE in idx["entries"]
    assert idx["entries"][EVT_NOTE]["event_time"] == "2026-07-26"
    assert amb["ambiguous_keys"]  # most notes have UNKNOWN event_time
    assert 0.0 <= amb["temporal_ambiguity_rate"] <= 1.0


def test_source_dependency_graph_groups_shared_host(r3_out):
    d = json.loads((r3_out / "SOURCE_DEPENDENCY_GRAPH.json").read_text(encoding="utf-8"))
    assert SHARED_HOST in d["host_map"]
    assert set(d["host_map"][SHARED_HOST]) == set(SHARED_PAIR)
    assert SHARED_HOST in d["shared_source_derivatives"]


def test_false_consensus_risk_flagged(r3_out):
    d = json.loads((r3_out / "FALSE_CONSENSUS_CASES.json").read_text(encoding="utf-8"))
    assert d["false_consensus_risk"] >= 1
    hosts = [c["source_host"] for c in d["cases"]]
    assert SHARED_HOST in hosts


def test_independent_source_estimate_positive(r3_out):
    d = json.loads((r3_out / "INDEPENDENT_SOURCE_ESTIMATE.json").read_text(encoding="utf-8"))
    assert d["estimate"] > 0
    assert d["notes_with_source"] > 0


def test_same_source_repetition_not_counted_as_independent(r3_out):
    # the shared pair is grouped under one host; it must not inflate the
    # "independent evidence" count beyond the distinct-host estimate
    dep = json.loads((r3_out / "SOURCE_DEPENDENCY_GRAPH.json").read_text(encoding="utf-8"))
    indep = json.loads((r3_out / "INDEPENDENT_SOURCE_ESTIMATE.json").read_text(encoding="utf-8"))
    # distinct hosts is the independent-source estimate, capped by host count
    assert indep["estimate"] == len(dep["host_map"])
