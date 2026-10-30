"""Synthetic fixtures for R4 acceptance/attack tests.

These build GENERIC, deterministic evidence directories and in-memory report
dictionaries so the audit engine can be tested without the private 836-note
corpus. No real note id, title, text or URL is used. The engine itself never
hard-codes the 836 count; these fixtures prove it scales to any N (including 836).
"""

from __future__ import annotations

import json
import os
import random
from typing import Any, Dict, List

NOTE_TYPES = ["link", "plain_text", "local_audio", "recorder_audio"]
CLAIM_CLASSES = ["AUTHOR_OBSERVATION", "SECONDARY_ARCHIVE_CLAIM", "TRANSCRIPT_INFERENCE"]


def _temporal(known: bool) -> Dict[str, Any]:
    if known:
        return {
            "event_time": "2021-01-01 00:00:00",
            "ingested_at": "2021-01-02 00:00:00",
            "note_created_at": "2021-01-01 09:00:00",
            "observed_at": "2021-01-01 00:00:00",
            "publication_time": "2021-01-01 00:00:00",
            "temporal_scope": "2021",
            "temporal_unknowns": [],
            "valid_from": "2021-01-01 00:00:00",
            "valid_to": "UNKNOWN",
        }
    return {
        "event_time": "UNKNOWN",
        "ingested_at": "UNKNOWN",
        "note_created_at": "2021-01-01 09:00:00",
        "observed_at": "UNKNOWN",
        "publication_time": "UNKNOWN",
        "temporal_scope": "UNKNOWN",
        "temporal_unknowns": ["event_time", "publication_time", "observed_at", "ingested_at"],
        "valid_from": "UNKNOWN",
        "valid_to": "UNKNOWN",
    }


def synthetic_receipt(object_key: str, note_type: str, claim_class: str,
                      source_ref_present: bool, inference_labeled: bool,
                      outcome: str = "SUCCESS", rights_boundary: str = "private") -> Dict[str, Any]:
    return {
        "object_key": object_key,
        "note_type": note_type,
        "claim_class": claim_class,
        "outcome": outcome,
        "source_ref_present": source_ref_present,
        "rights_boundary": rights_boundary,
        "promote_called": False,
        "evolve_called": False,
        "real_world_action": False,
        "byte_sha256": "deadbeef" + object_key,
        "normalized_text_digest": "cafe" + object_key,
        "path_digest": "face" + object_key,
        "receipt_id": "r3rcpt_" + object_key,
        "envelope_id": "r3env_" + object_key,
        "run_id": "r3run_synthetic",
        "temporal": _temporal(not source_ref_present) if False else _temporal(False),
    }


def synthetic_envelope(object_key: str, note_type: str, claim_class: str,
                       source_ref_present: bool, inference_labeled: bool) -> Dict[str, Any]:
    return {
        "claim_class": claim_class,
        "claim_surface": {
            "note_type": note_type,
            "source_ref_present": source_ref_present,
            "title_present": True,
        },
        "envelope_id": "r3env_" + object_key,
        "inference_labeled": inference_labeled,
        "object_key": object_key,
        "temporal": _temporal(False),
    }


