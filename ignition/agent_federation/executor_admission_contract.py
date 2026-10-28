"""Provider-neutral admission decisions for bounded synthetic read-only runs."""

from __future__ import annotations

from typing import Any, Mapping


AGENTIC_FAMILY = "AGENTIC_EXECUTOR"
ELIGIBLE = "ELIGIBLE_FOR_LIVE_READONLY"
GATES = (
    "public_auth",
    "auth_separation",
    "argv_contract",
    "structured_result",
    "workspace",
    "capture",
    "validator_binding",
    "cleanup",
    "permission_ceiling",
    "exact_binding",
    "no_effect_scope",
)
PASS_VALUES = {
    "public_auth": {"PASS"},
    "auth_separation": {"PROVEN"},
    "argv_contract": {"STRICT"},
    "structured_result": {"STRICT"},
    "workspace": {"PROVEN"},
    "capture": {"PROVEN"},
    "validator_binding": {"PROVEN"},
    "cleanup": {"PROVEN"},
    "permission_ceiling": {"PROVEN"},
    "exact_binding": {"PROVEN"},
    "no_effect_scope": {"PROVEN"},
}


class AdmissionContractError(ValueError):
    """Raised when a candidate is not a safe provider-neutral record."""


def classify_family(value: Any) -> str:
    if value not in {"AGENTIC_EXECUTOR", "REASONER_RUNTIME", "TOOL", "UI_SURFACE"}:
        raise AdmissionContractError(f"unknown executor class: {value!r}")
    return str(value)


def evaluate_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deterministic admission decision without probing or invoking."""

    if not isinstance(candidate, Mapping):
        raise AdmissionContractError("candidate must be a mapping")
    family = classify_family(candidate.get("family"))
    blockers = list(candidate.get("blockers", []))
    mismatches: list[str] = []
    if candidate.get("class_separation") != family:
        mismatches.append("class_separation")
    if family != AGENTIC_FAMILY:
        mismatches.append("family_not_live_eligible")
    for gate in GATES:
        if candidate.get(gate) not in PASS_VALUES[gate]:
            mismatches.append(gate)
    if blockers:
        mismatches.extend(f"blocker:{item}" for item in blockers)
    eligible = not mismatches
    return {
        "executor_id": candidate.get("executor_id"),
        "family": family,
        "decision": ELIGIBLE if eligible else "BLOCKED",
        "blockers": sorted(set(mismatches)),
        "side_effect_scope": "SYNTHETIC_READ_ONLY_NO_CHANNEL_BROWSER_REMOTE_GIT_CONFIG_OR_BILLING",
        "child_spawn": "DENY",
        "claim_ceiling": "Admission decision is repository-local and does not prove invocation, completion, external truth or production safety.",
    }


def validate_contract_shape(contract: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if contract.get("candidate_taxonomy") != ["AGENTIC_EXECUTOR", "REASONER_RUNTIME", "TOOL", "UI_SURFACE"]:
        errors.append("candidate taxonomy is not provider-neutral")
    if contract.get("required_gates") != list(GATES):
        errors.append("required gate order or names differ from the admission contract")
    policy = contract.get("live_policy", {})
    if policy.get("max_attempts_total") != 2 or policy.get("max_attempts_per_family") != 1:
        errors.append("live attempt bound is not two total and one per family")
    if policy.get("stop_on_first_validated_completion") is not True:
        errors.append("stop-on-first-validated-completion policy is missing")
    for candidate in contract.get("candidates", []):
        decision = evaluate_candidate(candidate)
        declared = candidate.get("live_eligibility")
        if declared == ELIGIBLE and decision["decision"] != ELIGIBLE:
            errors.append(f"candidate {candidate.get('executor_id')} claims eligibility despite blockers")
        if declared != ELIGIBLE and decision["decision"] == ELIGIBLE:
            errors.append(f"candidate {candidate.get('executor_id')} omits an eligible declaration")
    return errors


__all__ = ["AdmissionContractError", "ELIGIBLE", "GATES", "classify_family", "evaluate_candidate", "validate_contract_shape"]
