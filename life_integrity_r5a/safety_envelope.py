# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Practice / intervention safety-envelope contract (R5-A, Commit 1 skeleton).

Commit 1 provides the required-field closed set and the stop-treatment language
detector API. The envelope validation logic raises NotImplementedError and is
implemented in Commit 4.

Contract (task §5.5, §12): any future practice/intervention protocol concerning
health, psychology, sleep, diet, breath, meditation, exercise or altered states
must declare educational vs individualized status, intended population, exclusion
criteria, contraindications, risk severity, informed-consent requirement,
dependency/coercion risk, stop conditions, rollback/exit path, professional
referral boundary, emergency boundary, interaction with existing care, evidence
grade, UNKNOWNs and long-term follow-up. The contract must REJECT language that
encourages users to stop prescribed treatment or substitute an unverified
practice for professional care.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

REQUIRED_ENVELOPE_FIELDS = (
    "educational_vs_individualized",
    "intended_population",
    "exclusion_criteria",
    "contraindications",
    "risk_severity",
    "informed_consent_required",
    "dependency_coercion_risk",
    "stop_conditions",
    "rollback_exit_path",
    "professional_referral_boundary",
    "emergency_boundary",
    "interaction_with_existing_care",
    "evidence_grade",
    "unknowns",
    "long_term_followup_plan",
)


class SafetyEnvelopeError(Exception):
    """Base error for safety-envelope contract violations."""


class EnvelopeIncompleteError(SafetyEnvelopeError):
    """Raised when a required safety field is missing."""


class StopTreatmentRecommendationError(SafetyEnvelopeError):
    """Raised when a protocol encourages stopping prescribed treatment."""


class SafetyViolationError(SafetyEnvelopeError):
    """Raised for any other fail-closed safety violation."""


@dataclass
class PracticeSafetyEnvelope:
    educational_vs_individualized: str = "UNKNOWN"
    intended_population: str = "UNKNOWN"
    exclusion_criteria: str = "UNKNOWN"
    contraindications: str = "UNKNOWN"
    risk_severity: str = "UNKNOWN"
    informed_consent_required: bool = False
    dependency_coercion_risk: str = "UNKNOWN"
    stop_conditions: str = "UNKNOWN"
    rollback_exit_path: str = "UNKNOWN"
    professional_referral_boundary: str = "UNKNOWN"
    emergency_boundary: str = "UNKNOWN"
    interaction_with_existing_care: str = "UNKNOWN"
    evidence_grade: str = "UNKNOWN"
    unknowns: list[str] = field(default_factory=list)
    long_term_followup_plan: str = "UNKNOWN"
    raw_text: str = ""


# --- Stop-treatment language detection (pure, available in Commit 1) --------
_STOP_PHRASES = (
    "stop taking", "stop your", "discontinue", "replace your", "substitute for",
    "instead of your prescribed", "stop prescribed", "quit your medication",
    "replace prescribed", "stop the medication", "come off your",
)


def contains_stop_treatment_language(text: str) -> bool:
    lowered = (text or "").lower()
    return any(phrase in lowered for phrase in _STOP_PHRASES)


def envelope_field_set_complete() -> bool:
    return len(REQUIRED_ENVELOPE_FIELDS) == 15


# --- Envelope validation (implemented in Commit 4) -------------------------
def validate_envelope(env: PracticeSafetyEnvelope) -> None:  # pragma: no cover
    raise NotImplementedError("safety_envelope.validate_envelope implemented in Commit 4")
