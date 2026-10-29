# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Life Integrity Annex Candidate (R5-A, implemented Commit 2).

The annex sits BENEATH the Life Community Value Charter. It is a candidate
governance node, not a competing supreme charter, L7 layer, parallel truth
system, or replacement executor. It carries the user-authorized anti-
fragmentation principle and the set of invariants R5-A governs.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .registries import CHARTER_HIERARCHY, SUPREME_CHARTER

USER_AUTHORIZED_PRINCIPLE = (
    "性命一体，身心互成。点火在认识、评价和干预人时，不得将人的生理、心理、"
    "行为、关系、环境与意义系统彼此割裂；任何局部优化，都必须接受完整生命、"
    "长期反馈、主体同意、风险边界与可逆性的共同检验。"
)

# What the principle must NOT be represented as (task §3).
PRINCIPLE_NOT_AUTHORIZED_AS = (
    "proof of a metaphysical mind-body theory",
    "a scientific discovery attributed to Zhang Boduan",
    "evidence that South-School practices are effective in clinical terms",
    "authorization to offer individual medical/psychiatric/therapeutic advice",
    "a claim that all religions are equally true or scientifically supported",
)


@dataclass
class LifeIntegrityAnnexCandidate:
    title: str = "Life Integrity Annex Candidate"
    hierarchy_position: int = 1  # directly beneath the supreme charter (index 0)
    principle: str = USER_AUTHORIZED_PRINCIPLE
    not_authorized_as: tuple[str, ...] = PRINCIPLE_NOT_AUTHORIZED_AS
    activation_status: str = "CANDIDATE_ONLY"
    invariants: tuple[str, ...] = (
        "whole_person_non_totalization",
        "local_optimization_gate",
        "experience_mechanism_efficacy_separation",
        "historical_interpretation_boundary",
        "safety_consent_professional_boundary",
        "tests_are_not_human_evidence",
    )


def annex_beneath_supreme_charter() -> bool:
    """The annex must be the immediate child of the supreme charter and must not
    displace it."""
    if CHARTER_HIERARCHY[0] != SUPREME_CHARTER:
        return False
    if CHARTER_HIERARCHY[1] != "LifeIntegrityAnnexCandidate":
        return False
    if LifeIntegrityAnnexCandidate().activation_status != "CANDIDATE_ONLY":
        return False
    return True
