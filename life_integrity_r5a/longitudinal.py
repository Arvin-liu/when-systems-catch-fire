# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Machine-readable longitudinal feedback and revision contract for R5-A.

This is a candidate data/validation contract only.  It does not schedule,
perform, recommend, or evaluate a real human intervention.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .evidence import EvidenceObject


REVISION_STATUS_IDS = ("ACTIVE", "REOPENED", "DEPRECATED", "RETIRED")
REOPEN_TRIGGER_IDS = (
    "NONE",
    "DELAYED_ADVERSE_OUTCOME",
    "CONSENT_WITHDRAWN",
    "CONTRADICTORY_EVIDENCE",
    "EVIDENCE_THRESHOLD_NOT_MET",
)
ROLLBACK_STATUS_IDS = ("NOT_ATTEMPTED", "SUCCEEDED", "PARTIAL", "FAILED")
REVISION_AUTHORITY_ROLE_IDS = ("E", "F", "H")
EVIDENCE_THRESHOLD_IDS = ("SOFTWARE_CONTRACT_ONLY", "INDEPENDENT_REVIEW_REQUIRED")


class LongitudinalContractError(ValueError):
    """Raised when a longitudinal revision record is incomplete or contradictory."""


def _parse_time(value: str, field_name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise LongitudinalContractError(f"{field_name} must be a non-blank ISO timestamp")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LongitudinalContractError(f"{field_name} must be an ISO timestamp") from exc


@dataclass(frozen=True)
class LongitudinalEvent:
    event_id: str
    observation_time: str
    review_time: str
    consent_autonomy_version: str
    evidence_chain_id: str
    short_term_benefit: str
    short_term_harm: str
    long_term_benefit: str
    long_term_harm: str
    rollback_status: str
    residual_harm_after_rollback: str
    evidence_object: EvidenceObject


@dataclass(frozen=True)
class LongitudinalRevisionContract:
    contract_id: str
    observation_time: str
    decision_time: str
    intervention_time: str
    review_time: str
    consent_autonomy_version: str
    evidence_chain_id: str
    reopen_trigger: str
    revision_status: str
    retirement_state: str
    revision_authority_role: str
    evidence_threshold: str
    events: tuple[LongitudinalEvent, ...]


def validate_longitudinal_contract(contract: LongitudinalRevisionContract) -> None:
    for field_name in ("contract_id", "consent_autonomy_version", "evidence_chain_id"):
        value = getattr(contract, field_name)
        if not isinstance(value, str) or not value.strip():
            raise LongitudinalContractError(f"{field_name} must be non-blank")

    observation = _parse_time(contract.observation_time, "observation_time")
    decision = _parse_time(contract.decision_time, "decision_time")
    intervention = _parse_time(contract.intervention_time, "intervention_time")
    review = _parse_time(contract.review_time, "review_time")
    if not observation < decision < intervention < review:
        raise LongitudinalContractError(
            "observation, decision, intervention, and review times must be distinct ordered fields"
        )
    if contract.reopen_trigger not in REOPEN_TRIGGER_IDS:
        raise LongitudinalContractError("reopen_trigger must use the closed set")
    if contract.revision_status not in REVISION_STATUS_IDS:
        raise LongitudinalContractError("revision_status must use the closed set")
    if contract.retirement_state not in REVISION_STATUS_IDS:
        raise LongitudinalContractError("retirement_state must use the closed set")
    if contract.revision_authority_role not in REVISION_AUTHORITY_ROLE_IDS:
        raise LongitudinalContractError("revision_authority_role must use the closed set")
    if contract.evidence_threshold not in EVIDENCE_THRESHOLD_IDS:
        raise LongitudinalContractError("evidence_threshold must use the closed set")
    if not contract.events:
        raise LongitudinalContractError("events must preserve at least one versioned event")
    if len({event.event_id for event in contract.events}) != len(contract.events):
        raise LongitudinalContractError("event ids must be unique and append-only")

    delayed_adverse = False
    consent_versions: list[str] = []
    for event in contract.events:
        if event.evidence_chain_id != contract.evidence_chain_id:
            raise LongitudinalContractError("event evidence chain must match the contract")
        if not isinstance(event.evidence_object, EvidenceObject):
            raise LongitudinalContractError("each event requires a typed EvidenceObject")
        if event.evidence_object.evidence_class != "longitudinal_observation":
            raise LongitudinalContractError(
                "longitudinal events require longitudinal_observation evidence"
            )
        event_observation = _parse_time(event.observation_time, "event.observation_time")
        event_review = _parse_time(event.review_time, "event.review_time")
        if event_observation > event_review:
            raise LongitudinalContractError("event review may not precede observation")
        if event.rollback_status not in ROLLBACK_STATUS_IDS:
            raise LongitudinalContractError("rollback_status must use the closed set")
        for field_name in (
            "short_term_benefit",
            "short_term_harm",
            "long_term_benefit",
            "long_term_harm",
            "residual_harm_after_rollback",
        ):
            value = getattr(event, field_name)
            if not isinstance(value, str) or not value.strip():
                raise LongitudinalContractError(f"event {field_name} must be explicit")
        consent_versions.append(event.consent_autonomy_version)
        delayed_adverse = delayed_adverse or (
            event.long_term_harm.strip().upper() not in {"NONE_OBSERVED", "NOT_YET_OBSERVED"}
        )

    if len(set(consent_versions)) != len(consent_versions):
        raise LongitudinalContractError(
            "consent/autonomy changes must create new immutable versions"
        )
    if delayed_adverse and (
        contract.reopen_trigger != "DELAYED_ADVERSE_OUTCOME"
        or contract.revision_status != "REOPENED"
    ):
        raise LongitudinalContractError(
            "a delayed adverse outcome must reopen the candidate explicitly"
        )
    if contract.revision_status in {"DEPRECATED", "RETIRED"} and contract.revision_authority_role != "H":
        raise LongitudinalContractError(
            "deprecation or retirement requires independent role H"
        )
