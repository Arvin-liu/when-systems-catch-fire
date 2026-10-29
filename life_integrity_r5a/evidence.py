# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Typed repository evidence objects for the R5-A candidate contracts.

These objects describe why a software-contract decision was made.  They are
not human evidence and never authorize intervention, efficacy, or activation.
"""

from __future__ import annotations

from dataclasses import dataclass


EVIDENCE_CLASS_IDS = (
    "attack_reproduction",
    "local_optimization_risk_review",
    "multi_view_observation",
    "source_identification",
    "phenomenology_report",
    "practice_function_analysis",
    "mechanism_hypothesis",
    "empirical_support",
    "contradiction_evidence",
    "insufficient_evidence",
    "new_evidence",
    "longitudinal_observation",
    "non_impact_static_analysis",
)

CLAIM_CEILING_IDS = (
    "repository_contract_observed",
    "software_behavior_reproduced",
    "insufficient_evidence",
)

REVIEWER_ROLE_IDS = ("A", "B", "C", "D", "E", "F", "G", "H")


class EvidenceObjectError(ValueError):
    """Raised when a repository evidence object is incomplete or out of set."""


def _nonblank(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceObjectError(f"{field_name} must be a non-blank string")
    return value.strip()


@dataclass(frozen=True)
class EvidenceObject:
    evidence_id: str
    evidence_class: str
    provenance: str
    reviewer_role: str
    claim_ceiling: str = "repository_contract_observed"
    supports: tuple[str, ...] = ()
    observed_facts: tuple[str, ...] = ()
    unresolved_risks: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_id", _nonblank(self.evidence_id, "evidence_id"))
        object.__setattr__(self, "provenance", _nonblank(self.provenance, "provenance"))
        if self.evidence_class not in EVIDENCE_CLASS_IDS:
            raise EvidenceObjectError(
                f"unknown evidence_class: {self.evidence_class!r}"
            )
        if self.reviewer_role not in REVIEWER_ROLE_IDS:
            raise EvidenceObjectError(
                f"unknown reviewer_role: {self.reviewer_role!r}"
            )
        if self.claim_ceiling not in CLAIM_CEILING_IDS:
            raise EvidenceObjectError(
                f"unknown claim_ceiling: {self.claim_ceiling!r}"
            )
        if not self.supports:
            raise EvidenceObjectError("supports must identify at least one contract surface")
        for field_name, values in (
            ("supports", self.supports),
            ("observed_facts", self.observed_facts),
            ("unresolved_risks", self.unresolved_risks),
        ):
            if any(not isinstance(value, str) or not value.strip() for value in values):
                raise EvidenceObjectError(f"{field_name} entries must be non-blank strings")

    def supports_all(self, required: set[str]) -> bool:
        return required.issubset(set(self.supports))

    def as_dict(self) -> dict[str, object]:
        return {
            "evidence_id": self.evidence_id,
            "evidence_class": self.evidence_class,
            "provenance": self.provenance,
            "reviewer_role": self.reviewer_role,
            "claim_ceiling": self.claim_ceiling,
            "supports": list(self.supports),
            "observed_facts": list(self.observed_facts),
            "unresolved_risks": list(self.unresolved_risks),
        }