def build_synthetic_evidence(root: str, n: int, seed: int = 0) -> str:
    """Write n synthetic receipt/envelope pairs + minimal ledgers under root.
    Deterministic for a given (n, seed)."""
    rnd = random.Random(seed)
    receipts_dir = os.path.join(root, "receipts")
    envelopes_dir = os.path.join(root, "envelopes")
    os.makedirs(receipts_dir, exist_ok=True)
    os.makedirs(envelopes_dir, exist_ok=True)
    type_counts = {t: 0 for t in NOTE_TYPES}
    class_counts = {c: 0 for c in CLAIM_CLASSES}
    for i in range(n):
        key = f"syn_{i:08d}"
        note_type = rnd.choice(NOTE_TYPES)
        claim_class = rnd.choice(CLAIM_CLASSES)
        source_ref_present = rnd.random() < 0.2
        inference_labeled = (claim_class == "TRANSCRIPT_INFERENCE") or rnd.random() < 0.3
        type_counts[note_type] += 1
        class_counts[claim_class] += 1
        with open(os.path.join(receipts_dir, key + ".json"), "w", encoding="utf-8") as fh:
            json.dump(synthetic_receipt(key, note_type, claim_class, source_ref_present, inference_labeled), fh)
        with open(os.path.join(envelopes_dir, key + ".json"), "w", encoding="utf-8") as fh:
            json.dump(synthetic_envelope(key, note_type, claim_class, source_ref_present, inference_labeled), fh)

    # Minimal ledgers mimicking R3 shape (aggregate values derived from n).
    agg = {
        "corpus_notes_expected": n,
        "corpus_notes_selected": n,
        "corpus_receipts_final": n,
        "type_distribution": type_counts,
        "outcome_counts": {"SUCCESS": n},
        "independent_source_estimate": max(1, n // 90),
        "false_consensus_risk": 0,
        "temporal_ambiguity_rate": round(0.7, 4),
        "unknown_retention": 0,
        "source_link_completeness": round(0.2, 4),
        "crash_recovery_success_rate": 0.0,
        "incremental_selectivity": 0.0,
        "replay_duplicate_rate": 0.0,
        "promote_calls": 0,
        "evolve_calls": 0,
        "real_world_actions": 0,
        "public_private_content_leaks": 0,
    }
    run_ledger = {
        "schema": "r3/corpus_run_ledger/v1",
        "total_notes": n,
        "committed_count": n,
        "outcome_counts": {"SUCCESS": n},
        "replay_duplicate_rate": 0.0,
        "crash_recovery_success_rate": 1.0,
        "incremental_selectivity": round(1.0 / n, 10) if n else 0.0,
    }
    cap = {
        "schema": "r3/capability_coverage_matrix/v1",
        "total_items": 27,
        "all_pass": True,
        "items": [{"id": f"op_item_{i}", "pass": True, "evidence": "synthetic"} for i in range(27)],
    }
    src_est = {
        "schema": "independent_source_estimate/v1",
        "distinct_source_hosts": max(1, n // 90),
        "notes_with_source": int(n * 0.2),
        "estimate": max(1, n // 90),
    }
    false_consensus = {"schema": "false_consensus_cases/v1", "cases": [], "false_consensus_risk": 0}
    temporal_ledger = {
        "schema": "temporal_ambiguity_ledger/v1",
        "unknown_event_time_count": int(n * 0.7),
        "temporal_ambiguity_rate": round(0.7, 4),
        "ambiguous_keys": [f"syn_{i:08d}" for i in range(40)],
    }
    indep_src_graph = {
        "schema": "source_dependency_graph/v1",
        "host_map": {f"host_{j}.example": [f"syn_{i:08d}" for i in range(j, min(n, j + 3))]
                     for j in range(0, max(1, n // 10), max(1, n // 10))},
        "shared_source_derivatives": {},
    }
    for name, obj in {
        "AGGREGATE_METRICS": agg,
        "CORPUS_RUN_LEDGER": run_ledger,
        "CAPABILITY_COVERAGE_MATRIX": cap,
        "INDEPENDENT_SOURCE_ESTIMATE": src_est,
        "FALSE_CONSENSUS_CASES": false_consensus,
        "TEMPORAL_AMBIGUITY_LEDGER": temporal_ledger,
        "SOURCE_DEPENDENCY_GRAPH": indep_src_graph,
        "COUNTERS": {"CORPUS_NOTES_EXPECTED": n, "CORPUS_RECEIPTS_FINAL": n,
                     "PROMOTE_CALLS": 0, "EVOLVE_CALLS": 0, "REAL_WORLD_ACTIONS": 0,
                     "MAIN_CHANGES": 0, "FORCE_PUSHES": 0, "HISTORY_REWRITES": 0,
                     "EXTERNAL_ACCEPTANCE_CLAIMED": 0},
        "CRASH_RECOVERY_REPORT": {"schema": "r3/crash_recovery_report/v1", "all_resume_complete": True,
                                  "scenarios": []},
        "INCREMENTAL_RERUN_REPORT": {"schema": "r3/incremental_rerun_report/v1",
                                     "reprocessed_on_change": 1, "selective": True},
        "REPLAY_AND_DRIFT_REPORT": {"schema": "r3/replay_and_drift_report/v1",
                                    "replay_idempotent": True, "duplicate_receipts": 0},
        "FAILURE_ATTRIBUTION_LEDGER": {"schema": "r3/failure_attribution_ledger/v1",
                                       "failures": 0, "quarantines": 0},
    }.items():
        with open(os.path.join(root, name + ".json"), "w", encoding="utf-8") as fh:
            json.dump(obj, fh)
    return root


def r3_like_reports() -> Dict[str, Any]:
    """In-memory report dict mimicking the REAL R3 aggregate values, for
    contradiction-engine unit tests (no private content)."""
    return {
        "AGGREGATE_METRICS": {
            "corpus_notes_selected": 836,
            "outcome_counts": {"SUCCESS": 836},
            "independent_source_estimate": 9,
            "false_consensus_risk": 4,
            "temporal_ambiguity_rate": 0.5371,
            "unknown_retention": 0,
            "source_link_completeness": 0.0323,
            "crash_recovery_success_rate": 0.0,
            "incremental_selectivity": 0.0,
        },
        "CORPUS_RUN_LEDGER": {
            "crash_recovery_success_rate": 1.0,
            "incremental_selectivity": 0.0011961722488038277,
            "replay_duplicate_rate": 0.0,
        },
        "CRASH_RECOVERY_REPORT": {"all_resume_complete": True, "scenarios": [{}, {}, {}]},
        "INCREMENTAL_RERUN_REPORT": {"reprocessed_on_change": 1, "selective": True},
        "TEMPORAL_AMBIGUITY_LEDGER": {"unknown_event_time_count": 449, "temporal_ambiguity_rate": 0.5371},
        "INDEPENDENT_SOURCE_ESTIMATE": {"estimate": 9, "distinct_source_hosts": 9, "notes_with_source": 27},
        "SOURCE_DEPENDENCY_GRAPH": {"host_map": {"h1": ["a", "b"], "h2": ["c"], "h3": ["a"]},
                                    "shared_source_derivatives": {}},
        "FALSE_CONSENSUS_CASES": {"cases": [{"source_host": "h1", "note_keys": ["a", "b"],
                                             "repeated_claim_class": ["SECONDARY_ARCHIVE_CLAIM"]}],
                                  "false_consensus_risk": 4},
        "CAPABILITY_COVERAGE_MATRIX": {
            "all_pass": True, "total_items": 27,
            "items": [
                {"id": "op", "pass": True},
                {"id": "coverage_dimension_missing", "pass": True},
                {"id": "changed_path_propagation_residue_zero", "pass": True},
                {"id": "ambiguous_path_mapping_zero", "pass": True},
            ],
        },
    }
