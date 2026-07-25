# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Life Integrity Gate and local-optimization contract (R5-A, Commit 1 skeleton).

Commit 1 provides the local-optimization disclosure field closed set and the
gate API. The validation logic raises NotImplementedError and is implemented in
Commit 4.

Contract (task §4, §5.2, §12): any future proposal that optimizes one dimension
must disclose intended benefit, affected views, short-term effects, long-term
effects, externalities/tradeoffs, uncertainty, consent/autonomy status,
reversibility, stop conditions, referral boundary and residual harm after
rollback. A proposal without these fields fails closed. R5-A validates the
contract only; it must NOT execute the proposal.
"""

from __future__ import annotations

from dataclasses import dataclass, field

LOCAL_OPTIMIZATION_FIELDS = (
    "intended_benefit",
    "affected_views",
    "short_term_effects",
    "long_term_effects",
    "externalities_tradeoffs",
    "uncertainty",
    "consent_autonomy_status",
    "reversibility",
    "stop_conditions",
    "referral_boundary",
    "residual_harm_after_rollback",
)


class LifeIntegrityError(Exception):
    """Base error for life-integrity gate violations."""


class LocalOptimizationIncompleteError(LifeIntegrityError):
    """Raised when a local-optimization proposal omits required disclosures."""


@dataclass
class LocalOptimizationProposal:
    intended_benefit: str = "UNKNOWN"
    affected_views: list[str] = field(default_factory=list)
    short_term_effects: str = "UNKNOWN"
    long_term_effects: str = "UNKNOWN"
    externalities_tradeoffs: str = "UNKNOWN"
    uncertainty: str = "UNKNOWN"
    consent_autonomy_status: str = "UNKNOWN"
    reversibility: str = "UNKNOWN"
    stop_conditions: str = "UNKNOWN"
    referral_boundary: str = "UNKNOWN"
    residual_harm_after_rollback: str = "UNKNOWN"


@dataclass
class LifeIntegrityAssessment:
    proposal: LocalOptimizationProposal | None = None
    notes: str = ""


class LifeIntegrityGate:
    """Enforces the whole-person non-totalization and local-optimization gates.

    R5-A validates the contract; it never activates a human intervention.
    """

    def __init__(self) -> None:
        self.activated = False  # R5-A never sets this True

    def validate_proposal(self, proposal: LocalOptimizationProposal) -> None:
        """Fail-closed: a local-optimization proposal must disclose every required
        field. A proposal without these fields fails closed; the gate only
        validates the contract and must not execute the proposal."""
        if proposal.affected_views is None or len(proposal.affected_views) == 0:
            raise LocalOptimizationIncompleteError(
                "local-optimization proposal must declare affected_views"
            )
        for field_name in LOCAL_OPTIMIZATION_FIELDS:
            if field_name == "affected_views":
                continue
            value = getattr(proposal, field_name)
            if value is None or value == "UNKNOWN" or value == "":
                raise LocalOptimizationIncompleteError(
                    f"local-optimization proposal omits required disclosure: {field_name}"
                )

    def validate_assessment(self, assessment: LifeIntegrityAssessment) -> None:
        if assessment.proposal is not None:
            self.validate_proposal(assessment.proposal)


def local_optimization_field_set_complete() -> bool:
    return len(LOCAL_OPTIMIZATION_FIELDS) == 11
