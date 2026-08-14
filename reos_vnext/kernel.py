"""Pure operations over the R1 REOS case document.

All mutators return a new document.  Callers decide when to persist the new
document; Git remains the durable recovery/history mechanism for this round.
"""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .contract import (
    ActivationDecision,
    ArtifactRefRecord,
    ClaimCandidate,
    EvidenceRequest,
    HandoffBundle,
    QuestionContract,
    REOS_LIGHT,
    ResearchCase,
    ResearchObligation,
    ReviewDecision,
    ReviewRequest,
    SCHEMA_VERSION,
)
from .validation import (
    ContractError,
    ValidationIssue,
    canonical_json,
    sha256_json,
    validate_case,
    validate_handoff,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "as_dict"):
        return copy.deepcopy(value.as_dict())
    if not isinstance(value, Mapping):
        raise TypeError("REOS record must be a mapping or frozen contract object")
    return copy.deepcopy(dict(value))


def new_case(
    *,
    case_id: str,
    mode: str = REOS_LIGHT,
    activation_reason: str,
    observed_need: list[str] | tuple[str, ...],
    simpler_baseline: str,
    unnecessary_modules: list[str] | tuple[str, ...],
    preregistration_ref: str,
    preregistration_digest: str,
    frozen_validation_summary: Mapping[str, Any],
    budget_contract: Mapping[str, Any],
    stop_conditions: list[str] | tuple[str, ...],
    owner_boundary: str = "GPT_OWNER_REVIEW_ONLY",
) -> dict[str, Any]:
    summary = copy.deepcopy(dict(frozen_validation_summary))
    summary_digest = sha256_json(summary)
    question = QuestionContract(
        preregistration_ref=preregistration_ref,
        preregistration_digest=preregistration_digest,
        frozen_validation_summary=summary,
        current_validation_summary=summary,
        initial_validation_summary_digest=summary_digest,
        validation_summary_digest=summary_digest,
    )
    activation = ActivationDecision(
        mode=mode,
        reason=activation_reason,
        observed_need=tuple(observed_need),
        simpler_baseline=simpler_baseline,
        unnecessary_modules=tuple(unnecessary_modules),
    )
    case = ResearchCase(
        case_id=case_id,
        activation=activation,
        question_contract=question,
        owner_boundary=owner_boundary,
        budget_contract=copy.deepcopy(dict(budget_contract)),
        stop_conditions=tuple(stop_conditions),
    )
    document = case.as_document()
    validate_case(document)
    return document


def load_case(path: str | Path) -> dict[str, Any]:
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_case(document)
    return document


def serialize_case(document: Mapping[str, Any]) -> str:
    validate_case(document)
    return canonical_json(document) + "\n"


def save_case(path: str | Path, document: Mapping[str, Any]) -> None:
    Path(path).write_text(serialize_case(document), encoding="utf-8")


def _append(document: Mapping[str, Any], field: str, value: Any) -> dict[str, Any]:
    result = copy.deepcopy(dict(document))
    result["case"][field].append(_dict(value))
    validate_case(result)
    return result


def add_obligation(document: Mapping[str, Any], obligation: ResearchObligation | Mapping[str, Any]) -> dict[str, Any]:
    return _append(document, "obligations", obligation)


def record_artifact(document: Mapping[str, Any], artifact: ArtifactRefRecord | Mapping[str, Any]) -> dict[str, Any]:
    return _append(document, "artifact_refs", artifact)


def record_evidence_request(document: Mapping[str, Any], request: EvidenceRequest | Mapping[str, Any]) -> dict[str, Any]:
    return _append(document, "evidence_requests", request)


def record_claim_candidate(document: Mapping[str, Any], claim: ClaimCandidate | Mapping[str, Any]) -> dict[str, Any]:
    return _append(document, "claim_candidates", claim)


def request_review(document: Mapping[str, Any], request: ReviewRequest | Mapping[str, Any]) -> dict[str, Any]:
    entry = {"request": _dict(request), "decision": None}
    return _append(document, "reviews", entry)


