# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""R3 corpus runtime — Stage B semantic adapter: epistemic ceilings + temporal.

Verifies the bounded semantic pass never elevates a speaker/company claim to
INDEPENDENTLY_VERIFIED, enforces the temporal contract (event_time distinct from
created_at, never guessed), and emits one envelope + one receipt per note.
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
    EVT_NOTE,
    NO_CREATE_NOTE,
    BADFM_NOTE,
)
from tools.adaptive_relational_runtime.corpus import run_full


@pytest.fixture
def r3_out(tmp_path):
    out = tmp_path / "out"
    run_full(str(build_synthetic_corpus(tmp_path / "corpus")), str(out), "synthetic", shard_count=4)
    return out


def test_no_independently_verified_ever(r3_out):
    for f in (r3_out / "receipts").glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        assert d["claim_class"] != "INDEPENDENTLY_VERIFIED"


def test_claim_class_by_type(r3_out):
    by_key = {}
    for f in (r3_out / "receipts").glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        by_key[d["object_key"]] = d
    links = [k for k, v in by_key.items() if v["note_type"] == "link"]
    plains = [k for k, v in by_key.items() if v["note_type"] == "plain_text"]
    audios = [k for k, v in by_key.items() if v["note_type"] in ("local_audio", "recorder_audio")]
    assert all(by_key[k]["claim_class"] == "SECONDARY_ARCHIVE_CLAIM" for k in links)
    assert all(by_key[k]["claim_class"] == "AUTHOR_OBSERVATION" for k in plains)
    assert all(by_key[k]["claim_class"] == "TRANSCRIPT_INFERENCE" for k in audios)


def test_event_time_extracted_only_when_explicit(r3_out):
    for f in (r3_out / "receipts").glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        if d["object_key"] == EVT_NOTE:
            assert d["temporal"]["event_time"] == "2026-07-26"
        else:
            assert d["temporal"]["event_time"] == "UNKNOWN"


def test_event_time_distinct_from_created_at(r3_out):
    evt = json.loads((r3_out / "receipts" / f"{EVT_NOTE}.json").read_text(encoding="utf-8"))
    assert evt["temporal"]["event_time"] != evt["temporal"]["note_created_at"]
    assert evt["temporal"]["note_created_at"] == "2026-07-10 10:00:00"


def test_missing_created_at_not_guessed(r3_out):
    nc = json.loads((r3_out / "receipts" / f"{NO_CREATE_NOTE}.json").read_text(encoding="utf-8"))
    assert nc["temporal"]["note_created_at"] == "UNKNOWN"
    assert nc["temporal"]["event_time"] == "UNKNOWN"


def test_malformed_frontmatter_quarantined_not_silent(r3_out):
    bad = json.loads((r3_out / "receipts" / f"{BADFM_NOTE}.json").read_text(encoding="utf-8"))
    assert bad["outcome"] == "EXPECTED_QUARANTINE"
    summary = json.loads((r3_out / "RUN_SUMMARY.json").read_text(encoding="utf-8"))
    assert summary["receipts"] == 29  # every note accounted for


def test_one_envelope_per_note_and_inference_labeled(r3_out):
    env_files = list((r3_out / "envelopes").glob("*.json"))
    assert len(env_files) == 29
    for f in env_files:
        d = json.loads(f.read_text(encoding="utf-8"))
        assert d["inference_labeled"] is True
        assert "body" not in d and "text" not in d


def test_receipts_carry_no_promote_evolve_real_world(r3_out):
    for f in (r3_out / "receipts").glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        assert d["real_world_action"] is False
        assert d["promote"] is False
        assert d["evolve"] is False
        assert d["private_ref"]["kind"] == "corpus_note"


def test_speaker_company_claim_never_elevated_to_verified(r3_out):
    # plain_text notes are AUTHOR_OBSERVATION, never INDEPENDENTLY_VERIFIED
    for f in (r3_out / "receipts").glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        if d["claim_class"] in ("SPEAKER_CLAIM", "COMPANY_SELF_REPORT"):
            assert d["claim_class"] != "INDEPENDENTLY_VERIFIED"
