# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""R3 corpus runtime — Stage A inventory, manifest, audits, shard plan.

Mechanism-level acceptance (synthetic corpus only; the 836-note scale counts are
verified in the private evidence branch, not in public CI).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.r3_synthetic_corpus import (
    build_synthetic_corpus,
    EXPECTED_NOTE_COUNT,
    EXACT_DUP_PAIR,
    NEAR_DUP_PAIR,
    SHARED_PAIR,
    BADFM_NOTE,
    INDEX_FILE,
)
from tools.adaptive_relational_runtime.corpus import (
    stage_a_mechanical_pass,
    build_corpus_manifest,
    build_corpus_inventory,
    build_frontmatter_audit,
    build_note_id_audit,
    build_encoding_parse_errors,
    build_shard_plan,
    is_key_in_namespace,
)


def _notes(recs):
    return [r for r in recs if r.identity.note_type != "index"]


def test_record_count_is_notes_plus_index(tmp_path):
    recs = stage_a_mechanical_pass(build_synthetic_corpus(tmp_path / "corpus"))
    notes = _notes(recs)
    index = [r for r in recs if r.identity.note_type == "index"]
    assert len(notes) == EXPECTED_NOTE_COUNT
    assert len(index) == 1
    assert len(recs) == EXPECTED_NOTE_COUNT + 1


def test_type_distribution(tmp_path):
    recs = stage_a_mechanical_pass(build_synthetic_corpus(tmp_path / "corpus"))
    notes = _notes(recs)
    dist = {}
    for r in notes:
        dist[r.identity.note_type] = dist.get(r.identity.note_type, 0) + 1
    # link 8 base + 2 shared = 10; plain_text 6 + 2 dup + 2 near + evt + nocreate + badfm = 13
    assert dist["link"] == 10
    assert dist["plain_text"] == 13
    assert dist["local_audio"] == 3
    assert dist["recorder_audio"] == 3


def test_frontmatter_validity(tmp_path):
    recs = stage_a_mechanical_pass(build_synthetic_corpus(tmp_path / "corpus"))
    fa = build_frontmatter_audit(recs)
    assert fa["valid"] == EXPECTED_NOTE_COUNT - 1 + 1 - 1  # note: 28 notes valid + index
    # exactly badfm and index are invalid
    assert BADFM_NOTE in fa["invalid_object_keys"]
    assert INDEX_FILE in fa["invalid_object_keys"]
    assert len(fa["invalid_object_keys"]) == 2


def test_note_id_uniqueness_and_no_path_mismatch(tmp_path):
    recs = stage_a_mechanical_pass(build_synthetic_corpus(tmp_path / "corpus"))
    na = build_note_id_audit(recs)
    assert na["distinct_note_ids"] == EXPECTED_NOTE_COUNT
    assert na["duplicate_note_id_groups"] == {}
    assert na["path_note_id_mismatches"] == []


def test_encoding_and_parse_errors_capture_malformed(tmp_path):
    recs = stage_a_mechanical_pass(build_synthetic_corpus(tmp_path / "corpus"))
    epe = build_encoding_parse_errors(recs)
    assert epe["error_count"] == 2
    keys = [e["object_key"] for e in epe["entries"]]
    assert BADFM_NOTE in keys
    assert INDEX_FILE in keys


def test_manifest_constant_and_counts(tmp_path):
    recs = stage_a_mechanical_pass(build_synthetic_corpus(tmp_path / "corpus"))
    man = build_corpus_manifest(recs, "synthetic")
    assert man["expected_notes"] == 836  # locked spec expectation
    assert man["note_count"] == EXPECTED_NOTE_COUNT
    assert man["index_count"] == 1
    assert man["total_paths"] == EXPECTED_NOTE_COUNT + 1


def test_inventory_entries_have_only_typed_fields(tmp_path):
    recs = stage_a_mechanical_pass(build_synthetic_corpus(tmp_path / "corpus"))
    inv = build_corpus_inventory(recs)
    assert inv["count"] == EXPECTED_NOTE_COUNT + 1
    for e in inv["entries"]:
        assert set(e.keys()) <= {
            "object_key", "rel_path", "note_id", "note_type",
            "size_bytes", "byte_sha256", "normalized_text_digest", "is_note",
        }
        assert "body" not in e and "title" not in e


def test_shard_plan_deterministic_under_reorder(tmp_path):
    base = build_synthetic_corpus(tmp_path / "corpus")
    recs = stage_a_mechanical_pass(base)
    p1 = build_shard_plan([r.identity for r in recs], 8, "synthetic")
    import random
    shuffled = list(recs)
    random.shuffle(shuffled)
    p2 = build_shard_plan([r.identity for r in shuffled], 8, "synthetic")
    assert p1.plan_digest == p2.plan_digest
    assert p1.object_count == p2.object_count == EXPECTED_NOTE_COUNT + 1


def test_shard_namespace_isolation(tmp_path):
    recs = stage_a_mechanical_pass(build_synthetic_corpus(tmp_path / "corpus"))
    plan = build_shard_plan([r.identity for r in recs], 8, "synthetic")
    # every key belongs to exactly one shard
    counts = {}
    for m in plan.shards:
        for k in m["object_keys"]:
            counts[k] = counts.get(k, 0) + 1
    assert all(v == 1 for v in counts.values())
    # is_key_in_namespace agrees
    some_key = next(iter(counts))
    owners = [m["shard_id"] for m in plan.shards if some_key in m["object_keys"]]
    assert len(owners) == 1
    assert is_key_in_namespace(plan, owners[0], some_key)
    assert not is_key_in_namespace(plan, "shard-000", "nonexistent-key")


def test_shard_plan_membership_derived_from_frozen_identity(tmp_path):
    recs = stage_a_mechanical_pass(build_synthetic_corpus(tmp_path / "corpus"))
    plan = build_shard_plan([r.identity for r in recs], 4, "synthetic")
    # all object keys present exactly once across shards
    all_keys = [k for m in plan.shards for k in m["object_keys"]]
    assert len(all_keys) == len(set(all_keys)) == EXPECTED_NOTE_COUNT + 1
