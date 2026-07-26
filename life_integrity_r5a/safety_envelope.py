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
import re
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

_UNSAFE_PATTERNS = (
    r"\bstop\s+(?:taking\s+)?(?:your\s+)?(?:prescribed\s+)?(?:medication|medicine|treatment|therapy)\b",
    r"\b(?:replace|substitute|abandon)\s+(?:your\s+)?(?:prescribed\s+)?(?:medication|treatment|therapy|care)\b",
    r"\bthis\s+replaces\s+your\s+(?:treatment|therapy|care)\b",
    r"\byou\s+(?:must|have\s+to)\s+(?:continue|comply)\b",
    r"停(?:止|用).{0,8}(?:处方药|药物|治疗|心理治疗)",
    r"(?:改用|只用|以此).{0,12}(?:代替|替代).{0,8}(?:处方药|药物|治疗|专业照护)",
    r"(?:不得|不许|不能).{0,6}(?:退出|拒绝|停止)",
)

EDUCATIONAL_STATUS_IDS = ("EDUCATIONAL_ONLY",)
RISK_SEVERITY_IDS = ("LOW", "MODERATE", "HIGH", "CRITICAL")
COERCION_RISK_IDS = ("NONE_IDENTIFIED", "LOW", "MEDIUM", "HIGH")
CARE_DISPOSITION_IDS = ("COORDINATE_WITH_PROFESSIONAL", "NO_EXISTING_CARE_CLAIM")
EVIDENCE_GRADE_IDS = ("SOFTWARE_CONTRACT_ONLY", "LOW", "MODERATE", "HIGH")


def contains_stop_treatment_language(text: str) -> bool:
    normalized = " ".join((text or "").casefold().split())
    return any(phrase in normalized for phrase in _STOP_PHRASES) or any(
        re.search(pattern, normalized, flags=re.IGNORECASE) is not None
        for pattern in _UNSAFE_PATTERNS
    )


def envelope_field_set_complete() -> bool:
    return len(REQUIRED_ENVELOPE_FIELDS) == 15


# --- Envelope validation (implemented in Commit 4) -------------------------
def validate_envelope(env: PracticeSafetyEnvelope) -> None:
    """Fail-closed practice/intervention safety-envelope validation.

    Every required field must be present and non-UNKNOWN; informed consent must
    be required; stop conditions, rollback/exit path and professional referral
    boundary must be declared; and the envelope must NOT recommend stopping
    prescribed treatment or substituting an unverified practice for professional
    care.
    """
    for field_name in REQUIRED_ENVELOPE_FIELDS:
        value = getattr(env, field_name)
        if isinstance(value, str):
            if not value.strip() or value.strip().upper() in {"UNKNOWN", "NOT_OBSERVED"}:
                raise EnvelopeIncompleteError(
                    f"missing required safety field: {field_name}"
                )
        elif isinstance(value, bool):
            if field_name == "informed_consent_required" and value is False:
                raise EnvelopeIncompleteError(
                    "informed_consent_required must be True for any intervention protocol"
                )
        elif isinstance(value, list):
            if field_name == "unknowns" and (
                len(value) == 0
                or any(not isinstance(item, str) or not item.strip() for item in value)
            ):
                raise EnvelopeIncompleteError(
                    "unknowns must enumerate at least one UNKNOWN"
                )

    if not env.informed_consent_required:
        raise EnvelopeIncompleteError("informed_consent_required must be True")
    if env.stop_conditions == "UNKNOWN":
        raise EnvelopeIncompleteError("stop_conditions required")
    if env.professional_referral_boundary == "UNKNOWN":
        raise EnvelopeIncompleteError("professional_referral_boundary required")
    if env.rollback_exit_path == "UNKNOWN":
        raise EnvelopeIncompleteError("rollback_exit_path required")

    if env.educational_vs_individualized not in EDUCATIONAL_STATUS_IDS:
        raise SafetyViolationError(
            "R5-A permits only EDUCATIONAL_ONLY envelope status; individualized intervention is not authorized"
        )
    if env.risk_severity not in RISK_SEVERITY_IDS:
        raise SafetyViolationError("risk_severity must use the closed set")
    if env.dependency_coercion_risk not in COERCION_RISK_IDS:
        raise SafetyViolationError("dependency_coercion_risk must use the closed set")
    if env.dependency_coercion_risk == "HIGH":
        raise SafetyViolationError("high dependency/coercion risk fails closed")
    if env.interaction_with_existing_care not in CARE_DISPOSITION_IDS:
        raise SafetyViolationError("interaction_with_existing_care must use the closed set")
    if env.evidence_grade not in EVIDENCE_GRADE_IDS:
        raise SafetyViolationError("evidence_grade must use the closed set")

    if contains_stop_treatment_language(env.raw_text):
        raise StopTreatmentRecommendationError(
            "envelope must not recommend stopping prescribed treatment or "
            "substituting an unverified practice for professional care"
        )
