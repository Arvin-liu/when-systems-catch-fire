"""Frozen, deliberately small REOS vNext R1 object vocabulary.

These dataclasses describe nested records in one case document.  They are not
canonical Foundation objects and do not carry epistemic authority.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

SCHEMA_VERSION = "reos.vnext.minimal-kernel.r1"
SERIALIZATION_VERSION = "canonical-json-v1"

DIRECT_RESEARCH = "DIRECT_RESEARCH"
REOS_LIGHT = "REOS_LIGHT"
REOS_FULL = "REOS_FULL"
MODES = frozenset({DIRECT_RESEARCH, REOS_LIGHT, REOS_FULL})

CASE_STATES = frozenset(
    {
        "OPEN",
        "OPEN_WITH_REPAIR_OBLIGATIONS",
        "HANDOFF_READY_WITH_BOUNDED_RESULTS",
        "HANDOFF_READY_WITH_EXPLICIT_RESIDUALS",
        "BLOCKED_BY_EVIDENCE_ACCESS",
        "NOT_IDENTIFIABLE_WITH_AVAILABLE_EVIDENCE",
        "STOPPED_BY_BUDGET_OR_SCOPE",
        "REQUIRES_QUESTION_REFORMULATION",
        "NO_INCREMENTAL_VALUE_OBSERVED",
        "ABSTAINED",
    }
)

OBLIGATION_STATES = frozenset(
    {
        "OPEN",
        "READY",
        "WAITING_DEPENDENCY",
        "WAITING_REVIEW",
        "BLOCKED_TOOL_OR_ACCESS",
        "SATISFIED_WITH_SCOPE",
        "SATISFIED_WITH_RESIDUALS",
        "ABSTAINED",
        "CLOSED_NO_RESULT",
    }
)

EVIDENCE_STATES = frozenset(
    {
        "REQUESTED",
        "CANDIDATE_FOUND",
        "FULLTEXT_RECOVERED",
        "PARTIAL_ACCESS",
        "METADATA_ONLY",
        "SOURCE_NOT_RECOVERED",
        "SOURCE_IDENTITY_AMBIGUOUS",
        "BLOCKED",
        "NOT_APPLICABLE",
    }
)

REVIEW_VERDICTS = frozenset(
    {
        "PASS_WITHIN_QUESTION_SCOPE",
        "PASS_WITH_EXPLICIT_RESIDUALS",
        "MATERIAL_REPAIR_REQUIRED",
        "BLOCKED_MISSING_INPUT",
        "ABSTAIN",
        "DISAGREEMENT_REQUIRES_ADJUDICATION",
    }
)

PRIVACY_CLASSES = frozenset({"PRIVATE", "INTERNAL", "PUBLIC_SAFE_CANDIDATE", "PUBLIC"})
OWNER_BOUNDARIES = frozenset({"GPT_OWNER_REVIEW_ONLY"})


def _clean(value: Any) -> Any:
    """Convert dataclasses and tuples into JSON-compatible structures."""

    if hasattr(value, "as_dict"):
        return value.as_dict()
    if isinstance(value, tuple):
        return [_clean(item) for item in value]
    if isinstance(value, list):
        return [_clean(item) for item in value]
    if isinstance(value, dict):
        return {key: _clean(item) for key, item in value.items()}
    return value


@dataclass(frozen=True)
class ActivationDecision:
    mode: str
    reason: str
    observed_need: tuple[str, ...] = ()
    simpler_baseline: str = ""
    unnecessary_modules: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return _clean(asdict(self))


@dataclass(frozen=True)
class QuestionContract:
    """External preregistration pointer plus the minimum frozen gate summary.

    The full preregistration remains outside the REOS case.  Amendments chain
    only the compact validation summary digest.
    """

    preregistration_ref: str
    preregistration_digest: str
    frozen_validation_summary: Mapping[str, Any]
    current_validation_summary: Mapping[str, Any]
    initial_validation_summary_digest: str
    validation_summary_digest: str
    version: int = 1
    amendments: tuple[Mapping[str, Any], ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return _clean(asdict(self))


@dataclass(frozen=True)
class ResearchObligation:
    obligation_id: str
    type: str
    question_ref: str
    depends_on: tuple[str, ...] = ()
    inputs: tuple[str, ...] = ()
    required_capabilities: tuple[str, ...] = ()
    permission_scope: str = "ordinary-research"
    completion_contract: str = ""
    stop_fail_conditions: tuple[str, ...] = ()
    status: str = "OPEN"
    output_artifact_refs: tuple[str, ...] = ()
    review_required: bool = False

    def as_dict(self) -> dict[str, Any]:
        return _clean(asdict(self))


@dataclass(frozen=True)
class ArtifactRefRecord:
    artifact_id: str
    ref: str
    sha256: str
    provenance: Mapping[str, Any]
    scope: str
    privacy_class: str
    source_family: str = ""
    derivation_refs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return _clean(asdict(self))


@dataclass(frozen=True)
class EvidenceRequest:
    request_id: str
    obligation_id: str
    question: str
    desired_evidence_type: str
    source_family_requirement: str
    retrieval_state: str = "REQUESTED"
    access_limitation: str = ""
    result_artifact_ids: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return _clean(asdict(self))


@dataclass(frozen=True)
class ClaimCandidate:
    candidate_id: str
    proposition: str
    scope: str
    supporting_artifact_ids: tuple[str, ...] = ()
    contradicting_artifact_ids: tuple[str, ...] = ()
    alternative_explanations: tuple[str, ...] = ()
    measurement_definition: str = ""
    claim_ceiling: str = ""
    uncertainty: tuple[str, ...] = ()
    foundation_handoff_route: str = "Foundation L1 candidate route"
    canonical_status: str = "NONCANONICAL"

    def as_dict(self) -> dict[str, Any]:
        return _clean(asdict(self))


@dataclass(frozen=True)
class ReviewRequest:
    review_id: str
    named_question: str
    input_refs: tuple[str, ...]
    independence_requirement: str
    forbidden_assumptions: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return _clean(asdict(self))


@dataclass(frozen=True)
class ReviewDecision:
    review_id: str
    reviewer_ref: str
    exact_input_refs: tuple[str, ...]
    independent: bool
    verdict: str
    material_findings: tuple[str, ...] = ()
    repair_obligation_ids: tuple[str, ...] = ()
    residuals: tuple[str, ...] = ()
    scope_ceiling: str = ""

    def as_dict(self) -> dict[str, Any]:
        return _clean(asdict(self))


@dataclass(frozen=True)
class HandoffBundle:
    bundle_id: str
    bundle_type: str
    receiving_authority: str
    object_refs: tuple[str, ...]
    allowed_claims: tuple[str, ...]
    noncanonical_status: str
    scope: str
    prohibited_inference: tuple[str, ...]
    residuals: tuple[str, ...]
    independent_review_required: bool = True

    def as_dict(self) -> dict[str, Any]:
        return _clean(asdict(self))


@dataclass(frozen=True)
class ResearchCase:
    case_id: str
    activation: ActivationDecision
    question_contract: QuestionContract
    owner_boundary: str
    budget_contract: Mapping[str, Any]
    stop_conditions: tuple[str, ...]
    case_state: str = "OPEN"
    obligations: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)
    artifact_refs: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)
    evidence_requests: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)
    claim_candidates: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)
    reviews: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)

    def as_document(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "case": _clean(asdict(self)),
        }
