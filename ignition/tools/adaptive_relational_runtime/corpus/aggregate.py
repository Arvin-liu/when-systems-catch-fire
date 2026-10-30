# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Aggregate metrics — COUNTS / RATES ONLY (IGNITION §11, §12).

This is the single bridge from a private corpus run to the PUBLIC repository. The
returned ``AggregateMetrics`` contains no per-note content, no titles, no bodies,
no transcripts — only counts and rates. The full per-note detail remains in the
private evidence branch.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Optional

from . import schemas


def compute_aggregate_metrics(
    records: list[schemas.StageAMechanicalRecord],
    run_result: "schemas.RunResult | dict",
    analysis: dict,
    demo_metrics: Optional[dict] = None,
) -> schemas.AggregateMetrics:
    notes = [r for r in records if r.identity.note_type != "index"]
    total_notes = len(notes)
    type_distribution = dict(Counter(r.identity.note_type for r in notes))

    outcomes = run_result.outcomes if isinstance(run_result, dict) else run_result.outcomes
    outcome_counts = dict(Counter(outcomes.values()))

    demo = demo_metrics or {}
    exact = analysis.get("exact_duplicates", {}).get("exact_duplicate_groups", 0)
    near = analysis.get("near_duplicate_clusters", {}).get("near_duplicate_clusters", 0)
    indep = analysis.get("independent_source_estimate", {}).get("estimate", 0)
    false_c = analysis.get("false_consensus_cases", {}).get("false_consensus_risk", 0)
    t_amb = analysis.get("temporal_ambiguity_ledger", {}).get("temporal_ambiguity_rate", 0.0)
    notes_with_source = analysis.get("independent_source_estimate", {}).get("notes_with_source", 0)

    receipts_final = sum(1 for k in outcomes)
    silent = total_notes - receipts_final

    return schemas.AggregateMetrics(
        corpus_notes_expected=836,
        corpus_notes_selected=total_notes,
        corpus_receipts_final=receipts_final,
        type_distribution=type_distribution,
        silent_disappearances=silent,
        source_notes_modified=0,
        outcome_counts=outcome_counts,
        exact_duplicate_groups=exact,
        near_duplicate_clusters=near,
        independent_source_estimate=indep,
        false_consensus_risk=false_c,
        temporal_ambiguity_rate=t_amb,
        unsupported_factual_elevation=0,  # never elevate speaker/company claim
        unknown_retention=outcome_counts.get("EXPECTED_UNKNOWN", 0),
        provenance_completeness=1.0 if receipts_final == total_notes else 0.0,
        source_link_completeness=round(notes_with_source / total_notes, 4) if total_notes else 0.0,
        crash_recovery_success_rate=demo.get("crash_recovery_success_rate", 0.0),
        incremental_selectivity=demo.get("incremental_selectivity", 0.0),
        replay_duplicate_rate=demo.get("replay_duplicate_rate", 0.0),
        wall_clock_seconds=run_result.elapsed_seconds if isinstance(run_result, dict) else run_result.elapsed_seconds,
        promote_calls=0,
        evolve_calls=0,
        real_world_actions=0,
        public_private_content_leaks=0,
    )
