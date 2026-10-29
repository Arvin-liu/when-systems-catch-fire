"""R3/R4 metric semantics & observability closure (relay task R1).

This package builds a *versioned correction layer* over sealed historical R3
measurement evidence. It does NOT rewrite frozen history: it references the
exact historical input digests, exposes the original value, the authoritative
source, the corrected interpretation/value and the metric lifecycle, and marks
the historical value as preserved-but-superseded for current interpretation.

Public contract (relay task §5 / §9): generic schemas, tools, synthetic
fixtures, explicit public capability IDs and non-reconstructive aggregates /
corrections only. No private note content, titles, transcripts, URLs or
reconstructive features are emitted.
"""

from __future__ import annotations

from .schema import (
    SCHEMA_VERSION,
    APPLICABILITY,
    DIRECTIONALITY,
    SEMANTIC_KINDS,
    MetricComponent,
    MetricDefinition,
    validate_metric_definition,
)
from .sealed_inputs import (
    SEALED_R3_INPUTS,
    CORPUS_OBJECTS,
    FROZEN_CORPUS_REF,
    sealed_input_digest,
    build_sealed_manifest,
    input_identity_checks,
)
from .projector import (
    project_all,
    project_crash_recovery,
    project_incremental_rerun,
    project_unknown_retention,
    project_capability_interpretation,
    project_semantic_guardrail_understanding_split,
    project_contradiction_lifecycle,
    validate_all,
)

__all__ = [
    "SCHEMA_VERSION",
    "APPLICABILITY",
    "DIRECTIONALITY",
    "SEMANTIC_KINDS",
    "MetricComponent",
    "MetricDefinition",
    "validate_metric_definition",
    "SEALED_R3_INPUTS",
    "CORPUS_OBJECTS",
    "FROZEN_CORPUS_REF",
    "sealed_input_digest",
    "build_sealed_manifest",
    "input_identity_checks",
    "project_all",
    "project_crash_recovery",
    "project_incremental_rerun",
    "project_unknown_retention",
    "project_capability_interpretation",
    "project_semantic_guardrail_understanding_split",
    "project_contradiction_lifecycle",
    "validate_all",
]
