# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Generic corpus run orchestrator with deterministic checkpoint/resume.

The orchestrator owns the crash-safe loop: it processes objects shard-by-shard in
deterministic order, writing each receipt atomically and committing the key to the
checkpoint only afterwards (see ``checkpoint.crash_safe_step``). It supports:

  * resume          — skip already-committed keys
  * crash injection  — raise before processing a designated key (demo harness)
  * changed-key rerun — a note whose byte hash changed is force-rerun (closure
                        extension is handled by the analysis layer)
  * bounded retry    — a failing object is retried up to ``max_retries`` then
                        terminal-quarantined as ``RETRY_EXHAUSTED``

The semantic per-object processing is injected via ``process_fn`` so the orchestrator
stays generic (commit 3). The bounded semantic ARR adapter (commit 4) supplies the
default processor.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from . import schemas
from .checkpoint import Checkpoint, atomic_write
from .inventory import stage_a_mechanical_pass
from .shard import build_shard_plan

# A processing function: given (record, run_context) returns (outcome, receipt_dict).
ProcessFn = Callable[[schemas.StageAMechanicalRecord, dict], tuple[str, dict]]


class CrashInjection(Exception):
    """Raised by the demo harness to simulate a mid-run crash before commit."""


@dataclass
class CorpusRunConfig:
    corpus_root: str
    out_dir: str
    frozen_corpus_ref: str = "UNKNOWN"
    shard_count: int = 16
    max_retries: int = 2
    crash_at_key: Optional[str] = None      # demo only
    generation: int = 1
    process_fn: Optional[ProcessFn] = None
    receipts_subdir: str = "receipts"


@dataclass
class RunResult:
    run_id: str
    total: int
    committed: int
    outcomes: dict = field(default_factory=dict)
    elapsed_seconds: float = 0.0
    generation: int = 1
    replayed: bool = False
    reprocessed: int = 0


def _run_context(run_id: str, plan: schemas.ShardPlan) -> dict:
    return {
        "run_id": run_id,
        "plan_digest": plan.plan_digest,
        "frozen_corpus_ref": plan.frozen_corpus_ref,
    }


def run_corpus(config: CorpusRunConfig) -> RunResult:
    """Execute (or resume) the corpus run under the crash-safe contract."""
    t0 = time.time()
    out = Path(config.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    recs = stage_a_mechanical_pass(config.corpus_root)
    # The index file (索引.md) is recorded in the manifest/inventory but is not a
    # note; it is excluded from Stage B processing and receipt emission.
    recs = [r for r in recs if r.identity.note_type != "index"]
    by_key = {r.identity.object_key: r for r in recs}
    plan = build_shard_plan([r.identity for r in recs], config.shard_count, config.frozen_corpus_ref)
    run_id = schemas.make_run_id(config.frozen_corpus_ref, plan.object_count, plan.plan_digest)
    checkpoint = Checkpoint(out / "run_state.json")
    state = checkpoint.load()
    if state is None:
        state = checkpoint.init(run_id)
    elif state.run_id != run_id:
        # Corpus/plan changed: bump generation and treat as incremental rerun.
        state.generation = config.generation
        checkpoint._recompute_digest()
        checkpoint.save()

    if config.process_fn is None:
        raise RuntimeError("process_fn required (wire the semantic adapter in commit 4)")

    ctx = _run_context(run_id, plan)
    receipt_dir = out / config.receipts_subdir
    receipt_dir.mkdir(parents=True, exist_ok=True)

    outcomes: dict[str, str] = {}
    committed = 0
    reprocessed = 0
    crash_injected = False
    for shard in plan.shards:
        shard_id = shard["shard_id"]
        state.shard_status.setdefault(shard_id, "running")
        for key in shard["object_keys"]:
            # changed-key rerun: byte hash differs from the stored receipt.
            force = _key_changed(receipt_dir, key, by_key.get(key))
            if checkpoint.is_committed(key) and not force:
                outcomes[key] = state.outcomes[key]
                committed += 1
                continue
            if config.crash_at_key is not None and key == config.crash_at_key:
                state.shard_status[shard_id] = "interrupted"
                checkpoint.save()
                raise CrashInjection(f"simulated crash at {key}")
            rec = by_key[key]
            outcome, receipt = _process_with_retry(config, rec, ctx, key)
            receipt_text = schemas.canonical_json(receipt) if isinstance(receipt, dict) else str(receipt)
            receipt_path = receipt_dir / f"{_safe(key)}.json"
            atomic_write(receipt_path, receipt_text)
            checkpoint.mark_committed(key, outcome, shard_id)
            checkpoint.save()
            outcomes[key] = outcome
            committed += 1
            reprocessed += 1
        state.shard_status[shard_id] = "committed"

    result = RunResult(
        run_id=run_id,
        total=plan.object_count,
        committed=committed,
        outcomes=outcomes,
        elapsed_seconds=time.time() - t0,
        generation=state.generation,
        reprocessed=reprocessed,
    )
    return result


def _process_with_retry(config: CorpusRunConfig, rec, ctx, key) -> tuple[str, dict]:
    attempt = 0
    last_err: Optional[str] = None
    while attempt <= config.max_retries:
        try:
            outcome, receipt = config.process_fn(rec, ctx)
            if outcome in schemas.OUTCOME_CLASSES:
                return outcome, receipt
            return outcome or "SUCCESS", receipt
        except Exception as exc:  # pragma: no cover - defensive
            last_err = f"{type(exc).__name__}: {exc}"
            attempt += 1
    return "RETRY_EXHAUSTED", {
        "object_key": key,
        "error": last_err,
        "outcome": "RETRY_EXHAUSTED",
    }


def _key_changed(receipt_dir: Path, key: str, rec: Optional[schemas.StageAMechanicalRecord]) -> bool:
    if rec is None:
        return False
    path = receipt_dir / f"{_safe(key)}.json"
    if not path.exists():
        return False
    try:
        stored = json_load(path)
        return stored.get("byte_sha256") != rec.identity.byte_sha256
    except Exception:
        return True


def json_load(path: Path) -> dict:
    import json
    return json.loads(path.read_text(encoding="utf-8"))


def _safe(key: str) -> str:
    import re
    return re.sub(r"[^A-Za-z0-9_.-]", "_", key)[:200]
