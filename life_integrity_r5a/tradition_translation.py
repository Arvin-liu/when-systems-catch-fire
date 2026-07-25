# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Traditional / religious material translation contract (R5-A, Commit 1 skeleton).

Commit 1 provides the schema and closed-set claim-class registry API. The
deep validation logic raises NotImplementedError and is implemented in
Commit 3.

Contract (task §3, §7, §12): each translated claim carries provenance,
translation status, attribution, claim class, interpretation layer, evidence
grade, mechanism status, applicability, rights boundary, confidence, UNKNOWNs,
prohibited upgrades and revision history. Five upgrades are forbidden without
separately linked empirical evidence and independent review:
  PHENOMENOLOGICAL_REPORT -> EMPIRICALLY_SUPPORTED_MECHANISM
  METAPHYSICAL_CLAIM -> SCIENTIFIC_FACT
  PRACTICE_PROTOCOL -> CLINICAL_EFFICACY
  LATER_INTERPRETATION -> AUTHOR_INTENT
  HISTORICAL_LONGEVITY -> EFFECTIVENESS
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .registries import (
    TRADITION_CLAIM_CLASS_IDS,
    TRADITION_FORBIDDEN_TRANSITIONS,
    is_forbidden_tradition_upgrade,
    is_valid_claim_class,
)


class TraditionTranslationError(Exception):
    """Base error for tradition-translation contract violations."""


class UnknownClaimClassError(TraditionTranslationError):
    """Raised when a claim class is outside the closed set."""


class ForbiddenClaimUpgradeError(TraditionTranslationError):
    """Raised when a claim attempts a forbidden silent upgrade."""


@dataclass
class TranslatedClaim:
    source_provenance: str
    source_language: str
    translation_status: str
    attribution_status: str
    claim_class: str
    literal_reference: str = ""
    interpretation_layer: str = ""
    evidence_grade: str = "UNKNOWN"
    mechanism_status: str = "NOT_ASSERTED"
    applicability_scope: str = "UNKNOWN"
    rights_boundary: str = ""
    confidence: float = 0.0
    unknowns: list[str] = field(default_factory=list)
    prohibited_upgrades: list[str] = field(default_factory=list)
    revision_history: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not is_valid_claim_class(self.claim_class):
            raise UnknownClaimClassError(f"unknown claim class: {self.claim_class!r}")


# --- Pure predicates (available in Commit 1, used by tests) ----------------
def forbidden_upgrade_set() -> frozenset[tuple[str, str]]:
    return TRADITION_FORBIDDEN_TRANSITIONS


def claim_class_closed_set_complete() -> bool:
    return len(TRADITION_CLAIM_CLASS_IDS) == 8 and all(
        is_valid_claim_class(c) for c in TRADITION_CLAIM_CLASS_IDS
    )


# --- Deep validation (implemented in Commit 3) -----------------------------
def validate_claim_class_strict(claim_class: str) -> None:  # pragma: no cover
    raise NotImplementedError(
        "tradition_translation.validate_claim_class_strict implemented in Commit 3"
    )


def check_forbidden_upgrade_strict(from_status: str, to_status: str) -> None:  # pragma: no cover
    raise NotImplementedError(
        "tradition_translation.check_forbidden_upgrade_strict implemented in Commit 3"
    )


def translate_claim(
    source_provenance: str,
    claim_class: str,
    **kwargs: Any,
) -> TranslatedClaim:  # pragma: no cover
    raise NotImplementedError("tradition_translation.translate_claim implemented in Commit 3")
