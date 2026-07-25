# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Corpus analysis layer (IGNITION §8-§9): dedup, temporal, source-independence.

Single read-only pass over the corpus to derive, from hashes and typed fields
only:
  * exact duplicates (byte-identical, normalized-text-identical)
  * near-duplicate clusters (conservative content-signature proxy)
  * temporal index + ambiguity ledger (event_time vs created_at; never guessed)
  * source-dependency graph (grouped by source host, typed reference only)
  * false-consensus risk (same-source repeats presented as independent)
  * independent-source estimate (distinct hosts)

No note body, title, or transcript is stored. Only hashes, hosts, and types.
"""
from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from . import schemas
from .identity import normalize_note_text

_URL_HOST_RE = re.compile(r"https?://([A-Za-z0-9.-]+)")


def _source_hosts(text: str) -> list[str]:
    return sorted(set(_URL_HOST_RE.findall(text)))


def _near_sig(note_type: str, norm: str) -> str:
    head = norm[:256]
    tail = norm[-256:] if len(norm) >= 256 else norm
    return hashlib.sha256(f"{note_type}|{head}|{tail}".encode("utf-8")).hexdigest()


def compute_analysis(
    records: list[schemas.StageAMechanicalRecord],
    receipts: dict[str, dict],
    corpus_root: str | Path,
) -> dict:
    root = Path(corpus_root)
    notes = [r for r in records if r.identity.note_type != "index"]

    # --- dedup ---
    by_byte: dict[str, list[str]] = defaultdict(list)
    by_norm: dict[str, list[str]] = defaultdict(list)
    near_sig_map: dict[str, list[str]] = defaultdict(list)
    per_key: dict[str, dict] = {}
    for r in notes:
        by_byte[r.identity.byte_sha256].append(r.identity.object_key)
        by_norm[r.identity.normalized_text_digest].append(r.identity.object_key)
        text = ""
        try:
            text = root.joinpath(r.identity.rel_path).read_text(encoding="utf-8", errors="replace")
        except Exception:
            text = ""
        norm, _enc, _w = normalize_note_text(text)
        sig = _near_sig(r.identity.note_type, norm)
        near_sig_map[sig].append(r.identity.object_key)
        hosts = _source_hosts(text)
        per_key[r.identity.object_key] = {
            "note_type": r.identity.note_type,
            "hosts": hosts,
            "source_ref_present": r.source_ref_present,
            "claim_class": receipts.get(r.identity.object_key, {}).get("claim_class", "UNKNOWN"),
            "outcome": receipts.get(r.identity.object_key, {}).get("outcome", "UNKNOWN"),
        }

    byte_dup_groups = {h: ks for h, ks in by_byte.items() if len(ks) > 1}
    norm_dup_groups = {h: ks for h, ks in by_norm.items() if len(ks) > 1}
    norm_dup_sets = [set(v) for v in norm_dup_groups.values()]
    # near clusters = signature groups of size>1 that are NOT already an exact
    # normalized-duplicate group (no double counting).
    near_clusters = []
    for sig, ks in near_sig_map.items():
        if len(ks) > 1 and not any(set(ks) == s for s in norm_dup_sets):
            near_clusters.append(ks)

    exact_duplicate_groups = len(byte_dup_groups) + max(0, len(norm_dup_groups) - len(byte_dup_groups))
    near_duplicate_clusters = len(near_clusters)

    # --- temporal ---
    temporal_index: dict[str, dict] = {}
    ambiguity_keys: list[str] = []
    unknown_event = 0
    for r in notes:
        rc = receipts.get(r.identity.object_key, {})
        temporal = rc.get("temporal", {})
        temporal_index[r.identity.object_key] = temporal
        if temporal.get("event_time", schemas.UNKNOWN_TIME) == schemas.UNKNOWN_TIME:
            unknown_event += 1
            ambiguity_keys.append(r.identity.object_key)
    temporal_ambiguity_rate = round(unknown_event / len(notes), 4) if notes else 0.0

    # --- source dependency ---
    host_map: dict[str, list[str]] = defaultdict(list)
    for key, info in per_key.items():
        for h in info["hosts"]:
            host_map[h].append(key)
    shared_source_derivatives = {h: ks for h, ks in host_map.items() if len(ks) > 1}

    # --- false consensus ---
    false_consensus: list[dict] = []
    for h, ks in shared_source_derivatives.items():
        classes = {per_key[k]["claim_class"] for k in ks}
        # same claim class repeated across same-source notes = not independent evidence
        if len(ks) >= 2:
            false_consensus.append(
                {"source_host": h, "note_keys": ks, "repeated_claim_class": sorted(classes)}
            )
    false_consensus_risk = len(false_consensus)

    independent_source_estimate = len(host_map)

    return {
        "exact_duplicates": {
            "schema": "exact_duplicates/v1",
            "byte_identical_groups": byte_dup_groups,
            "normalized_identical_groups": {h: ks for h, ks in norm_dup_groups.items()},
            "exact_duplicate_groups": exact_duplicate_groups,
            "note_count_in_byte_dups": sum(len(v) for v in byte_dup_groups.values()),
        },
        "near_duplicate_clusters": {
            "schema": "near_duplicate_clusters/v1",
            "method": "conservative content-signature (type+head+tail)",
            "clusters": near_clusters,
            "near_duplicate_clusters": near_duplicate_clusters,
        },
        "temporal_index": {
            "schema": "temporal_index/v1",
            "entries": temporal_index,
        },
        "temporal_ambiguity_ledger": {
            "schema": "temporal_ambiguity_ledger/v1",
            "unknown_event_time_count": unknown_event,
            "temporal_ambiguity_rate": temporal_ambiguity_rate,
            "ambiguous_keys": ambiguity_keys,
        },
        "source_dependency_graph": {
            "schema": "source_dependency_graph/v1",
            "host_map": {h: ks for h, ks in host_map.items()},
            "shared_source_derivatives": shared_source_derivatives,
        },
        "false_consensus_cases": {
            "schema": "false_consensus_cases/v1",
            "cases": false_consensus,
            "false_consensus_risk": false_consensus_risk,
        },
        "independent_source_estimate": {
            "schema": "independent_source_estimate/v1",
            "distinct_source_hosts": independent_source_estimate,
            "notes_with_source": sum(1 for k in per_key if per_key[k]["source_ref_present"]),
            "estimate": independent_source_estimate,
        },
    }


def _norm_of(ks: list[str], by_norm: dict) -> str:
    # retained for backward compatibility; intentionally unused
    return ""
