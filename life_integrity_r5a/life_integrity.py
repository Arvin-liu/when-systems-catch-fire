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

from .evidence import EvidenceObject
from .registries import EMBODIED_VIEW_IDS

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


class LocalOptimizationSafetyError(LifeIntegrityError):
    """Raised when a complete proposal violates a bounded safety invariant."""


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
    evidence_objects: list[EvidenceObject] = field(default_factory=list)


@dataclass
class LifeIntegrityAssessment:
    proposal: LocalOptimizationProposal | None = None
    notes: str = ""


class LifeIntegrityGate:
    """Enforces the whole-person non-totalization and local-optimization gates.

    R5-A validates the contract; it never activates a human intervention.
    """

    __slots__ = ()

    @property
    def activated(self) -> bool:
        """Compatibility projection; immutable and permanently false in R5-A."""
        return False

    def validate_proposal(self, proposal: LocalOptimizationProposal) -> None:
        """Fail-closed: a local-optimization proposal must disclose every required
        field. A proposal without these fields fails closed; the gate only
        validates the contract and must not execute the proposal."""
        if not isinstance(proposal.affected_views, list) or not proposal.affected_views:
            raise LocalOptimizationIncompleteError(
                "local-optimization proposal must declare affected_views as a non-empty list"
            )
        if len(set(proposal.affected_views)) != len(proposal.affected_views):
            raise LocalOptimizationIncompleteError("affected_views must not contain duplicates")
        if any(view not in EMBODIED_VIEW_IDS for view in proposal.affected_views):
            raise LocalOptimizationIncompleteError(
                "affected_views must use the exact seven-view closed set"
            )
        for field_name in LOCAL_OPTIMIZATION_FIELDS:
            if field_name == "affected_views":
                continue
            value = getattr(proposal, field_name)
            if (
                not isinstance(value, str)
                or not value.strip()
                or value.strip().upper() in {"UNKNOWN", "NOT_OBSERVED"}
            ):
                raise LocalOptimizationIncompleteError(
                    f"local-optimization proposal omits required disclosure: {field_name}"
                )

        if proposal.consent_autonomy_status not in {
            "INFORMED_VOLUNTARY",
            "NOT_APPLICABLE_EDUCATIONAL",
        }:
            raise LocalOptimizationSafetyError(
                "consent_autonomy_status must be informed/voluntary or explicitly educational"
            )
        if proposal.reversibility not in {"REVERSIBLE", "PARTIALLY_REVERSIBLE"}:
            raise LocalOptimizationSafetyError(
                "local optimization must be reversible or partially reversible"
            )

        text = " ".join(
            getattr(proposal, name) for name in LOCAL_OPTIMIZATION_FIELDS if name != "affected_views"
        ).casefold()
        blocked_fragments = (
            "assumed consent",
            "consent is assumed",
            "no opt out",
            "never stop",
            "catastrophic residual harm",
            "guaranteed benefit",
            "zero uncertainty",
            "默认同意",
            "不得退出",
            "永不停止",
        )
        if any(fragment in text for fragment in blocked_fragments):
            raise LocalOptimizationSafetyError(
                "proposal contains a bounded coercion, false-certainty, or severe-harm signal"
            )

        required_support = set(LOCAL_OPTIMIZATION_FIELDS)
        risk_reviews = [
            item
            for item in proposal.evidence_objects
            if isinstance(item, EvidenceObject)
            and item.evidence_class == "local_optimization_risk_review"
        ]
        if not risk_reviews or not any(
            item.supports_all(required_support) for item in risk_reviews
        ):
            raise LocalOptimizationIncompleteError(
                "a typed local_optimization_risk_review evidence object must support every disclosure"
            )
        if any(item.unresolved_risks for item in risk_reviews):
            raise LocalOptimizationSafetyError(
                "local optimization has unresolved risks in its evidence object"
            )

    def validate_assessment(self, assessment: LifeIntegrityAssessment) -> None:
        if assessment.proposal is not None:
            self.validate_proposal(assessment.proposal)


def local_optimization_field_set_complete() -> bool:
    return len(LOCAL_OPTIMIZATION_FIELDS) == 11