def record_review(
    document: Mapping[str, Any],
    decision: ReviewDecision | Mapping[str, Any],
    repair_obligations: list[ResearchObligation | Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    validate_case(document)
    result = copy.deepcopy(dict(document))
    decision_record = _dict(decision)
    review_id = decision_record.get("review_id")
    entries = result["case"]["reviews"]
    matching = [entry for entry in entries if entry.get("request", {}).get("review_id") == review_id]
    if len(matching) != 1:
        raise ContractError(
            [
                ValidationIssue("UNKNOWN_REF", "$.case.reviews", "review decision has no unique request")
            ]
        )
    if repair_obligations:
        for repair in repair_obligations:
            result = add_obligation(result, repair)
            decision_record.setdefault("repair_obligation_ids", []).append(_dict(repair)["obligation_id"])
    for entry in result["case"]["reviews"]:
        if entry.get("request", {}).get("review_id") == review_id:
            entry["decision"] = decision_record
            break
    validate_case(result)
    return result


def amend_question(
    document: Mapping[str, Any],
    *,
    frozen_validation_summary: Mapping[str, Any],
    reason: str,
    amendment_id: str,
) -> dict[str, Any]:
    validate_case(document)
    result = copy.deepcopy(dict(document))
    question = result["case"]["question_contract"]
    new_summary = copy.deepcopy(dict(frozen_validation_summary))
    current_digest = question["validation_summary_digest"]
    next_digest = sha256_json(new_summary)
    question["current_validation_summary"] = new_summary
    question["validation_summary_digest"] = next_digest
    question["version"] += 1
    question["amendments"].append(
        {
            "amendment_id": amendment_id,
            "from_digest": current_digest,
            "to_digest": next_digest,
            "reason": reason,
            "version": question["version"],
        }
    )
    validate_case(result)
    return result


def set_case_state(document: Mapping[str, Any], state: str) -> dict[str, Any]:
    result = copy.deepcopy(dict(document))
    result["case"]["case_state"] = state
    validate_case(result)
    return result


def compute_case_status(document: Mapping[str, Any]) -> str:
    """Return an operational disposition without inferring truth."""

    validate_case(document)
    case = document["case"]
    if case["case_state"] != "OPEN":
        return case["case_state"]
    evidence_states = {request["retrieval_state"] for request in case["evidence_requests"]}
    if "BLOCKED" in evidence_states:
        return "BLOCKED_BY_EVIDENCE_ACCESS"
    for review in case["reviews"]:
        decision = review.get("decision")
        if decision and decision.get("verdict") == "MATERIAL_REPAIR_REQUIRED":
            repairs = set(decision.get("repair_obligation_ids", []))
            satisfied = {
                obligation["obligation_id"]
                for obligation in case["obligations"]
                if obligation.get("status") in {"SATISFIED_WITH_SCOPE", "SATISFIED_WITH_RESIDUALS", "CLOSED_NO_RESULT"}
            }
            if not repairs or not repairs.issubset(satisfied):
                return "OPEN_WITH_REPAIR_OBLIGATIONS"
    if any(obligation.get("status") in {"OPEN", "READY", "WAITING_DEPENDENCY", "WAITING_REVIEW", "BLOCKED_TOOL_OR_ACCESS"} for obligation in case["obligations"]):
        return "OPEN"
    if case["reviews"]:
        if any(review.get("decision", {}).get("residuals") for review in case["reviews"] if review.get("decision")):
            return "HANDOFF_READY_WITH_EXPLICIT_RESIDUALS"
        return "HANDOFF_READY_WITH_BOUNDED_RESULTS"
    return "OPEN"


def prepare_handoff(
    document: Mapping[str, Any],
    *,
    bundle_id: str,
    bundle_type: str,
    receiving_authority: str,
    object_refs: list[str] | tuple[str, ...],
    allowed_claims: list[str] | tuple[str, ...],
    noncanonical_status: str,
    scope: str,
    prohibited_inference: list[str] | tuple[str, ...],
    residuals: list[str] | tuple[str, ...],
    independent_review_required: bool = True,
) -> dict[str, Any]:
    validate_case(document)
    case = document["case"]
    known = {
        case["case_id"],
        *[item["obligation_id"] for item in case["obligations"]],
        *[item["artifact_id"] for item in case["artifact_refs"]],
        *[item["candidate_id"] for item in case["claim_candidates"]],
        *[item["request"]["review_id"] for item in case["reviews"]],
    }
    unknown = sorted(set(object_refs) - known)
    if unknown:
        raise ContractError([ValidationIssue("UNKNOWN_REF", "$.object_refs", f"unknown handoff refs: {unknown}")])
    bundle = HandoffBundle(
        bundle_id=bundle_id,
        bundle_type=bundle_type,
        receiving_authority=receiving_authority,
        object_refs=tuple(object_refs),
        allowed_claims=tuple(allowed_claims),
        noncanonical_status=noncanonical_status,
        scope=scope,
        prohibited_inference=tuple(prohibited_inference),
        residuals=tuple(residuals),
        independent_review_required=independent_review_required,
    ).as_dict()
    validate_handoff(bundle)
    return bundle


def status_snapshot(document: Mapping[str, Any]) -> dict[str, Any]:
    validate_case(document)
    case = document["case"]
    return {
        "schema_version": SCHEMA_VERSION,
        "case_id": case["case_id"],
        "declared_case_state": case["case_state"],
        "computed_status": compute_case_status(document),
        "obligation_count": len(case["obligations"]),
        "artifact_ref_count": len(case["artifact_refs"]),
        "evidence_request_count": len(case["evidence_requests"]),
        "claim_candidate_count": len(case["claim_candidates"]),
        "review_count": len(case["reviews"]),
    }
