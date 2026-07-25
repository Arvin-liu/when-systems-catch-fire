"""Deterministic correction projector (relay task §6 / §7 / §8).

Consumes the sealed historical R3 input identities and the sealed R3 capability
matrix, and produces the versioned correction artifacts:

* M2  unknown-retention clarification (§6.3)
* M3  crash-recovery aggregation correction (§6.1)
* M4  incremental-rerun selectivity correction (§6.2)
* M5  versioned R3 capability interpretation correction (§6.4)
* R4  semantic-guardrail vs semantic-understanding split (§7)
* M1-M6 contradiction lifecycle closure (§8)

The projector is deterministic and fail-closed: it never invents values, it
references the exact sealed inputs, and it never mutates history. The six
projection functions below are filled in across commits 2-3; until then they
raise ``NotImplementedError`` so the contract regression tests fail first.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .schema import (
    APPLICABILITY,
    SCHEMA_VERSION,
    MetricComponent,
    MetricDefinition,
    validate_metric_definition,
)
from .sealed_inputs import (
    CORPUS_OBJECTS,
    FROZEN_CORPUS_REF,
    SEALED_R3_INPUTS,
    input_identity_checks,
)


def _md(
    metric_id: str,
    display_name: str,
    semantic_kind: str,
    numerator: MetricComponent,
    denominator: MetricComponent,
    population: str,
    applicability: str,
    value: Any,
    unit: str,
    directionality: str,
    authority_source: str,
    precedence_rule: str,
    historical_value: Any,
    historical_source: str,
    correction_status: str,
    underlying_defect_present: bool,
    underlying_defect_repaired: bool,
    supersedes: bool,
    evidence_refs: List[str],
    note: str = "",
) -> MetricDefinition:
    """Convenience constructor for a typed MetricDefinition."""
    return MetricDefinition(
        metric_id=metric_id,
        schema_version=SCHEMA_VERSION,
        display_name=display_name,
        semantic_kind=semantic_kind,
        numerator=numerator,
        denominator=denominator,
        population=population,
        applicability=applicability,
        value=value,
        unit=unit,
        directionality=directionality,
        authority_source=authority_source,
        precedence_rule=precedence_rule,
        historical_value=historical_value,
        historical_source=historical_source,
        correction_status=correction_status,
        underlying_defect_present=underlying_defect_present,
        underlying_defect_repaired_in_current_layer=underlying_defect_repaired,
        supersedes_for_interpretation=supersedes,
        evidence_refs=evidence_refs,
        note=note,
    )


def project_unknown_retention(sealed: Dict[str, Dict[str, Any]]) -> Dict[str, MetricDefinition]:
    """M2 -- unknown-event-time retention clarification (§6.3)."""
    raise NotImplementedError("M2 projection implemented in commit 2")


def project_crash_recovery(sealed: Dict[str, Dict[str, Any]]) -> Dict[str, MetricDefinition]:
    """M3 -- crash-recovery aggregation correction (§6.1)."""
    raise NotImplementedError("M3 projection implemented in commit 2")


def project_incremental_rerun(sealed: Dict[str, Dict[str, Any]]) -> Dict[str, MetricDefinition]:
    """M4 -- incremental-rerun selectivity correction (§6.2)."""
    raise NotImplementedError("M4 projection implemented in commit 2")


def project_capability_interpretation(
    matrix: Dict[str, Any],
    independently_supported_count: int = 0,
    total_objects: int = CORPUS_OBJECTS,
) -> Dict[str, Any]:
    """M5 -- versioned R3 capability interpretation correction (§6.4)."""
    raise NotImplementedError("M5 projection implemented in commit 3")


def project_semantic_guardrail_understanding_split(
    classification: Dict[str, Any]
) -> Dict[str, Any]:
    """R4 -- semantic-guardrail vs semantic-understanding split (§7)."""
    raise NotImplementedError("semantic split implemented in commit 3")


def project_contradiction_lifecycle(
    corrections_validated: Dict[str, bool]
) -> Dict[str, Any]:
    """M1-M6 contradiction lifecycle closure (§8)."""
    raise NotImplementedError("lifecycle closure implemented in commit 3")


def validate_all(corrections: Dict[str, Any]) -> List[str]:
    """Validate every MetricDefinition in a projection bundle (fail-closed).

    ``corrections`` maps a metric group name to either a single
    ``MetricDefinition`` or a dict of ``MetricDefinition`` objects.
    """
    failures: List[str] = []
    for _group, payload in corrections.items():
        items = payload.values() if isinstance(payload, dict) else [payload]
        for item in items:
            if isinstance(item, MetricDefinition):
                failures.extend(validate_metric_definition(item))
    return failures


def project_all(
    sealed: Dict[str, Dict[str, Any]],
    matrix: Dict[str, Any],
    independently_supported_count: int = 0,
    total_objects: int = CORPUS_OBJECTS,
    corrections_validated: Dict[str, bool] | None = None,
) -> Dict[str, Any]:
    """Run the full correction projection deterministically.

    Fail-closed: any sealed-input identity mismatch aborts with a clear error.
    """
    if corrections_validated is None:
        corrections_validated = {}
    identity_failures = input_identity_checks(sealed)
    if identity_failures:
        raise ValueError("sealed-input identity mismatch: " + "; ".join(identity_failures))

    m2 = project_unknown_retention(sealed)
    m3 = project_crash_recovery(sealed)
    m4 = project_incremental_rerun(sealed)
    m5 = project_capability_interpretation(
        matrix, independently_supported_count, total_objects
    )
    split = project_semantic_guardrail_understanding_split(m5)
    lifecycle = project_contradiction_lifecycle(corrections_validated)

    corrections: Dict[str, Any] = {
        "M2_UNKNOWN_RETENTION": m2,
        "M3_CRASH_RECOVERY": m3,
        "M4_INCREMENTAL_RERUN": m4,
        "M5_CAPABILITY": m5,
        "R4_SEMANTIC_SPLIT": split,
        "CONTRADICTION_LIFECYCLE": lifecycle,
    }
    validation_failures = validate_all(corrections)
    return {
        "schema": "r3r4/correction-projection/v1",
        "frozen_corpus_ref": FROZEN_CORPUS_REF,
        "corpus_objects": total_objects,
        "sealed_inputs": SEALED_R3_INPUTS,
        "corrections": corrections,
        "validation_failures": validation_failures,
        "validation_ok": len(validation_failures) == 0,
    }
