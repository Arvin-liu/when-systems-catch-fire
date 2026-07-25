# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Generic schemas for the R3 corpus-scale runtime.

These are PURE TYPE DEFINITIONS. They contain no private corpus content and no
hard-coded note text. Every digest is content-addressed (sha256) so that the
public repository can carry *typed references* (hashes + types) without ever
carrying the underlying note body (IGNITION §12).

Conventions (mirror ``tools.adaptive_relational_runtime.canonical``):
  * identity digests are hex sha256
  * run / receipt ids are deterministic ``prefix + first 32 hex`` (no wall clock)
  * time fields are opaque strings; missing time is the literal ``"UNKNOWN"``
"""
from __future__ import annotations

import dataclasses
import json
from typing import Any, Optional

from ..canonical import canonical_json, deterministic_id, sha256_hex

# ---------------------------------------------------------------------------
# Enumerations (closed vocabularies from IGNITION §7-§8, §11)
# ---------------------------------------------------------------------------

CLAIM_CLASSES = (
    "SPEAKER_CLAIM",
    "COMPANY_SELF_REPORT",
    "HOST_SUMMARY",
    "AUTHOR_OBSERVATION",
    "TRANSCRIPT_INFERENCE",
    "SECONDARY_ARCHIVE_CLAIM",
    "INDEPENDENTLY_VERIFIED",  # forbidden unless corpus carries explicit primary evidence
    "UNKNOWN",
)

OUTCOME_CLASSES = (
    "SUCCESS",
    "EXPECTED_UNKNOWN",
    "EXPECTED_QUARANTINE",
    "FAILURE",
    "RETRY_EXHAUSTED",
)

NOTE_TYPES = ("link", "plain_text", "local_audio", "recorder_audio")

TEMPORAL_FIELDS = (
    "event_time",
    "publication_time",
    "note_created_at",
    "observed_at",
    "ingested_at",
    "valid_from",
    "valid_to",
    "temporal_scope",
)

UNKNOWN_TIME = "UNKNOWN"

# Epistemic ceiling constant: even when a speaker/company claim is extracted, the
# receipt may never assert it as independently verified (IGNITION §7, §13).
FORBIDDEN_CLAIM_CLASS_WITHOUT_PRIMARY_EVIDENCE = "INDEPENDENTLY_VERIFIED"

# Fixed render stamp for deterministic ids. The run NEVER auto-fills time from the
# wall clock (mirrors pilot_runner._T). The caller supplies ingestion time.
RENDER_STAMP = "2026-07-25T00:00:00Z"


@dataclasses.dataclass
class JsonModel:
    """Base for schema objects with canonical (deterministic) serialization."""

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "JsonModel":
        field_names = {f.name for f in dataclasses.fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in field_names})

    def canonical(self) -> str:
        return canonical_json(self.to_dict())


# ---------------------------------------------------------------------------
# Stage A — deterministic mechanical identity
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class CorpusObjectIdentity(JsonModel):
    object_key: str          # deterministic key (note_id when present, else path digest)
    rel_path: str            # relative path within the corpus root (typed ref only)
    path_digest: str         # sha256(rel_path)
    byte_sha256: str         # sha256(raw file bytes)
    normalized_text_digest: str  # sha256(normalized body text, frontmatter removed)
    note_id: Optional[str]
    note_type: str
    size_bytes: int


@dataclasses.dataclass
class StageAMechanicalRecord(JsonModel):
    identity: CorpusObjectIdentity
    title_present: bool
    frontmatter_valid: bool
    encoding_status: str          # "ok" | "error"
    body_present: bool
    body_length_class: str        # "empty" | "short" | "medium" | "long"
    declared_times: dict          # raw declared strings only; NOT interpreted
    source_ref_present: bool
    rights_boundary: str          # "private" | "public" | "unknown"
    parse_warnings: list


# ---------------------------------------------------------------------------
# Shard plan
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class ShardMember(JsonModel):
    shard_id: str
    object_keys: list


@dataclasses.dataclass
class ShardPlan(JsonModel):
    shard_count: int
    method: str
    frozen_corpus_ref: str
    object_count: int
    plan_digest: str
    shards: list  # list[ShardMember] serialized as dicts


# ---------------------------------------------------------------------------
# Checkpoint / run state
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class RunState(JsonModel):
    run_id: str
    generation: int
    committed_keys: list          # sorted, deterministic
    outcomes: dict                # object_key -> outcome
    shard_status: dict            # shard_id -> status
    checkpoint_index: int
    state_digest: str


# ---------------------------------------------------------------------------
# Stage B — corpus envelope + final receipt
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class CorpusEnvelope(JsonModel):
    envelope_id: str
    object_key: str
    claim_class: str
    claim_surface: dict           # typed only: {note_type, source_ref_present, title_present}
    temporal: dict                # all temporal fields, UNKNOWN-safe
    inference_labeled: bool       # every inferred premise is labeled inference


@dataclasses.dataclass
class CorpusReceipt(JsonModel):
    receipt_id: str
    run_id: str
    object_key: str
    note_type: str
    path_digest: str
    byte_sha256: str
    normalized_text_digest: str
    outcome: str
    claim_class: str
    temporal: dict
    source_ref_present: bool
    rights_boundary: str
    private_ref: dict             # {kind, note_id, byte_sha256, path_digest}
    real_world_action: bool       # always False
    promote: bool                 # always False
    evolve: bool                  # always False
    generated_at: str             # fixed render stamp, never wall clock


# ---------------------------------------------------------------------------
# Aggregate metrics — COUNTS / RATES ONLY (IGNITION §12, non-reconstructive)
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class AggregateMetrics(JsonModel):
    corpus_notes_expected: int
    corpus_notes_selected: int
    corpus_receipts_final: int
    type_distribution: dict
    silent_disappearances: int
    source_notes_modified: int
    outcome_counts: dict
    exact_duplicate_groups: int
    near_duplicate_clusters: int
    independent_source_estimate: int
    false_consensus_risk: int
    temporal_ambiguity_rate: float
    unsupported_factual_elevation: int
    unknown_retention: int
    provenance_completeness: float
    source_link_completeness: float
    crash_recovery_success_rate: float
    incremental_selectivity: float
    replay_duplicate_rate: float
    wall_clock_seconds: float
    promote_calls: int
    evolve_calls: int
    real_world_actions: int
    public_private_content_leaks: int


# ---------------------------------------------------------------------------
# Determinism helpers
# ---------------------------------------------------------------------------

def make_run_id(corpus_ref: str, object_count: int, plan_digest: str) -> str:
    payload = canonical_json(
        {"corpus_ref": corpus_ref, "object_count": object_count, "plan_digest": plan_digest}
    )
    return deterministic_id("r3run", payload)


def make_receipt_id(run_id: str, object_key: str) -> str:
    return deterministic_id("r3rcpt", canonical_json({"run_id": run_id, "k": object_key}))


def make_envelope_id(run_id: str, object_key: str) -> str:
    return deterministic_id("r3env", canonical_json({"run_id": run_id, "k": object_key}))


def digest_of(obj: Any) -> str:
    return sha256_hex(canonical_json(obj))


def assert_no_private_content_leak(text: str) -> None:
    """Guardrail: refuse to embed obviously private long-form content in a public
    artifact. Raises ValueError if a suspiciously long verbatim block is present.
    Used by tests and by the private-reference exporter as a defensive check."""
    # This is a structural guard only; the real boundary is enforced by design
    # (public code never receives note bodies). We simply cap any single emitted
    # string field at a length that cannot reproduce a full note.
    if isinstance(text, str) and len(text) > 240:
        raise ValueError(
            "refusing to embed a >240-char verbatim string in a public/runtime artifact"
        )
