# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""R3 corpus runtime — checkpoint/resume, crash recovery, replay, incremental.

Implements the six mandatory recovery demonstrations from IGNITION §10 against the
synthetic corpus: clean full run, >=10% interrupt+resume, ~50% interrupt+resume,
final-shard interrupt+resume, idempotent replay (no duplicate), and changed-note
selective rerun (isolated copy, never the frozen fixture).
"""
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.r3_synthetic_corpus import build_synthetic_corpus
from tools.adaptive_relational_runtime.corpus import (
    run_full,
    CrashInjection,
    stage_a_mechanical_pass,
    build_shard_plan,
)

SHARD_COUNT = 4


def _plan_keys(corpus):
    recs = [r for r in stage_a_mechanical_pass(corpus) if r.identity.note_type != "index"]
    plan = build_shard_plan([r.identity for r in recs], SHARD_COUNT, "synthetic")
    return plan, recs


def test_clean_full_run_produces_all_receipts(tmp_path):
    out = tmp_path / "out"
    run_full(str(build_synthetic_corpus(tmp_path / "corpus")), str(out), "synthetic", shard_count=SHARD_COUNT)
    receipts = list((out / "receipts").glob("*.json"))
    assert len(receipts) == 29
    summary = json.loads((out / "RUN_SUMMARY.json").read_text(encoding="utf-8"))
    assert summary["committed"] == 29
    assert summary["reprocessed"] == 29


def test_idempotent_replay_no_duplicate(tmp_path):
    out = tmp_path / "out"
    corpus = build_synthetic_corpus(tmp_path / "corpus")
    run_full(str(corpus), str(out), "synthetic", shard_count=SHARD_COUNT)
    before = {p.name for p in (out / "receipts").glob("*.json")}
    summary = run_full(str(corpus), str(out), "synthetic", shard_count=SHARD_COUNT)
    after = {p.name for p in (out / "receipts").glob("*.json")}
    assert before == after  # no new authoritative records
    assert summary["reprocessed"] == 0  # replay did not reprocess
    assert summary["committed"] == 29


def test_crash_at_10pct_then_resume(tmp_path):
    out = tmp_path / "out"
    corpus = build_synthetic_corpus(tmp_path / "corpus")
    plan, _ = _plan_keys(corpus)
    all_keys = [k for m in plan.shards for k in m["object_keys"]]
    crash_key = all_keys[max(1, len(all_keys) // 10)]
    with pytest.raises(CrashInjection):
        run_full(str(corpus), str(out), "synthetic", shard_count=SHARD_COUNT, crash_at_key=crash_key)
    # resume
    summary = run_full(str(corpus), str(out), "synthetic", shard_count=SHARD_COUNT)
    assert summary["committed"] == 29
    assert len(list((out / "receipts").glob("*.json"))) == 29


def test_crash_at_50pct_then_resume(tmp_path):
    out = tmp_path / "out"
    corpus = build_synthetic_corpus(tmp_path / "corpus")
    plan, _ = _plan_keys(corpus)
    all_keys = [k for m in plan.shards for k in m["object_keys"]]
    crash_key = all_keys[len(all_keys) // 2]
    with pytest.raises(CrashInjection):
        run_full(str(corpus), str(out), "synthetic", shard_count=SHARD_COUNT, crash_at_key=crash_key)
    summary = run_full(str(corpus), str(out), "synthetic", shard_count=SHARD_COUNT)
    assert summary["committed"] == 29
    assert len(list((out / "receipts").glob("*.json"))) == 29


def test_crash_at_final_shard_then_resume(tmp_path):
    out = tmp_path / "out"
    corpus = build_synthetic_corpus(tmp_path / "corpus")
    plan, _ = _plan_keys(corpus)
    last_shard = plan.shards[-1]["object_keys"]
    crash_key = last_shard[-1]
    with pytest.raises(CrashInjection):
        run_full(str(corpus), str(out), "synthetic", shard_count=SHARD_COUNT, crash_at_key=crash_key)
    summary = run_full(str(corpus), str(out), "synthetic", shard_count=SHARD_COUNT)
    assert summary["committed"] == 29
    assert len(list((out / "receipts").glob("*.json"))) == 29


def test_crash_leaves_only_committed_no_partial(tmp_path):
    out = tmp_path / "out"
    corpus = build_synthetic_corpus(tmp_path / "corpus")
    plan, _ = _plan_keys(corpus)
    all_keys = [k for m in plan.shards for k in m["object_keys"]]
    crash_key = all_keys[len(all_keys) // 3]
    with pytest.raises(CrashInjection):
        run_full(str(corpus), str(out), "synthetic", shard_count=SHARD_COUNT, crash_at_key=crash_key)
    # the crashed key must NOT have a receipt (it was never committed)
    crash_receipt = out / "receipts" / f"{crash_key}.json"
    assert not crash_receipt.exists()
    # every other key either has a receipt or will on resume; resume completes all
    run_full(str(corpus), str(out), "synthetic", shard_count=SHARD_COUNT)
    assert crash_receipt.exists()


def test_changed_note_selective_rerun_isolated(tmp_path):
    # isolated COPY of the corpus; never touch the frozen fixture
    src = tmp_path / "src"
    work = tmp_path / "work"
    shutil.copytree(build_synthetic_corpus(src), work)
    out = tmp_path / "out"
    run_full(str(work), str(out), "synthetic", shard_count=SHARD_COUNT)
    # modify exactly one note
    target = work / "syn-000.md"
    target.write_text(target.read_text(encoding="utf-8") + "\nAPPENDED CHANGE\n", encoding="utf-8")
    summary = run_full(str(work), str(out), "synthetic", shard_count=SHARD_COUNT)
    # only the changed note was reprocessed; the other 28 were skipped
    assert summary["reprocessed"] == 1
    assert summary["committed"] == 29
