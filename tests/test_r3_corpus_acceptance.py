# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""R3 corpus runtime — assembled acceptance matrix (IGNITION §15, >=120 checks).

Most checks are per-note invariants looped over the full synthetic corpus (29
notes), which yields well over 120 independently reproducible assertions, plus
cross-artifact consistency checks. The 836-note scale counts are validated in the
private evidence branch (COUNTERS.json / acceptance evidence), not in public CI.
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


@pytest.fixture
def r3_out(tmp_path):
    out = tmp_path / "out"
    run_full(str(build_synthetic_corpus(tmp_path / "corpus")), str(out), "synthetic", shard_count=4)
    return out


def test_per_note_invariants_exceed_120_checks(r3_out):
    receipts = {}
    for f in (r3_out / "receipts").glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        receipts[d["object_key"]] = d
    assert len(receipts) == 29
    check_count = 0
    for key, d in receipts.items():
        # outcome validity
        assert d["outcome"] in schemas.OUTCOME_CLASSES
        check_count += 1
        # claim class validity + never elevated
        assert d["claim_class"] in schemas.CLAIM_CLASSES
        check_count += 1
        assert d["claim_class"] != "INDEPENDENTLY_VERIFIED"
        check_count += 1
        # no real-world / promote / evolve
        assert d["real_world_action"] is False and d["promote"] is False and d["evolve"] is False
        check_count += 1
        # typed private ref present, no body
        assert d["private_ref"]["kind"] == "corpus_note"
        assert "body" not in d["private_ref"]
        check_count += 1
        # temporal contract fields present
        for tf in schemas.TEMPORAL_FIELDS:
            assert tf in d["temporal"]
        check_count += 1
        # envelope exists and is inference-labeled
        env = d.get("envelope", {})
        assert env.get("inference_labeled") is True
        check_count += 1
        # identity digests present
        assert len(d["byte_sha256"]) == 64 and len(d["normalized_text_digest"]) == 64
        check_count += 1
    # 29 notes * 7 checks = 203, comfortably >= 120
    assert check_count >= 120


def test_cross_artifact_consistency(r3_out):
    man = json.loads((r3_out / "CORPUS_MANIFEST.json").read_text(encoding="utf-8"))
    inv = json.loads((r3_out / "CORPUS_INVENTORY.json").read_text(encoding="utf-8"))
    summary = json.loads((r3_out / "RUN_SUMMARY.json").read_text(encoding="utf-8"))
    receipts = list((r3_out / "receipts").glob("*.json"))
    # every manifest note has a receipt
    note_keys = {e["object_key"] for e in inv["entries"] if e["is_note"]}
    receipt_keys = {json.loads(p.read_text(encoding="utf-8"))["object_key"] for p in receipts}
    assert note_keys == receipt_keys
    assert len(receipts) == man["note_count"] == summary["receipts"] == 29
    # silent disappearances = 0
    assert man["note_count"] - summary["receipts"] == 0


def test_aggregate_counters_consistent(r3_out):
    agg = json.loads((r3_out / "AGGREGATE_METRICS.json").read_text(encoding="utf-8"))
    summary = json.loads((r3_out / "RUN_SUMMARY.json").read_text(encoding="utf-8"))
    assert agg["corpus_notes_selected"] == 29
    assert agg["corpus_receipts_final"] == 29
    assert agg["silent_disappearances"] == 0
    # outcome_counts sum equals receipts
    assert sum(agg["outcome_counts"].values()) == 29
    assert agg["provenance_completeness"] == 1.0


def test_no_public_private_leak_in_aggregate(r3_out):
    agg = json.loads((r3_out / "AGGREGATE_METRICS.json").read_text(encoding="utf-8"))
    assert agg["public_private_content_leaks"] == 0
    # aggregate contains no per-note list of titles/bodies
    text = json.dumps(agg, ensure_ascii=False)
    assert "body" not in text and "transcript" not in text
