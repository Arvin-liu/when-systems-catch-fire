# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""R3 corpus runtime — public/private boundary guarantees (IGNITION §12).

The public runtime's data model MUST be structurally incapable of carrying private
content: receipts/envelopes carry only hashes + typed fields; aggregate metrics
carry only counts/rates. These tests assert that structure and that PROMOTE/EVOLVE/
real-world counters are zero.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.r3_synthetic_corpus import build_synthetic_corpus
from tools.adaptive_relational_runtime.corpus import run_full, schemas

RECEIPT_KEYS = {
    "receipt_id", "run_id", "object_key", "note_type", "path_digest",
    "byte_sha256", "normalized_text_digest", "outcome", "claim_class",
    "temporal", "source_ref_present", "rights_boundary", "private_ref",
    "real_world_action", "promote", "evolve", "generated_at", "envelope_id", "envelope",
}
PRIVATE_REF_KEYS = {"kind", "note_id", "note_type", "byte_sha256", "path_digest", "normalized_text_digest"}


@pytest.fixture
def r3_out(tmp_path):
    out = tmp_path / "out"
    run_full(str(build_synthetic_corpus(tmp_path / "corpus")), str(out), "synthetic", shard_count=4)
    return out


def test_receipt_schema_has_no_body_field(r3_out):
    for f in (r3_out / "receipts").glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        assert set(d.keys()) <= RECEIPT_KEYS
        assert "body" not in d and "content" not in d and "transcript" not in d and "title" not in d
        assert set(d["private_ref"].keys()) <= PRIVATE_REF_KEYS
        # defensive: no individual string field embeds a long verbatim block
        for v in d.values():
            if isinstance(v, str):
                assert len(v) <= 240, f"long verbatim field in receipt: {v[:40]!r}"


def test_envelope_has_no_body_field(r3_out):
    for f in (r3_out / "envelopes").glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        assert set(d.keys()) <= {"envelope_id", "object_key", "claim_class", "claim_surface", "temporal", "inference_labeled"}
        assert "body" not in d


def test_manifest_identities_have_no_body(r3_out):
    man = json.loads((r3_out / "CORPUS_MANIFEST.json").read_text(encoding="utf-8"))
    for ident in man["identities"]:
        assert "body" not in ident and "title" not in ident
        assert set(ident.keys()) <= {
            "object_key", "rel_path", "path_digest", "byte_sha256",
            "normalized_text_digest", "note_id", "note_type", "size_bytes",
        }


def test_aggregate_metrics_are_counts_only(r3_out):
    agg = json.loads((r3_out / "AGGREGATE_METRICS.json").read_text(encoding="utf-8"))
    # no nested per-note detail, only scalars
    for k, v in agg.items():
        assert isinstance(v, (int, float, dict)) or k in ("type_distribution", "outcome_counts")
        if isinstance(v, dict):
            # these two are small count maps, not per-note detail
            assert all(isinstance(x, (int, float, str)) for x in v.values())
    assert agg["promote_calls"] == 0
    assert agg["evolve_calls"] == 0
    assert agg["real_world_actions"] == 0
    assert agg["public_private_content_leaks"] == 0
    assert agg["source_notes_modified"] == 0
    assert agg["silent_disappearances"] == 0


def test_no_forbidden_action_in_any_receipt(r3_out):
    for f in (r3_out / "receipts").glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        assert d["promote"] is False
        assert d["evolve"] is False
        assert d["real_world_action"] is False
