# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Concept-mapping lifecycle (R5-A, Commit 1 skeleton).

Commit 1 provides the state closed set and transition-graph API. The
transition enforcement logic raises NotImplementedError and is implemented in
Commit 3.

Contract (task §8, §12): the closed lifecycle is UNMAPPED, SYMBOLIC_DESCRIPTION,
PHENOMENOLOGICAL_CANDIDATE, PRACTICE_FUNCTION_CANDIDATE, MECHANISM_HYPOTHESIS,
PARTIALLY_SUPPORTED, CONTRADICTED, UNKNOWN. Every transition requires an evidence
class, reviewer role, reversibility, superseded-interpretation handling,
contradiction handling, reason and receipt. Direct jumps from UNMAPPED or
SYMBOLIC_DESCRIPTION to PARTIALLY_SUPPORTED are forbidden. CONTRADICTED and
UNKNOWN remain first-class outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .evidence import EvidenceObject
from .registries import (
    CONCEPT_MAPPING_STATE_IDS,
    CONCEPT_MAPPING_TRANSITIONS,
    allowed_concept_transition,
    is_valid_concept_state,
)


class ConceptMappingError(Exception):
    """Base error for concept-mapping lifecycle violations."""


class InvalidConceptTransitionError(ConceptMappingError):
    """Raised when a transition is not in the allowed graph."""


class ForbiddenDirectJumpError(ConceptMappingError):
    """Raised when UNMAPPED/SYMBOLIC_DESCRIPTION jumps straight to PARTIALLY_SUPPORTED."""


class UnknownConceptStateError(ConceptMappingError):
    """Raised when a state is outside the closed set."""


class TransitionEvidenceError(ConceptMappingError):
    """Raised when evidence, reviewer, reversibility, or history does not match."""


@dataclass
class ConceptMapping:
    concept_id: str
    source_state: str
    current_state: str = ""
    transitions: list[dict[str, Any]] = field(default_factory=list)
    provenance: str = ""
    current_interpretation: str = ""
    superseded_interpretations: list[dict[str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.concept_id, str) or not self.concept_id.strip():
            raise ConceptMappingError("concept_id must be a non-blank string")
        if not is_valid_concept_state(self.source_state):
            raise UnknownConceptStateError(f"unknown state: {self.source_state!r}")
        if not self.current_state:
            self.current_state = self.source_state
        elif not is_valid_concept_state(self.current_state):
            raise UnknownConceptStateError(
                f"unknown current state: {self.current_state!r}"
            )
        if not isinstance(self.transitions, list):
            raise ConceptMappingError("transitions must be an array")


# --- Pure helpers (available in Commit 1, used by tests) -------------------
def concept_state_closed_set_complete() -> bool:
    return len(CONCEPT_MAPPING_STATE_IDS) == 8 and all(
        is_valid_concept_state(s) for s in CONCEPT_MAPPING_STATE_IDS
    )


def transition_graph_has_no_direct_jump_to_partially_supported() -> bool:
    """UNMAPPED and SYMBOLIC_DESCRIPTION must NOT have PARTIALLY_SUPPORTED as a
    direct allowed target."""
    direct = set(CONCEPT_MAPPING_TRANSITIONS.get("UNMAPPED", {})) | set(
        CONCEPT_MAPPING_TRANSITIONS.get("SYMBOLIC_DESCRIPTION", {})
    )
    return "PARTIALLY_SUPPORTED" not in direct


def direct_jump_forbidden(source_state: str) -> bool:
    return source_state in ("UNMAPPED", "SYMBOLIC_DESCRIPTION")


# --- Transition enforcement (implemented in Commit 3) ----------------------
def apply_transition(
    mapping: ConceptMapping,
    target_state: str,
    evidence_class: str,
    reviewer_role: str,
    reason: str,
    reversibility: bool = True,
    *,
    evidence_object: EvidenceObject | None = None,
    new_interpretation: str | None = None,
) -> None:
    """Apply a concept-mapping transition, fail-closed.

    Enforces the closed lifecycle: target must be valid; UNMAPPED /
    SYMBOLIC_DESCRIPTION may NOT jump directly to PARTIALLY_SUPPORTED; the
    transition must be in the allowed graph; every transition records the
    required evidence class, reviewer role, reversibility, contradiction
    handling, reason and receipt. CONTRADICTED and UNKNOWN remain first-class
    reachable outcomes.
    """
    if not is_valid_concept_state(target_state):
        raise UnknownConceptStateError(f"unknown target state: {target_state!r}")
    src = mapping.current_state
    if src == target_state:
        return  # idempotent, always allowed

    # Forbidden direct jump from an un-evidenced starting state to a supported
    # state without the intermediate evidence chain.
    if direct_jump_forbidden(src) and target_state == "PARTIALLY_SUPPORTED":
        raise ForbiddenDirectJumpError(
            f"direct jump {src} -> PARTIALLY_SUPPORTED forbidden without "
            f"intermediate evidence and review"
        )

    if not allowed_concept_transition(src, target_state):
        raise InvalidConceptTransitionError(
            f"transition not in allowed graph: {src} -> {target_state}"
        )

    meta = CONCEPT_MAPPING_TRANSITIONS[src][target_state]
    if evidence_class != meta["required_evidence_class"]:
        raise TransitionEvidenceError(
            f"provided evidence class {evidence_class!r} does not equal required "
            f"{meta['required_evidence_class']!r}"
        )
    if reviewer_role != meta["reviewer_role"]:
        raise TransitionEvidenceError(
            f"reviewer role {reviewer_role!r} does not equal required {meta['reviewer_role']!r}"
        )
    if reversibility is not meta["reversible"]:
        raise TransitionEvidenceError(
            "transition reversibility must equal the registry metadata"
        )
    if not isinstance(reason, str) or not reason.strip():
        raise TransitionEvidenceError("transition reason must be non-blank")
    if not isinstance(evidence_object, EvidenceObject):
        raise TransitionEvidenceError("transition requires a typed EvidenceObject")
    if evidence_object.evidence_class != evidence_class:
        raise TransitionEvidenceError(
            "evidence_object.evidence_class must equal the provided evidence class"
        )
    if evidence_object.reviewer_role != reviewer_role:
        raise TransitionEvidenceError(
            "evidence_object.reviewer_role must equal the transition reviewer role"
        )
    if not evidence_object.supports_all({f"transition:{src}->{target_state}"}):
        raise TransitionEvidenceError("evidence object does not support this exact transition")

    if new_interpretation is not None:
        if not isinstance(new_interpretation, str) or not new_interpretation.strip():
            raise TransitionEvidenceError("new_interpretation must be non-blank when provided")
        if mapping.current_interpretation:
            mapping.superseded_interpretations.append(
                {
                    "interpretation": mapping.current_interpretation,
                    "superseded_by_evidence_id": evidence_object.evidence_id,
                    "transition": f"{src}->{target_state}",
                }
            )
        mapping.current_interpretation = new_interpretation.strip()
    mapping.transitions.append(
        {
            "from": src,
            "to": target_state,
            "required_evidence_class": meta["required_evidence_class"],
            "provided_evidence_class": evidence_class,
            "reviewer_role": reviewer_role,
            "reversibility": reversibility,
            "contradiction_handling": meta["contradiction_handling"],
            "reason": reason,
            "evidence_id": evidence_object.evidence_id,
            "receipt": f"{mapping.concept_id}:{src}->{target_state}:{evidence_object.evidence_id}",
            "superseded_interpretations_preserved": len(mapping.superseded_interpretations),
        }
    )
    mapping.current_state = target_state
