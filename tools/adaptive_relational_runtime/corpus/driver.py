# SPDX-License-Identifier: LicenseRef-Identifier: LicenseRef-BUSL-1.1-PointFire
"""End-to-end R3 corpus run driver (generic, no embedded private content).

``run_full`` executes the complete pipeline against a corpus root and writes all
artifacts to ``out_dir``:
  * Stage A: manifest / inventory / frontmatter / note_id / encoding audits
  * deterministic shard plan
  * Stage B: 836 receipts + envelopes (via ``run_corpus`` + semantic adapter)
  * analysis: dedup / temporal / source-dependency / false-consensus / independent
  * aggregate metrics (counts/rates only)

The driver is boundary-agnostic: it writes whatever ``out_dir`` it is given. The
public formal repository never calls it on the private corpus; the private
evidence branch does. No note body, title, or transcript is written by the driver
— only hashes, hosts, and typed fields.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from . import schemas
from .aggregate import compute_aggregate_metrics
from .analysis import compute_analysis
from .checkpoint import atomic_write
from .inventory import (
    build_corpus_inventory,
    build_corpus_manifest,
    build_encoding_parse_errors,
    build_frontmatter_audit,
    build_note_id_audit,
    stage_a_mechanical_pass,
)
from .runner import CorpusRunConfig, run_corpus
from .semantic import default_semantic_processor
from .shard import build_shard_plan, shard_plan_digest


def _write(out_dir: Path, name: str, obj: Any) -> None:
    atomic_write(out_dir / name, json.dumps(obj, ensure_ascii=False, indent=2))


def run_full(
    corpus_root: str,
    out_dir: str,
    frozen_corpus_ref: str,
    shard_count: int = 16,
    max_retries: int = 2,
    crash_at_key: Optional[str] = None,
    generation: int = 1,
) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    records = stage_a_mechanical_pass(corpus_root)
    plan = build_shard_plan([r.identity for r in records], shard_count, frozen_corpus_ref)

    _write(out, "CORPUS_MANIFEST.json", build_corpus_manifest(records, frozen_corpus_ref))
    _write(out, "CORPUS_INVENTORY.json", build_corpus_inventory(records))
    _write(out, "FRONTMATTER_AUDIT.json", build_frontmatter_audit(records))
    _write(out, "NOTE_ID_AUDIT.json", build_note_id_audit(records))
    _write(out, "ENCODING_AND_PARSE_ERRORS.json", build_encoding_parse_errors(records))
    _write(out, "SHARD_PLAN.json", plan.to_dict())

    config = CorpusRunConfig(
        corpus_root=corpus_root,
        out_dir=str(out),
        frozen_corpus_ref=frozen_corpus_ref,
        shard_count=shard_count,
        max_retries=max_retries,
        crash_at_key=crash_at_key,
        generation=generation,
        process_fn=default_semantic_processor(corpus_root),
    )
    result = run_corpus(config)

    # Write envelopes separately + load receipts for analysis.
    receipt_dir = out / "receipts"
    envelopes_dir = out / "envelopes"
    envelopes_dir.mkdir(parents=True, exist_ok=True)
    receipts: dict[str, dict] = {}
    for p in receipt_dir.glob("*.json"):
        data = json.loads(p.read_text(encoding="utf-8"))
        receipts[data["object_key"]] = data
        if "envelope" in data:
            atomic_write(envelopes_dir / f"{p.name}", json.dumps(data["envelope"], ensure_ascii=False, indent=2))

    analysis = compute_analysis(records, receipts, corpus_root)
    _write(out, "EXACT_DUPLICATES.json", analysis["exact_duplicates"])
    _write(out, "NEAR_DUPLICATE_CLUSTERS.json", analysis["near_duplicate_clusters"])
    _write(out, "TEMPORAL_INDEX.json", analysis["temporal_index"])
    _write(out, "TEMPORAL_AMBIGUITY_LEDGER.json", analysis["temporal_ambiguity_ledger"])
    _write(out, "SOURCE_DEPENDENCY_GRAPH.json", analysis["source_dependency_graph"])
    _write(out, "FALSE_CONSENSUS_CASES.json", analysis["false_consensus_cases"])
    _write(out, "INDEPENDENT_SOURCE_ESTIMATE.json", analysis["independent_source_estimate"])

    agg = compute_aggregate_metrics(records, result, analysis)
    _write(out, "AGGREGATE_METRICS.json", agg.to_dict())

    summary = {
        "run_id": result.run_id,
        "total": result.total,
        "committed": result.committed,
        "reprocessed": result.reprocessed,
        "receipts": len(receipts),
        "plan_digest": plan.plan_digest,
        "outcomes": result.outcomes,
        "aggregate": agg.to_dict(),
    }
    _write(out, "RUN_SUMMARY.json", summary)
    return summary
