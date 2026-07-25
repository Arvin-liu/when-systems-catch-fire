# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""R3 corpus-scale runtime: a generic layer over Adaptive Relational Runtime R2.

This subpackage implements the first complete corpus-scale pressure test of ARR
(IGNITION R3 WAIC CORPUS SCALE RUN R1). It is a *layer*, not a second ARR and not
a second production executor. It may call existing ARR objectization / routing /
receipt interfaces (``tools.adaptive_relational_runtime.canonical``,
``adapter_protocol``, ``production_receipt_adapter``) but it MUST NOT call
PROMOTE or EVOLVE and MUST NOT perform any external real-world action.

Public-repository boundary (IGNITION §12): this code, its schemas, synthetic
fixtures and tests contain NO private corpus content. The generic runner reads a
corpus root supplied at runtime and emits typed references (hashes + types) only.
Per-note detail is produced only into a designated private evidence workspace.

The runtime modules (identity, shard, inventory, semantic, checkpoint, runner,
aggregate) are added in the subsequent R3 commits; this package re-exports them
as they land.
"""
from __future__ import annotations

from . import schemas
from .identity import compute_identity, normalize_note_text, parse_frontmatter, scan_corpus
from .inventory import (
    stage_a_mechanical_pass,
    build_corpus_manifest,
    build_corpus_inventory,
    build_frontmatter_audit,
    build_note_id_audit,
    build_encoding_parse_errors,
)
from .shard import build_shard_plan, shard_plan_digest, is_key_in_namespace
from .checkpoint import Checkpoint, atomic_write, crash_safe_step
from .runner import CorpusRunConfig, RunResult, run_corpus, CrashInjection

__all__ = [
    "schemas",
    "compute_identity",
    "normalize_note_text",
    "parse_frontmatter",
    "scan_corpus",
    "stage_a_mechanical_pass",
    "build_corpus_manifest",
    "build_corpus_inventory",
    "build_frontmatter_audit",
    "build_note_id_audit",
    "build_encoding_parse_errors",
    "build_shard_plan",
    "shard_plan_digest",
    "is_key_in_namespace",
    "Checkpoint",
    "atomic_write",
    "crash_safe_step",
    "CorpusRunConfig",
    "RunResult",
    "run_corpus",
    "CrashInjection",
]
