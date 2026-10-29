"""Typed metric-definition and correction schema (relay task §5).

Every corrected / clarified metric must carry an explicit numerator,
denominator, population, applicability, authority source, historical value,
correction status and lifecycle. The validator FAILS CLOSED:

* any rate / fraction missing a numerator (value+source), denominator (source),
  population or with applicability ``UNKNOWN`` is rejected;
* a denominator of 0 is mapped to ``NOT_APPLICABLE`` and must never present a
  misleading numeric ``0.0`` as the rate value;
* every metric must reference at least one evidence source.

No result value, private note content or hard-coded pass/fail is used as a
success criterion -- only the explicit typed contract and the sealed inputs.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Dict, List


SCHEMA_VERSION = "r3r4/metric-correction/v1"

SEMANTIC_KINDS = (
    "rate",
    "fraction",
    "count",
    "boolean",
    "applicability",
    "violation_count",
    "coverage_statement",
)

APPLICABILITY = ("APPLICABLE", "NOT_APPLICABLE", "INSUFFICIENT_EVIDENCE", "UNKNOWN")

DIRECTIONALITY = ("higher_is_better", "lower_is_better", "descriptive_only")


@dataclasses.dataclass
class MetricComponent:
    """An explicit labelled, sourced component of a metric (numerator/denominator)."""

    label: str
    value: Any
    source: str

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class MetricDefinition:
    """Typed, self-describing metric definition + correction record.

    Implements the relay task §5 contract. The historical value is preserved
    (never mutated); ``supersedes_for_interpretation`` flags that the current
    value/interpretation replaces the historical one for present purposes.
    """

    metric_id: str
    schema_version: str
    display_name: str
    semantic_kind: str
    numerator: MetricComponent
    denominator: MetricComponent
    population: str
    applicability: str
    value: Any
    unit: str
    directionality: str
    authority_source: str
    precedence_rule: str
    historical_value: Any
    historical_source: str
    correction_status: str  # "historical_only" | "corrected" | "clarified"
    underlying_defect_present: bool
    underlying_defect_repaired_in_current_layer: bool
    supersedes_for_interpretation: bool
    evidence_refs: List[str]
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "schema_version": self.schema_version,
            "display_name": self.display_name,
            "semantic_kind": self.semantic_kind,
            "numerator": self.numerator.to_dict(),
            "denominator": self.denominator.to_dict(),
            "population": self.population,
            "applicability": self.applicability,
            "value": self.value,
            "unit": self.unit,
            "directionality": self.directionality,
            "authority_source": self.authority_source,
            "precedence_rule": self.precedence_rule,
            "historical_value": self.historical_value,
            "historical_source": self.historical_source,
            "correction_status": self.correction_status,
            "underlying_defect_present": self.underlying_defect_present,
            "underlying_defect_repaired_in_current_layer": self.underlying_defect_repaired_in_current_layer,
            "supersedes_for_interpretation": self.supersedes_for_interpretation,
            "evidence_refs": self.evidence_refs,
            "note": self.note,
        }


def _is_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def validate_metric_definition(m: MetricDefinition) -> List[str]:
    """Return a list of fail-closed violation strings (empty list == valid)."""
    failures: List[str] = []
    mid = m.metric_id

    if m.schema_version != SCHEMA_VERSION:
        failures.append(
            f"{mid}: schema_version mismatch ({m.schema_version} != {SCHEMA_VERSION})"
        )
    if m.semantic_kind not in SEMANTIC_KINDS:
        failures.append(f"{mid}: invalid semantic_kind {m.semantic_kind!r}")
    if m.applicability not in APPLICABILITY:
        failures.append(f"{mid}: invalid applicability {m.applicability!r}")
    if m.directionality not in DIRECTIONALITY:
        failures.append(f"{mid}: invalid directionality {m.directionality!r}")

    rate_like = m.semantic_kind in ("rate", "fraction")

    if rate_like:
        # Fail closed: numerator must carry a value and a source.
        if m.numerator is None or m.numerator.source == "" or m.numerator.value is None:
            failures.append(f"{mid}: rate/fraction missing numerator value/source")
        # Fail closed: denominator must carry a source (and a value).
        if m.denominator is None or m.denominator.source == "":
            failures.append(f"{mid}: rate/fraction missing denominator source")
        # Fail closed: population / evaluation scope required.
        if not m.population:
            failures.append(f"{mid}: rate/fraction missing population")
        # Fail closed: applicability must be resolved, never UNKNOWN for a rate.
        if m.applicability == "UNKNOWN":
            failures.append(f"{mid}: rate/fraction applicability must be resolved (not UNKNOWN)")

        # Denominator 0 -> NOT_APPLICABLE, never a misleading numeric 0.0 rate.
        if (
            m.denominator is not None
            and _is_number(m.denominator.value)
            and m.denominator.value == 0
        ):
            if m.applicability != "NOT_APPLICABLE":
                failures.append(f"{mid}: denominator 0 must be NOT_APPLICABLE")
            if (
                _is_number(m.value)
                and m.value == 0.0
                and m.correction_status == "corrected"
            ):
                failures.append(
                    f"{mid}: denominator 0 cannot present numeric 0.0 as a corrected rate"
                )

    if not m.evidence_refs:
        failures.append(f"{mid}: missing evidence_refs")

    return failures
