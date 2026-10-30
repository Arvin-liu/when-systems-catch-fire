# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Explicit single-primary failure attribution for the R2 real-object pilot.

Every failed or partial pilot run lands in EXACTLY ONE primary failure class
(ADR-R2-03) plus optional ordered secondary factors. The nine classes are the
only legal values and come from the failure-classes registry.

Hard rules enforced here (and asserted by commit-5 tests):
- missing evidence -> SOURCE_FAILURE / REPRESENTATION_FAILURE, NEVER ARCHITECTURE_FAILURE;
- model/extraction error -> EXTRACTION_FAILURE / REPRESENTATION_FAILURE, NEVER MECHANISM_FAILURE;
- a single object failure NEVER yields an EVOLVE candidate (growth_gate stays
  SIGNAL_ONLY / NO_EVOLVE).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

PRIMARY_CLASSES = (
    "SOURCE_FAILURE", "EXTRACTION_FAILURE", "REPRESENTATION_FAILURE",
    "ROUTING_FAILURE", "MECHANISM_FAILURE", "RUNTIME_FAILURE",
    "ARCHITECTURE_FAILURE", "GOVERNANCE_REFUSAL", "UNKNOWN",
)


class FailureAttributionError(Exception):
    """Raised when attribution violates the single-primary contract."""


@dataclass(frozen=True)
class FailureAttribution:
    primary_class: str
    secondary_factors: tuple[str, ...] = field(default_factory=tuple)
    note: str = ""

    def __post_init__(self) -> None:
        if self.primary_class not in PRIMARY_CLASSES:
            raise FailureAttributionError(
                f"unknown primary_class: {self.primary_class!r}")
        if not self.primary_class:
            raise FailureAttributionError("primary_class must be non-empty")


def attribute(
    *,
    primary_class: str,
    secondary_factors: list[str] | None = None,
    note: str = "",
) -> FailureAttribution:
    """Construct a validated single-primary attribution (ADR-R2-03)."""
    return FailureAttribution(
        primary_class=primary_class,
        secondary_factors=tuple(secondary_factors or ()),
        note=note,
    )


def assert_no_misclassification(att: FailureAttribution, *,
                                missing_evidence: bool = False,
                                extraction_error: bool = False) -> None:
    """Guard the two forbidden misclassifications called out in ADR-R2-03."""
    if missing_evidence and att.primary_class == "ARCHITECTURE_FAILURE":
        raise FailureAttributionError(
            "missing evidence must not be classified as ARCHITECTURE_FAILURE")
    if extraction_error and att.primary_class == "MECHANISM_FAILURE":
        raise FailureAttributionError(
            "extraction/model error must not be classified as MECHANISM_FAILURE")


def growth_gate_for_single_object(att: FailureAttribution) -> str:
    """A single object's failure MUST NOT produce an EVOLVE candidate.

    Returns SIGNAL_ONLY or NO_EVOLVE (never EVOLVE_CANDIDATE).
    """
    return "NO_EVOLVE" if att.primary_class != "UNKNOWN" else "SIGNAL_ONLY"


def to_record(att: FailureAttribution) -> dict[str, Any]:
    return {
        "primary_class": att.primary_class,
        "secondary_factors": list(att.secondary_factors),
        "note": att.note,
    }
